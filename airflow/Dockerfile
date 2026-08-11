FROM apache/airflow:3.3.0

USER root

RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        unixodbc \
        unixodbc-dev \
        libgssapi-krb5-2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    "apache-airflow==3.3.0" \
    pyodbc \
    pandas \
    sqlalchemy \
    requests \
    python-dotenv \
