import logging
import sys
from pathlib import Path

from db_connection import get_connection
from load_staging import main as load_staging_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "full_pipeline.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)


def execute_procedure(procedure_name: str) -> None:
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        logging.info("Executing procedure: %s", procedure_name)

        cursor.execute(f"EXEC {procedure_name}")
        connection.commit()

        logging.info(
            "Procedure completed successfully: %s",
            procedure_name,
        )

    except Exception:
        if connection is not None:
            connection.rollback()

        logging.exception(
            "Procedure failed: %s",
            procedure_name,
        )
        raise

    finally:
        if connection is not None:
            connection.close()


def validate_pipeline() -> None:
    connection = None

    validation_query = """
        SELECT 'staging.Customers', COUNT_BIG(*)
        FROM staging.Customers

        UNION ALL

        SELECT 'staging.Products', COUNT_BIG(*)
        FROM staging.Products

        UNION ALL

        SELECT 'staging.Orders', COUNT_BIG(*)
        FROM staging.Orders

        UNION ALL

        SELECT 'staging.OrderItems', COUNT_BIG(*)
        FROM staging.OrderItems

        UNION ALL

        SELECT 'ecommerce.Customers', COUNT_BIG(*)
        FROM ecommerce.Customers

        UNION ALL

        SELECT 'ecommerce.Products', COUNT_BIG(*)
        FROM ecommerce.Products

        UNION ALL

        SELECT 'ecommerce.Orders', COUNT_BIG(*)
        FROM ecommerce.Orders

        UNION ALL

        SELECT 'ecommerce.OrderItems', COUNT_BIG(*)
        FROM ecommerce.OrderItems

        UNION ALL

        SELECT 'warehouse.DimCustomer', COUNT_BIG(*)
        FROM warehouse.DimCustomer

        UNION ALL

        SELECT 'warehouse.DimProduct', COUNT_BIG(*)
        FROM warehouse.DimProduct

        UNION ALL

        SELECT 'warehouse.DimDate', COUNT_BIG(*)
        FROM warehouse.DimDate

        UNION ALL

        SELECT 'warehouse.DimLocation', COUNT_BIG(*)
        FROM warehouse.DimLocation

        UNION ALL

        SELECT 'warehouse.FactSales', COUNT_BIG(*)
        FROM warehouse.FactSales;
    """

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(validation_query)
        results = cursor.fetchall()

        logging.info("Pipeline row-count validation:")

        for table_name, row_count in results:
            logging.info(
                "%-30s %,d",
                table_name,
                row_count,
            )

        cursor.execute(
            """
            SELECT TOP 1
                run_id,
                status,
                customers_loaded,
                products_loaded,
                orders_loaded,
                order_items_loaded,
                error_message
            FROM audit.ETLRun
            ORDER BY run_id DESC;
            """
        )

        audit_result = cursor.fetchone()

        if audit_result is None:
            raise RuntimeError("No ETL audit record found.")

        logging.info(
            "Latest ETL run: run_id=%s, status=%s",
            audit_result.run_id,
            audit_result.status,
        )

        if audit_result.status != "Success":
            raise RuntimeError(
                "Latest normalized ETL run did not complete successfully. "
                f"Error: {audit_result.error_message}"
            )

        cursor.execute(
            """
            SELECT
                check_name,
                failed_records,
                status
            FROM audit.DataQualityResults
            WHERE run_id = (
                SELECT MAX(run_id)
                FROM audit.ETLRun
            )
            ORDER BY quality_result_id;
            """
        )

        quality_results = cursor.fetchall()

        logging.info("Data-quality results:")

        for check_name, failed_records, status in quality_results:
            logging.info(
                "%s | failed=%s | %s",
                check_name,
                failed_records,
                status,
            )

    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    try:
        logging.info("=" * 70)
        logging.info("E-commerce data pipeline started")
        logging.info("=" * 70)

        logging.info("STEP 1: Loading CSV files into staging")
        load_staging_data()

        logging.info("STEP 2: Loading normalized ecommerce tables")
        execute_procedure(
            "ecommerce.usp_LoadNormalizedData"
        )

        logging.info("STEP 3: Loading star-schema warehouse")
        execute_procedure(
            "warehouse.usp_LoadWarehouse"
        )

        logging.info("STEP 4: Validating pipeline")
        validate_pipeline()

        logging.info("=" * 70)
        logging.info("Full pipeline completed successfully")
        logging.info("=" * 70)

    except Exception:
        logging.exception("Full pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()