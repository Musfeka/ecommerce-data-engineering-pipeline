from __future__ import annotations

import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from db_connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "website_logs"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_OUTPUT_FILE = OUTPUT_DIR / "website_events.csv"
JSONL_OUTPUT_FILE = OUTPUT_DIR / "website_events.jsonl"

RANDOM_SEED = 42
SESSION_COUNT = 50_000

DEVICES = [
    "mobile",
    "desktop",
    "tablet",
]

TRAFFIC_SOURCES = [
    "direct",
    "organic_search",
    "paid_search",
    "social_media",
    "email",
    "referral",
]

SEARCH_TERMS = [
    "electronics",
    "home decoration",
    "health beauty",
    "sports leisure",
    "furniture",
    "watches",
    "toys",
    "computers",
    "fashion",
    "books",
]

FIELD_NAMES = [
    "event_id",
    "session_id",
    "customer_id",
    "event_type",
    "product_id",
    "search_term",
    "event_timestamp",
    "page_url",
    "device_type",
    "traffic_source",
    "ip_address",
]


def load_reference_data() -> tuple[
    list[str],
    list[str],
    datetime,
    datetime,
]:
    connection = None

    try:
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
                MIN(order_purchase_timestamp)
                    AS minimum_order_date,
                MAX(order_purchase_timestamp)
                    AS maximum_order_date
            FROM ecommerce.Orders;
            """
        )

        date_result = cursor.fetchone()

        if not customer_ids:
            raise RuntimeError(
                "No customer records found."
            )

        if not product_ids:
            raise RuntimeError(
                "No product records found."
            )

        if (
            date_result is None
            or date_result.minimum_order_date is None
            or date_result.maximum_order_date is None
        ):
            raise RuntimeError(
                "Order date range could not be found."
            )

        return (
            customer_ids,
            product_ids,
            date_result.minimum_order_date,
            date_result.maximum_order_date,
        )

    finally:
        if connection is not None:
            connection.close()


def random_datetime(
    start_date: datetime,
    end_date: datetime,
) -> datetime:
    total_seconds = int(
        (end_date - start_date).total_seconds()
    )

    random_seconds = random.randint(
        0,
        max(total_seconds, 1),
    )

    return start_date + timedelta(
        seconds=random_seconds
    )


def create_event(
    session_id: str,
    customer_id: str | None,
    event_type: str,
    event_timestamp: datetime,
    device_type: str,
    traffic_source: str,
    ip_address: str,
    product_id: str | None = None,
    search_term: str | None = None,
) -> dict[str, Any]:
    page_url_map = {
        "page_view": "/",
        "search": "/search",
        "product_view": (
            f"/products/{product_id}"
            if product_id
            else "/products"
        ),
        "add_to_cart": "/cart",
        "checkout": "/checkout",
        "purchase": "/order-confirmation",
    }

    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id,
        "customer_id": customer_id,
        "event_type": event_type,
        "product_id": product_id,
        "search_term": search_term,
        "event_timestamp": (
            event_timestamp.isoformat(
                timespec="seconds"
            )
        ),
        "page_url": page_url_map[event_type],
        "device_type": device_type,
        "traffic_source": traffic_source,
        "ip_address": ip_address,
    }


def write_event(
    event: dict[str, Any],
    csv_writer: csv.DictWriter,
    jsonl_file: Any,
) -> None:
    csv_writer.writerow(event)

    jsonl_file.write(
        json.dumps(
            event,
            ensure_ascii=False,
        )
        + "\n"
    )


def generate_session_events(
    customer_ids: list[str],
    product_ids: list[str],
    minimum_date: datetime,
    maximum_date: datetime,
) -> int:
    total_events = 0

    with (
        CSV_OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file,
        JSONL_OUTPUT_FILE.open(
            "w",
            encoding="utf-8",
        ) as jsonl_file,
    ):
        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=FIELD_NAMES,
        )

        csv_writer.writeheader()

        for session_number in range(
            1,
            SESSION_COUNT + 1,
        ):
            session_id = (
                f"SES-{uuid.uuid4().hex[:16]}"
            )

            customer_id = (
                random.choice(customer_ids)
                if random.random() < 0.85
                else None
            )

            device_type = random.choice(DEVICES)
            traffic_source = random.choice(
                TRAFFIC_SOURCES
            )

            ip_address = (
                "198.51.100."
                f"{random.randint(1, 254)}"
            )

            event_time = random_datetime(
                minimum_date,
                maximum_date,
            )

            # Home page view
            event = create_event(
                session_id=session_id,
                customer_id=customer_id,
                event_type="page_view",
                event_timestamp=event_time,
                device_type=device_type,
                traffic_source=traffic_source,
                ip_address=ip_address,
            )

            write_event(
                event,
                csv_writer,
                jsonl_file,
            )
            total_events += 1

            # Optional search
            if random.random() < 0.55:
                event_time += timedelta(
                    seconds=random.randint(5, 90)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type="search",
                    event_timestamp=event_time,
                    device_type=device_type,
                    traffic_source=traffic_source,
                    ip_address=ip_address,
                    search_term=random.choice(
                        SEARCH_TERMS
                    ),
                )

                write_event(
                    event,
                    csv_writer,
                    jsonl_file,
                )
                total_events += 1

            selected_product = random.choice(
                product_ids
            )

            # Product view
            event_time += timedelta(
                seconds=random.randint(5, 120)
            )

            event = create_event(
                session_id=session_id,
                customer_id=customer_id,
                event_type="product_view",
                event_timestamp=event_time,
                device_type=device_type,
                traffic_source=traffic_source,
                ip_address=ip_address,
                product_id=selected_product,
            )

            write_event(
                event,
                csv_writer,
                jsonl_file,
            )
            total_events += 1

            # Optional second product view
            if random.random() < 0.35:
                selected_product = random.choice(
                    product_ids
                )

                event_time += timedelta(
                    seconds=random.randint(10, 180)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type="product_view",
                    event_timestamp=event_time,
                    device_type=device_type,
                    traffic_source=traffic_source,
                    ip_address=ip_address,
                    product_id=selected_product,
                )

                write_event(
                    event,
                    csv_writer,
                    jsonl_file,
                )
                total_events += 1

            added_to_cart = random.random() < 0.45

            if added_to_cart:
                event_time += timedelta(
                    seconds=random.randint(5, 120)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type="add_to_cart",
                    event_timestamp=event_time,
                    device_type=device_type,
                    traffic_source=traffic_source,
                    ip_address=ip_address,
                    product_id=selected_product,
                )

                write_event(
                    event,
                    csv_writer,
                    jsonl_file,
                )
                total_events += 1

            checkout_started = (
                added_to_cart
                and random.random() < 0.60
            )

            if checkout_started:
                event_time += timedelta(
                    seconds=random.randint(10, 180)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type="checkout",
                    event_timestamp=event_time,
                    device_type=device_type,
                    traffic_source=traffic_source,
                    ip_address=ip_address,
                    product_id=selected_product,
                )

                write_event(
                    event,
                    csv_writer,
                    jsonl_file,
                )
                total_events += 1

            purchase_completed = (
                checkout_started
                and random.random() < 0.70
            )

            if purchase_completed:
                event_time += timedelta(
                    seconds=random.randint(10, 180)
                )

                event = create_event(
                    session_id=session_id,
                    customer_id=customer_id,
                    event_type="purchase",
                    event_timestamp=event_time,
                    device_type=device_type,
                    traffic_source=traffic_source,
                    ip_address=ip_address,
                    product_id=selected_product,
                )

                write_event(
                    event,
                    csv_writer,
                    jsonl_file,
                )
                total_events += 1

            if session_number % 5_000 == 0:
                print(
                    f"{session_number:,} sessions "
                    f"processed — "
                    f"{total_events:,} events generated."
                )

    return total_events


def main() -> None:
    random.seed(RANDOM_SEED)

    print("Loading customer and product IDs...")

    (
        customer_ids,
        product_ids,
        minimum_date,
        maximum_date,
    ) = load_reference_data()

    print(
        f"Customers loaded: {len(customer_ids):,}"
    )
    print(
        f"Products loaded: {len(product_ids):,}"
    )
    print(
        f"Event date range: "
        f"{minimum_date} to {maximum_date}"
    )

    total_events = generate_session_events(
        customer_ids=customer_ids,
        product_ids=product_ids,
        minimum_date=minimum_date,
        maximum_date=maximum_date,
    )

    print("\nWebsite log generation completed.")
    print(f"Sessions: {SESSION_COUNT:,}")
    print(f"Events: {total_events:,}")
    print(f"CSV: {CSV_OUTPUT_FILE}")
    print(f"JSONL: {JSONL_OUTPUT_FILE}")


if __name__ == "__main__":
    main()