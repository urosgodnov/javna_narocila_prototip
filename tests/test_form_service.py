import pytest
import json
from unittest.mock import mock_open, patch, MagicMock
import sys
import os
from datetime import date, datetime
import sqlite3

# Add the parent directory to sys.path to allow importing app.py and database.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Streamlit functions
@pytest.fixture(autouse=True)
def mock_streamlit():
    # Patch individual Streamlit functions
    with patch('app.st') as mock_st:
        mock_st.text_input = MagicMock(return_value="")
        mock_st.text_area = MagicMock(return_value="")
        mock_st.number_input = MagicMock(return_value=0)
        mock_st.header = MagicMock()
        mock_st.form = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        mock_st.form_submit_button = MagicMock(return_value=False)
        mock_st.write = MagicMock()
        mock_st.json = MagicMock()
        mock_st.error = MagicMock()
        mock_st.stop = MagicMock()
        mock_st.session_state = {}
        mock_st.selectbox = MagicMock(return_value="")
        mock_st.multiselect = MagicMock(return_value=[])
        mock_st.date_input = MagicMock(return_value=date.today())
        mock_st.file_uploader = MagicMock(return_value=None)
        mock_st.success = MagicMock()
        mock_st.info = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
        mock_st.button = MagicMock(return_value=False)
        mock_st.experimental_rerun = MagicMock()
        mock_st.subheader = MagicMock()

        yield mock_st

# Mock database functions for app.py tests
@pytest.fixture(autouse=True)
def mock_database_app_level():
    with patch('app.database') as mock_db:
        mock_db.init_db = MagicMock()
        mock_db.save_draft = MagicMock(return_value=1)
        mock_db.get_all_draft_metadata = MagicMock(return_value=[])
        mock_db.load_draft = MagicMock(return_value={})
        yield mock_db


def test_load_json_schema_success():
    # Create a dummy JSON schema content
    json_content = '''
    {
        "title": "Test Form",
        "properties": {
            "name": {"type": "string", "title": "Name"}
        }
    }
    '''
    
    # Use mock_open to simulate reading the file
    with patch("builtins.open", mock_open(read_data=json_content)) as mock_file:
        from app import load_json_schema
        schema = load_json_schema("dummy_path.json")
        mock_file.assert_called_once_with("dummy_path.json", 'r', encoding='utf-8')
        assert schema == json.loads(json_content)

def test_main_file_not_found(mock_streamlit):
    # Mock builtins.open to raise FileNotFoundError
    with patch("builtins.open", side_effect=FileNotFoundError):
        from app import main
        # Initialize session_state.current_step before calling main
        mock_streamlit.session_state['current_step'] = 0
        main()
        mock_streamlit.error.assert_called_once()
        mock_streamlit.stop.assert_called_once()

def test_render_form_string_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "name": {"type": "string", "title": "Ime"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.text_input.assert_called_once_with("Ime", value="", key="name")

def test_render_form_textarea_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "description": {"type": "string", "title": "Opis", "format": "textarea"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.text_area.assert_called_once_with("Opis", value="", key="description")

def test_render_form_number_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "age": {"type": "number", "title": "Starost"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.number_input.assert_called_once_with("Starost", value=0.0, key="age")

def test_render_form_mixed_inputs(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "name": {"type": "string", "title": "Ime"},
        "notes": {"type": "string", "title": "Opombe", "format": "textarea"},
        "quantity": {"type": "number", "title": "Količina"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    assert mock_streamlit.text_input.call_count == 1
    assert mock_streamlit.text_area.call_count == 1
    assert mock_streamlit.number_input.call_count == 1

def test_render_form_no_properties(mock_streamlit):
    from app import render_form_section
    schema_properties = {}
    form_data = {}
    render_form_section(schema_properties, form_data)
    assert form_data == {}
    mock_streamlit.text_input.assert_not_called()
    mock_streamlit.text_area.assert_not_called()
    mock_streamlit.number_input.assert_not_called()

def test_render_form_selectbox_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "single_select": {"type": "string", "title": "Enojna izbira", "enum": ["Možnost A", "Možnost B"]}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.selectbox.assert_called_once_with("Enojna izbira", options=["Možnost A", "Možnost B"], index=0, key="single_select")

def test_render_form_multiselect_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "multi_select": {"type": "array", "title": "Večkratna izbira", "items": {"type": "string"}, "enum": ["Možnost X", "Možnost Y"], "uniqueItems": True}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.multiselect.assert_called_once_with("Večkratna izbira", options=["Možnost X", "Možnost Y"], default=[], key="multi_select")

def test_render_form_date_input(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "date_field": {"type": "string", "title": "Datumsko polje", "format": "date"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.date_input.assert_called_once_with("Datumsko polje", key="date_field", value=date.today())

def test_render_form_file_uploader(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "file_upload": {"type": "string", "title": "Nalaganje datoteke", "format": "file"}
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.file_uploader.assert_called_once_with("Nalaganje datoteke", key="file_upload")

def test_render_form_nested_object(mock_streamlit):
    from app import render_form_section
    schema_properties = {
        "clientData": {
            "type": "object",
            "title": "Podatki o naročniku",
            "properties": {
                "name": {"type": "string", "title": "Naziv"},
                "address": {"type": "string", "title": "Naslov"}
            }
        }
    }
    form_data = {}
    render_form_section(schema_properties, form_data)
    mock_streamlit.subheader.assert_called_once_with("Podatki o naročniku")
    mock_streamlit.text_input.assert_any_call("Naziv", value="", key="clientData.name")
    mock_streamlit.text_input.assert_any_call("Naslov", value="", key="clientData.address")

# Tests for database.py

@pytest.fixture
def mock_sqlite_connection():
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        yield mock_connect, mock_conn, mock_cursor

def test_init_db(mock_sqlite_connection):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connection
    from database import init_db, DATABASE_FILE
    init_db()
    mock_connect.assert_called_once_with(DATABASE_FILE)
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

def test_save_draft(mock_sqlite_connection):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connection
    from database import save_draft
    form_data = {"field1": "value1"}
    mock_cursor.lastrowid = 5
    
    # Mock init_db call within save_draft
    with patch('database.init_db') as mock_init_db:
        draft_id = save_draft(form_data)
        mock_init_db.assert_called_once()

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    assert draft_id == 5

def test_get_all_draft_metadata(mock_sqlite_connection):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connection
    from database import get_all_draft_metadata
    mock_cursor.fetchall.return_value = [(1, "2025-01-01"), (2, "2025-01-02")]

    # Mock init_db call within get_all_draft_metadata
    with patch('database.init_db') as mock_init_db:
        metadata = get_all_draft_metadata()
        mock_init_db.assert_called_once()

    mock_cursor.execute.assert_called_once_with('SELECT id, timestamp FROM drafts ORDER BY timestamp DESC')
    assert metadata == [(1, "2025-01-01"), (2, "2025-01-02")]

def test_load_draft_success(mock_sqlite_connection):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connection
    from database import load_draft
    test_data = {"field1": "loaded_value"}
    mock_cursor.fetchone.return_value = (json.dumps(test_data),)

    # Mock init_db call within load_draft
    with patch('database.init_db') as mock_init_db:
        loaded_data = load_draft(1)
        mock_init_db.assert_called_once()

    mock_cursor.execute.assert_called_once_with('SELECT form_data_json FROM drafts WHERE id = ?', (1,))
    assert loaded_data == test_data

def test_load_draft_not_found(mock_sqlite_connection):
    mock_connect, mock_conn, mock_cursor = mock_sqlite_connection
    from database import load_draft
    mock_cursor.fetchone.return_value = None

    # Mock init_db call within load_draft
    with patch('database.init_db') as mock_init_db:
        loaded_data = load_draft(99)
        mock_init_db.assert_called_once()

    mock_cursor.execute.assert_called_once_with('SELECT form_data_json FROM drafts WHERE id = ?', (99,))
    assert loaded_data is None

# Tests for Multi-Step Form Logic

def test_get_form_data_from_session(mock_streamlit):
    from app import get_form_data_from_session
    
    # Mock schema and session state
    mock_streamlit.session_state = {
        'schema': {
            'properties': {
                'clientData': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'address': {'type': 'string'}}},
                'projectName': {'type': 'string'}
            }
        },
        'clientData.name': 'Test Client',
        'clientData.address': '123 Test St',
        'projectName': 'Super Secret Project',
        'unrelated_key': 'some_other_value'
    }

    expected_data = {
        'clientData': {
            'name': 'Test Client',
            'address': '123 Test St'
        },
        'projectName': 'Super Secret Project'
    }

    form_data = get_form_data_from_session()
    assert form_data == expected_data

def test_get_form_data_from_session_empty(mock_streamlit):
    from app import get_form_data_from_session
    mock_streamlit.session_state = {'schema': {'properties': {}}}
    assert get_form_data_from_session() == {}

def test_main_navigation_next_button(mock_streamlit):
    from app import main
    
    # Set initial state
    mock_streamlit.session_state = {
        'current_step': 0,
        'schema': {
            'title': 'Test Form',
            'properties': {
                "clientData": {"type": "string"}, "projectName": {"type": "string"}, "submissionProcedure": {"type": "string"},
                "orderType": {"type": "string"}, "exclusionReasons": {"type": "string"}, "participationConditions": {"type": "string"},
                "financialGuarantees": {"type": "string"}, "selectionCriteria": {"type": "string"}, "socialCriteria": {"type": "string"}, "otherCriteria": {"type": "string"}, "contractType": {"type": "string"}
            }
        }
    }
    mock_streamlit.sidebar.radio.return_value = "Obrazec za vnos"
    
    # Simulate the "Next" button click
    mock_back_col, mock_next_col = MagicMock(), MagicMock()
    mock_next_col.button.return_value = True
    mock_back_col.button.return_value = False
    mock_streamlit.columns.return_value = [mock_back_col, mock_next_col]

    main()

    assert mock_streamlit.session_state['current_step'] == 1
    mock_streamlit.experimental_rerun.assert_called_once()

def test_main_navigation_back_button(mock_streamlit):
    from app import main

    # Set initial state
    mock_streamlit.session_state = {
        'current_step': 1,
        'schema': {
            'title': 'Test Form',
            'properties': {
                "clientData": {"type": "string"}, "projectName": {"type": "string"}, "submissionProcedure": {"type": "string"},
                "orderType": {"type": "string"}, "exclusionReasons": {"type": "string"}, "participationConditions": {"type": "string"},
                "financialGuarantees": {"type": "string"}, "selectionCriteria": {"type": "string"}, "socialCriteria": {"type": "string"}, "otherCriteria": {"type": "string"}, "contractType": {"type": "string"}
            }
        }
    }
    mock_streamlit.sidebar.radio.return_value = "Obrazec za vnos"

    # Simulate the "Back" button click
    mock_back_col, mock_next_col = MagicMock(), MagicMock()
    mock_back_col.button.return_value = True
    mock_next_col.button.return_value = False
    mock_streamlit.columns.return_value = [mock_back_col, mock_next_col]

    main()

    assert mock_streamlit.session_state['current_step'] == 0
    mock_streamlit.experimental_rerun.assert_called_once()

def test_main_final_step_submit(mock_streamlit):
    from app import main

    # Set initial state for the last step
    mock_streamlit.session_state = {
        'current_step': 2, # Last step
        'schema': {
            'title': 'Test Form',
            'properties': {
                "clientData": {"type": "string"}, "projectName": {"type": "string"}, "submissionProcedure": {"type": "string"},
                "orderType": {"type": "string"}, "exclusionReasons": {"type": "string"}, "participationConditions": {"type": "string"},
                "financialGuarantees": {"type": "string"}, "selectionCriteria": {"type": "string"}, "socialCriteria": {"type": "string"}, "otherCriteria": {"type": "string"}, "contractType": {"type": "string"}
            }
        },
        'financialGuarantees.some_data': 'Test Data'
    }
    mock_streamlit.sidebar.radio.return_value = "Obrazec za vnos"
    
    # Simulate the "Pripravi dokumente" button click
    mock_streamlit.button.return_value = True
    
    with patch('app.get_form_data_from_session') as mock_get_data:
        mock_get_data.return_value = {'financialGuarantees': {'some_data': 'Test Data'}}
        main()

        # Verify the final actions
        mock_get_data.assert_called_once()
        mock_streamlit.json.assert_called_once_with({'financialGuarantees': {'some_data': 'Test Data'}})
        mock_streamlit.success.assert_called_with("Dokumenti uspešno pripravljeni!")