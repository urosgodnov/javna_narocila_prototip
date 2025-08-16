import pytest
import os
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys

# Add the parent directory to sys.path to allow importing template_service.py and database.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock sqlite3.connect for template_service tests
@pytest.fixture(autouse=True)
def mock_sqlite_connect_for_template_service():
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        yield mock_connect, mock_conn, mock_cursor

@pytest.fixture
def setup_template_dir():
    test_template_dir = 'test_templates'
    if not os.path.exists(test_template_dir):
        os.makedirs(test_template_dir)
    yield test_template_dir
    shutil.rmtree(test_template_dir)

@pytest.fixture
def setup_backup_dir():
    test_backup_dir = 'test_backups'
    if not os.path.exists(test_backup_dir):
        os.makedirs(test_backup_dir)
    yield test_backup_dir
    shutil.rmtree(test_backup_dir)

def test_list_templates(setup_template_dir):
    from template_service import list_templates
    # Create dummy docx files
    with open(os.path.join(setup_template_dir, 'template1.docx'), 'w') as f: f.write("dummy")
    with open(os.path.join(setup_template_dir, 'template2.docx'), 'w') as f: f.write("dummy")
    with open(os.path.join(setup_template_dir, 'not_a_template.txt'), 'w') as f: f.write("dummy")

    templates = list_templates(template_dir=setup_template_dir)
    assert sorted(templates) == sorted(['template1.docx', 'template2.docx'])

def test_save_template_new_file(setup_template_dir):
    from template_service import save_template
    mock_uploaded_file = MagicMock()
    mock_uploaded_file.name = 'new_template.docx'
    mock_uploaded_file.getbuffer.return_value = b"dummy content"

    success, message = save_template(mock_uploaded_file, template_dir=setup_template_dir)
    assert success is True
    assert "uspešno shranjena" in message
    assert os.path.exists(os.path.join(setup_template_dir, 'new_template.docx'))

def test_save_template_overwrite_existing(setup_template_dir):
    from template_service import save_template
    # Create an existing file
    existing_file_path = os.path.join(setup_template_dir, 'existing_template.docx')
    with open(existing_file_path, 'w') as f: f.write("old content")

    mock_uploaded_file = MagicMock()
    mock_uploaded_file.name = 'existing_template.docx'
    mock_uploaded_file.getbuffer.return_value = b"new content"

    success, message = save_template(mock_uploaded_file, overwrite=True, template_dir=setup_template_dir)
    assert success is True
    assert "uspešno shranjena" in message
    with open(existing_file_path, 'r') as f: assert f.read() == "new content"

def test_save_template_no_overwrite(setup_template_dir):
    from template_service import save_template
    # Create an existing file
    existing_file_path = os.path.join(setup_template_dir, 'existing_template.docx')
    with open(existing_file_path, 'w') as f: f.write("old content")

    mock_uploaded_file = MagicMock()
    mock_uploaded_file.name = 'existing_template.docx'
    mock_uploaded_file.getbuffer.return_value = b"new content"

    success, message = save_template(mock_uploaded_file, overwrite=False, template_dir=setup_template_dir)
    assert success is False
    assert "že obstaja" in message
    with open(existing_file_path, 'r') as f: assert f.read() == "old content"

def test_clear_drafts_success(mock_sqlite_connect_for_template_service):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connect_for_template_service
    from template_service import clear_drafts
    from database import DATABASE_FILE # Import DATABASE_FILE from database.py
    
    success, message = clear_drafts()
    mock_connect.assert_called_once_with(DATABASE_FILE)
    mock_cursor.execute.assert_called_once_with('DELETE FROM drafts')
    mock_conn.commit.assert_called_once()
    assert success is True
    assert "uspešno izbrisani" in message

def test_clear_drafts_failure(mock_sqlite_connect_for_template_service):
    mock_connect, _, _ = mock_sqlite_connect_for_template_service
    mock_connect.side_effect = Exception("DB Error")
    from template_service import clear_drafts
    success, message = clear_drafts()
    assert success is False
    assert "Napaka pri brisanju osnutkov" in message

def test_backup_drafts_success(mock_sqlite_connect_for_template_service, setup_backup_dir):
    mock_connect, _, _ = mock_sqlite_connect_for_template_service
    from template_service import backup_drafts
    from database import DATABASE_FILE
    # Create a dummy db file
    with open(DATABASE_FILE, 'w') as f: f.write("db content")

    with patch('shutil.copyfile') as mock_copyfile:
        success, message = backup_drafts()
        mock_copyfile.assert_called_once()
        assert success is True
        assert "Varnostna kopija uspešno ustvarjena" in message
    os.remove(DATABASE_FILE) # Clean up dummy db

def test_backup_drafts_no_db(mock_sqlite_connect_for_template_service, setup_backup_dir):
    from template_service import backup_drafts
    from database import DATABASE_FILE
    # Ensure the dummy db file does not exist
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    success, message = backup_drafts()
    assert success is False
    assert "Ni baze podatkov za varnostno kopiranje" in message

def test_manage_chromadb_collections_list():
    from template_service import manage_chromadb_collections
    result, message = manage_chromadb_collections("list")
    assert result == []
    assert "ni implementirano" in message

def test_manage_chromadb_collections_create():
    from template_service import manage_chromadb_collections
    success, message = manage_chromadb_collections("create", "my_collection")
    assert success is False
    assert "ni implementirano" in message

def test_manage_chromadb_collections_delete():
    from template_service import manage_chromadb_collections
    success, message = manage_chromadb_collections("delete", "my_collection")
    assert success is False
    assert "ni implementirano" in message

def test_manage_chromadb_collections_unknown_action():
    from template_service import manage_chromadb_collections
    success, message = manage_chromadb_collections("unknown_action")
    assert success is False
    assert "Neznano dejanje ChromaDB" in message
