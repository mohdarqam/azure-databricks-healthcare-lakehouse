-- =============================================================================
-- Metadata database: Azure SQL Database
-- Creates the control schema and the three driving tables:
--   control.table_config  -- one row per ingested object (the driving table)
--   control.watermark     -- last processed watermark value per table (incremental)
--   control.audit_log     -- one row per stage execution (monitoring + alerting)
-- Run in the Azure SQL query editor after creating the DB.
-- =============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'control')
    EXEC('CREATE SCHEMA control');
GO

DROP TABLE IF EXISTS control.audit_log;
DROP TABLE IF EXISTS control.watermark;
DROP TABLE IF EXISTS control.table_config;
GO

-- -----------------------------------------------------------------------------
-- table_config — the driving table
-- -----------------------------------------------------------------------------
CREATE TABLE control.table_config (
    table_id           INT IDENTITY(1,1) PRIMARY KEY,
    source_system      VARCHAR(50)  NOT NULL,     -- 'postgres' | 'adls_csv'
    source_schema_name VARCHAR(50)  NULL,         -- e.g. 'public' (null for csv)
    source_table_name  VARCHAR(100) NULL,         -- e.g. 'patients'
    source_file_format VARCHAR(20)  NULL,         -- e.g. 'csv' (null for db)
    source_path        VARCHAR(400) NULL,         -- folder path for csv sources
    bronze_table_name  VARCHAR(100) NOT NULL,
    silver_table_name  VARCHAR(100) NOT NULL,
    gold_table_name    VARCHAR(100) NULL,
    load_type          VARCHAR(20)  NOT NULL,     -- 'full' | 'append' | 'merge'
    watermark_column   VARCHAR(100) NULL,         -- drives incremental reads
    merge_keys         VARCHAR(200) NULL,         -- comma-separated keys for 'merge'
    stage              VARCHAR(50)  NOT NULL,     -- 'source_to_silver' | 'silver_to_gold'
    is_active          BIT NOT NULL DEFAULT 1,
    created_at         DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at         DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- source_to_silver entries
INSERT INTO control.table_config
(source_system, source_schema_name, source_table_name, source_file_format, source_path,
 bronze_table_name, silver_table_name, gold_table_name, load_type, watermark_column, merge_keys, stage, is_active)
VALUES
-- Postgres sources
('postgres','public','hospitals', NULL, NULL,
 'bronze_hospitals','silver_hospitals', NULL, 'full',   NULL,          NULL,          'source_to_silver', 1),
('postgres','public','doctors',   NULL, NULL,
 'bronze_doctors','silver_doctors',     NULL, 'full',   NULL,          NULL,          'source_to_silver', 1),
('postgres','public','patients',  NULL, NULL,
 'bronze_patients','silver_patients',   NULL, 'merge',  'updated_at',  'patient_id',  'source_to_silver', 1),
-- ADLS CSV partner sources
('adls_csv', NULL,'lab_results','csv','source/lab_results',
 'bronze_lab_results','silver_lab_results', NULL, 'append', 'result_date', NULL,       'source_to_silver', 1),
('adls_csv', NULL,'insurance_providers','csv','source/insurance_providers',
 'bronze_insurance','silver_insurance', NULL, 'full',   NULL,          NULL,          'source_to_silver', 1);
GO

-- silver_to_gold entry (built later)
INSERT INTO control.table_config
(source_system, bronze_table_name, silver_table_name, gold_table_name, load_type, stage, is_active)
VALUES
('gold','silver_patients','silver_patients','gold_patient_360','full','silver_to_gold', 1);
GO

-- -----------------------------------------------------------------------------
-- watermark — last processed value per incremental table
-- -----------------------------------------------------------------------------
CREATE TABLE control.watermark (
    table_id        INT PRIMARY KEY,
    watermark_value VARCHAR(50) NOT NULL,   -- stored as string, cast at read time
    updated_at      DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- seed low watermarks so the first run picks up all history
-- table_id 3 = patients, 4 = lab_results (from the identity order above)
INSERT INTO control.watermark (table_id, watermark_value) VALUES
    (3, '1900-01-01 00:00:00'),
    (4, '1900-01-01 00:00:00');
GO

-- -----------------------------------------------------------------------------
-- audit_log — one row per stage execution
-- -----------------------------------------------------------------------------
CREATE TABLE control.audit_log (
    audit_id        BIGINT IDENTITY(1,1) PRIMARY KEY,
    adf_run_id      VARCHAR(100) NULL,
    table_id        INT NULL,
    stage           VARCHAR(50) NULL,       -- source_to_silver | silver_to_gold
    status          VARCHAR(20) NULL,       -- in_progress | success | failed
    records_written INT NULL,
    start_time      DATETIME2 NULL,
    end_time        DATETIME2 NULL,
    created_at      DATETIME2 DEFAULT SYSUTCDATETIME()
);
GO

-- Handy views for monitoring
-- SELECT * FROM control.table_config WHERE is_active = 1;
-- SELECT * FROM control.audit_log ORDER BY created_at DESC;
