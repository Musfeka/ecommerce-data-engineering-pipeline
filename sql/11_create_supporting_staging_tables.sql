USE EcommerceDataEngineering;
GO

DROP TABLE IF EXISTS staging.Payments;
DROP TABLE IF EXISTS staging.Sellers;
DROP TABLE IF EXISTS staging.Reviews;
DROP TABLE IF EXISTS staging.CategoryTranslation;
GO

CREATE TABLE staging.Payments (
    order_id VARCHAR(50) NULL,
    payment_sequential VARCHAR(20) NULL,
    payment_type VARCHAR(50) NULL,
    payment_installments VARCHAR(20) NULL,
    payment_value VARCHAR(30) NULL,

    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_StagingPayments_LoadedAt
        DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.Sellers (
    seller_id VARCHAR(50) NULL,
    seller_zip_code_prefix VARCHAR(20) NULL,
    seller_city NVARCHAR(150) NULL,
    seller_state VARCHAR(10) NULL,

    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_StagingSellers_LoadedAt
        DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.Reviews (
    review_id VARCHAR(50) NULL,
    order_id VARCHAR(50) NULL,
    review_score VARCHAR(20) NULL,
    review_comment_title NVARCHAR(MAX) NULL,
    review_comment_message NVARCHAR(MAX) NULL,
    review_creation_date VARCHAR(50) NULL,
    review_answer_timestamp VARCHAR(50) NULL,

    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_StagingReviews_LoadedAt
        DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.CategoryTranslation (
    product_category_name NVARCHAR(200) NULL,
    product_category_name_english NVARCHAR(200) NULL,

    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_StagingCategoryTranslation_LoadedAt
        DEFAULT SYSDATETIME()
);
GO