USE master;
GO

IF DB_ID('EcommerceDataEngineering') IS NULL
BEGIN
    CREATE DATABASE EcommerceDataEngineering;
END;
GO

USE EcommerceDataEngineering;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.schemas WHERE name = 'staging'
)
BEGIN
    EXEC('CREATE SCHEMA staging');
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.schemas WHERE name = 'ecommerce'
)
BEGIN
    EXEC('CREATE SCHEMA ecommerce');
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.schemas WHERE name = 'warehouse'
)
BEGIN
    EXEC('CREATE SCHEMA warehouse');
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.schemas WHERE name = 'audit'
)
BEGIN
    EXEC('CREATE SCHEMA audit');
END;
GO