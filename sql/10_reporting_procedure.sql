USE EcommerceDataEngineering;
GO

CREATE OR ALTER PROCEDURE warehouse.usp_GetSalesReport
    @StartDate DATE,
    @EndDate DATE,
    @StateCode CHAR(2) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @StartDate IS NULL OR @EndDate IS NULL
    BEGIN
        THROW 50001, 'Start date and end date are required.', 1;
    END;

    IF @StartDate > @EndDate
    BEGIN
        THROW 50002, 'Start date cannot be greater than end date.', 1;
    END;

    SELECT
        order_date,
        state_code,
        product_category_name,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_items,
        SUM(gross_amount) AS product_revenue,
        SUM(freight_value) AS freight_value,
        SUM(total_amount) AS total_revenue
    FROM warehouse.vw_SalesDetail
    WHERE order_date BETWEEN @StartDate AND @EndDate
      AND (
            @StateCode IS NULL
            OR state_code = @StateCode
          )
    GROUP BY
        order_date,
        state_code,
        product_category_name
    ORDER BY
        order_date,
        total_revenue DESC;
END;
GO