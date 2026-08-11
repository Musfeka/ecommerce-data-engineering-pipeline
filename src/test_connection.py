import os
import sys

import pyodbc
from dotenv import load_dotenv


load_dotenv()

driver = os.getenv("DB_DRIVER")
server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")

if not all([driver, server, database]):
    print("Missing database configuration in .env file.")
    sys.exit(1)

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

connection = None

try:
    connection = pyodbc.connect(connection_string, timeout=10)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            @@SERVERNAME AS server_name,
            DB_NAME() AS database_name,
            SUSER_SNAME() AS login_name
        """
    )

    result = cursor.fetchone()

    print("SQL Server connection successful.")
    print(f"Server: {result.server_name}")
    print(f"Database: {result.database_name}")
    print(f"Login: {result.login_name}")

except pyodbc.Error as error:
    print("SQL Server connection failed.")
    print(error)
    sys.exit(1)

finally:
    if connection is not None:
        connection.close()