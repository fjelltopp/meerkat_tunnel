import boto3
import time
import json
import datetime


sqs_message = "This is a test message sent at {}".format(datetime.datetime.now().isoformat())

incoming_name = "nest-queue-test"

sqs_incoming_queue = "https://sqs.eu-west-1.amazonaws.com/458315597956/" + incoming_name

sqs_outgoing_queue = "https://sqs.eu-west-1.amazonaws.com/458315597956/nest-queue-test-nest-queue-outgoing-test"

sns_arn = "arn:aws:sns:eu-west-1:458315597956:nest-incoming-topic-demo"

region_name = "eu-west-1"


sns_message = json.dumps(
    {
        "queue": incoming_name,
        "dead-letter-queue": incoming_name
    }
)

sns_client = boto3.client('sns', region_name=region_name)
sqs_client = boto3.client('sqs', region_name=region_name)
sts_client = boto3.client('sts', region_name=region_name)


def send(N=1):
    # Send SQS message
    for i in range(N):
        sqs_client.send_message(
            QueueUrl=sqs_incoming_queue,
            MessageBody=sqs_message
        )

    # Send SNS message
    sns_client.publish(
        TopicArn=sns_arn,
        Message=sns_message
    )

for i in range(10):
    send(i)
    time.sleep(2)

# Check outgoing SQS message
time.sleep(5)
mes = 1

received = 0
while mes != 0:
    outgoing = sqs_client.receive_message(
        QueueUrl=sqs_outgoing_queue,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=19
    
    )
    messages = outgoing.get("Messages", [])
    print(outgoing)

    for o in messages:
        response = sqs_client.delete_message(
            QueueUrl=sqs_outgoing_queue,
            ReceiptHandle=o['ReceiptHandle']
        )
    #print(response)
    mes = len(messages)
    received += mes
print(received)

