# meerkat_tunnel
Data transfer functions that distribute the data sent from the country server

## Setup
### Manual steps in AWS console:
#### Create standar SQS queues:
1. nest-queue-*COUNTRY_ID*
1. nest-queue-*COUNTRY_ID*-persistent_database_writer
#### [Optional] You may also need to create SNS topics:
1. nest-incoming-topic-*COUNTRY_ID*
1. nest-outgoing-topic-*COUNTRY_ID*
#### Create lambda functions
1. Lambda function name: `*COUNTRY_ID*_nest_queue_consumer`:
    - Handler: `nest_queue_consumer.lambda_handler`
    - Environmant variables:
        ```
        ORG=COUNTRY_ID
        ```
    - Timeout: 1 min
    - Assign IAM role with the following permissions:
        ```
        # standard AWS policy: AmazonEC2ReadOnlyAccess
        # SQS-nest 
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "VisualEditor0",
                    "Effect": "Allow",
                    "Action": [
                        "sqs:TagQueue",
                        "sqs:UntagQueue",
                        "sqs:CreateQueue",
                        "sqs:SetQueueAttributes"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "VisualEditor1",
                    "Effect": "Allow",
                    "Action": "sqs:*",
                    "Resource": [
                        "arn:aws:sqs:eu-west-1:ACCOUNT_ID:nest-queue-COUNTRY_ID*",
                        "arn:aws:sqs:eu-west-1:ACCOUNT_ID:nest-queue-COUNTRY_ID"
                    ]
                }
            ]
        }
        # lambda-logs
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        # SQS-nest-queue-COUNTRY_ID
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "VisualEditor0",
                    "Effect": "Allow",
                    "Action": [
                        "sqs:TagQueue",
                        "sqs:UntagQueue",
                        "sqs:CreateQueue",
                        "sqs:SetQueueAttributes"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "VisualEditor1",
                    "Effect": "Allow",
                    "Action": "sqs:*",
                    "Resource": [
                        "arn:aws:sqs:eu-west-1:ACCOUNT_ID:nest-queue-COUNTRY_ID*",
                        "arn:aws:sqs:eu-west-1:ACCOUNT_ID:nest-queue-COUNTRY_ID"
                    ]
                }
            ]
        }
        # SNS-nest
          {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "sns:*"
                    ],
                    "Effect": "Allow",
                    "Resource": "arn:aws:sns:eu-west-1:ACCOUNT_ID:nest*"
                }
            ]
        }
        ```    
1. Lambda function name: `*COUNTRY_ID*_persistent_database_writer`:
    - Handler: `persistent_database_writer.lambda_handler`
    - Environmant variables:
        ```
        ACCOUNT_ID=123123123123
        DATABASE_URL=pq://db_user:password1@rds-db-hostname.eu-west-1.rds.amazonaws.com
        DB_HOST=rds-db-hostname.eu-west-1.rds.amazonaws.com
        DB_NAME=COUNTRY_ID_db
        DB_PORT=5432
        DB_PW=password1
        DB_USER=db_user
        MAX_NUMBER_OF_MESSAGES=40
        PERSISTENT_DATABASE_WRITER_QUEUE=nest-queue-COUNTRY_ID-persistent_database_writer
        ORG=COUNTRY_ID
        ```
    - Timeout: 1 min
    - Assign IAM role with the following permissions:
        ```
        # standard AWS policy: AmazonSQSFullAccess
        # standard AWS policy: AWSXrayFullAccess
        # standard AWS policy: AWSLambdaVPCAccessExecutionRole
        # lambda-logs
          {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        ```
    - Network: the lambda should be with VPC and subnet that allows the access to selected RDS.