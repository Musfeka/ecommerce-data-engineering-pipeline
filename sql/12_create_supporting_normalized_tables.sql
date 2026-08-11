USE EcommerceDataEngineering;
GO

IF OBJECT_ID('ecommerce.ProductCategories', 'U') IS NULL
BEGIN
    CREATE TABLE ecommerce.ProductCategories (
        product_category_name NVARCHAR(200) NOT NULL,
        product_category_name_english NVARCHAR(200) NOT NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_ProductCategories_LoadedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_ProductCategories
            PRIMARY KEY (product_category_name)
    );
END;
GO

IF OBJECT_ID('ecommerce.Sellers', 'U') IS NULL
BEGIN
    CREATE TABLE ecommerce.Sellers (
        seller_id VARCHAR(50) NOT NULL,
        seller_zip_code_prefix INT NULL,
        seller_city NVARCHAR(150) NULL,
        seller_state CHAR(2) NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_Sellers_LoadedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_Sellers
            PRIMARY KEY (seller_id)
    );
END;
GO

IF OBJECT_ID('ecommerce.Payments', 'U') IS NULL
BEGIN
    CREATE TABLE ecommerce.Payments (
        order_id VARCHAR(50) NOT NULL,
        payment_sequential INT NOT NULL,
        payment_type VARCHAR(50) NOT NULL,
        payment_installments INT NOT NULL,
        payment_value DECIMAL(14,2) NOT NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_Payments_LoadedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_Payments
            PRIMARY KEY (
                order_id,
                payment_sequential
            ),

        CONSTRAINT FK_Payments_Orders
            FOREIGN KEY (order_id)
            REFERENCES ecommerce.Orders(order_id),

        CONSTRAINT CK_Payments_Installments
            CHECK (payment_installments >= 0),

        CONSTRAINT CK_Payments_Value
            CHECK (payment_value >= 0)
    );
END;
GO

IF OBJECT_ID('ecommerce.Reviews', 'U') IS NULL
BEGIN
    CREATE TABLE ecommerce.Reviews (
        review_id VARCHAR(50) NOT NULL,
        order_id VARCHAR(50) NOT NULL,
        review_score TINYINT NOT NULL,
        review_comment_title NVARCHAR(MAX) NULL,
        review_comment_message NVARCHAR(MAX) NULL,
        review_creation_date DATETIME2 NULL,
        review_answer_timestamp DATETIME2 NULL,
        loaded_at DATETIME2 NOT NULL
            CONSTRAINT DF_Reviews_LoadedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_Reviews
            PRIMARY KEY (
                review_id,
                order_id
            ),

        CONSTRAINT FK_Reviews_Orders
            FOREIGN KEY (order_id)
            REFERENCES ecommerce.Orders(order_id),

        CONSTRAINT CK_Reviews_Score
            CHECK (review_score BETWEEN 1 AND 5)
    );
END;
GO

CREATE INDEX IX_Payments_PaymentType
ON ecommerce.Payments(payment_type);
GO

CREATE INDEX IX_Reviews_OrderId
ON ecommerce.Reviews(order_id);
GO

CREATE INDEX IX_Sellers_State
ON ecommerce.Sellers(seller_state);
GO