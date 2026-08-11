import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT / ".env",
    override=False,
)


def get_connection():
    driver = os.getenv(
        "DB_DRIVER",
        "ODBC Driver 18 for SQL Server",
    )

    server = os.getenv(
        "DB_SERVER",
        "BS-01092",
    )

    database = os.getenv(
        "DB_DATABASE",
        "EcommerceDataEngineering",
    )

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    trust_certificate = os.getenv(
        "DB_TRUST_SERVER_CERTIFICATE",
        "yes",
    )

    connection_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        "Encrypt=yes",
        f"TrustServerCertificate={trust_certificate}",
    ]

    if user and password:
        connection_parts.extend(
            [
                f"UID={user}",
                f"PWD={password}",
            ]
        )
    else:
        connection_parts.append(
            "Trusted_Connection=yes"
        )

    connection_string = ";".join(
        connection_parts
    ) + ";"

    return pyodbc.connect(
        connection_string,
        timeout=30,
    )