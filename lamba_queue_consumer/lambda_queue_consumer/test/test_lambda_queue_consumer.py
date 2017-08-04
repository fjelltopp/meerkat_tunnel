"""
Lambda Queue Consumer Test
"""

import unittest
from unittest.mock import MagicMock, call

import lambda_queue_consumer.lambda_queue_consumer


class LambdaQueueConsumerTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.event = {
            'queue': 'nest-test-queue',
            'dead-letter-queue': 'nest-test-dead-letter-queue'
        }
        self.consumer = lambda_queue_consumer.lambda_queue_consumer.LambdaQueueConsumer()
        self.consumer.sts_client.get_caller_identity = MagicMock(return_value={
            'Account': 'test-account'
        })

        self.consumer.sqs_client.create_queue = MagicMock(return_value={
            'QueueUrl': 'aws:nest-test-queue-url'
        })
        self.consumer.sqs_client.get_queue_url = MagicMock(return_value={
            'QueueUrl': 'aws:nest-test-queue-url'
        })
        self.consumer.sqs_client.send_message = MagicMock(return_value={
            'MD5OfMessageBody': 'test-md5',
            'MD5OfMessageAttributes': 'test-md5',
            'MessageId': 'test-message-id',
            'SequenceNumber': 'test-sequence-number'
        })
        self.consumer.sqs_client.receive_message = MagicMock(return_value={
            'Messages': [
                {
                    'MessageId': 'test-message-id-1',
                    'ReceiptHandle': 'test-receipt-handle-1',
                    'MD5OfBody': 'test-md5-1',
                    'Body': 'test-body-1',
                    'Attributes': {
                        'test-attribute': 'test-attribute-value'
                    }
                },
                {
                    'MessageId': 'test-message-id-2',
                    'ReceiptHandle': 'test-receipt-handle-2',
                    'MD5OfBody': 'test-md5-2',
                    'Body': 'test-body-2',
                    'Attributes': {
                        'test-attribute': 'test-attribute-value'
                    }
                }
            ]
        })
        self.consumer.sqs_client.delete_message = MagicMock(return_value=None)

        self.consumer.sns_client.create_topic = MagicMock(return_value={
            'TopicArn': 'arn:aws:sns:eu-west-1:test-account:nest-test-topic'
        })
        self.consumer.sns_client.publish = MagicMock(return_value={
            'MessageId': 'test-message-id'
        })
        self.consumer.sns_client.list_subscriptions_by_topic = MagicMock(return_value={
            'Subscriptions': [
                {
                    'SubscriptionArn':
                        'arn:aws:sns:eu-west-1:458315597956:nest-test-notifier:0a314486-a412-40c3-ae62-8c1b00btest1',
                    'Owner': 'test-owner',
                    'Protocol': 'email',
                    'Endpoint': 'soppela.jyri@gmail.com',
                    'TopicArn': 'arn:aws:sns:eu-west-1:test-account:nest-test-topic'
                },
                {
                    'SubscriptionArn':
                        'arn:aws:sns:eu-west-1:458315597956:nest-test-notifier:0a314486-a412-40c3-ae62-8c1b00btest2',
                    'Owner': 'test-owner',
                    'Protocol': 'email',
                    'Endpoint': 'soppela.jyri@gmail.com',
                    'TopicArn': 'arn:aws:sns:eu-west-1:test-account:nest-test-topic'
                },
            ]
        })

        self.consumer.distribute_data(self.event)

    def test_account_operations(self):
        # Test account identity operation that is used to get resource ARNs tied to the account
        self.assertTrue(self.consumer.sts_client.get_caller_identity.called)

    def test_outgoing_queue_operations(self):
        # Test creating queues for endpoint consumers to consume.
        # Lambda consumer forwards incoming data to these queues.
        self.assertTrue(self.consumer.sqs_client.create_queue.called)
        self.assertEqual(self.consumer.sqs_client.create_queue.call_count,
                         len(self.consumer.sns_client.list_subscriptions_by_topic.return_value['Subscriptions']) *
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))
        create_queue_calls = [
            call(QueueName='nest-test-queue-0a314486-a412-40c3-ae62-8c1b00btest1'),
            call(QueueName='nest-test-queue-0a314486-a412-40c3-ae62-8c1b00btest2')
        ]
        self.consumer.sqs_client.create_queue.assert_has_calls(create_queue_calls, any_order=True)

    def test_queue_url_generation(self):
        self.assertTrue(self.consumer.sqs_client.get_queue_url.called)

    def test_incoming_queue_reading(self):
        # Test reading messages from incoming data queue
        self.assertTrue(self.consumer.sqs_client.receive_message.called)

    def test_message_acknowledging(self):
        # Test acknowledging and deleting messages from incoming queue once they are consumed
        self.assertTrue(self.consumer.sqs_client.delete_message.called)
        self.assertEqual(self.consumer.sqs_client.delete_message.call_count,
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))
        delete_message_calls = [
            call(
                QueueUrl='aws:nest-test-queue-url',
                ReceiptHandle='test-receipt-handle-1'
            ),
            call(
                QueueUrl='aws:nest-test-queue-url',
                ReceiptHandle='test-receipt-handle-2'
            )
        ]
        self.consumer.sqs_client.delete_message.assert_has_calls(delete_message_calls, any_order=True)

    def test_sending_messages_to_outgoing_queues(self):
        # Test sending messages out to endpoint queues.
        self.assertTrue(self.consumer.sqs_client.send_message.called)
        self.assertEqual(self.consumer.sqs_client.create_queue.call_count,
                         len(self.consumer.sns_client.list_subscriptions_by_topic.return_value['Subscriptions']) *
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))
        send_message_calls = [
            call(
                QueueUrl='aws:nest-test-queue-url',
                MessageBody='test-body-1'
            ),
            call(
                QueueUrl='aws:nest-test-queue-url',
                MessageBody='test-body-2'
            )
        ]
        self.consumer.sqs_client.send_message.assert_has_calls(send_message_calls, any_order=True)

    def test_topic_creation(self):
        # Check that the outgoing queue notification topics are created
        self.assertTrue(self.consumer.sns_client.create_topic.called)

        create_topic_calls = [
            call(
                Name='nest-outgoing-topic-demo'
            )
        ]
        self.consumer.sns_client.create_topic.assert_has_calls(create_topic_calls, any_order=True)

    def test_subscription_listing(self):
        # Test listing subscriptions of the outgoing topics
        self.assertTrue(self.consumer.sns_client.list_subscriptions_by_topic.called)

    def test_publishing_to_topic(self):
        # Test publishing the data received from the incoming pipeline into the subscribers of outgoing pipeline
        self.assertTrue(self.consumer.sns_client.publish.called)
        self.assertEqual(self.consumer.sns_client.publish.call_count,
                         len(self.consumer.sns_client.list_subscriptions_by_topic.return_value['Subscriptions']) *
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))

        publish_calls = [
            call(
                TopicArn='arn:aws:sns:eu-west-1:test-account:nest-test-topic',
                Message="{"\
                        + "'queue': 'nest-test-queue-0a314486-a412-40c3-ae62-8c1b00btest1',"\
                        + "'dead-letter-queue': 'nest-test-dead-letter-queue-0a314486-a412-40c3-ae62-8c1b00btest1'"\
                        "}"
            ),
            call(
                TopicArn='arn:aws:sns:eu-west-1:test-account:nest-test-topic',
                Message="{"\
                        + "'queue': 'nest-test-queue-0a314486-a412-40c3-ae62-8c1b00btest2',"\
                        + "'dead-letter-queue': 'nest-test-dead-letter-queue-0a314486-a412-40c3-ae62-8c1b00btest2'"\
                        "}"
            )
        ]

        self.consumer.sns_client.publish.assert_has_calls(publish_calls, any_order=True)
