-- Migration: Add form documents storage tables with deduplication and versioning
-- Date: 2025-01-15
-- Epic: EPIC-FORM-DOCS-001
-- Story 1: Database Schema and Storage Infrastructure

-- Create form_documents table for storing uploaded file metadata with deduplication support
CREATE TABLE IF NOT EXISTS form_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash TEXT NOT NULL,  -- SHA-256 hash for deduplication
    original_name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    mime_type TEXT,
    file_type TEXT NOT NULL,
    
    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'queued', 'processing', 'completed', 'failed', 'skipped')),
    processing_error TEXT,
    processing_started_at DATETIME,
    processing_completed_at DATETIME,
    
    -- AI integration
    ai_document_id INTEGER,
    chunks_count INTEGER DEFAULT 0,
    embeddings_count INTEGER DEFAULT 0,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    superseded_by INTEGER,  -- Points to newer version if replaced
    is_active BOOLEAN DEFAULT 1,  -- False if superseded
    
    -- Metadata
    extracted_text TEXT,  -- Cache extracted text
    metadata_json TEXT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ai_document_id) REFERENCES ai_documents(id) ON DELETE SET NULL,
    FOREIGN KEY (superseded_by) REFERENCES form_documents(id)
);

-- Create indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_form_documents_hash 
    ON form_documents(file_hash);  -- Critical for deduplication checks
CREATE INDEX IF NOT EXISTS idx_form_documents_status 
    ON form_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_form_documents_active
    ON form_documents(is_active) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_form_documents_upload_date 
    ON form_documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_form_documents_ai_link 
    ON form_documents(ai_document_id) WHERE ai_document_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_form_documents_superseded
    ON form_documents(superseded_by) WHERE superseded_by IS NOT NULL;

-- Create link table for many-to-many relationship (documents shared across forms)
CREATE TABLE IF NOT EXISTS form_document_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_document_id INTEGER NOT NULL,
    form_id INTEGER NOT NULL,
    form_type TEXT NOT NULL CHECK(form_type IN ('draft', 'submission')),
    field_name TEXT NOT NULL,  -- Which field this document belongs to
    organization_id INTEGER,
    association_type TEXT DEFAULT 'primary',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (form_document_id) REFERENCES form_documents(id) ON DELETE CASCADE,
    UNIQUE(form_document_id, form_id, form_type, field_name)
);

-- Create indexes for associations
CREATE INDEX IF NOT EXISTS idx_form_doc_assoc_document 
    ON form_document_associations(form_document_id);
CREATE INDEX IF NOT EXISTS idx_form_doc_assoc_form 
    ON form_document_associations(form_id, form_type);
CREATE INDEX IF NOT EXISTS idx_form_doc_assoc_org
    ON form_document_associations(organization_id);
CREATE INDEX IF NOT EXISTS idx_form_doc_assoc_field
    ON form_document_associations(field_name);

-- Create processing queue table for async document processing
CREATE TABLE IF NOT EXISTS form_document_processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_document_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_started_at DATETIME,
    completed_at DATETIME,
    next_retry_at DATETIME,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    FOREIGN KEY (form_document_id) REFERENCES form_documents(id) ON DELETE CASCADE
);

-- Create index for queue processing
CREATE INDEX IF NOT EXISTS idx_processing_queue_status 
    ON form_document_processing_queue(status, priority DESC, queued_at);
CREATE INDEX IF NOT EXISTS idx_processing_queue_retry 
    ON form_document_processing_queue(next_retry_at) WHERE status = 'pending' AND retry_count < max_retries;

-- Create audit log for document operations
CREATE TABLE IF NOT EXISTS form_document_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_document_id INTEGER,
    action TEXT NOT NULL CHECK(action IN ('upload', 'delete', 'process', 'download', 'view', 'error')),
    user_id TEXT,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (form_document_id) REFERENCES form_documents(id) ON DELETE CASCADE
);

-- Create index for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_log_document 
    ON form_document_audit_log(form_document_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
    ON form_document_audit_log(timestamp DESC);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_form_documents_timestamp 
AFTER UPDATE ON form_documents
BEGIN
    UPDATE form_documents 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Create document version history table
CREATE TABLE IF NOT EXISTS form_document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    original_name TEXT NOT NULL,
    change_type TEXT CHECK(change_type IN ('create', 'replace', 'update', 'delete')),
    change_reason TEXT,
    changed_by TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT,
    FOREIGN KEY (document_id) REFERENCES form_documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_doc_versions_document
    ON form_document_versions(document_id, version_number DESC);

-- Create view for document status overview with deduplication info
CREATE VIEW IF NOT EXISTS form_documents_overview AS
SELECT 
    fd.id,
    fd.file_hash,
    fd.original_name,
    fd.file_size,
    fd.processing_status,
    fd.upload_date,
    fd.is_active,
    fd.version,
    fd.chunks_count,
    fd.embeddings_count,
    CASE 
        WHEN fd.ai_document_id IS NOT NULL THEN 'linked'
        ELSE 'unlinked'
    END as ai_status,
    COUNT(DISTINCT fda.form_id) as shared_forms_count,
    COUNT(fda.id) as total_associations,
    GROUP_CONCAT(DISTINCT fda.organization_id) as organization_ids
FROM form_documents fd
LEFT JOIN form_document_associations fda ON fd.id = fda.form_document_id
WHERE fd.is_active = 1
GROUP BY fd.id;

-- Create view for processing queue status
CREATE VIEW IF NOT EXISTS processing_queue_status AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries,
    MIN(queued_at) as oldest_item,
    MAX(queued_at) as newest_item
FROM form_document_processing_queue
GROUP BY status;

-- Add metadata column to ai_documents if it doesn't exist
-- (This handles the case where ai_documents table already exists)
-- Note: SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS
-- so we need to check first in application code

-- Migration completed successfully