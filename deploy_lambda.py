import boto3
import botocore
import os
import argparse
import sys


def upload_deployment_package(lambda_function, pkg, country):
    ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", None)
    SECRET_KEY = os.environ.get("AWS_SECRET_KEY", None)
    REGION_NAME = os.environ.get("AWS_REGION_NAME", 'eu-west-1')

    if ACCESS_KEY and SECRET_KEY:
        print("Reading AWS access keys from env")
        region_name = REGION_NAME
        kwargs = {
            'aws_access_key_id': ACCESS_KEY,
            'aws_secret_access_key': SECRET_KEY,
            'region_name': region_name
        }
    else:
        print("Reading AWS access keys from default config")
        session = boto3.session.Session()
        region_name = session.region_name
        kwargs = {
            'region_name': region_name
        }
    s3_client = boto3.client('s3', **kwargs)
    s3 = boto3.resource('s3')
    lambda_client = boto3.client('lambda', **kwargs)

    bucket_name = f'meerkat-tunnel-{country}'
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': region_name
                }
            )
    s3_key = '{0}.zip'.format(lambda_function)
    function_name = '{0}_{1}'.format(country, lambda_function)

    s3_client.upload_file(pkg, bucket_name, s3_key)

    lambda_client.update_function_code(
        FunctionName=function_name,
        S3Bucket=bucket_name,
        S3Key=s3_key,
        Publish=True
    )

    print('Deployment package {0} deployed as AWS Lambda function {1}'.format(pkg, function_name))


def make_deployment_package(lambda_function, python_version):
    # copy packages
    cwd = os.getcwd()

    site_packages_lib_format = '{0}/venvs/{1}_env/lib/{2}/site-packages'.format(cwd, lambda_function, python_version)
    site_packages_lib64_format = '{0}/venvs/{1}_env/lib64/{2}/site-packages'.format(cwd, lambda_function, python_version)
    if os.path.isdir(site_packages_lib_format):
        packages = os.listdir(site_packages_lib_format)
    else:
        packages = []
    if os.path.isdir(site_packages_lib64_format):
        packages64 = os.listdir(site_packages_lib64_format)
    else:
        packages64 = []
    os.system('mkdir -p {0}/lambda_packages'.format(cwd))
    os.system('rm -f {0}/lambda_packages/{1}.zip'.format(cwd, lambda_function))

    os.system('zip -q {0}/lambda_packages/{1}.zip lambdas/{1}.py'.format(cwd, lambda_function))

    for pkg in packages:
        pkg_path = os.path.join(site_packages_lib_format, pkg)
        os.system('zip -q -r {0}/lambda_packages/{1}.zip {2}'.format(cwd, lambda_function, pkg_path))

    for pkg64 in packages64:
        pkg64_path = os.path.join(site_packages_lib_format, pkg64)
        os.system('zip -q -r {0}/lambda_packages/{1}.zip {2}'.format(cwd, lambda_function, pkg64_path))

    print('Deployment package {0}.zip created'.format(lambda_function))
    return '{0}/lambda_packages/{1}.zip'.format(cwd, lambda_function)


parser = argparse.ArgumentParser(description='Deploy Meerkat Tunnel Lambda functions')
parser.add_argument('function', type=str, help='name of Lambda function to deploy')
parser.add_argument('-c', '--country', type=str, help='name of the country to deploy the Lambda function to',
                    default='demo')
parser.add_argument('-p', '--python_interpreter', type=str, help='python interpreter version to use',
                    default='/usr/bin/python')
parser.add_argument('-n', '--noupload', help='create deployment packages but upload nothing',
                    action='store_true', default=False)


# Main method for executing args
def main(orig_args):

    args = parser.parse_args()

    lambda_function = args.function
    python_version = 'python{0}'.format(sys.version[:3])
    package = make_deployment_package(lambda_function=lambda_function,
                                      python_version=python_version)
    if not args.noupload:
        upload_deployment_package(lambda_function=lambda_function,
                                  pkg=package,
                                  country=vars(args)['country'])


if __name__ == '__main__':
    main(sys.argv[1:])