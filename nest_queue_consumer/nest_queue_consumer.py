import boto3
import os
import json


class NestQueueConsumer:
    def __init__(self):
        region_name = 'eu-west-1'
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        self.ec2_client = boto3.client('ec2', region_name=region_name)

    def get_account_id(self):
        """
        Returns AWS account ID

        Returns:\n
            account ID for the configured AWS user\n
        """
        account_id = self.sts_client.get_caller_identity()["Account"]
        return account_id

    def get_queue_url(self, queue_name):
        """
        Creates a queue URL based on given queue name

        Returns:\n
            URL for the given queue\n
        """
        response = self.sqs_client.get_queue_url(
            QueueName=queue_name,
            QueueOwnerAWSAccountId=self.get_account_id()
        )
        return response['QueueUrl']

    def get_outgoing_subscriptions(self, topic_arn):
        """
        Get all subscribers that have subscribed to the output of the Lambda function
        :param topic_arn: ARN of the output topic
        :return: return a list of subscriptions
        """
        subscriptions = []
        response = self.sns_client.list_subscriptions_by_topic(
            TopicArn=topic_arn
        )
        subscriptions += response['Subscriptions']
        next_token = response.get('NextToken', None)

        # SNS returns at most 100 subscriptions, concatenate them if needed
        while next_token is not None:
            response = self.sns_client.list_subscriptions_by_topic(
                TopicArn=topic_arn,
                NextToken=next_token
            )
            next_token = response.get('NextToken', None)
            subscriptions += response['Subscriptions']

        return subscriptions

    @staticmethod
    def get_outgoing_queue(subscriber, incoming_queue):
        return incoming_queue + '-' + subscriber

    @staticmethod
    def get_dead_letter_queue_for_outgoing(subscriber, dead_letter_queue_for_incoming):
        return dead_letter_queue_for_incoming + '-' + subscriber

    def get_outgoing_topic(self):
        """
        Get the topic for outgoing data from Lambda queue consumer
        :return: Topic object where lambda publishes notifications about new data
        """
        topic = self.sns_client.create_topic(
            Name='nest-outgoing-topic-' + os.environ['ORG'].lower()
        )
        return topic

    def get_incoming_data(self, queue_name, n=1):
        """
        Fetch data from SQS
        :param queue_name: name of the queue with incoming data
        :param n: how many times the receive_message function is run
        :return: returns a list of return values from AWS
        """
        return_set = []
        # TODO empty the whole queue

        for i in range(0, n):
            return_set += (self.sqs_client.receive_message(
                QueueUrl=self.get_queue_url(queue_name),
                MaxNumberOfMessages=10
            )
            ).get('Messages', [])
        return return_set

    def notify_outgoing_subscribers(self, outgoing_queue, dead_letter_queue_for_outgoing):
        """
        Send notification with information about the outgoing queue and its dead letter queue
        :param outgoing_queue: outgoing queue
        :param dead_letter_queue_for_outgoing: dead letter queue for outgoing data
        """
        notification_message_dict = {'queue': outgoing_queue, 'dead_letter_queue': dead_letter_queue_for_outgoing}
        notification_message = json.dumps(notification_message_dict)

        topic = self.get_outgoing_topic()
        self.sns_client.publish(
            TopicArn=topic['TopicArn'],
            Message=notification_message
        )

    def acknowledge_data_entry(self, queue, data_entry):
        """
        Sends an ACK message to SQS to delete the message from queue
        :param data_entry: data entry returned by SQS receive_message
        :param queue: queue the data entry was fetched from
        :return: AWS delete message return value
        """
        response = self.sqs_client.delete_message(
            QueueUrl=self.get_queue_url(queue),
            ReceiptHandle=data_entry['ReceiptHandle']
        )
        return response

    def redirect_data_to_subscriber(self, subscriber, incoming_queue, dead_letter_queue_for_incoming, data_entry):
        """
        Sends data fetched from the incoming queue to the subscriber and data type specific queues
        :param subscriber: Subscriber to redirect data to
        :param incoming_queue: Queue from where Lambda fetched the data
        :param dead_letter_queue_for_incoming: Queue for letters that the Lambda consumer could not handle
        :param data_entry: Data entry to be forwarded
        :return:
        """
        outgoing_queue = self.get_outgoing_queue(subscriber, incoming_queue)
        dead_letter_queue_for_outgoing = self.get_dead_letter_queue_for_outgoing(
            subscriber, dead_letter_queue_for_incoming)
        outgoing_queue_url = self.sqs_client.create_queue(
            QueueName=outgoing_queue
        )
        self.sqs_client.send_message(
            QueueUrl=outgoing_queue_url['QueueUrl'],
            MessageBody=data_entry['Body']
        )

    def get_ec2_instances(self, task):
        """
        Returns list of deploy_ids of existing ec2 instances for task (organization), indexed by
        deploy_id and filtered by any further tags or instance ids specified. Tags must
        be a list of dicts: [{'Name': 'tag_key', 'Values': ['tag_value']}].
        :param task:
        :param instance_ids:
        """
        # Assemble arguments to filter ec2 instances by task and branch tags.
        args = {}
        args['Filters'] = [{'Name': 'tag:meerkat:task', 'Values': [task]}]

        # Get instance data
        reservations = self.ec2_client.describe_instances(**args)['Reservations']

        # Structure the data and return.
        deploy_ids = []
        for res in reservations:
            for instance in res['Instances']:
                for tag in instance['Tags']:
                    if tag['Key'] == 'opsworks:instance':
                        deploy_ids.append(tag['Value'])
        return deploy_ids

    def distribute_data(self, message):
        """
        Main function to distribute data from incoming queue to subscriber queues
        :param message: Includes the queue name of the queue that has new data available
        """
        outgoing_queue_archivist = 'persistent_database_writer'

        subscriptions = self.get_ec2_instances(os.environ.get('ORG', ''))
        subscriptions.append(outgoing_queue_archivist)

        incoming_queue = message['queue']
        dead_letter_queue_for_incoming = message['dead-letter-queue']
        incoming_data = self.get_incoming_data(incoming_queue)
        for data_entry in incoming_data:
            for subscriber in subscriptions:
                self.redirect_data_to_subscriber(subscriber, incoming_queue, dead_letter_queue_for_incoming, data_entry)
            outgoing_queue = self.get_outgoing_queue(outgoing_queue_archivist, incoming_queue)
            dead_letter_queue_for_outgoing = self.get_dead_letter_queue_for_outgoing(
                outgoing_queue_archivist, dead_letter_queue_for_incoming)
            self.notify_outgoing_subscribers(outgoing_queue, dead_letter_queue_for_outgoing)
            self.acknowledge_data_entry(incoming_queue, data_entry)



def lambda_handler(event, context):
    """
    Iterates through the subscribers of a country data flow and distributes data forwards
    :param event: Includes the queue name of the queue that has new data available
    :param context:
    :return: returns information about where the data was forwarded to
    """
    consumer = NestQueueConsumer()
    message = json.loads(event['Records'][0]['Sns']['Message'])
    consumer.distribute_data(message)

    return 'Lambda run for ' + os.environ['ORG']
