import json
import os
import sys
from pathlib import Path
from typing import Any

from confluent_kafka import KafkaError, KafkaException, Producer
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "website_logs"
    / "website_events.jsonl"
)

BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

TOPIC = os.getenv(
    "KAFKA_WEBSITE_TOPIC",
    "ecommerce.website.events",
)


class DeliveryTracker:
    def __init__(self) -> None:
        self.delivered = 0
        self.failed = 0

    def callback(self, error: KafkaError | None, message: Any) -> None:
        if error is not None:
            self.failed += 1
            print(f"Delivery failed: {error}")
            return

        self.delivered += 1

        if self.delivered % 1000 == 0:
            print(
                f"{self.delivered:,} events delivered "
                f"to Kafka."
            )


def validate_event(event: dict[str, Any], line_number: int) -> None:
    required_fields = {
        "event_id",
        "session_id",
        "event_type",
        "event_timestamp",
    }

    missing_fields = [
        field
        for field in required_fields
        if not event.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"Line {line_number} missing required fields: "
            f"{missing_fields}"
        )


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)

    producer = Producer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "client.id": "ecommerce-website-producer",
            "acks": "all",
            "enable.idempotence": True,
            "linger.ms": 20,
            "compression.type": "snappy",
        }
    )

    tracker = DeliveryTracker()
    total_read = 0

    print(f"Kafka server: {BOOTSTRAP_SERVERS}")
    print(f"Kafka topic: {TOPIC}")
    print(f"Input file: {INPUT_FILE}")

    try:
        with INPUT_FILE.open(
            "r",
            encoding="utf-8",
        ) as input_handle:
            for line_number, line in enumerate(
                input_handle,
                start=1,
            ):
                line = line.strip()

                if not line:
                    continue

                event = json.loads(line)
                validate_event(event, line_number)

                message_value = json.dumps(
                    event,
                    ensure_ascii=False,
                ).encode("utf-8")

                message_key = event["session_id"].encode(
                    "utf-8"
                )

                while True:
                    try:
                        producer.produce(
                            topic=TOPIC,
                            key=message_key,
                            value=message_value,
                            on_delivery=tracker.callback,
                        )
                        break

                    except BufferError:
                        producer.poll(0.5)

                producer.poll(0)
                total_read += 1

        remaining_messages = producer.flush(30)

        if remaining_messages > 0:
            raise KafkaException(
                f"{remaining_messages} messages were not delivered."
            )

        print("\nKafka producer completed.")
        print(f"Events read: {total_read:,}")
        print(f"Events delivered: {tracker.delivered:,}")
        print(f"Events failed: {tracker.failed:,}")

        if tracker.failed > 0:
            sys.exit(1)

    except Exception as error:
        print(f"Kafka producer failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()