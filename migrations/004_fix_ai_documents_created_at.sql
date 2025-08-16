-- Migration: Fix missing created_at column in ai_documents table
-- Date: 2025-01-16
-- Issue: Code expects created_at but table has upload_date

-- Step 1: Add created_at column if it doesn't exist
-- We'll copy data from upload_date to maintain historical data
ALTER TABLE ai_documents ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Step 2: Copy existing upload_date values to created_at
UPDATE ai_documents SET created_at = upload_date WHERE created_at IS NULL;

-- Step 3: Add processed_at column (missing from current schema)
ALTER TABLE ai_documents ADD COLUMN processed_at DATETIME;

-- Step 4: Add updated_at column (missing from current schema)  
ALTER TABLE ai_documents ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Step 5: Ensure ai_query_sources has created_at if missing
-- (Some tables might need it based on the error)
ALTER TABLE ai_query_sources ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- Note: SQLite doesn't support DROP COLUMN easily, so we keep upload_date for backward compatibility
-- The application can use either created_at or upload_date

-- Migration complete