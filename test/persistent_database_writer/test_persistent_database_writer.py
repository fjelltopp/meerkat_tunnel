import unittest
import json
from unittest.mock import MagicMock, call

import uuid

uuid.uuid4 = MagicMock(return_value='test-uuid-1234')

from test_data.upload_payload import upload_payload
import lambdas.persistent_database_writer as persistent_database_writer


class PersistentDatabaseWriter(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.writer = persistent_database_writer.PersistentDatabaseWriter()

        persistent_database_writer.uuid.uuid4 = MagicMock(return_value='test-uuid-1234')

        self.event = {
            'queue': 'nest-test-queue-subscriber-id',
            'dead-letter-queue': 'nest-test-dead-letter-queue'
        }

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

        # Call data storage function
        self.writer.store_data_entries()

    def test_receiving_messages(self):
        self.assertTrue(self.writer.sqs_client.receive_message.called)
        read_queue_call = call(QueueUrl='aws:nest-test-queue-url')
        self.writer.sqs_client.receive_message.assert_has_calls([read_queue_call])

    def test_database_insert(self):
        # self.assertTrue(self.writer.session.add.called)

        table_name = 'dem_test'

        # new_row = self.writer.tables[table_name](uuid='test-uuid-1234', data=upload_payload['data'][0])
        # database_insert_calls = [call(new_row)]

        # TODO: Compare database insert calls
        # for insert_call in self.writer.session.add.call_args_list:
        #     self.assertTrue(insert_call[0][0].uuid == 'test-uuid-1234')
        #     self.assertTrue(insert_call[0][0].data == upload_payload['data'][0])
