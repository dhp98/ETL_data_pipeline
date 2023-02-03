import boto3
import hashlib
import pandas as pd
import json
import logging

from datetime import datetime, timezone
from sqlalchemy import create_engine

# Queue URL :TODO: Pass from command line or a config file
queue_url = "http://localstack:4566/000000000000/login-queue"

# Setting up postgresql engine for database operations
engine = create_engine("postgresql://postgres:postgres@postgres:5432/postgres")

# Setting up logger
logger = logging.getLogger()


def transform_data(json_data: dict) -> pd.DataFrame:
    """
    Function to transform fields in the raw data
    """
    # Mask the device_id and ip fields with SHA256 encryption
    hashed_device_id = hashlib.sha256(json_data["device_id"].encode()).hexdigest()
    hashed_ip = hashlib.sha256(json_data["ip"].encode()).hexdigest()

    # Flatten the JSON data and add the masked fields
    flat_data = pd.json_normalize(json_data)
    flat_data.rename(
        columns={"device_id": "masked_device_id", "ip": "masked_ip"},
        inplace=True,
    )
    flat_data["masked_device_id"] = hashed_device_id
    flat_data["masked_ip"] = hashed_ip

    # format app version to suit integer data type in table
    flat_data["app_version"] = flat_data["app_version"].apply(
        lambda s: s.replace(".", "")
    )

    # store current date in UTC
    curr_utc_date = datetime.now(timezone.utc).date()
    flat_data["create_date"] = curr_utc_date

    return flat_data


def clear_queue_messages(sqs, entries):
    """
    Function to clear the processed messages from queue
    """
    logging.info("Clearing processed messages from queue.")
    resp = sqs.delete_message_batch(QueueUrl=queue_url, Entries=entries)

    if len(resp["Successful"]) != len(entries):
        raise RuntimeError(
            f"Failed to delete messages: entries={entries!r} resp={resp!r}"
        )


def store_messages_in_db(sqs, entries, new_messages: pd.DataFrame):
    """
    Function to store all the new sqs messages in postgresql.
    """
    try:
        new_messages.to_sql("user_logins", engine, if_exists="append", index=False)

        clear_queue_messages(sqs, entries)

        logging.info(f"Successfully Inserted {len(entries)} new messages in database")
    except:
        raise RuntimeError("Error Occured while storing new messages in database")


def run_pipeline(sqs: boto3):
    """
    Function to ingest sqs queue message into postgresql database in batches.
    """
    logging.info("Running data pipeline")
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url, AttributeNames=["All"], MaxNumberOfMessages=10
        )

        logger.info("Reading messages from SQS queue")
        # Extract the JSON data from the SQS message

        try:
            messages = response["Messages"]
        except KeyError:
            logging.info("No more messages to read. Queue empty")
            break

        logger.info(f"Total new messages received {len(response['Messages'])}")

        new_messages = pd.DataFrame()
        entries = []

        for message in messages:
            json_data = json.loads(message["Body"])

            if ("device_id" not in json_data) or ("ip" not in json_data):
                continue

            flat_data = transform_data(json_data)

            new_messages = pd.concat([new_messages, flat_data])

            entries.append(
                {"Id": message["MessageId"], "ReceiptHandle": message["ReceiptHandle"]}
            )

        store_messages_in_db(sqs, entries, new_messages)


if __name__ == "__main__":
    """
    Main function
    """
    # Setting up logger
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s"
    )

    sqs = boto3.client(
        "sqs",
        endpoint_url=queue_url,
        region_name="localhost",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    run_pipeline(sqs)
