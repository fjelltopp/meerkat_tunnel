import boto3
import os
import json
import uuid
import logging
import postgresql
import requests


class PersistentDatabaseWriter:
    def __init__(self):
        region_name = 'eu-west-1'
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        # self.sts_client = boto3.client('sts', region_name=region_name)

        self.max_number_of_messages = 4
        self.call_again = False

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    def get_account_id(self):
        """
        Returns AWS account ID

        Returns:\n
            account ID for the configured AWS user\n
        """
        # account_id = self.sts_client.get_caller_identity()["Account"]
        account_id = os.environ["ACCOUNT_ID"]
        return account_id

    @staticmethod
    def get_outgoing_queue_name(outgoing_queue, subscription_arn):
        """
        Constructs the full queue name based on subscription ARN

        :param incoming_queue: SQS incoming queue name
        :param subscription_arn: Subscription ARN
        :return: returns 1 to 10 messages from SQS
        """

        return os.environ['PERSISTENT_DATABASE_WRITER_QUEUE']

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

    def fetch_data_from_queue(self, queue):
        """
        Polls messages from SQS queue

        :param queue: SQS queue name
        :return: returns 1 to 10 messages from SQS
        """
        #self.sqs_client.create_queue(
        #    QueueName=queue
        #)

        response = (self.sqs_client.receive_message(
            QueueUrl=self.get_queue_url(queue),
            MaxNumberOfMessages=self.max_number_of_messages,
            WaitTimeSeconds=1
        )
        ).get('Messages', [])

        return response


    def write_to_db(self, data_entry):
        """
        Writes data entry to database

        :param data_entry: data to enter
        :return:
        """
        table_name = data_entry['formId']
        data = json.dumps(data_entry['data'])

        db = postgresql.open(os.environ['DATABASE_URL'])

        create_table_statement = \
            'CREATE TABLE IF NOT EXISTS {0} (ID serial primary key, UUID text NOT NULL, DATA jsonb NOT NULL)'.format(
                table_name
            )
        self.logger.debug(create_table_statement)

        ret_create = db.execute(create_table_statement)
        logging.info(ret_create)

        insert_statement = 'INSERT INTO {0} (UUID, DATA) VALUES (\'{1}\', \'{2}\'::jsonb);'.format(
            table_name,
            uuid.uuid4(),
            data
        )
        self.logger.debug(insert_statement)

        ret_insert = db.execute(insert_statement)
        self.logger.debug(ret_insert)

    def acknowledge_messages(self, queue, data_entry):
        """
        Acknowledges and deletes messages that were received from SQS

        :param queue: SQS queue name
        :param data_entry: Message payload from SQS queue
        :return:
        """
        response = self.sqs_client.delete_message(
            QueueUrl=self.get_queue_url(queue),
            ReceiptHandle=data_entry['ReceiptHandle']
        )

        return response

    def notify_outgoing_topic(self, topic, message):
        """
        Send notification with information about the outgoing queue and its dead letter queue
        :param topic: Topic ARN that launches this function
        :param message: message in the notification
        """
        self.logger.info("Notifying topic {0} with message: {1}".format(str(topic),json.dumps(message)))

        #self.sns_client.publish(
        #    TopicArn=topic,
        #    Message=json.dumps(message)
        #)

    def store_data_entry(self, message, subscription_arn):
        """
        Main function to call functions

        :param message: message received by SNS
        :param subscription_arn: subscription ARN of the Lambda SNS subscription
        :return: Binary value whether the Lambda function should be launched again
        """

        nest_outgoing_queue = os.environ['PERSISTENT_DATABASE_WRITER_QUEUE'] # self.get_outgoing_queue_name(message['queue'], subscription_arn)
        self.logger.info("Fetching data from queue {0}".format(nest_outgoing_queue))
        data_entries = self.fetch_data_from_queue(nest_outgoing_queue)
        if len(data_entries) == self.max_number_of_messages:
            self.call_again = True
        for data_entry in data_entries:
            self.write_to_db(json.loads(data_entry['Body']))
            self.acknowledge_messages(nest_outgoing_queue, data_entry)

        self.logger.info("Handled {0} data entries".format(len(data_entries)))

        return self.call_again


def lambda_handler(event, context):
    """
    Gets data from queue and forwards it to persistent database
    :param event: Includes the queue name of the queue that has new data available
    :param context:
    :return: returns information about where the data was forwarded to
    """

    print("GETting google.com")
    print(str(requests.get("http://www.google.com")))

    writer = PersistentDatabaseWriter()
    message = json.loads(event['Records'][0]['Sns']['Message'])
    subscription_arn = event['Records'][0]['EventSubscriptionArn']
    topic = event['Records'][0]['Sns']['TopicArn']
    call_again = writer.store_data_entry(message, subscription_arn)

    if call_again:
        writer.notify_outgoing_topic(topic=topic, message=message)

    return 'Lambda run for ' + os.environ['ORG']
