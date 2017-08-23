import boto3
import os
import argparse

def upload_deployment_package(function, package):
    pass


def make_deployment_package(function, python_version):
    os.system('virtualenv -p /usr/bin/' + python_version + ' meerkat_tunnel_env')
    os.system('source ~/meerkat_tunnel_env/bin/activate')
    os.system('pip install -r ~/meerkat_tunnel/' + function + '/requirements.txt')
    os.system('cp ~/meerkat_tunnel_env/lib/' + python_version + '/site_packages/* ' +
              '~/meerkat_tunnel/' + function + '/')
    os.system('mkdir -p ~/lambda_packages')
    os.system('rm -f ~/lambda_packages/' + function + '.zip')
    os.system('zip -r ~lambda_packages/' + function + '.zip ~/meerkat_tunnel/' + function)
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