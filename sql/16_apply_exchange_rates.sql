USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE
    warehouse.usp_ApplyExchangeRates
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE fact_sales
        SET
            fact_sales.exchange_rate_to_usd =
                selected_rate.exchange_rate,

            fact_sales.gross_amount_usd =
                ROUND(
                    fact_sales.gross_amount
                    * selected_rate.exchange_rate,
                    2
                ),

            fact_sales.total_amount_usd =
                ROUND(
                    fact_sales.total_amount
                    * selected_rate.exchange_rate,
                    2
                )

        FROM warehouse.FactSales AS fact_sales

        INNER JOIN warehouse.DimDate AS dim_date
            ON dim_date.date_key =
                fact_sales.date_key

        CROSS APPLY (
            SELECT TOP 1
                exchange_rates.exchange_rate
            FROM ecommerce.ExchangeRates
                AS exchange_rates
            WHERE
                exchange_rates.base_currency = 'BRL'
                AND exchange_rates.quote_currency = 'USD'
                AND exchange_rates.rate_date
                    <= dim_date.full_date
            ORDER BY
                exchange_rates.rate_date DESC
        ) AS selected_rate;

        COMMIT TRANSACTION;

        PRINT 'USD conversion applied successfully.';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO