import json
import os
import random
import sys
import time
from datetime import datetime
from typing import Any

import pyodbc
from confluent_kafka import Consumer, KafkaError, KafkaException
from dotenv import load_dotenv

from db_connection import get_connection


load_dotenv()

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

TOPIC = os.getenv(
    "KAFKA_WEBSITE_TOPIC",
    "ecommerce.website.events",
)

CONSUMER_GROUP = os.getenv(
    "KAFKA_CONSUMER_GROUP",
    "ecommerce-sql-consumer",
)

BATCH_SIZE = 100
MAX_IDLE_POLLS = 10
MAX_DEADLOCK_RETRIES = 5


INSERT_SQL = """
IF NOT EXISTS (
    SELECT 1
    FROM streaming.WebsiteEvents
    WHERE event_id = ?
)
AND NOT EXISTS (
    SELECT 1
    FROM streaming.WebsiteEvents
    WHERE kafka_topic = ?
      AND kafka_partition = ?
      AND kafka_offset = ?
)
BEGIN
    INSERT INTO streaming.WebsiteEvents (
        event_id,
        session_id,
        customer_id,
        event_type,
        product_id,
        event_timestamp,
        device_type,
        traffic_source,
        kafka_topic,
        kafka_partition,
        kafka_offset
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
END;
"""


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).replace(tzinfo=None)


def is_deadlock(error: pyodbc.Error) -> bool:
    error_text = " ".join(
        str(argument)
        for argument in error.args
    )

    return (
        "1205" in error_text
        or "40001" in error_text
        or "deadlock" in error_text.lower()
    )


def insert_event(
    cursor: Any,
    record: dict[str, Any],
) -> None:
    event = record["event"]
    topic = record["topic"]
    partition = record["partition"]
    offset = record["offset"]

    parameters = (
        # First NOT EXISTS
        event["event_id"],

        # Second NOT EXISTS
        topic,
        partition,
        offset,

        # INSERT values
        event["event_id"],
        event["session_id"],
        event.get("customer_id"),
        event["event_type"],
        event.get("product_id"),
        parse_timestamp(event["event_timestamp"]),
        event.get("device_type"),
        event.get("traffic_source"),
        topic,
        partition,
        offset,
    )

    cursor.execute(INSERT_SQL, parameters)


def write_batch(
    records: list[dict[str, Any]],
) -> None:
    for attempt in range(
        1,
        MAX_DEADLOCK_RETRIES + 1,
    ):
        connection = None

        try:
            connection = get_connection()
            connection.autocommit = False

            cursor = connection.cursor()

            cursor.execute(
                "SET DEADLOCK_PRIORITY LOW;"
            )

            cursor.execute(
                "SET LOCK_TIMEOUT 15000;"
            )

            for record in records:
                insert_event(cursor, record)

            connection.commit()
            cursor.close()

            return

        except pyodbc.Error as error:
            if connection is not None:
                connection.rollback()

            if (
                is_deadlock(error)
                and attempt < MAX_DEADLOCK_RETRIES
            ):
                wait_seconds = (
                    2 ** (attempt - 1)
                    + random.uniform(0, 1)
                )

                print(
                    f"Deadlock detected. "
                    f"Retry {attempt}/"
                    f"{MAX_DEADLOCK_RETRIES} "
                    f"after {wait_seconds:.1f} seconds."
                )

                time.sleep(wait_seconds)
                continue

            raise

        finally:
            if connection is not None:
                connection.close()


def main() -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    batch: list[dict[str, Any]] = []
    total_processed = 0
    idle_polls = 0

    try:
        consumer.subscribe([TOPIC])

        print(f"Consumer group: {CONSUMER_GROUP}")
        print(f"Subscribed topic: {TOPIC}")
        print("Waiting for Kafka events...")

        while idle_polls < MAX_IDLE_POLLS:
            message = consumer.poll(1.0)

            if message is None:
                idle_polls += 1
                continue

            idle_polls = 0

            if message.error():
                if (
                    message.error().code()
                    == KafkaError._PARTITION_EOF
                ):
                    continue

                raise KafkaException(message.error())

            event = json.loads(
                message.value().decode("utf-8")
            )

            batch.append(
                {
                    "event": event,
                    "topic": message.topic(),
                    "partition": message.partition(),
                    "offset": message.offset(),
                }
            )

            if len(batch) >= BATCH_SIZE:
                write_batch(batch)

                # Commit Kafka offsets only after
                # SQL Server commit succeeds.
                consumer.commit(
                    asynchronous=False
                )

                total_processed += len(batch)

                print(
                    f"{total_processed:,} "
                    "events processed."
                )

                batch.clear()

        if batch:
            write_batch(batch)

            consumer.commit(
                asynchronous=False
            )

            total_processed += len(batch)
            batch.clear()

        print("\nKafka consumer completed.")
        print(
            f"Events processed: "
            f"{total_processed:,}"
        )

    except KeyboardInterrupt:
        print("\nConsumer stopped by user.")

    except Exception as error:
        print(f"Kafka consumer failed: {error}")
        sys.exit(1)

    finally:
        consumer.close()


if __name__ == "__main__":
    main()