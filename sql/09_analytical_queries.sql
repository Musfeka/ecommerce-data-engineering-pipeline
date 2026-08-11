USE EcommerceDataEngineering;
GO

SELECT
    year_number,
    month_number,
    month_name,
    total_orders,
    total_items,
    total_revenue
FROM warehouse.vw_MonthlySales
ORDER BY
    year_number,
    month_number;
GO