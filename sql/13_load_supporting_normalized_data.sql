USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE ecommerce.usp_LoadSupportingData
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM ecommerce.Reviews;
        DELETE FROM ecommerce.Payments;

        /* Product category translation update */
        UPDATE target
        SET
            target.product_category_name_english =
                LOWER(
                    LTRIM(
                        RTRIM(
                            source.product_category_name_english
                        )
                    )
                )
        FROM ecommerce.ProductCategories AS target
        INNER JOIN staging.CategoryTranslation AS source
            ON target.product_category_name =
                LOWER(
                    LTRIM(
                        RTRIM(
                            source.product_category_name
                        )
                    )
                );

        /* New product categories */
        INSERT INTO ecommerce.ProductCategories (
            product_category_name,
            product_category_name_english
        )
        SELECT DISTINCT
            LOWER(
                LTRIM(
                    RTRIM(
                        source.product_category_name
                    )
                )
            ),
            LOWER(
                LTRIM(
                    RTRIM(
                        source.product_category_name_english
                    )
                )
            )
        FROM staging.CategoryTranslation AS source
        WHERE NULLIF(
            LTRIM(RTRIM(source.product_category_name)),
            ''
        ) IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM ecommerce.ProductCategories AS target
            WHERE target.product_category_name =
                LOWER(
                    LTRIM(
                        RTRIM(
                            source.product_category_name
                        )
                    )
                )
        );

        /* Existing sellers update */
        UPDATE target
        SET
            target.seller_zip_code_prefix =
                TRY_CONVERT(
                    INT,
                    source.seller_zip_code_prefix
                ),
            target.seller_city =
                LOWER(
                    NULLIF(
                        LTRIM(RTRIM(source.seller_city)),
                        ''
                    )
                ),
            target.seller_state =
                UPPER(
                    NULLIF(
                        LTRIM(RTRIM(source.seller_state)),
                        ''
                    )
                )
        FROM ecommerce.Sellers AS target
        INNER JOIN staging.Sellers AS source
            ON target.seller_id =
                LTRIM(RTRIM(source.seller_id));

        /* New sellers */
        INSERT INTO ecommerce.Sellers (
            seller_id,
            seller_zip_code_prefix,
            seller_city,
            seller_state
        )
        SELECT
            LTRIM(RTRIM(source.seller_id)),
            TRY_CONVERT(
                INT,
                source.seller_zip_code_prefix
            ),
            LOWER(
                NULLIF(
                    LTRIM(RTRIM(source.seller_city)),
                    ''
                )
            ),
            UPPER(
                NULLIF(
                    LTRIM(RTRIM(source.seller_state)),
                    ''
                )
            )
        FROM staging.Sellers AS source
        WHERE NULLIF(
            LTRIM(RTRIM(source.seller_id)),
            ''
        ) IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM ecommerce.Sellers AS target
            WHERE target.seller_id =
                LTRIM(RTRIM(source.seller_id))
        );

        /* Payments */
        INSERT INTO ecommerce.Payments (
            order_id,
            payment_sequential,
            payment_type,
            payment_installments,
            payment_value
        )
        SELECT
            LTRIM(RTRIM(source.order_id)),
            TRY_CONVERT(
                INT,
                source.payment_sequential
            ),
            LOWER(
                LTRIM(
                    RTRIM(source.payment_type)
                )
            ),
            TRY_CONVERT(
                INT,
                source.payment_installments
            ),
            TRY_CONVERT(
                DECIMAL(14,2),
                source.payment_value
            )
        FROM staging.Payments AS source
        INNER JOIN ecommerce.Orders AS orders
            ON orders.order_id =
                LTRIM(RTRIM(source.order_id))
        WHERE TRY_CONVERT(
            INT,
            source.payment_sequential
        ) IS NOT NULL
        AND TRY_CONVERT(
            INT,
            source.payment_installments
        ) IS NOT NULL
        AND TRY_CONVERT(
            DECIMAL(14,2),
            source.payment_value
        ) IS NOT NULL;

        /* Reviews */
        ;WITH ReviewSource AS (
            SELECT
                source.*,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        source.review_id,
                        source.order_id
                    ORDER BY source.loaded_at DESC
                ) AS row_number
            FROM staging.Reviews AS source
        )
        INSERT INTO ecommerce.Reviews (
            review_id,
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            review_answer_timestamp
        )
        SELECT
            LTRIM(RTRIM(source.review_id)),
            LTRIM(RTRIM(source.order_id)),
            TRY_CONVERT(
                TINYINT,
                source.review_score
            ),
            NULLIF(
                LTRIM(RTRIM(source.review_comment_title)),
                ''
            ),
            NULLIF(
                LTRIM(RTRIM(source.review_comment_message)),
                ''
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(
                    source.review_creation_date,
                    ''
                )
            ),
            TRY_CONVERT(
                DATETIME2,
                NULLIF(
                    source.review_answer_timestamp,
                    ''
                )
            )
        FROM ReviewSource AS source
        INNER JOIN ecommerce.Orders AS orders
            ON orders.order_id =
                LTRIM(RTRIM(source.order_id))
        WHERE source.row_number = 1
        AND TRY_CONVERT(
            TINYINT,
            source.review_score
        ) BETWEEN 1 AND 5;

        /* Add English category to DimProduct */
        UPDATE dim_product
        SET
            dim_product.product_category_name_english =
                ISNULL(
                    categories.product_category_name_english,
                    'unknown'
                )
        FROM warehouse.DimProduct AS dim_product
        LEFT JOIN ecommerce.ProductCategories AS categories
            ON categories.product_category_name =
                dim_product.product_category_name;

        COMMIT TRANSACTION;

        PRINT 'Supporting normalized data loaded successfully.';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO