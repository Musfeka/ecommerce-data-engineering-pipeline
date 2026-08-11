from __future__ import annotations

import sys

import pendulum
from airflow.sdk import dag, task

sys.path.insert(0, "/opt/airflow/project/src")

from db_connection import get_connection
from load_staging import main as load_staging_data


def execute_procedure(procedure_name: str):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(f"EXEC {procedure_name};")
        connection.commit()

        print(f"{procedure_name} completed successfully.")

    finally:
        connection.close()


@dag(
    dag_id="ecommerce_pipeline",
    description="End-to-end E-Commerce ETL Pipeline",
    schedule=None,
    start_date=pendulum.datetime(2026, 8, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["ecommerce", "etl", "sql-server", "warehouse"],
)
def ecommerce_pipeline():

    @task
    def check_sql_server():
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    SUSER_SNAME(),
                    DB_NAME(),
                    @@SERVERNAME;
                """
            )

            row = cursor.fetchone()

            print(f"Login: {row[0]}")
            print(f"Database: {row[1]}")
            print(f"Server: {row[2]}")

        finally:
            connection.close()

    @task(retries=1)
    def load_staging():
        print("Starting CSV to staging load...")
        load_staging_data()
        print("CSV to staging load completed successfully.")

    @task(retries=2)
    def load_normalized():
        execute_procedure(
            "ecommerce.usp_LoadNormalizedData"
        )

    @task(retries=2)
    def load_supporting_data():
        execute_procedure(
            "ecommerce.usp_LoadSupportingData"
        )

    @task(retries=2)
    def extract_exchange_rates():
        from extract_exchange_rates import main

        print("Starting Exchange Rate API extraction...")
        main()
        print("Exchange Rate API extraction completed.")

    @task(retries=2)
    def load_exchange_rates():
        execute_procedure(
            "ecommerce.usp_LoadExchangeRates"
        )

    @task(retries=2)
    def load_warehouse():
        execute_procedure(
            "warehouse.usp_LoadWarehouse"
        )

    @task(retries=2)
    def apply_exchange_rates():
        execute_procedure(
            "warehouse.usp_ApplyExchangeRates"
        )

    @task
    def validate_pipeline():
        connection = get_connection()

        checks = [
            "staging.Customers",
            "staging.Products",
            "staging.Orders",
            "staging.OrderItems",
            "staging.ExchangeRates",
            "ecommerce.Customers",
            "ecommerce.Products",
            "ecommerce.Orders",
            "ecommerce.OrderItems",
            "ecommerce.ExchangeRates",
            "warehouse.DimCustomer",
            "warehouse.DimProduct",
            "warehouse.FactSales",
        ]

        try:
            cursor = connection.cursor()

            for table in checks:
                cursor.execute(
                    f"SELECT COUNT_BIG(*) FROM {table};"
                )

                count = cursor.fetchone()[0]

                print(f"{table}: {count:,} rows")

                if count == 0:
                    raise ValueError(
                        f"Validation failed: "
                        f"{table} contains zero rows."
                    )

            print("DATA QUALITY VALIDATION PASSED")

        finally:
            connection.close()

    check = check_sql_server()
    staging = load_staging()
    normalized = load_normalized()
    supporting = load_supporting_data()
    extract_rates = extract_exchange_rates()
    load_rates = load_exchange_rates()
    warehouse = load_warehouse()
    apply_rates = apply_exchange_rates()
    validation = validate_pipeline()

    (
        check
        >> staging
        >> normalized
        >> supporting
        >> extract_rates
        >> load_rates
        >> warehouse
        >> apply_rates
        >> validation
    )


ecommerce_pipeline()