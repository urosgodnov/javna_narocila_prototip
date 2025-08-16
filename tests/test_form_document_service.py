#!/usr/bin/env python3
"""
Test script for Story 28.2 - File Storage Service Layer
Tests the FormDocumentService with deduplication and versioning
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
import hashlib
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.form_document_service import FormDocumentService
import database

def create_test_file(content: bytes, filename: str) -> BytesIO:
    """Create a test file in memory"""
    file_data = BytesIO(content)
    file_data.name = filename
    return file_data

def create_test_pdf(text: str = "Test PDF content") -> bytes:
    """Create a minimal valid PDF in bytes"""
    # Minimal valid PDF structure
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
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
({text}) Tj
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

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def test_file_storage_service():
    """Test the FormDocumentService implementation"""
    
    print("Testing Story 28.2: File Storage Service Layer")
    print("=" * 60)
    
    # Initialize database
    database.init_db()
    print("✓ Database initialized")
    
    # Create service instance
    service = FormDocumentService()
    print("✓ FormDocumentService created")
    
    # Ensure storage directory exists
    assert service.storage_root.exists(), "Storage root should exist"
    print(f"✓ Storage root exists: {service.storage_root}")
    
    # Test 1: Save a new document
    print_section("Test 1: Save New Document")
    
    test_content1 = create_test_pdf("This is a test document for the procurement system.")
    file1 = create_test_file(test_content1, "test_document.pdf")
    
    doc_id1, is_new1, msg1 = service.save_document(
        file_data=file1,
        form_id=1,
        form_type='draft',
        field_name='technical_specs',
        original_name='test_document.pdf',
        mime_type='application/pdf',
        organization_id=1,
        user='test_user'
    )
    
    print(f"  Document ID: {doc_id1}")
    print(f"  Is new file: {is_new1}")
    print(f"  Message: {msg1}")
    
    assert doc_id1 > 0, "Document ID should be positive"
    assert is_new1 == True, "First upload should be new"
    assert "successfully" in msg1.lower(), "Should report success"
    print("  ✓ New document saved successfully")
    
    # Test 2: Save duplicate document (deduplication test)
    print_section("Test 2: Deduplication Test")
    
    file2 = create_test_file(test_content1, "different_name.pdf")  # Same content, different name
    
    doc_id2, is_new2, msg2 = service.save_document(
        file_data=file2,
        form_id=2,  # Different form
        form_type='draft',
        field_name='technical_specs',
        original_name='different_name.pdf',
        mime_type='application/pdf',
        organization_id=1,
        user='test_user'
    )
    
    print(f"  Document ID: {doc_id2}")
    print(f"  Is new file: {is_new2}")
    print(f"  Message: {msg2}")
    
    assert doc_id2 == doc_id1, "Should return same document ID for duplicate content"
    assert is_new2 == False, "Duplicate should not be new"
    assert "linked" in msg2.lower(), "Should report linking"
    print("  ✓ Deduplication working - file reused")
    
    # Test 3: Verify hash-based directory structure
    print_section("Test 3: Hash-based Directory Structure")
    
    # Get the document to check its file path
    doc = service.get_document(doc_id1)
    assert doc is not None, "Document should exist"
    
    file_path = Path(doc['file_path'])
    print(f"  File path: {file_path}")
    
    # Check directory structure (should be hash-based)
    parts = file_path.parts
    assert 'form_documents' in parts, "Should be in form_documents directory"
    
    # Verify file exists
    assert file_path.exists(), "Physical file should exist"
    print(f"  ✓ File exists at: {file_path}")
    
    # Verify hash-based path
    file_hash = doc['file_hash']
    print(f"  File hash: {file_hash}")
    assert file_hash[:2] in str(file_path), "Path should contain hash prefix"
    print("  ✓ Hash-based directory structure verified")
    
    # Test 4: Get document with associations
    print_section("Test 4: Document Retrieval")
    
    doc_full = service.get_document(doc_id1)
    assert doc_full is not None, "Document should be retrievable"
    
    print(f"  Original name: {doc_full['original_name']}")
    print(f"  File size: {doc_full['file_size']} bytes")
    print(f"  Associations: {len(doc_full['associations'])}")
    
    assert len(doc_full['associations']) == 2, "Should have 2 associations (2 forms)"
    print("  ✓ Document retrieved with all associations")
    
    # Test 5: Get documents for a specific form
    print_section("Test 5: Get Documents by Form")
    
    form1_docs = service.get_documents_for_form(1, 'draft')
    form2_docs = service.get_documents_for_form(2, 'draft')
    
    print(f"  Form 1 documents: {len(form1_docs)}")
    print(f"  Form 2 documents: {len(form2_docs)}")
    
    # Find the document we just created
    our_doc_in_form1 = [d for d in form1_docs if d['id'] == doc_id1]
    our_doc_in_form2 = [d for d in form2_docs if d['id'] == doc_id2]
    
    assert len(our_doc_in_form1) >= 1, "Form 1 should have our document"
    assert len(our_doc_in_form2) >= 1, "Form 2 should have our document"
    assert doc_id1 == doc_id2, "Both forms should share same document ID"
    print("  ✓ Document sharing across forms verified")
    
    # Test 6: File validation
    print_section("Test 6: File Validation")
    
    # Test oversized file
    large_content = b"x" * (service.max_file_size + 1)
    large_file = create_test_file(large_content, "large.pdf")
    
    try:
        service.save_document(
            file_data=large_file,
            form_id=3,
            form_type='draft',
            field_name='test',
            original_name='large.pdf',
            mime_type='application/pdf'
        )
        assert False, "Should reject oversized file"
    except ValueError as e:
        print(f"  ✓ Oversized file rejected: {e}")
    
    # Test invalid extension
    invalid_file = create_test_file(b"test", "test.exe")
    
    try:
        service.save_document(
            file_data=invalid_file,
            form_id=3,
            form_type='draft',
            field_name='test',
            original_name='test.exe',
            mime_type='application/x-msdownload'
        )
        assert False, "Should reject invalid file type"
    except ValueError as e:
        print(f"  ✓ Invalid file type rejected: {e}")
    
    # Test 7: Statistics
    print_section("Test 7: Deduplication Statistics")
    
    stats = service.get_document_statistics()
    
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Unique files: {stats['unique_files']}")
    print(f"  Deduplication ratio: {stats['deduplication_ratio']:.1%}")
    print(f"  Storage saved: {stats['storage_saved_mb']:.2f} MB")
    
    assert stats['total_documents'] >= 1, "Should have at least 1 document"
    assert stats['unique_files'] >= 1, "Should have at least 1 unique file"
    print("  ✓ Statistics calculated correctly")
    
    # Test 8: Cleanup orphaned files
    print_section("Test 8: Orphaned File Cleanup")
    
    # Create an orphaned file
    orphan_path = service.storage_root / "test" / "orphan.txt"
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_text("orphaned content")
    
    # Run cleanup
    orphaned_count = service.cleanup_orphaned_files()
    print(f"  Cleaned up {orphaned_count} orphaned file(s)")
    
    assert not orphan_path.exists(), "Orphaned file should be deleted"
    print("  ✓ Orphaned file cleanup working")
    
    # Test 9: Document deletion
    print_section("Test 9: Document Deletion")
    
    # Create a document with single association for deletion test
    test_content3 = create_test_pdf("Document for deletion test")
    file3 = create_test_file(test_content3, "delete_test.pdf")
    
    doc_id3, _, _ = service.save_document(
        file_data=file3,
        form_id=99,
        form_type='draft',
        field_name='test_delete',
        original_name='delete_test.pdf',
        mime_type='application/pdf'
    )
    
    # Delete the document
    success = service.delete_document(doc_id3, user='test_user')
    assert success, "Deletion should succeed"
    
    # Verify it's gone
    deleted_doc = service.get_document(doc_id3)
    assert deleted_doc is None, "Deleted document should not be retrievable"
    print("  ✓ Document deletion successful")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! FormDocumentService is working correctly.")
    print("\nSummary:")
    print("  - Deduplication: Working")
    print("  - Hash-based storage: Working")
    print("  - File validation: Working")
    print("  - Document sharing: Working")
    print("  - Statistics: Working")
    print("  - Cleanup: Working")
    
    return True

if __name__ == "__main__":
    try:
        success = test_file_storage_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)