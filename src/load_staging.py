import logging
from pathlib import Path
from typing import Any

import pandas as pd

from db_connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "staging_load.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)

DATASETS = [
    {
        "file": "olist_customers_dataset.csv",
        "table": "staging.Customers",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    },
    {
        "file": "olist_products_dataset.csv",
        "table": "staging.Products",
        "columns": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    },
    {
        "file": "olist_orders_dataset.csv",
        "table": "staging.Orders",
        "columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    {
        "file": "olist_order_items_dataset.csv",
        "table": "staging.OrderItems",
        "columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    },
]


def clean_value(value: Any) -> str | None:
    if pd.isna(value):
        return None

    return str(value).strip()


def load_dataset(
    connection,
    file_name: str,
    table_name: str,
    columns: list[str],
    batch_size: int = 5000,
) -> int:
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    logging.info("Reading file: %s", file_name)

    dataframe = pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=True,
    )

    missing_columns = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in {file_name}: {missing_columns}"
        )

    dataframe = dataframe[columns]

    cursor = connection.cursor()
    cursor.fast_executemany = True

    cursor.execute(f"DELETE FROM {table_name}")

    insert_columns = columns + ["source_file_name"]
    column_sql = ", ".join(insert_columns)
    placeholders = ", ".join(["?"] * len(insert_columns))

    insert_sql = (
        f"INSERT INTO {table_name} "
        f"({column_sql}) "
        f"VALUES ({placeholders})"
    )

    total_loaded = 0

    for start_index in range(0, len(dataframe), batch_size):
        batch = dataframe.iloc[
            start_index:start_index + batch_size
        ]

        rows = []

        for record in batch.itertuples(index=False, name=None):
            cleaned_record = [
                clean_value(value)
                for value in record
            ]

            cleaned_record.append(file_name)
            rows.append(tuple(cleaned_record))

        cursor.executemany(insert_sql, rows)
        connection.commit()

        total_loaded += len(rows)

        logging.info(
            "%s: %,d rows loaded",
            table_name,
            total_loaded,
        )

    cursor.close()

    return total_loaded


def main() -> None:
    connection = None

    try:
        connection = get_connection()

        logging.info("SQL Server connection successful")
        logging.info("Starting staging load")

        for dataset in DATASETS:
            loaded_rows = load_dataset(
                connection=connection,
                file_name=dataset["file"],
                table_name=dataset["table"],
                columns=dataset["columns"],
            )

            logging.info(
                "Completed %s: %,d rows",
                dataset["table"],
                loaded_rows,
            )

        logging.info("All staging datasets loaded successfully")

    except Exception:
        if connection is not None:
            connection.rollback()

        logging.exception("Staging load failed")
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()