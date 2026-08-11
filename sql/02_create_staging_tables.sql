USE EcommerceDataEngineering;
GO

DROP TABLE IF EXISTS staging.OrderItems;
DROP TABLE IF EXISTS staging.Orders;
DROP TABLE IF EXISTS staging.Products;
DROP TABLE IF EXISTS staging.Customers;
GO

CREATE TABLE staging.Customers (
    customer_id VARCHAR(50) NULL,
    customer_unique_id VARCHAR(50) NULL,
    customer_zip_code_prefix VARCHAR(20) NULL,
    customer_city NVARCHAR(150) NULL,
    customer_state VARCHAR(10) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.Products (
    product_id VARCHAR(50) NULL,
    product_category_name NVARCHAR(200) NULL,
    product_name_lenght VARCHAR(20) NULL,
    product_description_lenght VARCHAR(20) NULL,
    product_photos_qty VARCHAR(20) NULL,
    product_weight_g VARCHAR(20) NULL,
    product_length_cm VARCHAR(20) NULL,
    product_height_cm VARCHAR(20) NULL,
    product_width_cm VARCHAR(20) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.Orders (
    order_id VARCHAR(50) NULL,
    customer_id VARCHAR(50) NULL,
    order_status VARCHAR(50) NULL,
    order_purchase_timestamp VARCHAR(50) NULL,
    order_approved_at VARCHAR(50) NULL,
    order_delivered_carrier_date VARCHAR(50) NULL,
    order_delivered_customer_date VARCHAR(50) NULL,
    order_estimated_delivery_date VARCHAR(50) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE staging.OrderItems (
    order_id VARCHAR(50) NULL,
    order_item_id VARCHAR(20) NULL,
    product_id VARCHAR(50) NULL,
    seller_id VARCHAR(50) NULL,
    shipping_limit_date VARCHAR(50) NULL,
    price VARCHAR(30) NULL,
    freight_value VARCHAR(30) NULL,
    source_file_name NVARCHAR(255) NULL,
    loaded_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO