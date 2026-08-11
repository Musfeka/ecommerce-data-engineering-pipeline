USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE warehouse.usp_LoadWarehouse
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        /* Dimension Customer */
        MERGE warehouse.DimCustomer AS target
        USING (
            SELECT DISTINCT
                customer_id,
                customer_unique_id
            FROM ecommerce.Customers
        ) AS source
            ON target.customer_id = source.customer_id

        WHEN MATCHED THEN
            UPDATE SET
                target.customer_unique_id =
                    source.customer_unique_id

        WHEN NOT MATCHED THEN
            INSERT (
                customer_id,
                customer_unique_id
            )
            VALUES (
                source.customer_id,
                source.customer_unique_id
            );

        /* Dimension Product */
        MERGE warehouse.DimProduct AS target
        USING (
            SELECT DISTINCT
                product_id,
                product_category_name,
                product_weight_g,
                product_length_cm,
                product_height_cm,
                product_width_cm
            FROM ecommerce.Products
        ) AS source
            ON target.product_id = source.product_id

        WHEN MATCHED THEN
            UPDATE SET
                target.product_category_name =
                    source.product_category_name,
                target.product_weight_g =
                    source.product_weight_g,
                target.product_length_cm =
                    source.product_length_cm,
                target.product_height_cm =
                    source.product_height_cm,
                target.product_width_cm =
                    source.product_width_cm

        WHEN NOT MATCHED THEN
            INSERT (
                product_id,
                product_category_name,
                product_weight_g,
                product_length_cm,
                product_height_cm,
                product_width_cm
            )
            VALUES (
                source.product_id,
                source.product_category_name,
                source.product_weight_g,
                source.product_length_cm,
                source.product_height_cm,
                source.product_width_cm
            );

        /* Dimension Location */
        MERGE warehouse.DimLocation AS target
        USING (
            SELECT DISTINCT
                customer_zip_code_prefix AS zip_code_prefix,
                customer_city AS city,
                customer_state AS state_code
            FROM ecommerce.Customers
        ) AS source
            ON ISNULL(target.zip_code_prefix, -1)
                = ISNULL(source.zip_code_prefix, -1)
           AND ISNULL(target.city, '')
                = ISNULL(source.city, '')
           AND ISNULL(target.state_code, '')
                = ISNULL(source.state_code, '')

        WHEN NOT MATCHED THEN
            INSERT (
                zip_code_prefix,
                city,
                state_code
            )
            VALUES (
                source.zip_code_prefix,
                source.city,
                source.state_code
            );

        /* Dimension Date */
        DECLARE @start_date DATE;
        DECLARE @end_date DATE;
        DECLARE @current_date DATE;
        DECLARE @date_key INT;

        SELECT
            @start_date = MIN(
                CAST(order_purchase_timestamp AS DATE)
            ),
            @end_date = MAX(
                CAST(order_purchase_timestamp AS DATE)
            )
        FROM ecommerce.Orders;

        SET @current_date = @start_date;

        WHILE @current_date <= @end_date
        BEGIN
            SET @date_key = CONVERT(
                INT,
                CONVERT(
                    CHAR(8),
                    @current_date,
                    112
                )
            );

            IF NOT EXISTS (
                SELECT 1
                FROM warehouse.DimDate
                WHERE date_key = @date_key
            )
            BEGIN
                INSERT INTO warehouse.DimDate (
                    date_key,
                    full_date,
                    day_number,
                    day_name,
                    week_number,
                    month_number,
                    month_name,
                    quarter_number,
                    year_number,
                    is_weekend
                )
                VALUES (
                    @date_key,
                    @current_date,
                    DAY(@current_date),
                    DATENAME(WEEKDAY, @current_date),
                    DATEPART(WEEK, @current_date),
                    MONTH(@current_date),
                    DATENAME(MONTH, @current_date),
                    DATEPART(QUARTER, @current_date),
                    YEAR(@current_date),
                    CASE
                        WHEN DATENAME(
                            WEEKDAY,
                            @current_date
                        ) IN ('Saturday', 'Sunday')
                        THEN 1
                        ELSE 0
                    END
                );
            END;

            SET @current_date = DATEADD(
                DAY,
                1,
                @current_date
            );
        END;

        /* Full refresh of FactSales */
        DELETE FROM warehouse.FactSales;

        INSERT INTO warehouse.FactSales (
            order_id,
            order_item_id,
            date_key,
            customer_key,
            product_key,
            location_key,
            quantity,
            unit_price,
            freight_value,
            gross_amount,
            total_amount,
            order_status,
            delivery_days
        )
        SELECT
            oi.order_id,
            oi.order_item_id,

            CONVERT(
                INT,
                CONVERT(
                    CHAR(8),
                    CAST(
                        o.order_purchase_timestamp
                        AS DATE
                    ),
                    112
                )
            ) AS date_key,

            dc.customer_key,
            dp.product_key,
            dl.location_key,

            1 AS quantity,
            oi.price AS unit_price,
            oi.freight_value,
            oi.price AS gross_amount,
            oi.price + oi.freight_value
                AS total_amount,

            o.order_status,

            CASE
                WHEN o.order_delivered_customer_date
                    IS NOT NULL
                THEN DATEDIFF(
                    DAY,
                    o.order_purchase_timestamp,
                    o.order_delivered_customer_date
                )
                ELSE NULL
            END AS delivery_days

        FROM ecommerce.OrderItems AS oi

        INNER JOIN ecommerce.Orders AS o
            ON o.order_id = oi.order_id

        INNER JOIN ecommerce.Customers AS c
            ON c.customer_id = o.customer_id

        INNER JOIN warehouse.DimCustomer AS dc
            ON dc.customer_id = c.customer_id

        INNER JOIN warehouse.DimProduct AS dp
            ON dp.product_id = oi.product_id

        INNER JOIN warehouse.DimLocation AS dl
            ON ISNULL(dl.zip_code_prefix, -1)
                = ISNULL(
                    c.customer_zip_code_prefix,
                    -1
                )
           AND ISNULL(dl.city, '')
                = ISNULL(c.customer_city, '')
           AND ISNULL(dl.state_code, '')
                = ISNULL(c.customer_state, '');

        COMMIT TRANSACTION;

        PRINT 'Warehouse loaded successfully.';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO