#import boto3
import os
import argparse

def upload_deployment_package(function, package):
    print("We got this far!")


def make_deployment_package(function, python_version):
    cwd = os.getcwd()
    packages = os.listdir('{0}/{1}_env/lib/{2}/site-packages'.format(cwd, function, python_version))
    os.system('cp -r {0}/{1}_env/lib/{2}/site-packages/* {0}/{1}'.format(cwd, function, python_version))
    os.system('mkdir -p {0}/lambda_packages'.format(cwd))
    os.system('rm -f {0}/lambda_packages/{1}.zip'.format(cwd, function))
    os.system('zip -q -r {0}/lambda_packages/{1}.zip {0}/{1}'.format(cwd, function))

    # cleanup copied packages
    for pkg in packages:
        os.system('rm -r {0}/{1}/{2}'.format(cwd, function, pkg))
    return 'foo'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Meerkat Tunnel Lambda functions')
    parser.add_argument('function', type=str, help='name of Lambda function to deploy')
    parser.add_argument('-c', type=str, help='name of the country to deploy the functions to', default='demo')
    #parser.add_argument('-d', '--dependencies', type=str, help='path to dependencies directory', default='')
    parser.add_argument('-p', '--python_version', type=str, help='python interpreter version to use',
                        default='python35')

    args = parser.parse_args()
    print(vars(args))
    function = vars(args)['function']
    package = make_deployment_package(function=function,
                                      python_version=vars(args)['python_version'])
    upload_deployment_package(function=function,
                              package=package)