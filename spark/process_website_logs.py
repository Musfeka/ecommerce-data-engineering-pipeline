from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "website_logs"
    / "website_events.jsonl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "website_analytics"
)

EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("event_timestamp", StringType(), True),
        StructField("device_type", StringType(), True),
        StructField("traffic_source", StringType(), True),
    ]
)


def create_spark_session() -> SparkSession:
    warehouse_dir = PROJECT_ROOT / "spark_warehouse"

    return (
        SparkSession.builder
        .appName("OlistWebsiteAnalytics")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "8")
        .config(
            "spark.sql.warehouse.dir",
            str(warehouse_dir),
        )
        .getOrCreate()
    )


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Website log file not found: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        events = (
            spark.read
            .schema(EVENT_SCHEMA)
            .json(str(INPUT_FILE))
            .withColumn(
                "event_timestamp",
                F.to_timestamp("event_timestamp"),
            )
            .withColumn(
                "event_date",
                F.to_date("event_timestamp"),
            )
        )

        total_events = events.count()

        print(f"\nTotal events: {total_events:,}")

        valid_events = events.filter(
            F.col("event_id").isNotNull()
            & F.col("session_id").isNotNull()
            & F.col("event_type").isNotNull()
            & F.col("event_timestamp").isNotNull()
        )

        valid_count = valid_events.count()
        invalid_count = total_events - valid_count

        print(f"Valid events: {valid_count:,}")
        print(f"Invalid events: {invalid_count:,}")

        # Event type analysis
        event_summary = (
            valid_events
            .groupBy("event_type")
            .agg(
                F.count("*").alias("event_count"),
                F.countDistinct("session_id").alias(
                    "unique_sessions"
                ),
                F.countDistinct("customer_id").alias(
                    "unique_customers"
                ),
            )
            .orderBy(F.desc("event_count"))
        )

        # Daily website analytics
        daily_metrics = (
            valid_events
            .groupBy("event_date")
            .agg(
                F.count("*").alias("total_events"),
                F.countDistinct("session_id").alias(
                    "total_sessions"
                ),
                F.countDistinct("customer_id").alias(
                    "unique_customers"
                ),
                F.sum(
                    F.when(
                        F.col("event_type") == "product_view",
                        1,
                    ).otherwise(0)
                ).alias("product_views"),
                F.sum(
                    F.when(
                        F.col("event_type") == "add_to_cart",
                        1,
                    ).otherwise(0)
                ).alias("cart_additions"),
                F.sum(
                    F.when(
                        F.col("event_type") == "checkout",
                        1,
                    ).otherwise(0)
                ).alias("checkouts"),
                F.sum(
                    F.when(
                        F.col("event_type") == "purchase",
                        1,
                    ).otherwise(0)
                ).alias("purchases"),
            )
            .orderBy("event_date")
        )

        # One row per session
        session_funnel = (
            valid_events
            .groupBy("session_id")
            .agg(
                F.max(
                    F.when(
                        F.col("event_type") == "product_view",
                        1,
                    ).otherwise(0)
                ).alias("viewed_product"),
                F.max(
                    F.when(
                        F.col("event_type") == "add_to_cart",
                        1,
                    ).otherwise(0)
                ).alias("added_to_cart"),
                F.max(
                    F.when(
                        F.col("event_type") == "checkout",
                        1,
                    ).otherwise(0)
                ).alias("started_checkout"),
                F.max(
                    F.when(
                        F.col("event_type") == "purchase",
                        1,
                    ).otherwise(0)
                ).alias("completed_purchase"),
            )
        )

        funnel_metrics = (
            session_funnel
            .agg(
                F.count("*").alias("total_sessions"),
                F.sum("viewed_product").alias(
                    "product_view_sessions"
                ),
                F.sum("added_to_cart").alias(
                    "cart_sessions"
                ),
                F.sum("started_checkout").alias(
                    "checkout_sessions"
                ),
                F.sum("completed_purchase").alias(
                    "purchase_sessions"
                ),
            )
            .withColumn(
                "conversion_rate_percent",
                F.round(
                    F.col("purchase_sessions")
                    * 100.0
                    / F.col("total_sessions"),
                    2,
                ),
            )
            .withColumn(
                "cart_abandonment_rate_percent",
                F.when(
                    F.col("cart_sessions") > 0,
                    F.round(
                        (
                            F.col("cart_sessions")
                            - F.col("purchase_sessions")
                        )
                        * 100.0
                        / F.col("cart_sessions"),
                        2,
                    ),
                ),
            )
        )

        # Product engagement
        product_metrics = (
            valid_events
            .filter(F.col("product_id").isNotNull())
            .groupBy("product_id")
            .agg(
                F.sum(
                    F.when(
                        F.col("event_type") == "product_view",
                        1,
                    ).otherwise(0)
                ).alias("product_views"),
                F.sum(
                    F.when(
                        F.col("event_type") == "add_to_cart",
                        1,
                    ).otherwise(0)
                ).alias("cart_additions"),
                F.sum(
                    F.when(
                        F.col("event_type") == "purchase",
                        1,
                    ).otherwise(0)
                ).alias("purchases"),
            )
            .withColumn(
                "view_to_purchase_rate_percent",
                F.when(
                    F.col("product_views") > 0,
                    F.round(
                        F.col("purchases")
                        * 100.0
                        / F.col("product_views"),
                        2,
                    ),
                ),
            )
        )

        # Device analysis
        device_metrics = (
            valid_events
            .groupBy("device_type")
            .agg(
                F.count("*").alias("total_events"),
                F.countDistinct("session_id").alias(
                    "total_sessions"
                ),
            )
            .orderBy(F.desc("total_sessions"))
        )

        # Traffic source analysis
        traffic_metrics = (
            valid_events
            .groupBy("traffic_source")
            .agg(
                F.countDistinct("session_id").alias(
                    "total_sessions"
                ),
                F.sum(
                    F.when(
                        F.col("event_type") == "purchase",
                        1,
                    ).otherwise(0)
                ).alias("purchases"),
            )
            .withColumn(
                "purchase_rate_percent",
                F.round(
                    F.col("purchases")
                    * 100.0
                    / F.col("total_sessions"),
                    2,
                ),
            )
        )

        print("\nEvent summary:")
        event_summary.show(truncate=False)

        print("\nFunnel metrics:")
        funnel_metrics.show(truncate=False)

        print("\nDevice metrics:")
        device_metrics.show(truncate=False)

        # Parquet outputs
               # Windows-friendly local CSV outputs

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        CSV_OUTPUT_DIR = OUTPUT_DIR / "csv"

        CSV_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        def save_csv(dataframe, output_file):
            pandas_df = dataframe.toPandas()

            pandas_df.to_csv(
                output_file,
                index=False,
                encoding="utf-8",
            )

            print(f"Saved: {output_file}")

        save_csv(
            event_summary,
            OUTPUT_DIR / "event_summary.csv",
        )

        save_csv(
            daily_metrics,
            OUTPUT_DIR / "daily_metrics.csv",
        )

        save_csv(
            session_funnel,
            OUTPUT_DIR / "session_funnel.csv",
        )

        save_csv(
            product_metrics,
            OUTPUT_DIR / "product_metrics.csv",
        )

        save_csv(
            traffic_metrics,
            OUTPUT_DIR / "traffic_metrics.csv",
        )

        save_csv(
            funnel_metrics,
            CSV_OUTPUT_DIR / "funnel_metrics.csv",
        )

        save_csv(
            event_summary,
            CSV_OUTPUT_DIR / "event_summary.csv",
        )

        save_csv(
            device_metrics,
            CSV_OUTPUT_DIR / "device_metrics.csv",
        )

        save_csv(
            traffic_metrics,
            CSV_OUTPUT_DIR / "traffic_metrics.csv",
        )

        print("\nSpark processing completed successfully.")
        print(f"Output folder: {OUTPUT_DIR}")        # Windows-friendly local CSV outputs

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        CSV_OUTPUT_DIR = OUTPUT_DIR / "csv"

        CSV_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        def save_csv(dataframe, output_file):
            pandas_df = dataframe.toPandas()

            pandas_df.to_csv(
                output_file,
                index=False,
                encoding="utf-8",
            )

            print(f"Saved: {output_file}")

        save_csv(
            event_summary,
            OUTPUT_DIR / "event_summary.csv",
        )

        save_csv(
            daily_metrics,
            OUTPUT_DIR / "daily_metrics.csv",
        )

        save_csv(
            session_funnel,
            OUTPUT_DIR / "session_funnel.csv",
        )

        save_csv(
            product_metrics,
            OUTPUT_DIR / "product_metrics.csv",
        )

        save_csv(
            traffic_metrics,
            OUTPUT_DIR / "traffic_metrics.csv",
        )

        save_csv(
            funnel_metrics,
            CSV_OUTPUT_DIR / "funnel_metrics.csv",
        )

        save_csv(
            event_summary,
            CSV_OUTPUT_DIR / "event_summary.csv",
        )

        save_csv(
            device_metrics,
            CSV_OUTPUT_DIR / "device_metrics.csv",
        )

        save_csv(
            traffic_metrics,
            CSV_OUTPUT_DIR / "traffic_metrics.csv",
        )

        print("\nSpark processing completed successfully.")
        print(f"Output folder: {OUTPUT_DIR}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()