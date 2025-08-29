# tests/test_integration_data_manager.py
"""
Integration tests for data_manager module with other components.
Tests the actual integration points to ensure compatibility.
"""

import pytest
import sys
import os
import tempfile
import json
from datetime import datetime, date, time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_manager import serialize_datetime, deserialize_datetime, prepare_for_json
from database import convert_dates_to_strings


class TestDatabaseIntegration:
    """Test data_manager integration with database module."""
    
    def test_convert_dates_delegates_to_data_manager(self):
        """Ensure database.convert_dates_to_strings delegates to data_manager."""
        test_data = {
            'date': date(2024, 1, 15),
            'time': time(10, 30),
            'datetime': datetime(2024, 1, 15, 10, 30),
            'nested': {
                'value': 42,
                'date': date(2024, 2, 20)
            },
            'list': [1, 2, date(2024, 3, 1)]
        }
        
        result = convert_dates_to_strings(test_data)
        
        # Verify all dates are converted
        assert result['date'] == '2024-01-15'
        assert result['time'] == '10:30:00'
        assert result['datetime'] == '2024-01-15T10:30:00'
        assert result['nested']['date'] == '2024-02-20'
        assert result['list'][2] == '2024-03-01'
        
        # Ensure it's JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
    
    def test_database_save_with_dates(self):
        """Test saving complex data with dates through database module."""
        import sqlite3
        from database import init_db, save_draft
        
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Mock the DATABASE_FILE
            import database
            original_db = database.DATABASE_FILE
            database.DATABASE_FILE = db_path
            
            # Initialize database
            init_db()
            
            # Save data with various date types
            test_data = {
                'title': 'Test Procurement',
                'date_created': datetime.now(),
                'deadline': date(2024, 12, 31),
                'inspection_time': time(14, 30),
                'lots': [
                    {
                        'name': 'Lot 1',
                        'start_date': date(2024, 6, 1),
                        'meeting_time': time(9, 0)
                    }
                ]
            }
            
            # This should not raise any JSON serialization errors
            draft_id = save_draft(test_data)
            assert draft_id is not None
            
            # Verify data can be retrieved
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT form_data_json FROM drafts WHERE id = ?', (draft_id,))
                row = cursor.fetchone()
                assert row is not None
                
                # Parse JSON to verify it was saved correctly
                saved_data = json.loads(row[0])
                assert saved_data['title'] == 'Test Procurement'
                assert saved_data['deadline'] == '2024-12-31'
                assert saved_data['inspection_time'] == '14:30:00'
                assert saved_data['lots'][0]['start_date'] == '2024-06-01'
                assert saved_data['lots'][0]['meeting_time'] == '09:00:00'
            
            # Restore original database file
            database.DATABASE_FILE = original_db
            
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestFormRendererIntegration:
    """Test data_manager integration with form_renderer module."""
    
    def test_form_renderer_imports(self):
        """Ensure form_renderer can import and use data_manager functions."""
        from ui.form_renderer import serialize_datetime, deserialize_datetime
        
        # Test that these are the same functions from data_manager
        test_date = date(2024, 1, 15)
        assert serialize_datetime(test_date) == '2024-01-15'
        
        test_time = time(10, 30)
        assert serialize_datetime(test_time) == '10:30:00'
        
        # Test deserialization
        result_date = deserialize_datetime('2024-01-15', 'date')
        assert result_date == test_date
        
        result_time = deserialize_datetime('10:30:00', 'time')
        assert result_time == test_time


