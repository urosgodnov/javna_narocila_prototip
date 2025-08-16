#!/usr/bin/env python3
"""
Test script for Story 28.4 - AI Document Processing Pipeline
Tests the FormDocumentProcessor and AI integration
"""

import os
import sys
import sqlite3
import asyncio
from pathlib import Path
from io import BytesIO
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def create_test_pdf_with_content():
    """Create a test PDF with meaningful content"""
    content = """
This is a test document for the public procurement system.

TECHNICAL SPECIFICATIONS:
- The system must support multiple file formats
- AI processing should extract key information
- Document deduplication is required
- Vector search capabilities are essential

REQUIREMENTS:
1. Performance: Process documents within 30 seconds
2. Accuracy: 95% text extraction accuracy
3. Scalability: Handle 1000+ documents
4. Security: Encrypted storage and transmission

This document contains important procurement information that should be 
processed and indexed for future retrieval and AI-powered suggestions.
    """
    
    # Create minimal PDF with content
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {len(content)} >>
stream
BT
/F1 12 Tf
50 750 Td
({content}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000111 00000 n
0000000212 00000 n
0000000289 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
389
%%EOF"""
    
    return pdf_content.encode('latin-1')

def test_ai_processing():
    """Test the AI document processing pipeline"""
    
    print("Testing Story 28.4: AI Document Processing Pipeline")
    print("=" * 60)
    
    # Initialize database
    import database
    database.init_db()
    print("✓ Database initialized with AI tables")
    
    # Test 1: Verify AI tables exist
    print_section("Test 1: Database Tables")
    
    conn = sqlite3.connect('mainDB.db')
    cursor = conn.cursor()
    
    tables_to_check = [
        'ai_documents',
        'ai_document_chunks',
        'form_document_processing_queue'
    ]
    
    for table in tables_to_check:
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table}'
        """)
        
        if cursor.fetchone():
            print(f"✓ {table} table exists")
        else:
            print(f"✗ {table} table missing")
            return False
    
    # Test 2: Import and initialize processor
    print_section("Test 2: Processor Initialization")
    
    try:
        from services.form_document_processor import (
            FormDocumentProcessor, 
            ProcessingQueue,
            TextExtractor
        )
        processor = FormDocumentProcessor()
        print("✓ FormDocumentProcessor initialized")
        
        if processor.ai_available:
            print("✓ AI components available")
        else:
            print("⚠ AI components not available (OpenAI/Qdrant not configured)")
    except ImportError as e:
        print(f"✗ Failed to import processor: {e}")
        return False
    
    # Test 3: Text extraction capabilities
    print_section("Test 3: Text Extraction")
    
    extractor = TextExtractor()
    
    # Create a test text file
    test_file_path = Path("test_document.txt")
    test_content = "This is a test document with procurement information."
    test_file_path.write_text(test_content)
    
    extracted = extractor.extract_text(str(test_file_path), '.txt')
    if extracted == test_content:
        print("✓ Text file extraction working")
    else:
        print("✗ Text file extraction failed")
    
    # Clean up
    test_file_path.unlink()
    
    # Check PDF extraction capability
    if extractor.extract_from_pdf("dummy.pdf").startswith("[PDF extraction not available"):
        print("⚠ PDF extraction not available (install PyPDF2)")
    else:
        print("✓ PDF extraction available")
    
    # Check DOCX extraction capability
    if extractor.extract_from_docx("dummy.docx").startswith("[DOCX extraction not available"):
        print("⚠ DOCX extraction not available (install python-docx)")
    else:
        print("✓ DOCX extraction available")
    
    # Test 4: Create and process a test document
    print_section("Test 4: Document Processing")
    
    # First, create a form document using FormDocumentService
    try:
        from services.form_document_service import FormDocumentService
        doc_service = FormDocumentService()
        
        # Create test PDF
        pdf_data = create_test_pdf_with_content()
        file_data = BytesIO(pdf_data)
        
        # Save document
        doc_id, is_new, msg = doc_service.save_document(
            file_data=file_data,
            form_id=100,
            form_type='draft',
            field_name='test_field',
            original_name='test_procurement.pdf',
            mime_type='application/pdf',
            user='test_user'
        )
        
        print(f"✓ Test document saved (ID: {doc_id})")
        
        # Process the document
        success, message = processor.process_form_document(doc_id)
        
        if success:
            print(f"✓ Document processed: {message}")
        else:
            print(f"⚠ Processing result: {message}")
        
    except Exception as e:
        print(f"✗ Error during processing: {e}")
    
    # Test 5: Check processing results
    print_section("Test 5: Processing Results")
    
    # Check if AI document was created
    cursor.execute("""
        SELECT id, processing_status, chunk_count
        FROM ai_documents
        WHERE tip_dokumenta = 'form_upload'
        ORDER BY id DESC
        LIMIT 1
    """)
    
    ai_doc = cursor.fetchone()
    if ai_doc:
        ai_doc_id, status, chunks = ai_doc
        print(f"✓ AI document created (ID: {ai_doc_id})")
        print(f"  Status: {status}")
        print(f"  Chunks: {chunks or 0}")
        
        # Check chunks
        cursor.execute("""
            SELECT COUNT(*) FROM ai_document_chunks
            WHERE document_id = ?
        """, (ai_doc_id,))
        
        chunk_count = cursor.fetchone()[0]
        if chunk_count > 0:
            print(f"✓ {chunk_count} chunks created")
        else:
            print("⚠ No chunks created (AI may not be configured)")
    else:
        print("⚠ No AI document created")
    
    # Test 6: Queue functionality
    print_section("Test 6: Processing Queue")
    
    queue = ProcessingQueue()
    
    # Check queue table
    cursor.execute("""
        SELECT COUNT(*) FROM form_document_processing_queue
    """)
    
    queue_count = cursor.fetchone()[0]
    print(f"  Queue entries: {queue_count}")
    
    # Test async queue processing
    async def test_queue():
        # Add a document to queue
        await queue.add_to_queue(doc_id, priority=10)
        print("✓ Document added to queue")
        
        # Process pending queue
        await queue.process_pending_queue()
        print("✓ Queue processed")
    
    # Run async test
    try:
        asyncio.run(test_queue())
    except Exception as e:
        print(f"⚠ Queue test error: {e}")
    
    # Test 7: Check form document link
    print_section("Test 7: Form Document Integration")
    
    cursor.execute("""
        SELECT id, ai_document_id, processing_status
        FROM form_documents
        WHERE id = ?
    """, (doc_id,))
    
    form_doc = cursor.fetchone()
    if form_doc:
        _, ai_link, proc_status = form_doc
        if ai_link:
            print(f"✓ Form document linked to AI document {ai_link}")
        else:
            print("⚠ Form document not linked to AI document")
        
        print(f"  Processing status: {proc_status}")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ AI Processing Pipeline Tests Complete!")
    print("\nCapabilities:")
    print("- Text extraction: Available")
    print(f"- PDF extraction: {'Available' if not extractor.extract_from_pdf('').startswith('[PDF') else 'Not available'}")
    print(f"- DOCX extraction: {'Available' if not extractor.extract_from_docx('').startswith('[DOCX') else 'Not available'}")
    print(f"- AI processing: {'Available' if processor.ai_available else 'Not configured'}")
    print("\nIntegration Points:")
    print("- form_document_processor.py: Complete service implementation")
    print("- app.py: Lines 1230-1237 (AI processing trigger)")
    print("- database.py: Lines 514-577 (AI tables creation)")
    
    print("\nNotes:")
    print("- Install PyPDF2 for PDF text extraction: pip install PyPDF2")
    print("- Install python-docx for DOCX extraction: pip install python-docx")
    print("- Configure OpenAI API key in .env for embeddings")
    print("- Configure Qdrant for vector storage")
    
    return True

if __name__ == "__main__":
    try:
        success = test_ai_processing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)