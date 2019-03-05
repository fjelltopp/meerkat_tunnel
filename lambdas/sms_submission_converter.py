import collections
import json
import logging
import requests
import os
import xmltodict

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
        form_definition = xmltodict.parse(form_xml)

        return form_definition

    def payload_json_to_xml(self, form_definition, prepared_payload):
        ids_map = self._short_to_long_field_names(form_definition)
        submission_dict = self._submission_to_ordered_dict(ids_map, prepared_payload)
        form_id = prepared_payload['form_id']
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

    def _short_to_long_field_names(self, form_definition):
        form_fields = form_definition['h:html']['h:head']['model']['instance']['sms_test_form']
        ids_map = dict()
        for key, field in form_fields.items():
            print(key)
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


def lambda_handler(event, context):
    #logger.info('got event{}'.format(event))
    translator = SmsSubmissionConverter()

    payload = translator.prepare_payload(event)

    aggregate_url = os.environ.get('AGGREGATE_URL')

    form_definition = translator.get_form_definition(aggregate_url, payload['form_id'])

    logger.info('form xml {}'.format(str(form_definition)))
    logger.info(f'payload: {payload}')
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


