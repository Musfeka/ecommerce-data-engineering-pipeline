import logging

from db_connection import get_connection
from load_staging import load_dataset


SUPPORTING_DATASETS = [
    {
        "file": "olist_order_payments_dataset.csv",
        "table": "staging.Payments",
        "columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    },
    {
        "file": "olist_sellers_dataset.csv",
        "table": "staging.Sellers",
        "columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    },
    {
        "file": "olist_order_reviews_dataset.csv",
        "table": "staging.Reviews",
        "columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    },
    {
        "file": "product_category_name_translation.csv",
        "table": "staging.CategoryTranslation",
        "columns": [
            "product_category_name",
            "product_category_name_english",
        ],
    },
]


def main() -> None:
    connection = None

    try:
        connection = get_connection()

        print("SQL Server connection successful.")
        print("Supporting staging load started.")

        for dataset in SUPPORTING_DATASETS:
            loaded_rows = load_dataset(
                connection=connection,
                file_name=dataset["file"],
                table_name=dataset["table"],
                columns=dataset["columns"],
                batch_size=5000,
            )

            print(
                f"{dataset['table']}: "
                f"{loaded_rows:,} rows loaded."
            )

        print("Supporting staging load completed successfully.")

    except Exception:
        if connection is not None:
            connection.rollback()

        logging.exception("Supporting staging load failed.")
        raise

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()