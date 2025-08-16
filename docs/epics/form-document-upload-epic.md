# Form Document Storage and AI Processing Backend - Brownfield Enhancement

**Epic ID:** EPIC-FORM-DOCS-001  
**Created:** 2025-01-15  
**Status:** Ready for Development  
**Type:** Brownfield Enhancement  

## Epic Goal

Create backend infrastructure to store and process documents uploaded through existing form file upload fields (logos, technical documents, attachments), integrating them with the AI knowledge base for enhanced suggestions and analysis.

## Epic Description

**Existing System Context:**

- Current relevant functionality: 
  - Forms already have file upload fields (`format: "file"` in form_renderer.py)
  - File uploaders accept PDF, JPG, PNG, DOC, DOCX formats
  - AI system has document processing pipeline for knowledge base documents
  - Form data is stored as JSON in database
- Technology stack: Streamlit UI with st.file_uploader, SQLite database, OpenAI embeddings, Qdrant vector store
- Integration points: `ui/form_renderer.py` (lines 744-751), `ui/ai_processor.py`, existing `ai_documents` table

**Enhancement Details:**

- What's being added/changed: 
  - Backend storage system for files uploaded through existing form fields
  - New database tables to track form documents separately from form JSON data
  - Integration with existing AI document processing pipeline
  - File retrieval and management capabilities
  - Document deduplication and sharing across multiple forms
  - Admin testing interface for uploaded documents

- How it integrates:
  - Intercepts file uploads from existing st.file_uploader widgets
  - Stores files in organized directory structure with hash-based deduplication
  - Links files to form drafts/submissions via database
  - Processes documents through existing DocumentProcessor
  - Makes document content available for AI suggestions
  - Shares documents across multiple javna naročila when same file is used

- Success criteria:
  - Files uploaded through existing form fields are properly stored
  - Documents are linked to their parent forms in database
  - Uploaded documents are processed into AI knowledge base
  - AI suggestions can reference form-specific uploaded documents
  - Files can be retrieved when viewing saved forms
  - Same document used in multiple forms is stored only once
  - Admin can test document AI integration through chat interface

## Document Lifecycle & AI Integration Strategy

### Document Processing Flow

1. **Upload & Deduplication:**
   - User uploads document through form field (logo, technical spec, attachment)
   - System calculates SHA-256 hash of file content
   - Check if document with same hash already exists:
     - If exists: Link existing document to new form (avoid duplicate storage)
     - If new: Store file and create new document record

2. **AI Processing Pipeline:**
   - Extract text from document (PDFs, DOCX, etc.)
   - Split into chunks with overlap (chunk size: 500 tokens, overlap: 100 tokens)
   - Generate embeddings using OpenAI text-embedding-ada-002
   - Store in Qdrant vector database with metadata:
     - Organization ID
     - Form IDs (multiple if shared)
     - Document type (logo, technical, attachment)
     - Original filename
     - Upload timestamp

3. **Document Persistence:**
   - **Physical Storage:** Files stored permanently in `data/form_documents/` directory
   - **Database Records:** Persistent in `form_documents` table
   - **Vector Store:** Persistent in Qdrant collection with form-specific metadata
   - **Retention Policy:** Documents retained indefinitely unless explicitly deleted

4. **Document Replacement Strategy:**
   - When user uploads new version of document:
     - Mark old document as "superseded" (keep for audit trail)
     - Process new document through pipeline
     - Update vector store: Remove old embeddings, add new ones
     - Update all form associations to point to new document
     - Keep version history in `form_document_versions` table

5. **Document Sharing Across Forms:**
   - Same document can be linked to multiple javna naročila
   - Use `form_document_associations` table for many-to-many relationships
   - When querying AI, include documents from:
     - Current form
     - Same organization's other forms (with lower weight)
     - Template documents (if applicable)

### AI Context Usage

Documents participate in AI processes at multiple points:

1. **Form Field Suggestions:**
   - When AI generates suggestions for form fields
   - Uploaded technical specs provide context for requirements
   - Previous similar documents guide content generation

2. **Validation & Compliance:**
   - Check uploaded documents against requirements
   - Verify technical specifications match tender criteria
   - Ensure logos meet format requirements

3. **Query Answering:**
   - Admin queries about specific forms include their documents
   - Documents provide authoritative source for details
   - Cross-reference between forms using shared documents

## Stories

### Story 1: Database Schema and Storage Infrastructure
**Priority:** High  
**Effort:** 3 points  

Design and implement the database schema and file storage infrastructure for form documents.

**Key Tasks:**
- Design `form_documents` table schema with all necessary fields
- Create database migration script with proper indexes
- Design file storage directory structure (`data/form_documents/`)
- Implement file naming convention to prevent conflicts
- Create database initialization/migration utilities

**Acceptance Criteria:**
- [ ] Database schema designed with proper normalization
- [ ] Migration script creates tables without errors
- [ ] Indexes created for query performance
- [ ] File storage directories created with proper permissions
- [ ] Naming convention prevents file conflicts
- [ ] Rollback script available for schema changes

### Story 2: File Storage Service Layer
**Priority:** High  
**Effort:** 5 points  

Create a service layer to handle all file operations including saving, retrieving, and deleting files.

**Key Tasks:**
- Create `FormDocumentService` class with CRUD operations
- Implement file save with metadata extraction
- Implement file retrieval with error handling
- Create file deletion with cascade cleanup
- Add file validation (size, type, virus scan placeholder)
- Implement orphaned file cleanup routine

**Acceptance Criteria:**
- [ ] Service class handles all file operations
- [ ] Files are saved with unique identifiers
- [ ] Metadata (size, type, hash) is extracted and stored
- [ ] File retrieval handles missing files gracefully
- [ ] Deletion removes both file and database records
- [ ] Orphaned files are identified and cleaned up
- [ ] File operations are logged for audit trail

### Story 3: Form Renderer Integration
**Priority:** High  
**Effort:** 5 points  

Integrate file storage capabilities into the existing form renderer without breaking current functionality.

**Key Tasks:**
- Modify file upload handling in `form_renderer.py` (lines 744-751)
- Implement session state management for uploaded files
- Add file preview/info display for uploaded files
- Integrate with form save process
- Handle file retrieval when loading existing forms
- Add UI feedback for upload/delete operations

**Acceptance Criteria:**
- [ ] File uploads are captured without breaking existing forms
- [ ] Files are stored in session state before form save
- [ ] Form save process includes file persistence
- [ ] Loading saved forms displays existing files
- [ ] Users can replace uploaded files
- [ ] Users can delete uploaded files
- [ ] Upload progress and status are visible
- [ ] File size limits are enforced with clear messages

### Story 4: AI Document Processing Pipeline
**Priority:** Medium  
**Effort:** 5 points  

Connect uploaded form documents to the AI processing system for knowledge extraction and embedding generation.

**Key Tasks:**
- Create `FormDocumentProcessor` extending existing `DocumentProcessor`
- Implement automatic processing triggers on file upload
- Add document type detection and routing
- Create processing queue management
- Implement status tracking and error handling
- Add form-document linking in vector store

**Acceptance Criteria:**
- [ ] Documents are automatically queued for processing
- [ ] Different file types are handled appropriately
- [ ] Processing status is tracked in database
- [ ] Embeddings are generated and stored in Qdrant
- [ ] Failed processing is retried with backoff
- [ ] Form documents are tagged in vector store
- [ ] Processing logs are available for debugging

### Story 5: AI Context Enhancement and Retrieval
**Priority:** Medium  
**Effort:** 4 points  

Enhance AI suggestion system to utilize uploaded form documents for better context-aware suggestions.

**Key Tasks:**
- Modify `FormAIAssistant` to include form documents in context
- Implement relevance scoring for form-specific documents
- Create document filtering by form field and type
- Add contextual prompts that reference uploaded documents
- Implement caching for frequently accessed documents
- Create fallback strategies when documents are unavailable

**Acceptance Criteria:**
- [ ] AI suggestions reference uploaded documents when relevant
- [ ] Form-specific documents are prioritized in search results
- [ ] Different document types provide appropriate context
- [ ] System works gracefully when no documents are uploaded
- [ ] Document context improves suggestion quality
- [ ] Performance remains acceptable with document context
- [ ] Cache reduces repeated document processing

### Story 6: Admin Document Testing Interface
**Priority:** Medium  
**Effort:** 5 points  

Create an admin interface to test and validate uploaded documents' AI integration through a chat interface.

**Key Tasks:**
- Create document testing page in admin panel
- Implement organization/form/document selector UI
- Build chat interface for document-specific queries
- Add document preview capability
- Implement query context filtering (single doc, form docs, org docs)
- Create document quality metrics display
- Add export capability for test results

**Acceptance Criteria:**
- [ ] Admin can select organization, javno naročilo, and specific document
- [ ] Chat interface allows natural language queries about selected documents
- [ ] System shows which chunks/sections are used for answers
- [ ] Preview shows document content and extracted text
- [ ] Quality metrics display (chunk count, embedding status, processing time)
- [ ] Ability to reprocess documents if needed
- [ ] Export test queries and results for documentation
- [ ] Clear indication of document sharing across multiple forms

## Compatibility Requirements

- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible (new tables only)
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact is minimal (async processing for large files)
- [x] Existing AI processing pipeline is reused, not modified
- [x] Form submission process remains unchanged for forms without uploads

## Risk Mitigation

**Primary Risk:** File storage could consume significant disk space with large documents  
**Mitigation:** Implement file size limits (10MB per file), compression for storage, and cleanup for orphaned files  
**Rollback Plan:** New tables can be dropped without affecting existing functionality; file uploads can be disabled via feature flag  

**Secondary Risk:** AI processing delays could block form submission  
**Mitigation:** Process documents asynchronously, allow form submission without waiting  
**Rollback Plan:** Disable AI processing while keeping upload functionality  

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Existing form functionality verified through testing
- [ ] Document uploads work for logos, technical specs, and attachments
- [ ] AI processing successfully integrates uploaded documents
- [ ] File storage is organized and manageable
- [ ] No regression in existing form or AI features
- [ ] Documentation updated with upload field specifications
- [ ] Performance benchmarks met (upload < 5s, processing queued immediately)

## Detailed Technical Specifications

### Story 1 - Database Schema (Detailed):
```sql
-- New table for form document management
CREATE TABLE IF NOT EXISTS form_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id INTEGER,
    form_type TEXT, -- 'draft' or 'submission'
    field_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    ai_document_id INTEGER,
    metadata_json TEXT,
    FOREIGN KEY (ai_document_id) REFERENCES ai_documents(id)
);

-- Index for quick lookups
CREATE INDEX idx_form_documents_form ON form_documents(form_id, form_type);
CREATE INDEX idx_form_documents_status ON form_documents(processing_status);

-- Link table for many-to-many relationship if needed
CREATE TABLE IF NOT EXISTS form_document_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_document_id INTEGER,
    entity_type TEXT, -- 'draft', 'submission', 'template'
    entity_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (form_document_id) REFERENCES form_documents(id) ON DELETE CASCADE
);
```

### Story 2 - File Storage Service with Deduplication (Detailed):
```python
# services/form_document_service.py
import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, List, BinaryIO, Tuple
import sqlite3
from datetime import datetime
import json

class FormDocumentService:
    """Service layer for form document operations with deduplication"""
    
    def __init__(self):
        self.storage_root = Path("data/form_documents")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
    
    def save_document(self, 
                     file_data: BinaryIO,
                     form_id: int,
                     form_type: str,
                     field_name: str,
                     original_name: str,
                     mime_type: str) -> Tuple[int, bool]:
        """Save a document with deduplication. Returns (doc_id, is_new)"""
        
        # Validate file
        if not self._validate_file(file_data, original_name):
            raise ValueError("Invalid file")
        
        # Generate file hash for deduplication
        file_hash = self._generate_file_hash(file_data)
        
        # Check if document already exists
        existing_doc = self._find_existing_document(file_hash)
        
        if existing_doc:
            # Document exists - create association only
            doc_id = self._create_document_association(
                existing_doc_id=existing_doc['id'],
                form_id=form_id,
                form_type=form_type,
                field_name=field_name
            )
            return doc_id, False
        
        # New document - save file and metadata
        file_ext = Path(original_name).suffix
        stored_filename = f"{file_hash}{file_ext}"
        
        # Use hash-based path to avoid directory overflow
        hash_dir = file_hash[:2] + "/" + file_hash[2:4]
        storage_path = self.storage_root / hash_dir
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = storage_path / stored_filename
        with open(file_path, 'wb') as f:
            file_data.seek(0)
            f.write(file_data.read())
        
        # Save metadata to database
        doc_id = self._save_metadata(
            form_id=form_id,
            form_type=form_type,
            field_name=field_name,
            original_name=original_name,
            file_path=str(file_path),
            file_size=file_data.tell(),
            mime_type=mime_type,
            file_hash=file_hash
        )
        
        return doc_id, True
    
    def _find_existing_document(self, file_hash: str) -> Optional[Dict]:
        """Find document by hash"""
        with sqlite3.connect('mainDB.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM form_documents 
                WHERE file_hash = ? AND processing_status != 'failed'
                LIMIT 1
            """, (file_hash,))
            
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        return None
    
    def _create_document_association(self, existing_doc_id: int, 
                                    form_id: int, form_type: str, 
                                    field_name: str) -> int:
        """Create association for existing document"""
        with sqlite3.connect('mainDB.db') as conn:
            cursor = conn.cursor()
            
            # Create association record
            cursor.execute("""
                INSERT INTO form_document_associations
                (form_document_id, entity_type, entity_id, association_type)
                VALUES (?, ?, ?, ?)
            """, (existing_doc_id, form_type, form_id, field_name))
            
            conn.commit()
            return existing_doc_id
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Retrieve document metadata and file path"""
        with sqlite3.connect('mainDB.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM form_documents WHERE id = ?
            """, (doc_id,))
            
            result = cursor.fetchone()
            if result:
                # Convert to dictionary
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        return None
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete document file and metadata"""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        
        # Delete file
        if os.path.exists(doc['file_path']):
            os.remove(doc['file_path'])
        
        # Delete metadata
        with sqlite3.connect('mainDB.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM form_documents WHERE id = ?", (doc_id,))
            conn.commit()
        
        return True
    
    def cleanup_orphaned_files(self) -> int:
        """Remove files not referenced in database"""
        orphaned_count = 0
        
        # Get all file paths from database
        with sqlite3.connect('mainDB.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM form_documents")
            db_files = {row[0] for row in cursor.fetchall()}
        
        # Check all files in storage
        for file_path in self.storage_root.rglob('*'):
            if file_path.is_file():
                if str(file_path) not in db_files:
                    os.remove(file_path)
                    orphaned_count += 1
        
        return orphaned_count
    
    def _validate_file(self, file_data: BinaryIO, filename: str) -> bool:
        """Validate file type and size"""
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            return False
        
        # Check size
        file_data.seek(0, 2)  # Seek to end
        size = file_data.tell()
        file_data.seek(0)  # Reset
        
        if size > self.max_file_size:
            return False
        
        # TODO: Add virus scan here
        
        return True
    
    def _generate_file_hash(self, file_data: BinaryIO) -> str:
        """Generate unique hash for file"""
        file_data.seek(0)
        file_hash = hashlib.sha256(file_data.read()).hexdigest()[:16]
        file_data.seek(0)
        return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_hash}"
    
    def _get_storage_path(self, form_id: int, form_type: str, field_name: str) -> Path:
        """Generate storage path for file"""
        return self.storage_root / form_type / str(form_id) / field_name
```

### Story 3 - Form Renderer Integration (Detailed):
```python
# In form_renderer.py - Modify existing file upload handling (lines 744-751)
elif prop_details.get("format") == "file":
    # Existing file uploader
    uploaded_file = st.file_uploader(
        display_label, 
        key=session_key, 
        help=help_text,
        type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
    )
    
    # NEW: Handle file storage
    if uploaded_file is not None:
        # Store in session state temporarily
        if f"{session_key}_file" not in st.session_state:
            st.session_state[f"{session_key}_file"] = {
                'data': uploaded_file.read(),
                'name': uploaded_file.name,
                'type': uploaded_file.type,
                'size': uploaded_file.size,
                'field': prop_name
            }
            uploaded_file.seek(0)  # Reset file pointer
            
        # Show file info
        st.info(f"📎 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        # Option to remove file
        if st.button(f"Remove {uploaded_file.name}", key=f"remove_{session_key}"):
            del st.session_state[f"{session_key}_file"]
            st.rerun()
    
    # NEW: Show previously uploaded file if exists
    elif form_id and session_key:
        existing_file = get_form_document(form_id, prop_name)
        if existing_file:
            st.info(f"📄 Existing file: {existing_file['original_name']}")
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("View", key=f"view_{session_key}"):
                    display_file(existing_file)
            with col2:
                if st.button("Replace", key=f"replace_{session_key}"):
                    st.session_state[f"{session_key}_replace"] = True
                    st.rerun()

# In form save function - persist files from session state
def save_form_with_documents(form_data, form_id, form_type='draft'):
    """Save form and any uploaded documents"""
    
    # Save form data as before
    save_form_data(form_data, form_id, form_type)
    
    # NEW: Save any uploaded files
    for key in st.session_state:
        if key.endswith('_file'):
            file_data = st.session_state[key]
            save_form_document(
                form_id=form_id,
                form_type=form_type,
                field_name=file_data['field'],
                file_data=file_data['data'],
                original_name=file_data['name'],
                mime_type=file_data['type'],
                file_size=file_data['size']
            )
            # Clear from session after saving
            del st.session_state[key]
```

### Story 4 - AI Document Processing (Detailed):
```python
# services/form_document_processor.py
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
from ui.ai_processor import DocumentProcessor, EmbeddingGenerator, VectorStoreManager
import sqlite3
import json

class FormDocumentProcessor:
    """Process form documents through AI pipeline"""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        self.processing_queue = []
        
    def queue_for_processing(self, form_doc_id: int) -> bool:
        """Add document to processing queue"""
        try:
            # Update status to queued
            self._update_processing_status(form_doc_id, 'queued')
            
            # Add to queue
            self.processing_queue.append({
                'doc_id': form_doc_id,
                'queued_at': datetime.now(),
                'attempts': 0
            })
            
            # Trigger async processing
            asyncio.create_task(self._process_queue())
            
            return True
        except Exception as e:
            print(f"Error queuing document: {e}")
            return False
    
    async def _process_queue(self):
        """Process documents in queue"""
        while self.processing_queue:
            item = self.processing_queue.pop(0)
            
            try:
                await self._process_single_document(item['doc_id'])
            except Exception as e:
                # Handle retry logic
                item['attempts'] += 1
                if item['attempts'] < 3:
                    # Re-queue with exponential backoff
                    await asyncio.sleep(2 ** item['attempts'])
                    self.processing_queue.append(item)
                else:
                    # Mark as failed after 3 attempts
                    self._update_processing_status(item['doc_id'], 'failed', str(e))
    
    async def _process_single_document(self, form_doc_id: int):
        """Process a single form document"""
        
        # Get document metadata
        doc_info = self._get_form_document(form_doc_id)
        if not doc_info:
            raise ValueError(f"Document {form_doc_id} not found")
        
        # Update status
        self._update_processing_status(form_doc_id, 'processing')
        
        # Extract text based on file type
        text = await self._extract_text(doc_info['file_path'], doc_info['mime_type'])
        
        # Chunk the document
        chunks = self.doc_processor.chunk_document(text, form_doc_id)
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_gen.generate_embeddings(texts)
        
        # Store in vector database with form metadata
        self._store_in_vector_db(chunks, embeddings, doc_info)
        
        # Update AI document reference
        ai_doc_id = self._create_ai_document_entry(doc_info)
        self._link_to_ai_document(form_doc_id, ai_doc_id)
        
        # Update status to completed
        self._update_processing_status(form_doc_id, 'completed')
    
    def _store_in_vector_db(self, chunks: List[Dict], embeddings: List[List[float]], 
                            doc_info: Dict):
        """Store chunks in Qdrant with form-specific metadata"""
        
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append({
                'id': f"form_{doc_info['form_id']}_{chunk['chunk_index']}",
                'vector': embedding,
                'payload': {
                    'text': chunk['text'],
                    'form_id': doc_info['form_id'],
                    'form_type': doc_info['form_type'],
                    'field_name': doc_info['field_name'],
                    'document_type': 'form_upload',
                    'original_name': doc_info['original_name'],
                    'chunk_index': chunk['chunk_index']
                }
            })
        
        self.vector_store.client.upsert(
            collection_name=self.vector_store.collection_name,
            points=points
        )
```

### Story 5 - AI Context Enhancement (Detailed):
```python
# In ai_form_integration.py - Extend to use uploaded documents
class FormDocumentAIProcessor:
    """Process form-uploaded documents for AI context"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager()
    
    def process_form_document(self, form_doc_id: int):
        """Process a form document through AI pipeline"""
        # Get document metadata
        doc = get_form_document_by_id(form_doc_id)
        
        # Create entry in ai_documents
        ai_doc_id = create_ai_document_entry(
            filename=doc['original_name'],
            file_path=doc['file_path'],
            tip_dokumenta='form_upload',
            metadata={'form_id': doc['form_id'], 'field': doc['field_name']}
        )
        
        # Process through existing pipeline
        success = self.document_processor.process_uploaded_document(ai_doc_id)
        
        # Update form_documents with AI reference
        if success:
            update_form_document_ai_link(form_doc_id, ai_doc_id)
        
        return success
    
    def get_form_document_context(self, form_id: int, field_name: str = None,
                                  query_embedding: List[float] = None):
        """Get AI context from uploaded form documents"""
        # Get all processed documents for this form
        form_docs = get_processed_form_documents(form_id, field_name)
        
        # Extract vector IDs
        vector_ids = [doc['ai_document_id'] for doc in form_docs]
        
        # Use existing vector search with filtering
        if vector_ids and query_embedding:
            # Prioritize these documents in search results
            return self.vector_store.search_with_boost(
                query_vector=query_embedding,
                boost_ids=vector_ids,
                boost_factor=2.0  # Double the relevance score
            )
        elif vector_ids:
            # Return all form documents without search
            return self.vector_store.get_by_ids(vector_ids)
        return []
    
    def enhance_ai_suggestions(self, form_id: int, field_name: str, 
                               base_prompt: str) -> str:
        """Enhance AI prompts with form document context"""
        
        # Get relevant form documents
        form_context = self.get_form_document_context(form_id, field_name)
        
        if not form_context:
            return base_prompt
        
        # Build enhanced prompt with document context
        enhanced_prompt = f"{base_prompt}\n\nRelevantni dokumenti iz obrazca:\n"
        
        for idx, doc in enumerate(form_context[:3], 1):  # Top 3 documents
            enhanced_prompt += f"\n{idx}. {doc['original_name']}:\n"
            enhanced_prompt += f"   {doc['text'][:500]}...\n"  # First 500 chars
        
        enhanced_prompt += "\nUpoštevaj zgornje dokumente pri pripravi predloga."
        
        return enhanced_prompt

# Enhanced FormAIAssistant integration
class EnhancedFormAIAssistant(FormAIAssistant):
    """Extended AI assistant that uses uploaded form documents"""
    
    def __init__(self):
        super().__init__()
        self.doc_processor = FormDocumentAIProcessor()
        self.cache = {}  # Simple in-memory cache
        
    def get_ai_suggestion(self, form_section: str, field_name: str, 
                         context: Dict[str, Any]) -> str:
        """Get AI suggestion with form document enhancement"""
        
        # Check cache first
        cache_key = f"{form_section}_{field_name}_{hash(str(context))}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get form ID from context
        form_id = context.get('form_id')
        
        # Build base prompt
        base_prompt = self._build_base_prompt(form_section, field_name, context)
        
        # Enhance with document context if available
        if form_id:
            enhanced_prompt = self.doc_processor.enhance_ai_suggestions(
                form_id=form_id,
                field_name=field_name,
                base_prompt=base_prompt
            )
        else:
            enhanced_prompt = base_prompt
        
        # Generate suggestion
        suggestion = self._generate_with_gpt4(enhanced_prompt)
        
        # Cache result
        self.cache[cache_key] = suggestion
        
        return suggestion
    
    def clear_cache(self, form_id: int = None):
        """Clear cached suggestions"""
        if form_id:
            # Clear only cache entries for specific form
            keys_to_remove = [k for k in self.cache.keys() 
                            if f"_{form_id}_" in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            # Clear entire cache
            self.cache.clear()

# Helper functions for database operations
def get_processed_form_documents(form_id: int, field_name: str = None):
    """Get all processed documents for a form"""
    with sqlite3.connect('mainDB.db') as conn:
        cursor = conn.cursor()
        
        if field_name:
            query = """
                SELECT * FROM form_documents 
                WHERE form_id = ? AND field_name = ? 
                AND processing_status = 'completed'
                AND ai_document_id IS NOT NULL
            """
            cursor.execute(query, (form_id, field_name))
        else:
            query = """
                SELECT * FROM form_documents 
                WHERE form_id = ? 
                AND processing_status = 'completed'
                AND ai_document_id IS NOT NULL
            """
            cursor.execute(query, (form_id,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_form_document_by_id(form_doc_id: int):
    """Get form document by ID"""
    with sqlite3.connect('mainDB.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM form_documents WHERE id = ?", (form_doc_id,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
    return None

def create_ai_document_entry(filename: str, file_path: str, 
                            tip_dokumenta: str, metadata: Dict):
    """Create entry in ai_documents table"""
    with sqlite3.connect('mainDB.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_documents 
            (filename, file_path, tip_dokumenta, upload_date, 
             processed, metadata_json)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 0, ?)
        """, (filename, file_path, tip_dokumenta, json.dumps(metadata)))
        conn.commit()
        return cursor.lastrowid

def update_form_document_ai_link(form_doc_id: int, ai_doc_id: int):
    """Link form document to AI document"""
    with sqlite3.connect('mainDB.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE form_documents 
            SET ai_document_id = ?, processing_status = 'completed'
            WHERE id = ?
        """, (ai_doc_id, form_doc_id))
        conn.commit()
```

### Story 6 - Admin Document Testing Interface (Detailed):
```python
# ui/admin_document_tester.py
import streamlit as st
import sqlite3
from typing import Dict, List, Optional
from ui.ai_processor import VectorStoreManager, EmbeddingGenerator
from services.form_document_service import FormDocumentService
import json

class DocumentTestingInterface:
    """Admin interface for testing document AI integration"""
    
    def __init__(self):
        self.doc_service = FormDocumentService()
        self.vector_store = VectorStoreManager()
        self.embedding_gen = EmbeddingGenerator()
        
    def render(self):
        """Render the document testing interface"""
        st.title("🧪 Test dokumentov AI integracije")
        
        # Organization selector
        col1, col2, col3 = st.columns(3)
        
        with col1:
            organizations = self._get_organizations()
            selected_org = st.selectbox(
                "Organizacija",
                options=organizations,
                format_func=lambda x: x['naziv']
            )
        
        with col2:
            if selected_org:
                forms = self._get_forms_for_org(selected_org['id'])
                selected_form = st.selectbox(
                    "Javno naročilo",
                    options=forms,
                    format_func=lambda x: f"{x['naziv']} ({x['status']})"
                )
        
        with col3:
            if selected_form:
                documents = self._get_form_documents(selected_form['id'])
                selected_doc = st.selectbox(
                    "Dokument",
                    options=documents,
                    format_func=lambda x: f"{x['original_name']} ({x['field_name']})"
                )
        
        # Document info and metrics
        if selected_doc:
            self._render_document_info(selected_doc)
            
            # Query context selector
            st.markdown("### 🎯 Kontekst poizvedbe")
            context_mode = st.radio(
                "Vključi dokumente:",
                ["Samo izbrani dokument", 
                 "Vsi dokumenti obrazca",
                 "Vsi dokumenti organizacije"],
                horizontal=True
            )
            
            # Chat interface
            st.markdown("### 💬 Testni pogovor")
            
            # Initialize chat history
            if 'doc_test_messages' not in st.session_state:
                st.session_state.doc_test_messages = []
            
            # Display chat history
            for message in st.session_state.doc_test_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "chunks" in message:
                        with st.expander("Uporabljeni deli dokumenta"):
                            for chunk in message["chunks"]:
                                st.text(f"Chunk {chunk['index']}: {chunk['text'][:200]}...")
            
            # Chat input
            if prompt := st.chat_input("Vprašajte kaj o dokumentu..."):
                # Add user message
                st.session_state.doc_test_messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Analiziram dokument..."):
                        response, used_chunks = self._generate_response(
                            prompt, selected_doc, context_mode, 
                            selected_org, selected_form
                        )
                        st.markdown(response)
                        
                        # Show used chunks
                        if used_chunks:
                            with st.expander(f"Uporabljenih {len(used_chunks)} delov"):
                                for chunk in used_chunks:
                                    st.text(f"Relevanca: {chunk['score']:.2f}")
                                    st.text(chunk['text'][:300] + "...")
                
                # Add assistant message
                st.session_state.doc_test_messages.append({
                    "role": "assistant",
                    "content": response,
                    "chunks": used_chunks
                })
        
        # Export section
        if st.session_state.get('doc_test_messages'):
            st.markdown("### 📥 Izvoz rezultatov")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Izvozi pogovor"):
                    self._export_conversation()
            with col2:
                if st.button("Počisti pogovor"):
                    st.session_state.doc_test_messages = []
                    st.rerun()
    
    def _render_document_info(self, document: Dict):
        """Display document information and metrics"""
        st.markdown("### 📄 Informacije o dokumentu")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tip datoteke", document['file_type'])
            st.metric("Velikost", f"{document['file_size'] / 1024:.1f} KB")
        
        with col2:
            st.metric("Status procesiranja", document['processing_status'])
            chunks_count = self._get_chunk_count(document['id'])
            st.metric("Število kosov", chunks_count)
        
        with col3:
            st.metric("Datum nalaganja", document['upload_date'])
            shared_count = self._get_shared_forms_count(document['id'])
            st.metric("Deljeno z obrazci", shared_count)
        
        with col4:
            if document['processing_status'] == 'completed':
                st.success("✅ Pripravljen za AI")
            elif document['processing_status'] == 'processing':
                st.info("⏳ V obdelavi")
            else:
                st.warning("⚠️ Ni procesiran")
                if st.button("Procesiraj zdaj"):
                    self._trigger_processing(document['id'])
                    st.rerun()
        
        # Show preview if possible
        if st.checkbox("Prikaži predogled vsebine"):
            extracted_text = self._get_extracted_text(document['id'])
            if extracted_text:
                st.text_area("Izvlečena vsebina", extracted_text[:2000], height=200)
            else:
                st.warning("Vsebina še ni izvlečena")
    
    def _generate_response(self, query: str, document: Dict, 
                          context_mode: str, org: Dict, form: Dict):
        """Generate AI response based on document context"""
        
        # Get relevant documents based on context mode
        if context_mode == "Samo izbrani dokument":
            doc_filter = {"document_id": document['id']}
        elif context_mode == "Vsi dokumenti obrazca":
            doc_filter = {"form_id": form['id']}
        else:  # All organization documents
            doc_filter = {"organization_id": org['id']}
        
        # Generate query embedding
        query_embedding = self.embedding_gen.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_vector=query_embedding,
            filter=doc_filter,
            top_k=5
        )
        
        # Format context
        context = "\n\n".join([r['text'] for r in results])
        
        # Generate response with GPT-4
        prompt = f"""
        Na podlagi naslednjih dokumentov odgovori na vprašanje.
        
        Kontekst iz dokumentov:
        {context}
        
        Vprašanje: {query}
        
        Odgovor:
        """
        
        # Here you would call OpenAI API
        response = "Generated response based on documents..."
        
        return response, results
    
    def _export_conversation(self):
        """Export test conversation to JSON"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.doc_test_messages,
            "metadata": {
                "document": st.session_state.get('selected_doc'),
                "organization": st.session_state.get('selected_org'),
                "form": st.session_state.get('selected_form')
            }
        }
        
        st.download_button(
            label="Prenesi JSON",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"doc_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Integration into admin panel
def render_document_testing_tab():
    """Render document testing tab in admin panel"""
    tester = DocumentTestingInterface()
    tester.render()
```

### File Storage Structure (Updated with Hash-based):
```
data/
└── form_documents/
    ├── a7/  # First 2 chars of hash
    │   └── b3/  # Next 2 chars of hash
    │       ├── a7b3c4d5e6f7_logo.png
    │       └── a7b3f8g9h0i1_specs.pdf
    ├── c2/
    │   └── d4/
    │       └── c2d4e5f6g7h8_contract.docx
    └── temp/  # Temporary uploads before processing
        └── pending_files/

## Dependencies

- Existing AI document processing pipeline must be operational
- Qdrant vector store must be accessible
- OpenAI API key must be configured
- Sufficient disk space for document storage (estimate: 100MB per form with documents)

## Testing Strategy

1. **Unit Tests:**
   - File upload validation
   - Database operations for form_documents
   - File storage operations

2. **Integration Tests:**
   - End-to-end document upload and processing
   - AI context retrieval with form documents
   - Form submission with documents

3. **Performance Tests:**
   - Large file upload (10MB)
   - Multiple concurrent uploads
   - AI processing queue handling

## Success Metrics

- Document upload success rate > 95%
- AI processing completion rate > 90%
- Average upload time < 5 seconds
- User satisfaction with document management features
- Reduction in manual document handling time

## Notes

- Consider implementing virus scanning for uploaded files in future iteration
- May want to add document preview functionality for images and PDFs
- Consider implementing document versioning for updated files
- Future enhancement: OCR for scanned documents

---

**Status:** Ready for story breakdown and development
**Next Steps:** Story Manager to create detailed user stories with specific acceptance criteria
**Owner:** Development Team
**Estimated Timeline:** 2-3 sprints (4-6 weeks)