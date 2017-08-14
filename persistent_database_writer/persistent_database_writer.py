import boto3
import os
import json
import uuid
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class PersistentDatabaseWriter:
    def __init__(self):
        region_name = 'eu-west-1'
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)

        self.engine = create_engine(os.environ['DATABASE_URL'])
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.tables = {}

        self.Base = declarative_base()

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

    def fetch_data_from_queue(self, queue):
        """
        Polls messages from SQS queue

        :param queue: SQS queue name
        :return: returns 1 to 10 messages from SQS
        """
        queue_ret_val = self.sqs_client.receive_message(
            QueueUrl=self.get_queue_url(queue),
        )
        return queue_ret_val

    def set_up_meta_data(self, data_entry):
        """
        Generates the meta data objects for data entry in case it doesn't exist alreade
        :param data_entry: data to enter
        :return:
        """
        table_name = data_entry['formId']

        if table_name not in self.tables.keys():
            self.tables[table_name] = type(table_name, (self.Base,), {
                                "__tablename__": table_name,
                                "id": Column(Integer, primary_key=True),
                                "uuid": Column(String, index=True),
                                "data": Column(JSONB)})

    def write_to_db(self, data_entry):
        """
        Writes data entry to database

        :param data_entry: data to enter
        :return:
        """
        table_name = data_entry['formId']

        self.Base.metadata.create_all(self.engine, checkfirst=True)
        new_row = self.tables[table_name](uuid=uuid.uuid4(), data=data_entry['data'])
        self.session.add(new_row)
        self.session.commit()

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

    def store_data_entry(self, message):
        """
        Main function to call functions

        :param message: message received by SNS
        :return:
        """

        data_entries = self.fetch_data_from_queue(message['queue'])
        for data_entry in data_entries['Messages']:
            self.set_up_meta_data(json.loads(data_entry['Body']))
            self.write_to_db(json.loads(data_entry['Body']))
            self.acknowledge_messages(message['queue'], data_entry)


def lambda_handler(event, context):
    """
    Gets data from queue and forwards it to persistent database
    :param event: Includes the queue name of the queue that has new data available
    :param context:
    :return: returns information about where the data was forwarded to
    """
    writer = PersistentDatabaseWriter()
    message = json.loads(event['Records'][0]['Sns']['Message'])
    writer.store_data_entry(message)

    return 'Lambda run for ' + os.environ['ORG']