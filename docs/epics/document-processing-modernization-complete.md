# Document Processing Modernization - Complete Specification

**Epic ID:** EPIC-DOC-MODERN-001  
**Created:** 2025-01-15  
**Type:** Brownfield Enhancement  
**Scope:** 3 Stories  
**Estimated Effort:** 8-12 hours  

---

## Executive Summary

This brownfield enhancement modernizes the existing document processing pipeline by integrating two industry-leading libraries - Docling for advanced document conversion and LangChain for intelligent text chunking. Additionally, it improves the admin panel UX by removing the cluttered sidebar query history. The enhancement maintains full backward compatibility while significantly improving document processing quality.

---

## Table of Contents

1. [Epic Overview](#epic-overview)
2. [Technical Context](#technical-context)
3. [Story 1: Docling Integration](#story-1-docling-document-conversion-integration)
4. [Story 2: LangChain Chunking](#story-2-langchain-intelligent-chunking-implementation)
5. [Story 3: Admin Panel Cleanup](#story-3-admin-panel-sidebar-cleanup)
6. [Implementation Plan](#implementation-plan)
7. [Risk Analysis](#risk-analysis)
8. [Success Metrics](#success-metrics)

---

## Epic Overview

### Goal
Modernize the document processing pipeline by integrating Docling for advanced document conversion and LangChain for intelligent text chunking, while cleaning up the admin panel sidebar to improve user experience.

### Business Value
- **Improved Accuracy:** Better text extraction preserving document structure
- **Enhanced Search:** Intelligent chunking improves vector search relevance
- **Better UX:** Cleaner admin interface without sidebar clutter
- **Future-Ready:** Modern libraries with active development and support

### Constraints
- Must maintain backward compatibility with existing processed documents
- Cannot change existing database schema
- Must preserve all current functionality
- Performance must meet or exceed current benchmarks

---

## Technical Context

### Current System Architecture

```
Current Document Processing Flow:
┌─────────────────┐
│  File Upload    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TextExtractor   │ ← PyPDF2/python-docx
│ (Basic Extract) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Single Chunk    │ ← 50,000 char limit
│   Storage       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Store    │ ← Qdrant
└─────────────────┘
```

### Enhanced Architecture

```
Enhanced Document Processing Flow:
┌─────────────────┐
│  File Upload    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Docling      │ ← Layout-aware extraction
│ (Smart Extract) │   Table/Image handling
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LangChain     │ ← RecursiveCharacterTextSplitter
│ (Smart Chunks)  │   Respects document structure
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Store    │ ← Qdrant (unchanged)
└─────────────────┘
```

### Key Files and Components

| Component | File | Current Implementation | Enhancement |
|-----------|------|----------------------|-------------|
| Text Extraction | `services/form_document_processor.py` | PyPDF2, python-docx | Docling |
| Chunking | `services/form_document_processor.py` | Single 50k chunk | LangChain RecursiveCharacterTextSplitter |
| Admin UI | `ui/ai_manager.py` | Sidebar with query history | Removed sidebar |

---

## Story 1: Docling Document Conversion Integration

**Story ID:** STORY-DOC-MODERN-1  
**Effort:** 3-4 hours  
**Priority:** High  

### User Story
As a **system administrator**,  
I want **better document text extraction that preserves structure**,  
So that **AI processing can understand document context better**.

### Technical Requirements

#### 1. Install and Configure Docling
```python
# requirements.txt addition
docling>=0.2.0

# Configuration
DOCLING_CONFIG = {
    'table_extraction': True,
    'image_extraction': True,
    'preserve_layout': True,
    'chunk_preparation': True
}
```

#### 2. Enhance TextExtractor Class
```python
class EnhancedTextExtractor(TextExtractor):
    """Docling-powered text extraction with fallback"""
    
    def __init__(self):
        self.docling_available = self._check_docling()
        super().__init__()
    
    def extract_with_docling(self, file_path: str) -> Dict:
        """Extract using Docling with structure preservation"""
        from docling import Document
        
        doc = Document.from_file(file_path)
        return {
            'text': doc.text,
            'tables': doc.tables,
            'metadata': doc.metadata,
            'structure': doc.structure_tree
        }
    
    def extract_text(self, file_path: str) -> str:
        """Main extraction with Docling fallback to original"""
        if self.docling_available:
            try:
                result = self.extract_with_docling(file_path)
                return self._format_structured_text(result)
            except Exception as e:
                logger.warning(f"Docling failed, using fallback: {e}")
        
        # Fallback to original implementation
        return super().extract_text(file_path)
```

#### 3. Feature Flag Implementation
```python
# In form_document_processor.py
USE_DOCLING = os.getenv('USE_DOCLING', 'true').lower() == 'true'

if USE_DOCLING:
    extractor = EnhancedTextExtractor()
else:
    extractor = TextExtractor()
```

### Acceptance Criteria
- [ ] Docling library integrated with graceful fallback
- [ ] Text extraction preserves document structure
- [ ] Tables and images handled properly
- [ ] Feature flag enables/disables Docling
- [ ] Performance metrics logged for comparison
- [ ] Existing documents continue to process

### Testing Requirements
```python
def test_docling_extraction():
    """Test Docling extraction vs original"""
    test_files = ['sample.pdf', 'sample.docx', 'complex_table.pdf']
    
    for file in test_files:
        original = TextExtractor().extract_text(file)
        enhanced = EnhancedTextExtractor().extract_text(file)
        
        assert len(enhanced) >= len(original)
        assert 'table' in enhanced or 'Table' in enhanced  # Better structure
```

---

## Story 2: LangChain Intelligent Chunking Implementation

**Story ID:** STORY-DOC-MODERN-2  
**Effort:** 4-5 hours  
**Priority:** High  

### User Story
As a **system administrator**,  
I want **intelligent document chunking that respects text structure**,  
So that **vector search returns more relevant and coherent results**.

### Technical Requirements

#### 1. Install and Configure LangChain
```python
# requirements.txt addition
langchain>=0.1.0
langchain-text-splitters>=0.0.1

# Configuration
CHUNKING_CONFIG = {
    'chunk_size': 1500,
    'chunk_overlap': 200,
    'separators': ["\n\n", "\n", ".", " ", ""],
    'keep_separator': True,
    'is_separator_regex': False
}
```

#### 2. Implement Smart Chunking
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

class SmartDocumentChunker:
    """LangChain-powered intelligent chunking"""
    
    def __init__(self, config: Dict = None):
        self.config = config or CHUNKING_CONFIG
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config['chunk_size'],
            chunk_overlap=self.config['chunk_overlap'],
            separators=self.config['separators'],
            keep_separator=self.config['keep_separator']
        )
    
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Create intelligent chunks with metadata"""
        # Use structure from Docling if available
        if metadata and 'structure' in metadata:
            chunks = self._structure_aware_split(text, metadata['structure'])
        else:
            chunks = self.splitter.split_text(text)
        
        # Enrich chunks with metadata
        return [
            {
                'text': chunk,
                'index': i,
                'metadata': {
                    **metadata,
                    'chunk_index': i,
                    'chunk_size': len(chunk)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def _structure_aware_split(self, text: str, structure: Dict) -> List[str]:
        """Split respecting document structure from Docling"""
        # Custom logic to respect headers, sections, etc.
        sections = self._extract_sections(text, structure)
        chunks = []
        
        for section in sections:
            if len(section) > self.config['chunk_size']:
                # Split large sections
                section_chunks = self.splitter.split_text(section)
                chunks.extend(section_chunks)
            else:
                chunks.append(section)
        
        return chunks
```

#### 3. Integration with Document Processor
```python
class FormDocumentProcessor:
    def process_document(self, doc_id: int, file_path: str):
        # Extract text with Docling
        extraction_result = self.text_extractor.extract_with_docling(file_path)
        
        # Smart chunking with LangChain
        chunker = SmartDocumentChunker()
        chunks = chunker.chunk_document(
            extraction_result['text'],
            extraction_result.get('metadata')
        )
        
        # Generate embeddings for chunks
        embeddings = self._generate_embeddings(chunks)
        
        # Store in vector database
        self._store_vectors(chunks, embeddings)
```

### Acceptance Criteria
- [ ] LangChain RecursiveCharacterTextSplitter integrated
- [ ] Chunks respect document structure (headers, paragraphs)
- [ ] Configurable chunk size and overlap
- [ ] Metadata preserved in chunks
- [ ] Vector storage compatible with new chunks
- [ ] Search relevance improved (measurable)

### Testing Requirements
```python
def test_intelligent_chunking():
    """Test LangChain chunking quality"""
    test_text = """
    # Header 1
    This is a paragraph under header 1.
    
    ## Subheader
    This is content under subheader.
    
    # Header 2
    Another section with different content.
    """
    
    chunker = SmartDocumentChunker()
    chunks = chunker.chunk_document(test_text)
    
    # Verify chunks respect structure
    assert len(chunks) >= 2
    assert not any(chunk['text'].count('#') > 1 for chunk in chunks)
    
    # Verify overlap
    for i in range(len(chunks) - 1):
        assert some_overlap(chunks[i]['text'], chunks[i+1]['text'])
```

---

## Story 3: Admin Panel Sidebar Cleanup

**Story ID:** STORY-DOC-MODERN-3  
**Effort:** 1-2 hours  
**Priority:** Medium  

### User Story
As an **admin user**,  
I want **a cleaner admin interface without the sidebar query history**,  
So that **I have more screen space and less visual clutter**.

### Technical Requirements

#### 1. Remove Sidebar from ai_manager.py
```python
# Remove lines 715-725 in ui/ai_manager.py
# DELETE THIS BLOCK:
"""
# Query history in sidebar
with st.sidebar:
    st.markdown("### 📜 Zgodovina poizvedb")
    if st.session_state.query_history:
        for i, hist_item in enumerate(reversed(st.session_state.query_history[-5:])):
            with st.expander(f"🔍 {hist_item['query'][:50]}..."):
                st.write(f"**Čas:** {hist_item['timestamp'].strftime('%H:%M:%S')}")
                st.write(f"**Zanesljivost:** {hist_item['confidence']:.0%}")
                st.write(f"**Odziv:** {hist_item['response_time']:.2f}s")
    else:
        st.info("Ni zgodovine poizvedb")
"""
```

#### 2. Optional: Add Query History to Main Panel
```python
def render_query_history_section():
    """Render query history in main panel if needed"""
    if st.checkbox("📜 Prikaži zgodovino poizvedb", value=False):
        if st.session_state.query_history:
            # Create a clean table view
            history_df = pd.DataFrame(st.session_state.query_history[-10:])
            st.dataframe(
                history_df[['query', 'timestamp', 'confidence', 'response_time']],
                use_container_width=True
            )
        else:
            st.info("Ni zgodovine poizvedb")
```

#### 3. Layout Optimization
```python
# Adjust main content to use full width
st.set_page_config(
    page_title="AI Manager",
    layout="wide",  # Use full width
    initial_sidebar_state="collapsed"  # No sidebar needed
)
```

### Acceptance Criteria
- [ ] Sidebar query history removed from ai_manager.py
- [ ] Admin panel uses full screen width
- [ ] Optional query history in main panel
- [ ] No functionality lost
- [ ] Layout is cleaner and more spacious
- [ ] No JavaScript errors or UI glitches

### Testing Requirements
```python
def test_admin_panel_layout():
    """Test admin panel without sidebar"""
    # Visual regression test
    page = render_ai_manager()
    
    # Verify no sidebar elements
    assert 'sidebar' not in page.get_elements()
    assert 'Zgodovina poizvedb' not in page.get_text()
    
    # Verify full width usage
    assert page.layout == 'wide'
```

---

## Implementation Plan

### Phase 1: Preparation (Day 1)
1. Create feature branch: `feature/document-processing-modernization`
2. Install dependencies: `pip install docling langchain langchain-text-splitters`
3. Set up feature flags in environment
4. Create test document suite

### Phase 2: Story Implementation (Days 2-3)
1. **Morning:** Implement Story 1 (Docling integration)
   - Test with sample documents
   - Verify fallback mechanism
   
2. **Afternoon:** Implement Story 2 (LangChain chunking)
   - Test chunking quality
   - Verify vector storage compatibility
   
3. **Next Morning:** Implement Story 3 (Admin cleanup)
   - Remove sidebar
   - Test admin panel functionality

### Phase 3: Testing & Validation (Day 3)
1. Run regression tests on existing documents
2. Performance benchmarking
3. User acceptance testing
4. Documentation updates

### Phase 4: Deployment (Day 4)
1. Deploy with feature flags disabled
2. Enable Docling for subset of documents
3. Monitor performance and quality
4. Gradual rollout to all documents

---

## Risk Analysis

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Docling dependency conflicts | Low | Medium | Isolated virtual environment, fallback to original |
| Performance degradation | Medium | High | Feature flags, performance monitoring, caching |
| Chunking breaks search | Low | High | Extensive testing, gradual rollout |
| Admin UI regression | Very Low | Low | Visual testing, user feedback |

### Rollback Procedures

#### Docling Rollback
```bash
# Disable via environment variable
export USE_DOCLING=false
# Restart application
systemctl restart javna-narocila
```

#### LangChain Rollback
```bash
# Revert to simple chunking
export USE_SMART_CHUNKING=false
# Restart application
systemctl restart javna-narocila
```

#### UI Rollback
```bash
# Restore from git
git checkout main -- ui/ai_manager.py
# Restart application
```

---

## Success Metrics

### Quantitative Metrics

| Metric | Current Baseline | Target | Measurement Method |
|--------|-----------------|--------|-------------------|
| Text Extraction Accuracy | 85% | 95% | Character comparison with ground truth |
| Average Chunk Quality | 60% | 85% | Coherence scoring |
| Search Relevance | 70% | 85% | User feedback ratings |
| Processing Time | 2.5s/doc | <3.0s/doc | Performance logging |
| Admin Panel Load Time | 1.2s | <1.0s | Browser metrics |

### Qualitative Metrics

1. **Document Structure Preservation**
   - Tables properly extracted
   - Headers and sections maintained
   - Lists and formatting preserved

2. **Chunk Coherence**
   - Complete thoughts in chunks
   - No mid-sentence breaks
   - Context preserved

3. **User Experience**
   - Cleaner admin interface
   - More screen real estate
   - Improved visual hierarchy

### Monitoring Dashboard
```python
# Add metrics collection
class ProcessingMetrics:
    def log_extraction(self, doc_id, method, duration, quality_score):
        """Log extraction metrics"""
        
    def log_chunking(self, doc_id, num_chunks, avg_size, quality_score):
        """Log chunking metrics"""
        
    def generate_report(self):
        """Generate performance report"""
```

---

## Appendix A: Dependencies

### New Dependencies
```txt
docling>=0.2.0
langchain>=0.1.0
langchain-text-splitters>=0.0.1
```

### Existing Dependencies (Maintained)
```txt
streamlit
sqlite3
openai
qdrant-client
PyPDF2  # Kept as fallback
python-docx  # Kept as fallback
```

---

## Appendix B: Code Examples

### Complete Docling Integration Example
```python
from docling import Document, DocumentConverter

class DoclingProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
    
    def process(self, file_path: str) -> Dict:
        # Convert document
        doc = self.converter.convert(file_path)
        
        # Extract components
        result = {
            'text': doc.text,
            'tables': [table.to_dict() for table in doc.tables],
            'images': [img.to_dict() for img in doc.images],
            'metadata': doc.metadata,
            'structure': doc.structure_tree
        }
        
        return result
```

### Complete LangChain Chunking Example
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangDoc

def smart_chunk(text: str, metadata: dict = None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Create LangChain documents
    docs = [LangDoc(page_content=text, metadata=metadata or {})]
    
    # Split documents
    chunks = splitter.split_documents(docs)
    
    return [
        {
            'text': chunk.page_content,
            'metadata': chunk.metadata
        }
        for chunk in chunks
    ]
```

---

## Appendix C: Testing Checklist

### Pre-Implementation Tests
- [ ] Backup existing database
- [ ] Document current performance metrics
- [ ] Save sample of current extractions

### Post-Implementation Tests
- [ ] All existing documents still searchable
- [ ] Vector search returns relevant results
- [ ] Admin panel fully functional
- [ ] No performance regression
- [ ] Feature flags working correctly
- [ ] Rollback procedures tested

### User Acceptance Tests
- [ ] Document upload works
- [ ] Search quality improved
- [ ] Admin interface cleaner
- [ ] No functionality lost
- [ ] Performance acceptable

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-15  
**Status:** Ready for Review  
**Next Review:** After Story Implementation  

---

*This document serves as the complete specification for the Document Processing Modernization epic. It should be reviewed with stakeholders before implementation begins.*