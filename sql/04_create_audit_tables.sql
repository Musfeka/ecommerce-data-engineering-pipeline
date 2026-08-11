USE EcommerceDataEngineering;
GO

IF OBJECT_ID('audit.ETLRun', 'U') IS NULL
BEGIN
    CREATE TABLE audit.ETLRun (
        run_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        pipeline_name NVARCHAR(150) NOT NULL,
        start_time DATETIME2 NOT NULL,
        end_time DATETIME2 NULL,
        customers_loaded BIGINT NOT NULL DEFAULT 0,
        products_loaded BIGINT NOT NULL DEFAULT 0,
        orders_loaded BIGINT NOT NULL DEFAULT 0,
        order_items_loaded BIGINT NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL,
        error_message NVARCHAR(MAX) NULL
    );
END;
GO

IF OBJECT_ID('audit.DataQualityResults', 'U') IS NULL
BEGIN
    CREATE TABLE audit.DataQualityResults (
        quality_result_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        run_id BIGINT NOT NULL,
        table_name NVARCHAR(150) NOT NULL,
        check_name NVARCHAR(200) NOT NULL,
        failed_records BIGINT NOT NULL,
        status VARCHAR(20) NOT NULL,
        checked_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

        CONSTRAINT FK_DataQualityResults_ETLRun
            FOREIGN KEY (run_id)
            REFERENCES audit.ETLRun(run_id)
    );
END;
GO