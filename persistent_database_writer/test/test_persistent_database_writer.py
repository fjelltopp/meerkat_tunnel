import unittest
import json
from unittest.mock import MagicMock

from persistent_database_writer.test.test_data.upload_payload import upload_payload

import persistent_database_writer.persistent_database_writer


class PersistentDatabaseWriter(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.writer = persistent_database_writer.persistent_database_writer.PersistentDatabaseWriter()

        self.event = {
            'queue': 'nest-test-queue-subscriber-id',
            'dead-letter-queue': 'nest-test-dead-letter-queue'
        }

        self.writer.session.add = MagicMock(return_value={})
        self.writer.session.commit = MagicMock(return_value={})

        self.writer.sts_client.get_caller_identity = MagicMock(return_value={
            'Account': 'test-account'
        })

        self.writer.sqs_client.get_queue_url = MagicMock(return_value={
            'QueueUrl': 'aws:nest-test-queue-url'
        })
        self.writer.sqs_client.send_message = MagicMock(return_value={
            'MD5OfMessageBody': 'test-md5',
            'MD5OfMessageAttributes': 'test-md5',
            'MessageId': 'test-message-id',
            'SequenceNumber': 'test-sequence-number'
        })
        self.writer.sqs_client.receive_message = MagicMock(return_value={
            'Messages': [
                {
                    'MessageId': 'test-message-id-1',
                    'ReceiptHandle': 'test-receipt-handle-1',
                    'MD5OfBody': 'test-md5-1',
                    'Body': json.dumps(upload_payload),
                    'Attributes': {
                        'test-attribute': 'test-attribute-value'
                    }
                },
                {
                    'MessageId': 'test-message-id-2',
                    'ReceiptHandle': 'test-receipt-handle-2',
                    'MD5OfBody': 'test-md5-2',
                    'Body': json.dumps(upload_payload),
                    'Attributes': {
                        'test-attribute': 'test-attribute-value'
                    }
                }
            ]
        })
        self.writer.sqs_client.delete_message = MagicMock(return_value=None)

        self.writer.store_data_entry(self.event)

    def test_database_insert(self):
        self.assertTrue(self.writer.session.add.called)