class TestSchemaUtilsIntegration:
    """Test data_manager integration with schema_utils module."""
    
    def test_schema_utils_imports(self):
        """Ensure schema_utils can import and use data_manager functions."""
        from utils.schema_utils import (
            reconstruct_arrays, 
            fields_to_lots, 
            lots_to_fields,
            prepare_for_json
        )
        
        # Test array reconstruction
        test_data = {
            'items.0.name': 'Item 1',
            'items.1.name': 'Item 2',
            'widget_ignore': 'should be ignored'
        }
        
        result = reconstruct_arrays(test_data)
        assert 'items' in result
        assert len(result['items']) == 2
        assert result['items'][0]['name'] == 'Item 1'
        assert 'widget_ignore' not in result
        
        # Test lot conversion
        lot_data = {
            'lot_0.name': 'Test Lot',
            'lot_0.value': 100,
            'lot_1.name': 'Another Lot',
            'other_field': 'ignored'
        }
        
        lots = fields_to_lots(lot_data)
        assert len(lots) == 2
        assert lots[0]['name'] == 'Test Lot'
        assert lots[0]['value'] == 100
        assert lots[1]['name'] == 'Another Lot'
    
    def test_get_form_data_with_lots(self):
        """Test that get_form_data_from_session uses data_manager correctly."""
        import streamlit as st
        from utils.schema_utils import get_form_data_from_session
        
        # Mock session state
        if 'schema' not in st.session_state:
            st.session_state.schema = {'properties': {'test': {}}}
        
        st.session_state['lot_mode'] = 'multiple'
        st.session_state['lot_0.name'] = 'Lot 1'
        st.session_state['lot_0.orderType.estimatedValue'] = 50000
        st.session_state['lot_1.name'] = 'Lot 2'
        st.session_state['lot_1.orderType.estimatedValue'] = 75000
        st.session_state['lot_names'] = ['Lot 1', 'Lot 2']
        
        # Get form data
        form_data = get_form_data_from_session()
        
        # Verify lots were reconstructed correctly
        assert 'lots' in form_data
        assert len(form_data['lots']) == 2
        assert form_data['lots'][0]['name'] == 'Lot 1'
        assert form_data['lots'][0]['orderType']['estimatedValue'] == 50000
        assert form_data['lots'][1]['name'] == 'Lot 2'
        assert form_data['lots'][1]['orderType']['estimatedValue'] == 75000
        
        # Clean up session state
        for key in list(st.session_state.keys()):
            if key.startswith('lot_'):
                del st.session_state[key]
        del st.session_state['lot_mode']
        del st.session_state['lot_names']


class TestEndToEndIntegration:
    """Test complete data flow through all integrated modules."""
    
    def test_complete_data_flow(self):
        """Test data transformation from session state to database and back."""
        import streamlit as st
        from utils.schema_utils import get_form_data_from_session
        from database import convert_dates_to_strings
        
        # Setup mock session state with complex data
        if 'schema' not in st.session_state:
            st.session_state.schema = {'properties': {'test': {}}}
        
        st.session_state['lot_mode'] = 'multiple'
        st.session_state['lot_0.name'] = 'Infrastructure'
        st.session_state['lot_0.orderType.estimatedValue'] = 100000
        st.session_state['lot_0.inspectionInfo.inspectionDates.0.date'] = '2024-03-15'
        st.session_state['lot_0.inspectionInfo.inspectionDates.0.time'] = '10:30'
        st.session_state['lot_names'] = ['Infrastructure']
        
        # Step 1: Get form data from session (uses reconstruct_arrays and fields_to_lots)
        form_data = get_form_data_from_session()
        
        # Verify lot structure
        assert 'lots' in form_data
        assert len(form_data['lots']) == 1
        lot = form_data['lots'][0]
        assert lot['name'] == 'Infrastructure'
        assert lot['orderType']['estimatedValue'] == 100000
        assert lot['inspectionInfo']['inspectionDates'][0]['date'] == '2024-03-15'
        assert lot['inspectionInfo']['inspectionDates'][0]['time'] == '10:30'
        
        # Step 2: Prepare for database save (uses prepare_for_json)
        json_ready = convert_dates_to_strings(form_data)
        
        # Step 3: Ensure it's JSON serializable
        json_str = json.dumps(json_ready)
        assert json_str is not None
        
        # Step 4: Parse back and verify
        parsed = json.loads(json_str)
        assert parsed['lots'][0]['name'] == 'Infrastructure'
        assert parsed['lots'][0]['orderType']['estimatedValue'] == 100000
        
        # Clean up session state
        for key in list(st.session_state.keys()):
            if key.startswith('lot_'):
                del st.session_state[key]
        if 'lot_mode' in st.session_state:
            del st.session_state['lot_mode']
        if 'lot_names' in st.session_state:
            del st.session_state['lot_names']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])