import boto3
import os
import argparse

def upload_deployment_package(function, package):
    pass


def make_deployment_package(function, python_version):
    cwd = os.getcwd()
    # os.chdir(cwd+'/meerkat_tunnel')
    os.system('git checkout master')
    os.system('git pull origin master')
    #os.chdir('~')

    os.system('virtualenv -p /usr/bin/{0} {1}_env'.format(python_version, function))
    os.system('source {0}/{1}_env/bin/activate'.format(cwd, function))
    os.system('pip install -r ~/meerkat_tunnel/{0}/requirements.txt'.format(function))
    os.system('cp {0}/{1}_env/lib/{2}/site_packages/* {0}/meerkat_tunnel/{1}/'.format(cwd, function, python_version))
    os.system('mkdir -p {0}/lambda_packages'.format(cwd))
    os.system('rm -f {0}/lambda_packages/{1}.zip'.format(cwd, function))
    os.system('zip -r {0}lambda_packages/{1}.zip {0}/meerkat_tunnel/{1}'.format(cwd,function))
    return 'foo'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Meerkat Tunnel Lambda functions')
    parser.add_argument('function', type=str, help='name of Lambda function to deploy')
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