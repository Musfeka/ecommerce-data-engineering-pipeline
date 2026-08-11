USE EcommerceDataEngineering;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'streaming'
)
BEGIN
    EXEC('CREATE SCHEMA streaming');
END;
GO

IF OBJECT_ID('streaming.WebsiteEvents', 'U') IS NULL
BEGIN
    CREATE TABLE streaming.WebsiteEvents (
        event_id VARCHAR(50) NOT NULL,
        session_id VARCHAR(100) NOT NULL,
        customer_id VARCHAR(50) NULL,
        event_type VARCHAR(50) NOT NULL,
        product_id VARCHAR(50) NULL,
        event_timestamp DATETIME2 NOT NULL,
        device_type VARCHAR(30) NULL,
        traffic_source VARCHAR(50) NULL,

        kafka_topic VARCHAR(200) NOT NULL,
        kafka_partition INT NOT NULL,
        kafka_offset BIGINT NOT NULL,

        ingested_at DATETIME2 NOT NULL
            CONSTRAINT DF_WebsiteEvents_IngestedAt
            DEFAULT SYSDATETIME(),

        CONSTRAINT PK_WebsiteEvents
            PRIMARY KEY (event_id),

        CONSTRAINT UQ_WebsiteEvents_KafkaPosition
            UNIQUE (
                kafka_topic,
                kafka_partition,
                kafka_offset
            ),

        CONSTRAINT CK_WebsiteEvents_EventType
            CHECK (
                event_type IN (
                    'page_view',
                    'search',
                    'product_view',
                    'add_to_cart',
                    'checkout',
                    'purchase'
                )
            )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_WebsiteEvents_Timestamp'
      AND object_id =
          OBJECT_ID('streaming.WebsiteEvents')
)
BEGIN
    CREATE INDEX IX_WebsiteEvents_Timestamp
    ON streaming.WebsiteEvents(event_timestamp);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_WebsiteEvents_EventType'
      AND object_id =
          OBJECT_ID('streaming.WebsiteEvents')
)
BEGIN
    CREATE INDEX IX_WebsiteEvents_EventType
    ON streaming.WebsiteEvents(event_type);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_WebsiteEvents_Session'
      AND object_id =
          OBJECT_ID('streaming.WebsiteEvents')
)
BEGIN
    CREATE INDEX IX_WebsiteEvents_Session
    ON streaming.WebsiteEvents(session_id);
END;
GO