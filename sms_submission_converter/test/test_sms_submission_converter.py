"""
Lambda SMS Converter Test
"""

import unittest
from unittest.mock import MagicMock, call
import datetime
import boto3

import sms_submission_converter

test_payload = {
  "resource": "/smsHandler",
  "path": "/smsHandler",
  "httpMethod": "POST",
  "headers": {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Host": "x57wu2xbrc.execute-api.eu-west-1.amazonaws.com",
    "User-Agent": "Jakarta Commons-HttpClient/3.1",
    "X-Amzn-Trace-Id": "Root=1-5c52f5ca-f970744ac0a1baf684939358",
    "X-Forwarded-For": "169.63.86.167",
    "X-Forwarded-Port": "443",
    "X-Forwarded-Proto": "https"
  },
  "multiValueHeaders": {
    "Accept": [
      "*/*"
    ],
    "Content-Type": [
      "application/json"
    ],
    "Host": [
      "x57wu2xbrc.execute-api.eu-west-1.amazonaws.com"
    ],
    "User-Agent": [
      "Jakarta Commons-HttpClient/3.1"
    ],
    "X-Amzn-Trace-Id": [
      "Root=1-5c52f5ca-f970744ac0a1baf684939358"
    ],
    "X-Forwarded-For": [
      "169.63.86.167"
    ],
    "X-Forwarded-Port": [
      "443"
    ],
    "X-Forwarded-Proto": [
      "https"
    ]
  },
  "queryStringParameters": None,
  "multiValueQueryStringParameters": None,
  "pathParameters": None,
  "stageVariables": None,
  "requestContext": {
    "resourceId": "z1mv99",
    "resourcePath": "/smsHandler",
    "httpMethod": "POST",
    "extendedRequestId": "UXtXkHWjDoEFaFA=",
    "requestTime": "31/Jan/2019:13:19:06 +0000",
    "path": "/default/smsHandler",
    "accountId": "856481977980",
    "protocol": "HTTP/1.1",
    "stage": "default",
    "domainPrefix": "x57wu2xbrc",
    "requestTimeEpoch": 1548940746091,
    "requestId": "c8fe6482-255a-11e9-aed9-e7d23fbdae96",
    "identity": {
      "cognitoIdentityPoolId": None,
      "accountId": None,
      "cognitoIdentityId": None,
      "caller": None,
      "sourceIp": "169.63.86.167",
      "accessKey": None,
      "cognitoAuthenticationType": None,
      "cognitoAuthenticationProvider": None,
      "userArn": None,
      "userAgent": "Jakarta Commons-HttpClient/3.1",
      "user": None
    },
    "domainName": "x57wu2xbrc.execute-api.eu-west-1.amazonaws.com",
    "apiId": "x57wu2xbrc"
  },
  "body": "{'msisdn':'358123123123','to':'37282720102','messageId':'16000002645683B9','text':'d_test;did;356123123123123;yn;no;hm;123;','type':'text','keyword':'D_TEST','message-timestamp':'2019-01-31 13:19:05'}",
  "isBase64Encoded": False
}


class SmsSubmissionConverterTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.event = test_payload
        self.form_id = 'car_case'
        self.aggregate_url = 'https://odk.car.fjelltopp.org'
        self.converter = sms_submission_converter.SmsSubmissionConverter()

    def test_preparing_payload(self):
        prepared_payload = self.converter.prepare_payload(self.event)
        
    def test_fetching_form_definition(self):
        form_definition = self.converter.get_form_definition(self.aggregate_url, self.form_id)