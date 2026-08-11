import csv
import json
import random
import uuid
from datetime import timedelta
from pathlib import Path

from db_connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "website_logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = OUTPUT_DIR / "website_events.csv"
JSONL_FILE = OUTPUT_DIR / "website_events.jsonl"

SESSION_COUNT = 5000

EVENT_FIELDS = [
    "event_id",
    "session_id",
    "customer_id",
    "event_type",
    "product_id",
    "event_timestamp",
    "device_type",
    "traffic_source",
]


def load_reference_data():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT customer_id
        FROM ecommerce.Customers;
        """
    )

    customer_ids = [
        row.customer_id
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT product_id
        FROM ecommerce.Products;
        """
    )

    product_ids = [
        row.product_id
        for row in cursor.fetchall()
    ]

    cursor.execute(
        """
        SELECT
            MIN(order_purchase_timestamp),
            MAX(order_purchase_timestamp)
        FROM ecommerce.Orders;
        """
    )

    date_result = cursor.fetchone()

    cursor.close()
    connection.close()

    if not customer_ids:
        raise RuntimeError("No customers found.")

    if not product_ids:
        raise RuntimeError("No products found.")

    if not date_result[0] or not date_result[1]:
        raise RuntimeError("Order date range not found.")

    return (
        customer_ids,
        product_ids,
        date_result[0],
        date_result[1],
    )


def random_datetime(start_date, end_date):
    total_seconds = int(
        (end_date - start_date).total_seconds()
    )

    return start_date + timedelta(
        seconds=random.randint(0, total_seconds)
    )


def create_event(
    session_id,
    customer_id,
    event_type,
    product_id,
    timestamp,
    device_type,
    traffic_source,
):
    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id,
        "customer_id": customer_id,
        "event_type": event_type,
        "product_id": product_id,
        "event_timestamp": timestamp.isoformat(
            timespec="seconds"
        ),
        "device_type": device_type,
        "traffic_source": traffic_source,
    }


def generate_logs():
    (
        customer_ids,
        product_ids,
        minimum_date,
        maximum_date,
    ) = load_reference_data()

    devices = [
        "mobile",
        "desktop",
        "tablet",
    ]

    traffic_sources = [
        "direct",
        "organic_search",
        "paid_search",
        "social_media",
        "email",
    ]

    total_events = 0

    with (
        CSV_FILE.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_handle,
        JSONL_FILE.open(
            "w",
            encoding="utf-8",
        ) as json_handle,
    ):
        csv_writer = csv.DictWriter(
            csv_handle,
            fieldnames=EVENT_FIELDS,
        )

        csv_writer.writeheader()

        for session_number in range(
            1,
            SESSION_COUNT + 1,
        ):
            session_id = (
                f"SES-{uuid.uuid4().hex[:16]}"
            )

            customer_id = random.choice(
                customer_ids
            )

            product_id = random.choice(
                product_ids
            )

            timestamp = random_datetime(
                minimum_date,
                maximum_date,
            )

            device_type = random.choice(devices)

            traffic_source = random.choice(
                traffic_sources
            )

            event_types = [
                "page_view",
                "product_view",
            ]

            if random.random() < 0.45:
                event_types.append("add_to_cart")

            if (
                "add_to_cart" in event_types
                and random.random() < 0.60
            ):
                event_types.append("checkout")

            if (
                "checkout" in event_types
                and random.random() < 0.70
            ):
                event_types.append("purchase")

            for event_type in event_types:
                timestamp += timedelta(
                    seconds=random.randint(5, 120)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type=event_type,
                    product_id=product_id,
                    timestamp=timestamp,
                    device_type=device_type,
                    traffic_source=traffic_source,
                )

                csv_writer.writerow(event)

                json_handle.write(
                    json.dumps(event) + "\n"
                )

                total_events += 1

            if session_number % 1000 == 0:
                print(
                    f"{session_number:,} sessions processed"
                )

    print("\nWebsite logs created successfully.")
    print(f"Sessions: {SESSION_COUNT:,}")
    print(f"Events: {total_events:,}")
    print(f"CSV file: {CSV_FILE}")
    print(f"JSONL file: {JSONL_FILE}")


if __name__ == "__main__":
    random.seed(42)
    generate_logs()