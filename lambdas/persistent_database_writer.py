import boto3
import os
import json
import uuid
import logging
import psycopg2


class PersistentDatabaseWriter:
    def __init__(self):
        region_name = 'eu-west-1'
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)

        self.max_number_of_messages = int(os.environ.get('MAX_NUMBER_OF_MESSAGES', 10))
        self.call_again = False

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def get_account_id(self):
        """
        Returns AWS account ID

        :return: returns the account ID configured in the environment variables
        """

        account_id = os.environ["ACCOUNT_ID"]
        return account_id

    @staticmethod
    def get_outgoing_queue_name(outgoing_queue, subscription_arn):
        """
        Constructs the full queue name based on subscription ARN

        :param incoming_queue: SQS incoming queue name
        :param subscription_arn: Subscription ARN
        :return: returns SQS queue name
        """

        return os.environ['PERSISTENT_DATABASE_WRITER_QUEUE']

    def get_queue_url(self, queue_name):
        """
        Creates a queue URL based on given queue name

        :param queue_name: name of the AWS SQS queue
        :return: AWS SQS URL for the given queue
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
        :return: returns 1 to 10 messages from SQS as set by max_number_of_messages
        """

        response = (self.sqs_client.receive_message(
            QueueUrl=self.get_queue_url(queue),
            MaxNumberOfMessages=min(self.max_number_of_messages, 10),
            WaitTimeSeconds=1
        )
        ).get('Messages', [])

        return response

    def write_to_db(self, db_cur, data_entry):
        """
        Writes data entry to database

        :param db: database object
        :param data_entry: data to enter
        """
        data_dict = data_entry.get('data', {})
        data = json.dumps(data_dict)

        insert_statement = 'INSERT INTO {0} (UUID, DATA) VALUES (%s, %s) ON CONFLICT (UUID) DO UPDATE SET DATA=%s WHERE {0}.UUID=%s;'.format(data_entry['formId'])
        self.logger.debug(insert_statement)

        uuid_new = data_dict.get('meta/instanceID', str(uuid.uuid4()))
        db_cur.execute(insert_statement, (uuid_new, data, data, uuid_new))

    def acknowledge_messages(self, queue, data_entry):
        """
        Acknowledges and deletes messages that were received from SQS

        :param queue: SQS queue name
        :param data_entry: Message payload from SQS queue
        :return: returns the response
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

        self.sns_client.publish(
            TopicArn=topic,
            Message=json.dumps(message)
        )

    def store_data_entries(self):
        """
        Main function to call functions

        :return: binary value whether the Lambda function should be launched again
        """

        nest_outgoing_queue = os.environ['PERSISTENT_DATABASE_WRITER_QUEUE']
        self.logger.info("Fetching data from queue {0}".format(nest_outgoing_queue))

        data_entries = self.fetch_data_from_queue(nest_outgoing_queue)

        if len(data_entries) > 0:
            db_conn = psycopg2.connect(dbname=os.environ['DB_NAME'],
                                       user=os.environ['DB_USER'],
                                       password=os.environ['DB_PW'],
                                       host=os.environ['DB_HOST'],
                                       port=os.environ.get('DB_PORT', '5432'))
            db_cur = db_conn.cursor()
        else:
            return False

        while len(data_entries) < self.max_number_of_messages:
            new_entries = self.fetch_data_from_queue(nest_outgoing_queue)

            if len(new_entries) == 0:
                break
            else:
                data_entries = data_entries + new_entries

        if len(data_entries) == self.max_number_of_messages:
            self.call_again = True

        for data_entry in data_entries:
            self.write_to_db(db_cur, json.loads(data_entry['Body']))
            db_conn.commit()
            self.acknowledge_messages(nest_outgoing_queue, data_entry)

        self.logger.info("Handled {0} data entries".format(len(data_entries)))

        # Close db cursor
        if db_cur:
            db_cur.close()

        # Close db connection
        if db_conn:
            db_conn.close()

        return self.call_again


def lambda_handler(event, context):
    """
    Gets data from queue and forwards it to persistent database
    :param event: Includes the queue name of the queue that has new data available
    :param context:
    :return: returns information about where the data was forwarded to
    """

    writer = PersistentDatabaseWriter()
    message = json.loads(event['Records'][0]['Sns']['Message'])
    subscription_arn = event['Records'][0]['EventSubscriptionArn']
    topic = event['Records'][0]['Sns']['TopicArn']
    call_again = writer.store_data_entries()

#    if call_again:
#        writer.notify_outgoing_topic(topic=topic, message=message)

    return 'Lambda run for ' + os.environ['ORG']
