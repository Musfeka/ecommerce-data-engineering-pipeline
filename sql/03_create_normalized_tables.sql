USE EcommerceDataEngineering;
GO

/* Child tables আগে drop করতে হবে */
DROP TABLE IF EXISTS ecommerce.OrderItems;
DROP TABLE IF EXISTS ecommerce.Orders;
DROP TABLE IF EXISTS ecommerce.Products;
DROP TABLE IF EXISTS ecommerce.Customers;
GO

CREATE TABLE ecommerce.Customers (
    customer_id VARCHAR(50) NOT NULL,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix INT NULL,
    customer_city NVARCHAR(150) NULL,
    customer_state CHAR(2) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_Customers_LoadedAt DEFAULT SYSDATETIME(),

    CONSTRAINT PK_Customers
        PRIMARY KEY (customer_id)
);
GO

CREATE TABLE ecommerce.Products (
    product_id VARCHAR(50) NOT NULL,
    product_category_name NVARCHAR(200) NULL,
    product_name_length INT NULL,
    product_description_length INT NULL,
    product_photos_quantity INT NULL,
    product_weight_g DECIMAL(12, 2) NULL,
    product_length_cm DECIMAL(12, 2) NULL,
    product_height_cm DECIMAL(12, 2) NULL,
    product_width_cm DECIMAL(12, 2) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_Products_LoadedAt DEFAULT SYSDATETIME(),

    CONSTRAINT PK_Products
        PRIMARY KEY (product_id)
);
GO

CREATE TABLE ecommerce.Orders (
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    order_purchase_timestamp DATETIME2 NOT NULL,
    order_approved_at DATETIME2 NULL,
    order_delivered_carrier_date DATETIME2 NULL,
    order_delivered_customer_date DATETIME2 NULL,
    order_estimated_delivery_date DATETIME2 NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_Orders_LoadedAt DEFAULT SYSDATETIME(),

    CONSTRAINT PK_Orders
        PRIMARY KEY (order_id),

    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (customer_id)
        REFERENCES ecommerce.Customers(customer_id),

    CONSTRAINT CK_Orders_Status
        CHECK (
            order_status IN (
                'approved',
                'canceled',
                'created',
                'delivered',
                'invoiced',
                'processing',
                'shipped',
                'unavailable'
            )
        )
);
GO

CREATE TABLE ecommerce.OrderItems (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INT NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date DATETIME2 NULL,
    price DECIMAL(12, 2) NOT NULL,
    freight_value DECIMAL(12, 2) NOT NULL,
    line_total AS (price + freight_value) PERSISTED,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL
        CONSTRAINT DF_OrderItems_LoadedAt DEFAULT SYSDATETIME(),

    CONSTRAINT PK_OrderItems
        PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (order_id)
        REFERENCES ecommerce.Orders(order_id),

    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (product_id)
        REFERENCES ecommerce.Products(product_id),

    CONSTRAINT CK_OrderItems_Price
        CHECK (price >= 0),

    CONSTRAINT CK_OrderItems_Freight
        CHECK (freight_value >= 0)
);
GO

CREATE INDEX IX_Orders_CustomerId
ON ecommerce.Orders(customer_id);
GO

CREATE INDEX IX_Orders_PurchaseTimestamp
ON ecommerce.Orders(order_purchase_timestamp);
GO

CREATE INDEX IX_Orders_Status
ON ecommerce.Orders(order_status);
GO

CREATE INDEX IX_OrderItems_ProductId
ON ecommerce.OrderItems(product_id);
GO