USE EcommerceDataEngineering;
GO

CREATE OR ALTER VIEW warehouse.vw_SalesDetail
AS
SELECT
    fs.sales_key,
    fs.order_id,
    fs.order_item_id,
    dd.full_date AS order_date,
    dd.month_name,
    dd.quarter_number,
    dd.year_number,
    dc.customer_id,
    dc.customer_unique_id,
    dp.product_id,
    dp.product_category_name,
    dl.city,
    dl.state_code,
    fs.quantity,
    fs.unit_price,
    fs.freight_value,
    fs.gross_amount,
    fs.total_amount,
    fs.order_status,
    fs.delivery_days
FROM warehouse.FactSales AS fs
INNER JOIN warehouse.DimDate AS dd
    ON dd.date_key = fs.date_key
INNER JOIN warehouse.DimCustomer AS dc
    ON dc.customer_key = fs.customer_key
INNER JOIN warehouse.DimProduct AS dp
    ON dp.product_key = fs.product_key
INNER JOIN warehouse.DimLocation AS dl
    ON dl.location_key = fs.location_key;
GO