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

    def prepare_payload(self, payload):
        t = json.loads(payload['body'].replace("'", '"'))
        submission = t['text'].split(";")

        if submission[-1] == '':
            submission.pop(-1)

        form_id = submission.pop(0)

        form_columns = submission[0::2]
        form_values = submission[1::2]

        form_content = {}

        for i in range(len(form_columns)):
            form_content[form_columns[i]] = form_values[i]

        return {'form_id': form_id,
                'data': form_content}

    def get_form_definition(self, aggregate_url, form_id):
        form_url = "{}/formXml".format(aggregate_url)

        form_response = requests.get(form_url, params={'formId': form_id})

        form_xml = form_response.text

        form_definition = et.fromstring(form_xml)

        return form_definition

def lambda_handler(event, context):
    #logger.info('got event{}'.format(event))
    translator = SmsSubmissionConverter()

    payload = translator.prepare_payload(event)

    aggregate_url = os.environ.get('AGGREGATE_URL')

    form_definition = translator.get_form_definition(aggregate_url, payload['form_id'])

    logger.info('form xml {}'.format(str(form_definition)))
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
