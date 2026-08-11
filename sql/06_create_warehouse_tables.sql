USE EcommerceDataEngineering;
GO

DROP TABLE IF EXISTS warehouse.FactSales;
DROP TABLE IF EXISTS warehouse.DimLocation;
DROP TABLE IF EXISTS warehouse.DimDate;
DROP TABLE IF EXISTS warehouse.DimProduct;
DROP TABLE IF EXISTS warehouse.DimCustomer;
GO

CREATE TABLE warehouse.DimCustomer (
    customer_key BIGINT IDENTITY(1,1) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    customer_unique_id VARCHAR(50) NOT NULL,
    created_at DATETIME2 NOT NULL
        CONSTRAINT DF_DimCustomer_CreatedAt
        DEFAULT SYSDATETIME(),

    CONSTRAINT PK_DimCustomer
        PRIMARY KEY (customer_key),

    CONSTRAINT UQ_DimCustomer_CustomerId
        UNIQUE (customer_id)
);
GO

CREATE TABLE warehouse.DimProduct (
    product_key BIGINT IDENTITY(1,1) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_category_name NVARCHAR(200) NULL,
    product_weight_g DECIMAL(12,2) NULL,
    product_length_cm DECIMAL(12,2) NULL,
    product_height_cm DECIMAL(12,2) NULL,
    product_width_cm DECIMAL(12,2) NULL,
    created_at DATETIME2 NOT NULL
        CONSTRAINT DF_DimProduct_CreatedAt
        DEFAULT SYSDATETIME(),

    CONSTRAINT PK_DimProduct
        PRIMARY KEY (product_key),

    CONSTRAINT UQ_DimProduct_ProductId
        UNIQUE (product_id)
);
GO

CREATE TABLE warehouse.DimDate (
    date_key INT NOT NULL,
    full_date DATE NOT NULL,
    day_number INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    week_number INT NOT NULL,
    month_number INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter_number INT NOT NULL,
    year_number INT NOT NULL,
    is_weekend BIT NOT NULL,

    CONSTRAINT PK_DimDate
        PRIMARY KEY (date_key),

    CONSTRAINT UQ_DimDate_FullDate
        UNIQUE (full_date)
);
GO

CREATE TABLE warehouse.DimLocation (
    location_key BIGINT IDENTITY(1,1) NOT NULL,
    zip_code_prefix INT NULL,
    city NVARCHAR(150) NULL,
    state_code CHAR(2) NULL,
    created_at DATETIME2 NOT NULL
        CONSTRAINT DF_DimLocation_CreatedAt
        DEFAULT SYSDATETIME(),

    CONSTRAINT PK_DimLocation
        PRIMARY KEY (location_key)
);
GO

CREATE TABLE warehouse.FactSales (
    sales_key BIGINT IDENTITY(1,1) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    order_item_id INT NOT NULL,

    date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    location_key BIGINT NOT NULL,

    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    freight_value DECIMAL(12,2) NOT NULL,
    gross_amount DECIMAL(14,2) NOT NULL,
    total_amount DECIMAL(14,2) NOT NULL,

    order_status VARCHAR(30) NOT NULL,
    delivery_days INT NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_FactSales_LoadedAt
        DEFAULT SYSDATETIME(),

    CONSTRAINT PK_FactSales
        PRIMARY KEY (sales_key),

    CONSTRAINT UQ_FactSales_OrderItem
        UNIQUE (order_id, order_item_id),

    CONSTRAINT FK_FactSales_DimDate
        FOREIGN KEY (date_key)
        REFERENCES warehouse.DimDate(date_key),

    CONSTRAINT FK_FactSales_DimCustomer
        FOREIGN KEY (customer_key)
        REFERENCES warehouse.DimCustomer(customer_key),

    CONSTRAINT FK_FactSales_DimProduct
        FOREIGN KEY (product_key)
        REFERENCES warehouse.DimProduct(product_key),

    CONSTRAINT FK_FactSales_DimLocation
        FOREIGN KEY (location_key)
        REFERENCES warehouse.DimLocation(location_key),

    CONSTRAINT CK_FactSales_Quantity
        CHECK (quantity > 0),

    CONSTRAINT CK_FactSales_Amounts
        CHECK (
            unit_price >= 0
            AND freight_value >= 0
            AND gross_amount >= 0
            AND total_amount >= 0
        )
);
GO

CREATE INDEX IX_FactSales_DateKey
ON warehouse.FactSales(date_key);
GO

CREATE INDEX IX_FactSales_CustomerKey
ON warehouse.FactSales(customer_key);
GO

CREATE INDEX IX_FactSales_ProductKey
ON warehouse.FactSales(product_key);
GO

CREATE INDEX IX_FactSales_LocationKey
ON warehouse.FactSales(location_key);
GO