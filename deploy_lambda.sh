#!/bin/bash
set -e
FUNCTION="$1"
COUNTRY="$2"
PYTHON_INTERPRETER="$3"

# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
PYTHON_INTERPRETER="/usr/bin/python3"

while getopts "h?p:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    p)  PYTHON_INTERPRETER=$OPTARG
        ;;
    d)  PULL_DEPENDENCIES=$OPTARG
    esac
done

echo "Running Deploy Lambda with parameters:" 
echo "Function $FUNCTION" 
echo "country $COUNTRY" 
echo "python interpreter $PYTHON_INTERPRETER"
#git checkout master
#git pull origin master
mkdir -p venvs
pip3 install virtualenv
$PYTHON_INTERPRETER -m venv venvs/${FUNCTION}_env
source venvs/${FUNCTION}_env/bin/activate
pip install -r requirements/${FUNCTION}_requirements.txt

echo "Requirements installed, do you want to deploy the Lambda function $FUNCTION to $COUNTRY after building the deployment package?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) python deploy_lambda.py $FUNCTION -c $COUNTRY; break;;
        No ) python deploy_lambda.py $FUNCTION -c $COUNTRY -n; break;;
    esac
done
