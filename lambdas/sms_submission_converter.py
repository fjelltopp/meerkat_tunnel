import collections
import json
import logging
import os
import time

import boto3
import requests
import xmltodict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SmsSubmissionConverter:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def store_multi_sms_payload(self, payload):
        body = json.loads(payload['body'])
        ref = body['concat-ref']
        total = body['concat-total']
        part = body['concat-part']
        text = body['text']
        client = boto3.client('dynamodb')
        client.put_item(
            Item={
                'ref': {
                    'S': ref,
                },
                'total': {
                    'N': total,
                },
                'part': {
                    'S': part,
                },
                'text': {
                    'S': text,
                },
                'receivedTime': {
                    'S': str(time.strftime("%Y-%m-%d %H:%M %Z"))
                }
            },
            ReturnConsumedCapacity='TOTAL',
            TableName='SmsParts',
        )
        r = client.update_item(
            TableName='SmsReceived',
            Key={
                'ref': {
                    'S': ref
                }
            },
            ExpressionAttributeNames={
                '#count': "count"
            },
            UpdateExpression='ADD #count :inc',
            ExpressionAttributeValues={
                ':inc': {'N': '1'}
            },
            ReturnValues="UPDATED_NEW"
        )
        received_count = int(r['Attributes']['count']['N'])
        is_complete = received_count == int(total)
        logger.info(f"Counter: received {received_count}, total {total}, is_complete {is_complete}")
        return ref, total, part, is_complete

    def is_multi_sms_payload(self, payload):
        logger.info(f"Got2: {payload}")
        body = json.loads(payload['body'])
        return body.get('concat', '').lower() == 'true'

    def prepare_single_sms_payload(self, payload):
        body = json.loads(payload['body'])
        return body['text']

    def format_payload(self, text):
        logger.info(f"Got: {text}")
        submission = text.split(";")

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
        form_definition = xmltodict.parse(form_xml)

        return form_definition

    def payload_json_to_xml(self, form_definition, prepared_payload):
        form_id = prepared_payload['form_id']
        ids_map = self._short_to_long_field_names(form_definition, form_id)
        submission_dict = self._submission_to_ordered_dict(ids_map, prepared_payload)
        xml_str = self._to_xml_string(form_id, submission_dict)
        return xml_str

    def _to_xml_string(self, form_id, submission_dict):
        xml_dict = dict()
        xml_dict[form_id] = submission_dict
        xml_str = xmltodict.unparse(xml_dict)
        xml_str = xml_str.replace(f"<{form_id}>", f"<{form_id} id=\"{form_id}\">", 1)
        return xml_str

    def _submission_to_ordered_dict(self, ids_map, prepared_payload):
        submission_dict = collections.OrderedDict()
        for name, value in prepared_payload['data'].items():
            if name == 'form_id':
                continue
            field_name = ids_map[name]['fieldName']
            group_name = ids_map[name]['groupName']
            if group_name:
                if group_name not in submission_dict:
                    submission_dict[group_name] = collections.OrderedDict()
                submission_dict[group_name][field_name] = value
            else:
                submission_dict[field_name] = value
        return submission_dict

    def _short_to_long_field_names(self, form_definition, form_id):
        form_instance = form_definition['h:html']['h:head']['model']['instance']
        if isinstance(form_instance, list):
            form_fields = form_instance[0][form_id]
        else:
            form_fields = form_instance[form_id]
        ids_map = dict()
        for key, field in form_fields.items():
            try:
                short_id = field['@odk:tag']
                ids_map[short_id] = {
                    "fieldName": key,
                    "groupName": '',
                }
            except (KeyError, TypeError):
                pass
            if not isinstance(field, collections.OrderedDict):
                continue
            for child_key, child in field.items():
                if isinstance(child, collections.OrderedDict):
                    try:
                        short_id = child['@odk:tag']
                        ids_map[short_id] = {
                            "fieldName": child_key,
                            "groupName": key
                        }
                    except (KeyError, TypeError):
                        pass
        return ids_map


    def get_complete_multi_sms_payload(self, ref):
        client = boto3.client('dynamodb')
        response = client.query(TableName='SmsParts',
                                ExpressionAttributeValues={':ref_value': {'S': str(ref)}},
                                ExpressionAttributeNames={'#ref_alias': 'ref'},
                                KeyConditionExpression='#ref_alias = :ref_value'
                                )
        return ''.join([part['text']['S'] for part in response['Items']])


def lambda_handler(event, context):
    translator = SmsSubmissionConverter()
    is_multi_sms = translator.is_multi_sms_payload(event)
    if is_multi_sms:
        logger.info("Multi part sms submission.")
        ref, total, part, is_complete = translator.store_multi_sms_payload(event)
        if is_complete:
            logger.info("Multi part sms submission is complete.")
            raw_payload = translator.get_complete_multi_sms_payload(ref)
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "success"})
            }
    else:
        logger.info("Single sms submission.")
        raw_payload = translator.prepare_single_sms_payload(event)

    payload = translator.format_payload(raw_payload)
    aggregate_url = os.environ.get('AGGREGATE_URL')

    form_definition = translator.get_form_definition(aggregate_url, payload['form_id'])
    submission_xml = translator.payload_json_to_xml(form_definition, payload)

    files = {'xml_submission_file': ('form.xml', submission_xml, "text/xml")}
    r = requests.post(aggregate_url + "/submission", files=files)

    logger.info(f'Send submission to aggregate with code {r.status_code}')
    return {
        'statusCode': 200,
        'body': json.dumps({"message": "success"})
    }

if __name__ == '__main__':
    s = SmsSubmissionConverter()
    fd = s.get_form_definition("https://odk.car.fjelltopp.org", "d_test")
    print(fd)