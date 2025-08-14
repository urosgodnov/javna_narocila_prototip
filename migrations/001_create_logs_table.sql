-- Migration: Create application_logs table with tiered retention support
-- Date: 2024-01-14
-- Purpose: Store application logs with automatic retention management
-- Database: SQLite

-- Drop table if exists (for development - remove in production)
DROP TABLE IF EXISTS application_logs;

-- Create organizacija table if it doesn't exist (for foreign key reference)
CREATE TABLE IF NOT EXISTS organizacija (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naziv TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the main logs table
CREATE TABLE application_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Organization context
    organization_id INTEGER,
    organization_name TEXT,
    session_id TEXT,
    
    -- Log details
    log_level TEXT NOT NULL CHECK (log_level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
    module TEXT,
    function_name TEXT,
    line_number INTEGER,
    message TEXT,
    
    -- Retention management
    retention_hours INTEGER NOT NULL DEFAULT 24,
    expires_at DATETIME,
    
    -- Additional context
    additional_context TEXT, -- JSON stored as text in SQLite
    log_type TEXT, -- For special retention rules
    
    -- Performance and search
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (organization_id) REFERENCES organizacija(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_logs_expires ON application_logs(expires_at);
CREATE INDEX idx_logs_timestamp ON application_logs(timestamp DESC);
CREATE INDEX idx_logs_org_level ON application_logs(organization_id, log_level);
CREATE INDEX idx_logs_level ON application_logs(log_level);
CREATE INDEX idx_logs_type ON application_logs(log_type) WHERE log_type IS NOT NULL;
CREATE INDEX idx_logs_message ON application_logs(message);

-- Create a view for log statistics
CREATE VIEW IF NOT EXISTS log_statistics AS
SELECT 
    log_level,
    COUNT(*) as count,
    DATE(timestamp) as date,
    organization_name,
    AVG(retention_hours) as avg_retention_hours,
    MIN(timestamp) as oldest_entry,
    MAX(timestamp) as newest_entry
FROM application_logs
GROUP BY log_level, DATE(timestamp), organization_name;

-- Create a view for retention summary
CREATE VIEW IF NOT EXISTS retention_summary AS
SELECT 
    log_level,
    retention_hours,
    COUNT(*) as count,
    SUM(LENGTH(message) + LENGTH(COALESCE(additional_context, ''))) as total_size
FROM application_logs
GROUP BY log_level, retention_hours
ORDER BY log_level, retention_hours;