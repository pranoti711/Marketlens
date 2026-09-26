import pandas as pd
import psycopg2
from io import StringIO

# ============================================================
# MARKETLENS - LOAD CLEANED DATA INTO POSTGRESQL
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "marketlens",
    "user": "postgres",
    "password": "IASTOBE7"
}

BASE_PATH = (
    r"C:\Users\Pranoti munjankar"
    r"\OneDrive\Desktop\DA PROJECTS\Marketlens"
)

FILES = {
    "global_ads": rf"{BASE_PATH}\data\cleaned\global_ads_performance_cleaned.csv",
    "kag_conversion": rf"{BASE_PATH}\data\cleaned\KAG_conversion_data_cleaned.csv",
    "marketing_ab": rf"{BASE_PATH}\data\cleaned\marketing_AB_cleaned.csv",
}


def quote_identifier(name):
    """Safely quote a PostgreSQL identifier."""
    return '"' + name.replace('"', '""') + '"'


def load_csv_to_postgres(cursor, table_name, file_path):
    print(f"\nLoading: {table_name}")
    print(f"File: {file_path}")

    df = pd.read_csv(file_path)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # Create table using TEXT first.
    # PostgreSQL will receive the exact CSV values.
    column_definitions = []

    for column in df.columns:
        column_definitions.append(
            f"{quote_identifier(column)} TEXT"
        )

    create_sql = f"""
        DROP TABLE IF EXISTS clean.{quote_identifier(table_name)};

        CREATE TABLE clean.{quote_identifier(table_name)} (
            {", ".join(column_definitions)}
        );
    """

    cursor.execute(create_sql)

    # Convert dataframe to CSV in memory
    buffer = StringIO()
    df.to_csv(buffer, index=False, na_rep="")

    buffer.seek(0)

    columns = ", ".join(
        quote_identifier(column)
        for column in df.columns
    )

    copy_sql = f"""
        COPY clean.{quote_identifier(table_name)}
        ({columns})
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER TRUE,
            NULL ''
        );
    """

    cursor.copy_expert(copy_sql, buffer)

    print(f"Loaded successfully: clean.{table_name}")


def main():

    connection = None

    try:

        connection = psycopg2.connect(**DB_CONFIG)

        connection.autocommit = False

        cursor = connection.cursor()

        # Make sure schema exists
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS clean;
        """)

        for table_name, file_path in FILES.items():

            load_csv_to_postgres(
                cursor,
                table_name,
                file_path
            )

        connection.commit()

        print("\n========================================")
        print("ALL DATASETS LOADED SUCCESSFULLY")
        print("========================================")

        cursor.close()

    except Exception as e:

        if connection:
            connection.rollback()

        print("\nERROR:")
        print(e)

    finally:

        if connection:
            connection.close()


if __name__ == "__main__":
    main()
