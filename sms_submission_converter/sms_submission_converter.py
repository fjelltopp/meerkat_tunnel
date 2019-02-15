import boto3
import json
import logging
import requests
import os
import xml.etree.ElementTree as et

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SmsSubmissionConverter:
    def __init__(self):
        region_name = 'eu-west-1'


        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    #logger.info('got event{}'.format(event))

    payload = event['body']['text']

    submission = payload.split(";")

    form_id = submission.pop(0)

    form_columns = submission[0::2]
    form_values = submission[1::2]

    data = {}
    for i in range(0, len(form_columns)):
        data[form_columns[i]] = form_values[i]

    logger.info('data {}'.format(str(data)))

    form_xml = requests.get(os.environ.get("aggregate_url") + "/formXml",
                               params={"formId": form_id})



    logger.info('form xml {}'.format(str(form_xml)))
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
