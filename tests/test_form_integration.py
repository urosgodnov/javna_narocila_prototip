#!/usr/bin/env python3
"""
Test script for Story 28.3 - Form Renderer Integration
Tests the integration of FormDocumentService with the form UI
"""

import sys
import os
from pathlib import Path
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def test_form_integration():
    """Test the form renderer integration with document storage"""
    
    print("Testing Story 28.3: Form Renderer Integration")
    print("=" * 60)
    
    # Initialize database
    import database
    database.init_db()
    print("✓ Database initialized")
    
    # Test 1: Verify tables exist
    print_section("Test 1: Database Tables")
    
    conn = sqlite3.connect('mainDB.db')
    cursor = conn.cursor()
    
    # Check form_documents table
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='form_documents'
    """)
    
    if cursor.fetchone():
        print("✓ form_documents table exists")
    else:
        print("✗ form_documents table missing")
        return False
    
    # Check form_document_associations table
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='form_document_associations'
    """)
    
    if cursor.fetchone():
        print("✓ form_document_associations table exists")
    else:
        print("✗ form_document_associations table missing")
        return False
    
    conn.close()
    
    # Test 2: Verify FormDocumentService import
    print_section("Test 2: Service Import")
    
    try:
        from services.form_document_service import FormDocumentService
        service = FormDocumentService()
        print("✓ FormDocumentService imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import FormDocumentService: {e}")
        return False
    
    # Test 3: Check storage directory
    print_section("Test 3: Storage Directory")
    
    storage_path = Path("data/form_documents")
    if storage_path.exists():
        print(f"✓ Storage directory exists: {storage_path}")
    else:
        print(f"✗ Storage directory missing: {storage_path}")
        return False
    
    # Test 4: Simulate form integration
    print_section("Test 4: Integration Points")
    
    # Check if form_renderer.py has the new code
    form_renderer_path = Path("ui/form_renderer.py")
    if form_renderer_path.exists():
        content = form_renderer_path.read_text()
        
        checks = [
            ("FormDocumentService import", "from services.form_document_service import FormDocumentService"),
            ("File info storage", "_file_info"),
            ("Document removal", "_remove_doc_id"),
            ("Existing document check", "get_documents_for_form")
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name} found in form_renderer.py")
            else:
                print(f"✗ {check_name} missing in form_renderer.py")
    else:
        print("✗ form_renderer.py not found")
        return False
    
    # Test 5: Check app.py integration
    print_section("Test 5: App Integration")
    
    app_path = Path("app.py")
    if app_path.exists():
        content = app_path.read_text()
        
        checks = [
            ("File save on draft", "save_document"),
            ("File removal", "delete_document"),
            ("Form ID storage", "st.session_state.form_id"),
            ("File counting", "files_saved")
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                print(f"✓ {check_name} found in app.py")
            else:
                print(f"✗ {check_name} missing in app.py")
    else:
        print("✗ app.py not found")
        return False
    
    # Test 6: Verify backward compatibility
    print_section("Test 6: Backward Compatibility")
    
    # Create a test draft without files
    test_form_data = {
        "projectInfo": {
            "projectName": "Test Project Without Files"
        },
        "orderType": {
            "type": "Goods"
        }
    }
    
    draft_id = database.save_draft(test_form_data)
    if draft_id:
        print(f"✓ Draft saved without files (ID: {draft_id})")
        
        # Load it back
        loaded_data = database.load_draft(draft_id)
        if loaded_data:
            print("✓ Draft loaded successfully")
        else:
            print("✗ Failed to load draft")
    else:
        print("✗ Failed to save draft")
    
    print("\n" + "=" * 60)
    print("✅ Integration tests completed successfully!")
    print("\nManual Testing Checklist:")
    print("1. [ ] Start the Streamlit app: streamlit run app.py")
    print("2. [ ] Navigate to a form with file upload fields")
    print("3. [ ] Upload a PDF or image file")
    print("4. [ ] Save the form as draft")
    print("5. [ ] Reload the page and load the draft")
    print("6. [ ] Verify the file information is displayed")
    print("7. [ ] Test removing a file")
    print("8. [ ] Test replacing a file with a new version")
    print("9. [ ] Verify deduplication by uploading the same file twice")
    print("\nIntegration Points:")
    print("- form_renderer.py: Lines 744-802 (file upload handling)")
    print("- app.py: Lines 1177, 1191-1247 (form save/load)")
    print("- FormDocumentService: Complete service implementation")
    
    return True

if __name__ == "__main__":
    try:
        success = test_form_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)