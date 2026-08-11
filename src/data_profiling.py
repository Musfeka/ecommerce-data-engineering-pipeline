from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "olist"

FILES = [
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "product_category_name_translation.csv",
]


def profile_file(file_name: str) -> None:
    file_path = DATA_DIR / file_name

    print("\n" + "=" * 80)
    print(f"FILE: {file_name}")
    print("=" * 80)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    try:
        df = pd.read_csv(file_path)

        print(f"Rows: {df.shape[0]:,}")
        print(f"Columns: {df.shape[1]}")
        print(f"Duplicate rows: {df.duplicated().sum():,}")

        print("\nColumn names:")
        for column in df.columns:
            print(f"- {column}")

        print("\nData types:")
        print(df.dtypes)

        print("\nNull values:")
        null_counts = df.isnull().sum()
        print(null_counts[null_counts > 0])

        print("\nFirst 5 rows:")
        print(df.head())

    except Exception as error:
        print(f"Error reading {file_name}: {error}")


def main() -> None:
    print(f"Dataset folder: {DATA_DIR}")

    for file_name in FILES:
        profile_file(file_name)


if __name__ == "__main__":
    main()