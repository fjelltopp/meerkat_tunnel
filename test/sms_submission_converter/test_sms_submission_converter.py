"""
Lambda SMS Converter Test
"""

import unittest
from unittest import mock
from unittest.mock import MagicMock, call
import datetime
import boto3

from lambdas.sms_submission_converter import SmsSubmissionConverter

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

xml_form_str = """
<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:odk="http://www.opendatakit.org/xforms" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head><!-- ODK Aggregate upload time: 2019-03-01T09:39:02.184+0000 on https://odk.car.fjelltopp.org -->
    <h:title>Simple test form</h:title>
    <model>
      <instance>
        <sms_test_form id="sms_test_form" odk:delimiter=";" odk:prefix="d_test" version="1">
          <start/>
          <end/>
          <today/>
          <deviceid odk:tag="did"/>
          <subscriberid/>
          <simid/>
          <phonenumber/>
          <note_title/>
          <yesno odk:tag="yn"/>
          <howmany odk:tag="hm"/>
          <meta>
            <instanceID/>
          </meta>
        </sms_test_form>
      </instance>
      <bind jr:preload="timestamp" jr:preloadParams="start" nodeset="/sms_test_form/start" type="dateTime"/>
      <bind jr:preload="timestamp" jr:preloadParams="end" nodeset="/sms_test_form/end" type="dateTime"/>
      <bind jr:preload="date" jr:preloadParams="today" nodeset="/sms_test_form/today" type="date"/>
      <bind jr:preload="property" jr:preloadParams="deviceid" nodeset="/sms_test_form/deviceid" type="string"/>
      <bind jr:preload="property" jr:preloadParams="subscriberid" nodeset="/sms_test_form/subscriberid" type="string"/>
      <bind jr:preload="property" jr:preloadParams="simserial" nodeset="/sms_test_form/simid" type="string"/>
      <bind jr:preload="property" jr:preloadParams="phonenumber" nodeset="/sms_test_form/phonenumber" type="string"/>
      <bind nodeset="/sms_test_form/note_title" readonly="true()" type="string"/>
      <bind nodeset="/sms_test_form/yesno" type="select1"/>
      <bind nodeset="/sms_test_form/howmany" type="int"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/sms_test_form/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/sms_test_form/note_title">
      <label>## Simple test form</label>
    </input>
    <select1 ref="/sms_test_form/yesno">
      <label>Yes or no?</label>
      <item>
        <label>No</label>
        <value>no</value>
      </item>
      <item>
        <label>Yes</label>
        <value>yes</value>
      </item>
    </select1>
    <input ref="/sms_test_form/howmany">
      <label>How many?</label>
    </input>
  </h:body>
</h:html>
"""

class SmsSubmissionConverterTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.event = test_payload
        self.form_id = 'sms_test_form'
        self.aggregate_url = 'https://odk.car.fjelltopp.org'
        self.converter = SmsSubmissionConverter()

    def test_preparing_payload(self):
        prepared_payload = self.converter.prepare_payload(self.event)
        
    def test_fetching_form_definition(self):
        form_definition = self.converter.get_form_definition(self.aggregate_url, self.form_id)