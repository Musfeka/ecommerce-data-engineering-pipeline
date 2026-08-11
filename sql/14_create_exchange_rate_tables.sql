USE EcommerceDataEngineering;
GO

IF OBJECT_ID('staging.ExchangeRates', 'U') IS NULL
BEGIN
    CREATE TABLE staging.ExchangeRates (
        rate_date VARCHAR(20) NULL,
        base_currency VARCHAR(10) NULL,
        quote_currency VARCHAR(10) NULL,
        exchange_rate VARCHAR(50) NULL,
        source_file_name NVARCHAR(255) NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_StagingExchangeRates_LoadedAt
            DEFAULT SYSDATETIME()
    );
END;
GO

IF OBJECT_ID('ecommerce.ExchangeRates', 'U') IS NULL
BEGIN
    CREATE TABLE ecommerce.ExchangeRates (
        rate_date DATE NOT NULL,
        base_currency CHAR(3) NOT NULL,
        quote_currency CHAR(3) NOT NULL,
        exchange_rate DECIMAL(18,8) NOT NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_ExchangeRates_LoadedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_ExchangeRates
            PRIMARY KEY (
                rate_date,
                base_currency,
                quote_currency
            ),

        CONSTRAINT CK_ExchangeRates_Rate
            CHECK (exchange_rate > 0)
    );
END;
GO

IF COL_LENGTH(
    'warehouse.FactSales',
    'exchange_rate_to_usd'
) IS NULL
BEGIN
    ALTER TABLE warehouse.FactSales
    ADD exchange_rate_to_usd DECIMAL(18,8) NULL;
END;
GO

IF COL_LENGTH(
    'warehouse.FactSales',
    'gross_amount_usd'
) IS NULL
BEGIN
    ALTER TABLE warehouse.FactSales
    ADD gross_amount_usd DECIMAL(18,2) NULL;
END;
GO

IF COL_LENGTH(
    'warehouse.FactSales',
    'total_amount_usd'
) IS NULL
BEGIN
    ALTER TABLE warehouse.FactSales
    ADD total_amount_usd DECIMAL(18,2) NULL;
END;
GO