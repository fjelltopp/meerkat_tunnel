"""
Lambda SMS Converter Test
"""

import unittest
from unittest.mock import MagicMock, call
import datetime
import boto3

import sms_submission_converter


class SmsSubmissionConverterTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.event = {
            'queue': 'nest-test-queue',
            'dead-letter-queue': 'nest-test-dead-letter-queue'
        }
        self.converter = sms_submission_converter.sms_submission_converter.SmsSubmissionConverter()