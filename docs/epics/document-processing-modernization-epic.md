# Document Processing Modernization - Brownfield Enhancement

**Epic ID:** EPIC-DOC-MODERN-001  
**Created:** 2025-01-15  
**Type:** Brownfield Enhancement  
**Effort:** 2-3 stories  

## Epic Goal

Modernize the document processing pipeline by integrating Docling for advanced document conversion and LangChain for intelligent text chunking, while cleaning up the admin panel sidebar to improve user experience.

## Epic Description

**Existing System Context:**

- **Current functionality:** Basic text extraction using PyPDF2/python-docx with single-chunk storage (50k characters)
- **Technology stack:** Python, SQLite, Streamlit, OpenAI embeddings, Qdrant vector store
- **Integration points:** 
  - `services/form_document_processor.py` - Document processing pipeline
  - `ui/ai_manager.py` - Admin query interface with sidebar
  - AI document storage tables and vector embeddings

**Enhancement Details:**

- **What's being added:** 
  1. Docling integration for superior document layout understanding and text extraction
  2. LangChain RecursiveCharacterTextSplitter for intelligent, structure-aware chunking
  3. Removal of "Zgodovina poizvedb" sidebar from admin panel for cleaner interface

- **How it integrates:** 
  - Replace existing TextExtractor with Docling-powered extraction
  - Replace simple chunking with LangChain's recursive text splitter
  - Remove sidebar component while preserving query functionality
  - Maintain existing database schema and vector storage

- **Success criteria:**
  - Improved text extraction quality and document structure preservation
  - Better chunk boundaries respecting document hierarchy
  - Cleaner admin interface without sidebar clutter
  - Backward compatibility with existing processed documents

## Stories

### Story 1: Docling Document Conversion Integration
**Goal:** Replace existing text extraction with Docling for better document understanding
- Integrate Docling library for document conversion
- Enhance TextExtractor class with layout-aware extraction
- Preserve existing API while improving extraction quality
- Add support for more document formats and better table/image handling

### Story 2: LangChain Intelligent Chunking Implementation  
**Goal:** Implement RecursiveCharacterTextSplitter for structure-aware document chunking
- Replace basic single-chunk approach with LangChain text splitters
- Configure recursive splitting to respect document hierarchy
- Optimize chunk sizes for embedding and retrieval performance
- Maintain compatibility with existing vector storage

### Story 3: Admin Panel Sidebar Cleanup
**Goal:** Remove "Zgodovina poizvedb" sidebar and streamline admin interface
- Remove query history sidebar from ai_manager.py
- Preserve query history functionality in main panel if needed
- Clean up layout and improve admin panel user experience
- Ensure no regression in admin functionality

## Compatibility Requirements

- [ ] Existing document processing API remains unchanged
- [ ] Database schema for ai_documents and chunks compatible
- [ ] Vector storage format maintains consistency
- [ ] Admin panel functionality preserved (minus sidebar)
- [ ] Performance impact is minimal or improved
- [ ] Existing processed documents continue to work

## Risk Mitigation

**Primary Risk:** New libraries may have different dependencies or processing behavior that breaks existing document processing

**Mitigation:** 
- Implement new extractors alongside existing ones with feature flags
- Gradual rollout with fallback to existing TextExtractor
- Comprehensive testing with existing document samples
- Document format validation before processing

**Rollback Plan:** 
- Feature flags to revert to original TextExtractor
- Database schema supports both chunking approaches
- Keep existing dependencies alongside new ones during transition

## Definition of Done

- [ ] Docling integration complete with improved document conversion
- [ ] LangChain RecursiveCharacterTextSplitter implemented
- [ ] Admin panel sidebar removed and layout cleaned
- [ ] All existing document processing functionality verified
- [ ] No regression in vector search or AI suggestions
- [ ] Performance benchmarks meet or exceed current system
- [ ] Documentation updated for new processing capabilities

## Scope Validation

✅ **Epic can be completed in 3 stories maximum**  
✅ **No architectural documentation required** - builds on existing patterns  
✅ **Enhancement follows existing patterns** - extends current document processor  
✅ **Integration complexity manageable** - replaces components without API changes  

## Risk Assessment

✅ **Risk to existing system is low** - gradual replacement with fallbacks  
✅ **Rollback plan is feasible** - feature flags and parallel implementations  
✅ **Testing approach covers existing functionality** - regression test suite  
✅ **Team has sufficient knowledge** - building on established document processing pipeline  

---

**Status:** Ready for Story Development  
**Dependencies:** None (builds on existing EPIC-FORM-DOCS-001)  
**Next Steps:** Develop detailed user stories with Story Manager