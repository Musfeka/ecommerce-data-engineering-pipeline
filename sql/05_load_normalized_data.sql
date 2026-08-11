USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE ecommerce.usp_LoadNormalizedData
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @run_id BIGINT;
    DECLARE @customers_loaded BIGINT = 0;
    DECLARE @products_loaded BIGINT = 0;
    DECLARE @orders_loaded BIGINT = 0;
    DECLARE @order_items_loaded BIGINT = 0;

    INSERT INTO audit.ETLRun (
        pipeline_name,
        start_time,
        status
    )
    VALUES (
        'Olist Staging To Normalized',
        SYSDATETIME(),
        'Running'
    );

    SET @run_id = SCOPE_IDENTITY();

    BEGIN TRY
        BEGIN TRANSACTION;

        /* Existing data child table থেকে delete */
        DELETE FROM ecommerce.OrderItems;
        DELETE FROM ecommerce.Orders;
        DELETE FROM ecommerce.Products;
        DELETE FROM ecommerce.Customers;

        /* Customers */
        ;WITH CustomerSource AS (
            SELECT
                customer_id,
                customer_unique_id,
                customer_zip_code_prefix,
                customer_city,
                customer_state,
                source_file_name,
                ROW_NUMBER() OVER (
                    PARTITION BY customer_id
                    ORDER BY loaded_at DESC
                ) AS row_number
            FROM staging.Customers
            WHERE NULLIF(LTRIM(RTRIM(customer_id)), '') IS NOT NULL
              AND NULLIF(
                    LTRIM(RTRIM(customer_unique_id)),
                    ''
                  ) IS NOT NULL
        )
        INSERT INTO ecommerce.Customers (
            customer_id,
            customer_unique_id,
            customer_zip_code_prefix,
            customer_city,
            customer_state,
            source_file_name
        )
        SELECT
            LTRIM(RTRIM(customer_id)),
            LTRIM(RTRIM(customer_unique_id)),
            TRY_CONVERT(
                INT,
                NULLIF(customer_zip_code_prefix, '')
            ),
            LOWER(
                NULLIF(LTRIM(RTRIM(customer_city)), '')
            ),
            UPPER(
                NULLIF(LTRIM(RTRIM(customer_state)), '')
            ),
            source_file_name
        FROM CustomerSource
        WHERE row_number = 1;

        SET @customers_loaded = @@ROWCOUNT;

        /* Products */
        ;WITH ProductSource AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY product_id
                    ORDER BY loaded_at DESC
                ) AS row_number
            FROM staging.Products
            WHERE NULLIF(LTRIM(RTRIM(product_id)), '') IS NOT NULL
        )
        INSERT INTO ecommerce.Products (
            product_id,
            product_category_name,
            product_name_length,
            product_description_length,
            product_photos_quantity,
            product_weight_g,
            product_length_cm,
            product_height_cm,
            product_width_cm,
            source_file_name
        )
        SELECT
            LTRIM(RTRIM(product_id)),
            LOWER(
                NULLIF(
                    LTRIM(RTRIM(product_category_name)),
                    ''
                )
            ),
            TRY_CONVERT(INT, product_name_lenght),
            TRY_CONVERT(INT, product_description_lenght),
            TRY_CONVERT(INT, product_photos_qty),
            TRY_CONVERT(DECIMAL(12,2), product_weight_g),
            TRY_CONVERT(DECIMAL(12,2), product_length_cm),
            TRY_CONVERT(DECIMAL(12,2), product_height_cm),
            TRY_CONVERT(DECIMAL(12,2), product_width_cm),
            source_file_name
        FROM ProductSource
        WHERE row_number = 1;

        SET @products_loaded = @@ROWCOUNT;

        /* Orders */
        ;WITH OrderSource AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id
                    ORDER BY loaded_at DESC
                ) AS row_number
            FROM staging.Orders
            WHERE NULLIF(LTRIM(RTRIM(order_id)), '') IS NOT NULL
        )
        INSERT INTO ecommerce.Orders (
            order_id,
            customer_id,
            order_status,
            order_purchase_timestamp,
            order_approved_at,
            order_delivered_carrier_date,
            order_delivered_customer_date,
            order_estimated_delivery_date,
            source_file_name
        )
        SELECT
            LTRIM(RTRIM(s.order_id)),
            LTRIM(RTRIM(s.customer_id)),
            LOWER(LTRIM(RTRIM(s.order_status))),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_purchase_timestamp, '')
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_approved_at, '')
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_delivered_carrier_date, '')
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_delivered_customer_date, '')
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_estimated_delivery_date, '')
            ),
            s.source_file_name
        FROM OrderSource AS s
        INNER JOIN ecommerce.Customers AS c
            ON c.customer_id = LTRIM(RTRIM(s.customer_id))
        WHERE s.row_number = 1
          AND TRY_CONVERT(
                DATETIME2,
                NULLIF(s.order_purchase_timestamp, '')
              ) IS NOT NULL;

        SET @orders_loaded = @@ROWCOUNT;

        /* Order Items */
        ;WITH OrderItemSource AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY order_id, order_item_id
                    ORDER BY loaded_at DESC
                ) AS row_number
            FROM staging.OrderItems
            WHERE NULLIF(LTRIM(RTRIM(order_id)), '') IS NOT NULL
        )
        INSERT INTO ecommerce.OrderItems (
            order_id,
            order_item_id,
            product_id,
            seller_id,
            shipping_limit_date,
            price,
            freight_value,
            source_file_name
        )
        SELECT
            LTRIM(RTRIM(s.order_id)),
            TRY_CONVERT(INT, s.order_item_id),
            LTRIM(RTRIM(s.product_id)),
            LTRIM(RTRIM(s.seller_id)),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(s.shipping_limit_date, '')
            ),
            TRY_CONVERT(DECIMAL(12,2), s.price),
            TRY_CONVERT(DECIMAL(12,2), s.freight_value),
            s.source_file_name
        FROM OrderItemSource AS s
        INNER JOIN ecommerce.Orders AS o
            ON o.order_id = LTRIM(RTRIM(s.order_id))
        INNER JOIN ecommerce.Products AS p
            ON p.product_id = LTRIM(RTRIM(s.product_id))
        WHERE s.row_number = 1
          AND TRY_CONVERT(INT, s.order_item_id) IS NOT NULL
          AND TRY_CONVERT(DECIMAL(12,2), s.price) IS NOT NULL
          AND TRY_CONVERT(
                DECIMAL(12,2),
                s.freight_value
              ) IS NOT NULL;

        SET @order_items_loaded = @@ROWCOUNT;

        /* Data-quality checks */
        INSERT INTO audit.DataQualityResults (
            run_id,
            table_name,
            check_name,
            failed_records,
            status
        )
        SELECT
            @run_id,
            'staging.Customers',
            'Null customer ID',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.Customers
        WHERE NULLIF(LTRIM(RTRIM(customer_id)), '') IS NULL

        UNION ALL

        SELECT
            @run_id,
            'staging.Products',
            'Null product ID',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.Products
        WHERE NULLIF(LTRIM(RTRIM(product_id)), '') IS NULL

        UNION ALL

        SELECT
            @run_id,
            'staging.Orders',
            'Invalid customer reference',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.Orders AS s
        LEFT JOIN ecommerce.Customers AS c
            ON c.customer_id = LTRIM(RTRIM(s.customer_id))
        WHERE c.customer_id IS NULL

        UNION ALL

        SELECT
            @run_id,
            'staging.OrderItems',
            'Invalid order reference',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.OrderItems AS s
        LEFT JOIN ecommerce.Orders AS o
            ON o.order_id = LTRIM(RTRIM(s.order_id))
        WHERE o.order_id IS NULL

        UNION ALL

        SELECT
            @run_id,
            'staging.OrderItems',
            'Invalid product reference',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.OrderItems AS s
        LEFT JOIN ecommerce.Products AS p
            ON p.product_id = LTRIM(RTRIM(s.product_id))
        WHERE p.product_id IS NULL

        UNION ALL

        SELECT
            @run_id,
            'staging.OrderItems',
            'Invalid price',
            COUNT_BIG(*),
            CASE WHEN COUNT_BIG(*) = 0
                THEN 'PASS'
                ELSE 'FAIL'
            END
        FROM staging.OrderItems
        WHERE TRY_CONVERT(DECIMAL(12,2), price) IS NULL;

        COMMIT TRANSACTION;

        UPDATE audit.ETLRun
        SET
            end_time = SYSDATETIME(),
            customers_loaded = @customers_loaded,
            products_loaded = @products_loaded,
            orders_loaded = @orders_loaded,
            order_items_loaded = @order_items_loaded,
            status = 'Success'
        WHERE run_id = @run_id;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        UPDATE audit.ETLRun
        SET
            end_time = SYSDATETIME(),
            status = 'Failed',
            error_message = ERROR_MESSAGE()
        WHERE run_id = @run_id;

        THROW;
    END CATCH;
END;
GO