import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from db_connection import get_connection


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "exchange_rates"
)
LOG_DIR = PROJECT_ROOT / "logs"

RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "exchange_rate_load.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)


def get_order_date_range(
    connection: Any,
) -> tuple[str, str]:
    """
    Fetch the Olist order date range.

    Seven extra days are included before the first order
    so weekend orders can use the previous business day's rate.
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            CONVERT(
                VARCHAR(10),
                DATEADD(
                    DAY,
                    -7,
                    MIN(
                        CAST(
                            order_purchase_timestamp
                            AS DATE
                        )
                    )
                ),
                23
            ) AS start_date,
            CONVERT(
                VARCHAR(10),
                MAX(
                    CAST(
                        order_purchase_timestamp
                        AS DATE
                    )
                ),
                23
            ) AS end_date
        FROM ecommerce.Orders;
        """
    )

    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise RuntimeError(
            "Could not determine the order date range."
        )

    if not result.start_date or not result.end_date:
        raise RuntimeError(
            "ecommerce.Orders contains no order dates."
        )

    return result.start_date, result.end_date


def fetch_exchange_rates(
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, Any]], Path]:
    api_url = os.getenv("EXCHANGE_RATE_API_URL")
    base_currency = os.getenv(
        "EXCHANGE_RATE_BASE",
        "BRL",
    )
    quote_currency = os.getenv(
        "EXCHANGE_RATE_QUOTE",
        "USD",
    )

    if not api_url:
        raise ValueError(
            "EXCHANGE_RATE_API_URL is missing from .env."
        )

    params = {
        "from": start_date,
        "to": end_date,
        "base": base_currency,
        "quotes": quote_currency,
    }

    logging.info(
        "Requesting %s/%s exchange rates "
        "from %s to %s",
        base_currency,
        quote_currency,
        start_date,
        end_date,
    )

    response = requests.get(
        api_url,
        params=params,
        timeout=120,
    )
    response.raise_for_status()

    output_file = RAW_OUTPUT_DIR / (
        f"{base_currency}_{quote_currency}"
        f"_{start_date}_{end_date}.json"
    )

    # Preserve the original API response.
    output_file.write_text(
        response.text,
        encoding="utf-8",
    )

    data = json.loads(
        response.text,
        parse_float=Decimal,
    )

    if not isinstance(data, list):
        raise ValueError(
            "Unexpected API response: expected a list."
        )

    if not data:
        raise ValueError(
            "The exchange-rate API returned no rows."
        )

    required_fields = {
        "date",
        "base",
        "quote",
        "rate",
    }

    for row_number, row in enumerate(data, start=1):
        missing_fields = required_fields - row.keys()

        if missing_fields:
            raise ValueError(
                f"Row {row_number} is missing fields: "
                f"{sorted(missing_fields)}"
            )

    logging.info(
        "%s exchange-rate rows received.",
        len(data),
    )
    logging.info(
        "Raw response saved to: %s",
        output_file,
    )

    return data, output_file


def load_staging_exchange_rates(
    connection: Any,
    exchange_rates: list[dict[str, Any]],
    source_file: Path,
) -> int:
    cursor = connection.cursor()
    cursor.fast_executemany = True

    cursor.execute(
    "DELETE FROM staging.ExchangeRates;"
)

    insert_sql = """
        INSERT INTO staging.ExchangeRates (
            rate_date,
            base_currency,
            quote_currency,
            exchange_rate,
            source_file_name
        )
        VALUES (?, ?, ?, ?, ?);
    """

    rows = [
        (
            row["date"],
            row["base"],
            row["quote"],
            str(row["rate"]),
            source_file.name,
        )
        for row in exchange_rates
    ]

    cursor.executemany(insert_sql, rows)
    connection.commit()
    cursor.close()

    logging.info(
        "%s rows loaded into staging.ExchangeRates.",
        len(rows),
    )

    return len(rows)


def main() -> None:
    connection = None

    try:
        connection = get_connection()

        start_date, end_date = get_order_date_range(
            connection
        )

        exchange_rates, source_file = (
            fetch_exchange_rates(
                start_date=start_date,
                end_date=end_date,
            )
        )

        loaded_rows = load_staging_exchange_rates(
            connection=connection,
            exchange_rates=exchange_rates,
            source_file=source_file,
        )

        print(
            "Exchange-rate extraction completed "
            f"successfully: {loaded_rows:,} rows."
        )

    except Exception:
        if connection is not None:
            connection.rollback()

        logging.exception(
            "Exchange-rate extraction failed."
        )
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()