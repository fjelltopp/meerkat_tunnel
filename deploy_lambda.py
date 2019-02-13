import boto3
import os
import argparse
import sys


def upload_deployment_package(lambda_function, pkg, country):
    ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", None)
    SECRET_KEY = os.environ.get("AWS_SECRET_KEY", None)

    region_name = 'eu-west-1'

    if ACCESS_KEY and SECRET_KEY:
        print("Reading AWS access keys from env")
        s3_client = boto3.client('s3',
                                 aws_access_key_id=ACCESS_KEY,
                                 aws_secret_access_key=SECRET_KEY,
                                 region_name=region_name)
        lambda_client = boto3.client('lambda',
                                     aws_access_key_id=ACCESS_KEY,
                                     aws_secret_access_key=SECRET_KEY,
                                     region_name=region_name)
    else:
        print("Reading AWS access keys from default config")
        s3_client = boto3.client('s3', region_name=region_name)
        lambda_client = boto3.client('lambda', region_name=region_name)

    s3_bucket = 'meerkat-tunnel-' + country
    s3_key = '{0}.zip'.format(lambda_function)
    function_name = '{0}_{1}'.format(country, lambda_function)

    s3_client.upload_file(pkg, s3_bucket, s3_key)

    lambda_client.update_function_code(
        FunctionName=function_name,
        S3Bucket=s3_bucket,
        S3Key=s3_key,
        Publish=True
    )

    print('Deployment package {0} deployed as AWS Lambda function {1}'.format(pkg, function_name))


def make_deployment_package(lambda_function, python_version):
    # copy packages
    cwd = os.getcwd()

    if os.path.isdir('{0}/{1}_env/lib/{2}/site-packages'.format(cwd, lambda_function, python_version)):
        packages = os.listdir('{0}/{1}_env/lib/{2}/site-packages'.format(cwd, lambda_function, python_version))
        os.system('cp -r {0}/{1}_env/lib/{2}/site-packages/* {0}/{1}'.format(cwd, lambda_function, python_version))
    else:
        packages = []
    if os.path.isdir('{0}/{1}_env/lib64/{2}/site-packages'.format(cwd, lambda_function, python_version)):
        packages64 = os.listdir('{0}/{1}_env/lib64/{2}/site-packages'.format(cwd, lambda_function, python_version))
        os.system('cp -r {0}/{1}_env/lib64/{2}/site-packages/* {0}/{1}'.format(cwd, lambda_function, python_version))
    else:
        packages64 = []
    os.system('mkdir -p {0}/lambda_packages'.format(cwd))
    os.system('rm -f {0}/lambda_packages/{1}.zip'.format(cwd, lambda_function))

    # change directory to zip on correct folder level
    os.chdir('{0}/{1}'.format(cwd, lambda_function))
    os.system('zip -q {0}/lambda_packages/{1}.zip {1}.py'.format(cwd, lambda_function))

    for pkg in packages:
        os.system('zip -q -r {0}/lambda_packages/{1}.zip {2}'.format(cwd, lambda_function, pkg))
        os.system('rm -r {0}/{1}/{2}'.format(cwd, lambda_function, pkg))

    for pkg64 in packages64:
        os.system('zip -q -r {0}/lambda_packages/{1}.zip {2}'.format(cwd, lambda_function, pkg64))
        os.system('rm -r {0}/{1}/{2}'.format(cwd, lambda_function, pkg64))

    # go back to original working directory
    os.chdir(cwd)

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