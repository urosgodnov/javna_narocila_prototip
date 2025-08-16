-- Story 28.4: AI Document Processing Pipeline
-- Creates tables for AI document processing and vector storage
-- Date: 2025-01-15

-- AI documents table (main document metadata)
CREATE TABLE IF NOT EXISTS ai_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    tip_dokumenta TEXT DEFAULT 'general',
    tags TEXT,
    description TEXT,
    processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    chunk_count INTEGER DEFAULT 0,
    embedding_count INTEGER DEFAULT 0,
    metadata_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI document chunks table
CREATE TABLE IF NOT EXISTS ai_document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    vector_id TEXT,
    embedding_generated BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES ai_documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

-- Processing queue table for async processing
CREATE TABLE IF NOT EXISTS form_document_processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_document_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (form_document_id) REFERENCES form_documents(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_documents_status 
ON ai_documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_ai_documents_type 
ON ai_documents(tip_dokumenta);

CREATE INDEX IF NOT EXISTS idx_ai_chunks_document 
ON ai_document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_ai_chunks_vector 
ON ai_document_chunks(vector_id);

CREATE INDEX IF NOT EXISTS idx_processing_queue_status 
ON form_document_processing_queue(status);

CREATE INDEX IF NOT EXISTS idx_processing_queue_priority 
ON form_document_processing_queue(priority DESC, created_at ASC);

-- View for processing statistics
CREATE VIEW IF NOT EXISTS ai_processing_stats AS
SELECT 
    processing_status,
    COUNT(*) as document_count,
    SUM(chunk_count) as total_chunks,
    SUM(embedding_count) as total_embeddings,
    AVG(chunk_count) as avg_chunks_per_doc,
    MIN(created_at) as oldest_document,
    MAX(processed_at) as latest_processed
FROM ai_documents
GROUP BY processing_status;

-- View for queue status
CREATE VIEW IF NOT EXISTS processing_queue_status AS
SELECT 
    status,
    COUNT(*) as task_count,
    AVG(retry_count) as avg_retries,
    MIN(created_at) as oldest_task,
    MAX(completed_at) as latest_completion
FROM form_document_processing_queue
GROUP BY status;

-- Migration complete
-- This migration is idempotent and can be run multiple times safely