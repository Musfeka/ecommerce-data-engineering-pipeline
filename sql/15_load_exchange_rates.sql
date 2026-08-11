USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE
    ecommerce.usp_LoadExchangeRates
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM ecommerce.ExchangeRates;

        ;WITH ExchangeRateSource AS (
            SELECT
                TRY_CONVERT(
                    DATE,
                    rate_date
                ) AS converted_rate_date,

                UPPER(
                    LTRIM(
                        RTRIM(base_currency)
                    )
                ) AS converted_base_currency,

                UPPER(
                    LTRIM(
                        RTRIM(quote_currency)
                    )
                ) AS converted_quote_currency,

                TRY_CONVERT(
                    DECIMAL(18,8),
                    exchange_rate
                ) AS converted_exchange_rate,

                ROW_NUMBER() OVER (
                    PARTITION BY
                        TRY_CONVERT(DATE, rate_date),
                        UPPER(
                            LTRIM(RTRIM(base_currency))
                        ),
                        UPPER(
                            LTRIM(RTRIM(quote_currency))
                        )
                    ORDER BY loaded_at DESC
                ) AS row_number

            FROM staging.ExchangeRates
        )

        INSERT INTO ecommerce.ExchangeRates (
            rate_date,
            base_currency,
            quote_currency,
            exchange_rate
        )
        SELECT
            converted_rate_date,
            converted_base_currency,
            converted_quote_currency,
            converted_exchange_rate
        FROM ExchangeRateSource
        WHERE row_number = 1
          AND converted_rate_date IS NOT NULL
          AND LEN(converted_base_currency) = 3
          AND LEN(converted_quote_currency) = 3
          AND converted_exchange_rate > 0;

        COMMIT TRANSACTION;

        PRINT 'Exchange rates loaded successfully.';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO