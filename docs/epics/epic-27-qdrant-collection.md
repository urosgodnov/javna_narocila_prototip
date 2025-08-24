# Epic 27: Qdrant Collection Setup and Admin Management - Brownfield Enhancement

## Epic Goal
Establish a dedicated `javna_narocila` collection in the Qdrant cluster with proper metadata structure and implement admin interface for managing vector documents, enabling centralized semantic search across all procurement documentation.

## Epic Description

### Existing System Context
- **Current relevant functionality**: The system already has document processing capabilities via `/services/form_document_processor.py` that generates embeddings and stores them in Qdrant
- **Technology stack**: Python 3, Qdrant Client, OpenAI text-embedding-3-small, LangChain, Docling, Streamlit admin panel at `/ui/admin_panel.py`
- **Integration points**: 
  - Existing document processor service that creates embeddings
  - Admin panel with multiple tabs for system management
  - SQLite tables `ai_documents` and `ai_document_chunks` tracking document metadata

### Enhancement Details
- **What's being added/changed**: 
  - Create dedicated `javna_narocila` collection in Qdrant with proper configuration
  - Add new admin module tab for Qdrant management (upload, update, delete documents)
  - Implement metadata schema for better document categorization and retrieval
  - Support multiple document formats (PDF, HTML, DOC, DOCX) using Docling for extraction
- **How it integrates**:
  - Extends existing admin panel with new "Vector Database" tab
  - Uses existing QdrantClient configuration from provided API credentials
  - Leverages current document processing pipeline
- **Success criteria**:
  - Collection created with appropriate vector dimensions (1536 for OpenAI text-embedding-3-small)
  - Documents chunked using LangChain RecursiveCharacterTextSplitter
  - Multiple document formats supported (PDF, HTML, DOC, DOCX) via Docling
  - Admin can perform CRUD operations on vector documents
  - Metadata properly stored and searchable
  - Existing document processing continues to work

## Stories

### Story 1: Create Qdrant Collection with Metadata Schema
- Set up `javna_narocila` collection with 1536 dimensions for text-embedding-3-small
- Configure collection with cosine distance metric
- Define metadata schema (document_type, organization, created_at, etc.)
- Implement collection initialization check on app startup

### Story 2: Implement Document Processing Pipeline
- Integrate Docling for document extraction (PDF, HTML, DOC, DOCX)
- Implement LangChain RecursiveCharacterTextSplitter for document chunking
- Configure OpenAI text-embedding-3-small for vector generation
- Add "Vector Database" tab to existing admin panel
- Create interface for uploading and processing documents
- Display existing vectors with metadata and search functionality

### Story 3: Integrate CRUD Operations and Testing
- Implement update and delete operations for vectors
- Add batch operations support
- Create test suite for vector operations

## Compatibility Requirements
- ✅ Existing APIs remain unchanged - Document processor continues using same interfaces
- ✅ Database schema changes are backward compatible - Only adding to admin UI, not changing schema
- ✅ UI changes follow existing patterns - New tab follows admin panel pattern
- ✅ Performance impact is minimal - Vector operations are async where possible

## Risk Mitigation
- **Primary Risk**: Disruption to existing document processing pipeline that may already be using Qdrant
- **Mitigation**: 
  - Check for existing collections before creating new one
  - Implement collection versioning if needed
  - Keep existing document processor interfaces unchanged
- **Rollback Plan**: 
  - Collection can be renamed or deleted without affecting SQLite data
  - Admin UI changes are isolated to new tab
  - Document processor fallback to previous collection if configured

## Definition of Done
- All stories completed with acceptance criteria met
- Existing document processing functionality verified through testing
- Integration with admin panel working correctly
- Documentation updated in memory bank
- No regression in AI document features

## Technical Details

### Document Extraction Configuration (Docling)
```python
from docling import DocumentConverter
from docling.datamodel import ConversionResult
from pathlib import Path

# Docling configuration for document extraction
doc_converter = DocumentConverter()

def extract_document_content(file_path: str) -> str:
    """
    Extract text content from various document formats using Docling.
    Supports: PDF, HTML, DOC, DOCX, and more.
    """
    # Convert document to text
    result: ConversionResult = doc_converter.convert(Path(file_path))
    
    # Extract text with structure preservation
    text_content = result.document.export_to_markdown()
    
    # Metadata extraction
    metadata = {
        "title": result.document.title if hasattr(result.document, 'title') else None,
        "pages": len(result.document.pages) if hasattr(result.document, 'pages') else None,
        "tables_count": len(result.document.tables) if hasattr(result.document, 'tables') else 0,
        "figures_count": len(result.document.figures) if hasattr(result.document, 'figures') else 0,
    }
    
    return text_content, metadata

# Supported file formats
SUPPORTED_FORMATS = [
    '.pdf',    # PDF documents
    '.html',   # HTML pages
    '.doc',    # Microsoft Word (legacy)
    '.docx',   # Microsoft Word
    '.pptx',   # PowerPoint presentations
    '.xlsx',   # Excel spreadsheets
    '.md',     # Markdown files
    '.txt',    # Plain text
]
```

### Embedding Configuration
```python
from openai import OpenAI

# OpenAI client for embeddings
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

def create_embedding(text: str) -> List[float]:
    """Create embedding using OpenAI text-embedding-3-small model"""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding
```

### Document Processing Pipeline
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

# LangChain chunking configuration
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,           # Target chunk size in characters
    chunk_overlap=200,          # Overlap between chunks for context preservation
    length_function=len,        # Function to calculate text length
    separators=[
        "\n\n",                 # Double newline (paragraph boundary)
        "\n",                   # Single newline
        ". ",                   # Sentence boundary
        ", ",                   # Clause boundary
        " ",                    # Word boundary
        ""                      # Character boundary (fallback)
    ],
    is_separator_regex=False   # Treat separators as literal strings
)

def process_document(file_path: str) -> Dict[str, Any]:
    """
    Complete document processing pipeline:
    1. Extract content with Docling
    2. Chunk with LangChain
    3. Generate embeddings with OpenAI
    """
    # Step 1: Extract document content
    text_content, doc_metadata = extract_document_content(file_path)
    
    # Step 2: Chunk the document
    chunks = text_splitter.split_text(text_content)
    
    # Step 3: Generate embeddings for each chunk
    embeddings = []
    for chunk in chunks:
        embedding = create_embedding(chunk)
        embeddings.append({
            "text": chunk,
            "vector": embedding,
            "metadata": {
                **doc_metadata,
                "chunk_index": len(embeddings),
                "total_chunks": len(chunks)
            }
        })
    
    return {
        "chunks": chunks,
        "embeddings": embeddings,
        "metadata": doc_metadata
    }
```

### Qdrant Configuration
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

qdrant_client = QdrantClient(
    url="https://df29e6ff-cca0-4d8c-826e-043a5685787b.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.n__ZT9tBQXV-61x77kygnAJDh7rSKdnfZTuN17u_jCc",
)

# Collection configuration
collection_config = VectorParams(
    size=EMBEDDING_DIMENSIONS,  # 1536 for text-embedding-3-small
    distance=Distance.COSINE    # Cosine similarity for semantic search
)
```

### Collection Name
- Primary collection: `javna_narocila`

### Metadata Schema (Proposed)
- document_id: string
- document_type: string (procurement, contract, specification, etc.)
- organization: string
- created_at: datetime
- updated_at: datetime
- form_id: integer (reference to form if applicable)
- chunk_index: integer
- total_chunks: integer
- original_filename: string
- file_format: string (e.g., "pdf", "docx", "html")
- processing_status: string
- embedding_model: string (e.g., "text-embedding-3-small")
- chunk_method: string (e.g., "recursive_character_text_splitter")
- chunk_size: integer
- chunk_overlap: integer
- extraction_method: string (e.g., "docling")
- page_count: integer (for multi-page documents)
- tables_count: integer (extracted tables)
- figures_count: integer (extracted figures)

## Validation Checklist

### Scope Validation
- ✅ Epic can be completed in 3 stories
- ✅ No architectural documentation required - follows existing patterns
- ✅ Enhancement follows existing admin panel and service patterns
- ✅ Integration complexity is manageable - uses existing QdrantClient

### Risk Assessment
- ✅ Risk to existing system is low - additive changes only
- ✅ Rollback plan is feasible - can remove collection without data loss
- ✅ Testing approach covers existing functionality
- ✅ Team has sufficient knowledge - existing Qdrant usage in codebase

### Completeness Check
- ✅ Epic goal is clear and achievable
- ✅ Stories are properly scoped (collection setup, UI, integration)
- ✅ Success criteria are measurable
- ✅ Dependencies identified (QdrantClient, admin panel, document processor)

---
**Status**: Ready for Story Development
**Created**: 2025-01-24
**Epic Number**: 27
**Type**: Brownfield Enhancement