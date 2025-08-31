"""
Comprehensive tests for FormContext - the foundation of unified lot architecture.
These tests verify Story 40.4 implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils.form_helpers import FormContext


class TestAutomaticLotStructure:
    """Test that lot structure is always created automatically"""
    
    def test_empty_session_state_creates_general_lot(self):
        """Test that empty session state gets General lot"""
        session_state = {}
        context = FormContext(session_state)
        
        assert 'lots' in session_state
        assert len(session_state['lots']) == 1
        assert session_state['lots'][0]['name'] == 'General'
        assert session_state['lots'][0]['index'] == 0
        assert session_state['current_lot_index'] == 0
        
    def test_empty_lots_list_creates_general_lot(self):
        """Test that empty lots list gets General lot"""
        session_state = {'lots': []}
        context = FormContext(session_state)
        
        assert len(session_state['lots']) == 1
        assert session_state['lots'][0]['name'] == 'General'
        
    def test_existing_lots_preserved(self):
        """Test that existing lots are not overwritten"""
        session_state = {
            'lots': [
                {'name': 'Custom Lot', 'index': 0},
                {'name': 'Another Lot', 'index': 1}
            ],
            'current_lot_index': 1
        }
        context = FormContext(session_state)
        
        assert len(session_state['lots']) == 2
        assert session_state['lots'][0]['name'] == 'Custom Lot'
        assert context.lot_index == 1
        
    def test_invalid_current_lot_index_reset(self):
        """Test that invalid current_lot_index is reset to 0"""
        session_state = {
            'lots': [{'name': 'General', 'index': 0}],
            'current_lot_index': 5  # Invalid
        }
        context = FormContext(session_state)
        
        assert session_state['current_lot_index'] == 0
        assert context.lot_index == 0


class TestLotScopedKeys:
    """Test that all keys are lot-scoped except globals"""
    
    def test_regular_field_gets_lot_scoped_key(self):
        """Test regular fields get lot-scoped keys"""
        session_state = {}
        context = FormContext(session_state)
        
        key = context.get_field_key("test_field")
        assert key == "lots.0.test_field"
        
        # Switch lot and verify key changes
        context.add_lot("Lot 2")
        context.switch_to_lot(1)
        key = context.get_field_key("test_field")
        assert key == "lots.1.test_field"
        
    def test_nested_field_gets_lot_scoped_key(self):
        """Test nested fields get lot-scoped keys"""
        session_state = {}
        context = FormContext(session_state)
        
        key = context.get_field_key("parent.child.field")
        assert key == "lots.0.parent.child.field"
        
    def test_global_fields_not_lot_scoped(self):
        """Test global fields remain global"""
        session_state = {}
        context = FormContext(session_state)
        
        # Test all defined global fields
        global_fields = ['schema', 'current_step', 'form_metadata', 
                         'lots', 'current_lot_index', 'validation_mode']
        
        for field in global_fields:
            key = context.get_field_key(field)
            assert key == field, f"Field {field} should not be lot-scoped"
            
    def test_force_global_parameter(self):
        """Test force_global parameter works"""
        session_state = {}
        context = FormContext(session_state)
        
        key = context.get_field_key("normally_scoped", force_global=True)
        assert key == "normally_scoped"


class TestFieldValueManagement:
    """Test field value get/set operations"""
    
    def test_set_and_get_field_value(self):
        """Test basic set and get operations"""
        session_state = {}
        context = FormContext(session_state)
        
        context.set_field_value("test_field", "test_value")
        value = context.get_field_value("test_field")
        
        assert value == "test_value"
        assert session_state["lots.0.test_field"] == "test_value"
        
    def test_get_field_with_default(self):
        """Test getting field with default value"""
        session_state = {}
        context = FormContext(session_state)
        
        value = context.get_field_value("nonexistent", default="default_value")
        assert value == "default_value"
        
    def test_delete_field_value(self):
        """Test deleting field value"""
        session_state = {}
        context = FormContext(session_state)
        
        context.set_field_value("test_field", "value")
        assert context.field_exists("test_field")
        
        context.delete_field_value("test_field")
        assert not context.field_exists("test_field")
        assert "lots.0.test_field" not in session_state
        
    def test_field_exists_check(self):
        """Test field existence check"""
        session_state = {}
        context = FormContext(session_state)
        
        assert not context.field_exists("test_field")
        context.set_field_value("test_field", "value")
        assert context.field_exists("test_field")


class TestLotManagement:
    """Test lot management operations"""
    
    def test_add_lot_with_default_name(self):
        """Test adding lot with auto-generated name"""
        session_state = {}
        context = FormContext(session_state)
        
        new_index = context.add_lot()
        
        assert new_index == 1
        assert len(session_state['lots']) == 2
        assert session_state['lots'][1]['name'] == 'Lot 2'
        assert session_state['lots'][1]['index'] == 1
        
    def test_add_lot_with_custom_name(self):
        """Test adding lot with custom name"""
        session_state = {}
        context = FormContext(session_state)
        
        new_index = context.add_lot("Custom Name")
        
        assert session_state['lots'][1]['name'] == 'Custom Name'
        
    def test_cannot_remove_last_lot(self):
        """Test that last lot cannot be removed"""
        session_state = {}
        context = FormContext(session_state)
        
        result = context.remove_lot(0)
        
        assert result == False
        assert len(session_state['lots']) == 1
        
    def test_remove_lot_with_data_migration(self):
        """Test removing lot migrates data correctly"""
        session_state = {}
        context = FormContext(session_state)
        
        # Add lots and data
        context.add_lot("Lot 2")
        context.add_lot("Lot 3")
        
        # Add data to each lot
        context.switch_to_lot(0)
        context.set_field_value("field1", "lot0_value")
        
        context.switch_to_lot(1)
        context.set_field_value("field1", "lot1_value")
        
        context.switch_to_lot(2)
        context.set_field_value("field1", "lot2_value")
        
        # Remove middle lot
        result = context.remove_lot(1)
        
        assert result == True
        assert len(session_state['lots']) == 2
        
        # Check data migration
        assert session_state.get("lots.0.field1") == "lot0_value"
        assert session_state.get("lots.1.field1") == "lot2_value"  # Migrated from lot 2
        assert "lots.2.field1" not in session_state
        
    def test_switch_to_lot(self):
        """Test switching between lots"""
        session_state = {}
        context = FormContext(session_state)
        
        context.add_lot("Lot 2")
        
        assert context.lot_index == 0
        result = context.switch_to_lot(1)
        
        assert result == True
        assert context.lot_index == 1
        assert session_state['current_lot_index'] == 1
        
        # Test invalid switch
        result = context.switch_to_lot(5)
        assert result == False
        assert context.lot_index == 1  # Unchanged
        
    def test_rename_lot(self):
        """Test renaming a lot"""
        session_state = {}
        context = FormContext(session_state)
        
        result = context.rename_lot(0, "New Name")
        
        assert result == True
        assert session_state['lots'][0]['name'] == 'New Name'
        
        # Test invalid index
        result = context.rename_lot(5, "Invalid")
        assert result == False
        
    def test_copy_lot_data(self):
        """Test copying data between lots"""
        session_state = {}
        context = FormContext(session_state)
        
        # Setup source lot data
        context.set_field_value("field1", "value1")
        context.set_field_value("field2", "value2")
        
        # Add target lot
        context.add_lot("Target Lot")
        
        # Copy data
        result = context.copy_lot_data(0, 1)
        
        assert result == True
        assert session_state.get("lots.1.field1") == "value1"
        assert session_state.get("lots.1.field2") == "value2"
        
    def test_clear_lot_data(self):
        """Test clearing all data for a lot"""
        session_state = {}
        context = FormContext(session_state)
        
        context.set_field_value("field1", "value1")
        context.set_field_value("field2", "value2")
        
        context.clear_lot_data(0)
        
        assert "lots.0.field1" not in session_state
        assert "lots.0.field2" not in session_state
        
    def test_get_lot_info(self):
        """Test getting lot information"""
        session_state = {}
        context = FormContext(session_state)
        
        current_lot = context.get_current_lot()
        assert current_lot['name'] == 'General'
        assert current_lot['index'] == 0
        
        all_lots = context.get_all_lots()
        assert len(all_lots) == 1
        
        lot_count = context.get_lot_count()
        assert lot_count == 1


class TestValidationContext:
    """Test validation error management"""
    
    def test_add_validation_error(self):
        """Test adding validation errors"""
        session_state = {}
        context = FormContext(session_state)
        
        context.add_validation_error("field1", "Error 1")
        context.add_validation_error("field1", "Error 2")
        
        errors = context.get_validation_errors("field1")
        assert len(errors) == 2
        assert "Error 1" in errors
        assert "Error 2" in errors
        
    def test_validation_errors_are_lot_scoped(self):
        """Test that validation errors use lot-scoped keys"""
        session_state = {}
        context = FormContext(session_state)
        
        context.add_validation_error("field1", "Error in lot 0")
        
        context.add_lot()
        context.switch_to_lot(1)
        context.add_validation_error("field1", "Error in lot 1")
        
        all_errors = context.validation_errors
        assert "lots.0.field1" in all_errors
        assert "lots.1.field1" in all_errors
        
    def test_clear_validation_errors(self):
        """Test clearing validation errors"""
        session_state = {}
        context = FormContext(session_state)
        
        context.add_validation_error("field1", "Error 1")
        context.add_validation_error("field2", "Error 2")
        
        # Clear specific field
        context.clear_validation_errors("field1")
        assert not context.has_errors("field1")
        assert context.has_errors("field2")
        
        # Clear all
        context.clear_validation_errors()
        assert not context.has_errors()
        
    def test_has_errors_check(self):
        """Test checking for errors"""
        session_state = {}
        context = FormContext(session_state)
        
        assert not context.has_errors()
        
        context.add_validation_error("field1", "Error")
        assert context.has_errors()
        assert context.has_errors("field1")
        assert not context.has_errors("field2")
        
    def test_duplicate_errors_not_added(self):
        """Test that duplicate errors are not added"""
        session_state = {}
        context = FormContext(session_state)
        
        context.add_validation_error("field1", "Same error")
        context.add_validation_error("field1", "Same error")
        
        errors = context.get_validation_errors("field1")
        assert len(errors) == 1


class TestUtilityMethods:
    """Test utility methods for data extraction"""
    
    def test_get_lot_data(self):
        """Test getting all data for a specific lot"""
        session_state = {}
        context = FormContext(session_state)
        
        context.set_field_value("field1", "value1")
        context.set_field_value("field2", "value2")
        
        lot_data = context.get_lot_data()
        
        assert lot_data == {
            'field1': 'value1',
            'field2': 'value2'
        }
        
    def test_get_all_form_data(self):
        """Test getting all form data across lots"""
        session_state = {
            'schema': 'test_schema',
            'validation_mode': 'strict'
        }
        context = FormContext(session_state)
        
        # Add data to first lot
        context.set_field_value("field1", "lot0_value")
        
        # Add second lot with data
        context.add_lot("Lot 2")
        context.switch_to_lot(1)
        context.set_field_value("field1", "lot1_value")
        
        all_data = context.get_all_form_data()
        
        assert len(all_data['lots']) == 2
        assert all_data['lots'][0]['name'] == 'General'
        assert all_data['lots'][0]['data']['field1'] == 'lot0_value'
        assert all_data['lots'][1]['name'] == 'Lot 2'
        assert all_data['lots'][1]['data']['field1'] == 'lot1_value'
        assert all_data['schema'] == 'test_schema'
        assert all_data['validation_mode'] == 'strict'


class TestNoLegacySupport:
    """Test that there's no legacy data migration or backward compatibility"""
    
    def test_no_migration_of_flat_keys(self):
        """Test that flat keys are not migrated to lot structure"""
        session_state = {
            'old_field': 'old_value',  # Legacy flat key
            'another_field': 'another_value'
        }
        context = FormContext(session_state)
        
        # Old keys should remain untouched
        assert 'old_field' in session_state
        assert 'another_field' in session_state
        
        # No automatic migration to lot structure
        assert 'lots.0.old_field' not in session_state
        assert 'lots.0.another_field' not in session_state
        
    def test_no_support_for_old_lot_format(self):
        """Test that old lot format (lot_0.field) is not supported"""
        session_state = {
            'lot_0.field': 'value',  # Old format
            'lot_1.field': 'value'
        }
        context = FormContext(session_state)
        
        # Old format keys remain untouched
        assert 'lot_0.field' in session_state
        
        # No migration to new format
        assert 'lots.0.field' not in session_state


class TestThreadSafety:
    """Test thread safety for Streamlit usage"""
    
    def test_multiple_context_instances_share_state(self):
        """Test that multiple FormContext instances share the same session state"""
        session_state = {}
        
        context1 = FormContext(session_state)
        context2 = FormContext(session_state)
        
        context1.set_field_value("field1", "value1")
        value = context2.get_field_value("field1")
        
        assert value == "value1"
        
    def test_lot_changes_reflected_across_instances(self):
        """Test that lot changes are reflected across instances"""
        session_state = {}
        
        context1 = FormContext(session_state)
        context2 = FormContext(session_state)
        
        context1.add_lot("New Lot")
        context1.switch_to_lot(1)
        
        # Context2 should see the changes after re-syncing
        context2.lot_index = session_state['current_lot_index']
        assert context2.lot_index == 1
        assert context2.get_lot_count() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])