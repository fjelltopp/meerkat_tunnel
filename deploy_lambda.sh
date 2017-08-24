#!/bin/bash
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
    esac
done

echo "Running Deploy Lambda with parameters:" 
echo "Function $FUNCTION" 
echo "country $COUNTRY" 
echo "python interpreter $PYTHON_INTERPRETER"
git checkout master
git pull origin master
pip install virtualenv
virtualenv -p $PYTHON_INTERPRETER ${FUNCTION}_env
source ${FUNCTION}_env/bin/activate
pip install -r ${FUNCTION}/requirements.txt
$PYTHON_INTERPRETER deploy_lambda.py $FUNCTION -c $COUNTRY -p python2.7
