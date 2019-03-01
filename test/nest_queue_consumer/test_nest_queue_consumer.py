"""
Lambda Queue Consumer Test
"""

import unittest
from unittest.mock import MagicMock, call
import datetime
from dateutil.tz import tzutc

import lambdas.nest_queue_consumer as nest_queue_consumer


class NestQueueConsumerTest(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        """Setup for testing"""

    def setUp(self):
        self.event = {
            'queue': 'nest-test-queue',
            'dead-letter-queue': 'nest-test-dead-letter-queue'
        }
        self.consumer = nest_queue_consumer.NestQueueConsumer()
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
                        'arn:aws:sns:eu-west-1:123456789012:nest-test-notifier:0a314486-a412-40c3-ae62-8c1b00btest1',
                    'Owner': 'test-owner',
                    'Protocol': 'email',
                    'Endpoint': 'soppela.jyri@gmail.com',
                    'TopicArn': 'arn:aws:sns:eu-west-1:test-account:nest-test-topic'
                },
                {
                    'SubscriptionArn':
                        'arn:aws:sns:eu-west-1:123456789012:nest-test-notifier:0a314486-a412-40c3-ae62-8c1b00btest2',
                    'Owner': 'test-owner',
                    'Protocol': 'email',
                    'Endpoint': 'soppela.jyri@gmail.com',
                    'TopicArn': 'arn:aws:sns:eu-west-1:test-account:nest-test-topic'
                },
            ]
        })

        self.consumer.ec2_client.describe_instances = MagicMock(return_value=
        {'Reservations':[
            {'RequesterId': '890756736270', 'OwnerId': '123456789012', 'ReservationId': 'r-0fadc886b230212a8',
             'Instances': [
                 {'VpcId': 'vpc-92da8ef7', 'RootDeviceType': 'ebs', 'AmiLaunchIndex': 0, 'ImageId': 'ami-c51e3eb6',
                  'State': {'Name': 'running', 'Code': 16}, 'Architecture': 'x86_64',
                  'Monitoring': {'State': 'disabled'}, 'EnaSupport': True, 'VirtualizationType': 'hvm',
                  'StateTransitionReason': '', 'InstanceType': 't2.micro',
                  'ClientToken': '5d14c877-7f00-4aaa-af9c-7a7365e7846b', 'Hypervisor': 'xen',
                  'SecurityGroups': [{'GroupId': 'sg-7c32d704', 'GroupName': 'NTP'},
                                     {'GroupId': 'sg-34069e50', 'GroupName': 'Container Servers'},
                                     {'GroupId': 'sg-e6d34082', 'GroupName': 'AWS-OpsWorks-Default-Server'}],
                  'KeyName': 'development',
                  'BlockDeviceMappings': [{'DeviceName': '/dev/xvda',
                                           'Ebs': {'VolumeId': 'vol-004f7221931ebf796',
                                                   'DeleteOnTermination': True,
                                                   'Status': 'attached',
                                                   'AttachTime': datetime.datetime(2017, 4,
                                                                                   14, 9, 50,
                                                                                   5,
                                                                                   tzinfo=tzutc())}}],
                  'ProductCodes': [],
                  'Placement': {'Tenancy': 'default', 'GroupName': '', 'AvailabilityZone': 'eu-west-1a'},
                  'PrivateIpAddress': '10.0.1.207', 'InstanceId': 'i-07cf6f3caf3c5bd42',
                  'LaunchTime': datetime.datetime(2017, 4, 14, 9, 50, 5, tzinfo=tzutc()), 'EbsOptimized': False,
                  'NetworkInterfaces': [{'VpcId': 'vpc-92da8ef7',
                                         'Attachment': {'AttachmentId': 'eni-attach-3bf24542', 'DeviceIndex': 0,
                                                        'DeleteOnTermination': True, 'Status': 'attached',
                                                        'AttachTime': datetime.datetime(2017, 4, 14, 9, 50, 5,
                                                                                        tzinfo=tzutc())},
                                         'PrivateIpAddress': '10.0.1.207', 'MacAddress': '0a:02:6d:b9:18:83',
                                         'PrivateIpAddresses': [
                                             {'PrivateDnsName': 'ip-10-0-1-207.eu-west-1.compute.internal',
                                              'Primary': True, 'PrivateIpAddress': '10.0.1.207'}],
                                         'PrivateDnsName': 'ip-10-0-1-207.eu-west-1.compute.internal',
                                         'Ipv6Addresses': [], 'OwnerId': '123456789012', 'SubnetId': 'subnet-cb592792',
                                         'Groups': [{'GroupId': 'sg-7c32d704', 'GroupName': 'NTP'},
                                                    {'GroupId': 'sg-34069e50', 'GroupName': 'Container Servers'},
                                                    {'GroupId': 'sg-e6d34082',
                                                     'GroupName': 'AWS-OpsWorks-Default-Server'}],
                                         'NetworkInterfaceId': 'eni-a9624afa', 'SourceDestCheck': True,
                                         'Description': '', 'Status': 'in-use'}],
                  'PrivateDnsName': 'ip-10-0-1-207.eu-west-1.compute.internal',
                  'Tags': [{'Key': 'opsworks:stack', 'Value': 'demo'},
                           {'Key': 'opsworks:instance', 'Value': 'master-demo-f914fa'},
                           {'Key': 'opsworks:layer:ecs-cluster', 'Value': 'Amazon ECS Cluster'},
                           {'Key': 'meerkat:branch', 'Value': 'master'}, {'Key': 'meerkat:id', 'Value': 'f914fa'},
                           {'Key': 'meerkat:task', 'Value': 'demo'},
                           {'Key': 'Name', 'Value': 'demo - master-demo-f914fa'},
                           {'Key': 'meerkat:type', 'Value': 'live'}], 'RootDeviceName': '/dev/xvda',
                  'IamInstanceProfile': {'Id': 'AIPAISXEFBDE7GGK2HWTA',
                                         'Arn': 'arn:aws:iam::123456789012:instance-profile/DemoContainerServer'},
                  'SourceDestCheck': True, 'PublicDnsName': '', 'SubnetId': 'subnet-cb592792'}], 'Groups': []},
            {'RequesterId': '890756736270', 'OwnerId': '123456789012', 'ReservationId': 'r-06fef7e597f0301bb',
             'Instances': [
                 {'VpcId': 'vpc-92da8ef7', 'RootDeviceType': 'ebs', 'AmiLaunchIndex': 0, 'ImageId': 'ami-c51e3eb6',
                  'State': {'Name': 'running', 'Code': 16}, 'Architecture': 'x86_64',
                  'Monitoring': {'State': 'disabled'}, 'EnaSupport': True, 'VirtualizationType': 'hvm',
                  'StateTransitionReason': '', 'InstanceType': 't2.micro',
                  'ClientToken': '6f19d084-b654-402c-b5e2-59c70e4e1634', 'Hypervisor': 'xen',
                  'SecurityGroups': [{'GroupId': 'sg-7c32d704', 'GroupName': 'NTP'},
                                     {'GroupId': 'sg-34069e50', 'GroupName': 'Container Servers'},
                                     {'GroupId': 'sg-e6d34082', 'GroupName': 'AWS-OpsWorks-Default-Server'}],
                  'KeyName': 'development',
                  'BlockDeviceMappings': [{'DeviceName': '/dev/xvda',
                                           'Ebs': {'VolumeId': 'vol-0d4bf9f41450027bf',
                                                   'DeleteOnTermination': True,
                                                   'Status': 'attached',
                                                   'AttachTime': datetime.datetime(2017, 10,
                                                                                   3, 1, 3,
                                                                                   tzinfo=tzutc())}}],
                  'ProductCodes': [],
                  'Placement': {'Tenancy': 'default', 'GroupName': '', 'AvailabilityZone': 'eu-west-1a'},
                  'PrivateIpAddress': '10.0.1.70', 'InstanceId': 'i-02c871b2af418e610',
                  'LaunchTime': datetime.datetime(2017, 10, 3, 1, 2, 59, tzinfo=tzutc()), 'EbsOptimized': False,
                  'NetworkInterfaces': [{'VpcId': 'vpc-92da8ef7',
                                         'Attachment': {'AttachmentId': 'eni-attach-919ca4e9', 'DeviceIndex': 0,
                                                        'DeleteOnTermination': True, 'Status': 'attached',
                                                        'AttachTime': datetime.datetime(2017, 10, 3, 1, 2, 59,
                                                                                        tzinfo=tzutc())},
                                         'PrivateIpAddress': '10.0.1.70', 'MacAddress': '0a:bc:66:27:ed:d2',
                                         'PrivateIpAddresses': [
                                             {'PrivateDnsName': 'ip-10-0-1-70.eu-west-1.compute.internal',
                                              'Primary': True, 'PrivateIpAddress': '10.0.1.70'}],
                                         'PrivateDnsName': 'ip-10-0-1-70.eu-west-1.compute.internal',
                                         'Ipv6Addresses': [], 'OwnerId': '123456789012', 'SubnetId': 'subnet-cb592792',
                                         'Groups': [{'GroupId': 'sg-7c32d704', 'GroupName': 'NTP'},
                                                    {'GroupId': 'sg-34069e50', 'GroupName': 'Container Servers'},
                                                    {'GroupId': 'sg-e6d34082',
                                                     'GroupName': 'AWS-OpsWorks-Default-Server'}],
                                         'NetworkInterfaceId': 'eni-e1beeae0', 'SourceDestCheck': True,
                                         'Description': '', 'Status': 'in-use'}],
                  'PrivateDnsName': 'ip-10-0-1-70.eu-west-1.compute.internal',
                  'Tags': [{'Key': 'meerkat:branch', 'Value': 'development'}, {'Key': 'meerkat:id', 'Value': 'a57f82'},
                           {'Key': 'opsworks:instance', 'Value': 'development-demo-a57f82'},
                           {'Key': 'opsworks:stack', 'Value': 'demo'},
                           {'Key': 'opsworks:layer:ecs-cluster', 'Value': 'Amazon ECS Cluster'},
                           {'Key': 'meerkat:type', 'Value': 'live'}, {'Key': 'meerkat:task', 'Value': 'demo'},
                           {'Key': 'Name', 'Value': 'demo - development-demo-a57f82'}], 'RootDeviceName': '/dev/xvda',
                  'IamInstanceProfile': {'Id': 'AIPAISXEFBDE7GGK2HWTA',
                                         'Arn': 'arn:aws:iam::123456789012:instance-profile/DemoContainerServer'},
                  'SourceDestCheck': True, 'PublicDnsName': '', 'SubnetId': 'subnet-cb592792'}], 'Groups': []}]}
                                                                )

        self.consumer.distribute_data(self.event)

    def test_account_operations(self):
        # Test account identity operation that is used to get resource ARNs tied to the account
        self.assertTrue(self.consumer.sts_client.get_caller_identity.called)

    def test_outgoing_queue_operations(self):
        # Test creating queues for endpoint consumers to consume.
        # Lambda consumer forwards incoming data to these queues.
        self.assertTrue(self.consumer.sqs_client.create_queue.called)
        self.assertEqual(self.consumer.sqs_client.create_queue.call_count,
                         (len(self.consumer.ec2_client.describe_instances.return_value['Reservations']) + 1) *
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))
        create_queue_calls = [
            call(QueueName='nest-test-queue-development-demo-a57f82'),
            call(QueueName='nest-test-queue-master-demo-f914fa'),
            call(QueueName='nest-test-queue-persistent_database_writer')
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
                         (len(self.consumer.ec2_client.describe_instances.return_value['Reservations']) + 1) *
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

    def test_publishing_to_topic(self):
        # Test publishing the data received from the incoming pipeline into the subscribers of outgoing pipeline
        self.assertTrue(self.consumer.sns_client.publish.called)
        self.assertEqual(self.consumer.sns_client.publish.call_count,
                         len(self.consumer.sqs_client.receive_message.return_value['Messages']))

        publish_calls = [
            call(
                TopicArn='arn:aws:sns:eu-west-1:test-account:nest-test-topic',
                Message="{"\
                        + "'queue': 'nest-test-queue-persistent_database_writer',"\
                        + "'dead-letter-queue': 'nest-test-dead-letter-queue-persistent_database_writer'"\
                        "}"
            )
        ]

        #self.consumer.sns_client.publish.assert_has_calls(publish_calls, any_order=True)
