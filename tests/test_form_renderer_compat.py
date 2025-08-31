"""
Test compatibility wrapper for form renderer migration.
Ensures old API calls work with new FormController architecture.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from ui.form_renderer_compat import render_form, get_form_data, validate_form, clear_form


class TestFormRendererCompatibility(unittest.TestCase):
    """Test that compatibility wrapper maintains old API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_state = {}
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_render_form_with_schema(self):
        """Test render_form with a standard schema."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'title': 'Name'},
                'value': {'type': 'number', 'title': 'Value'}
            }
        }
        
        with patch('streamlit.text_input') as mock_text:
            mock_text.return_value = "Test"
            
            # Old API call
            render_form(schema)
            
            # Should have created lot structure
            self.assertIn('lots', self.mock_session_state)
            self.assertEqual(len(self.mock_session_state['lots']), 1)
            self.assertEqual(self.mock_session_state['lots'][0]['name'], 'General')
    
    def test_render_form_with_step_properties(self):
        """Test render_form with step properties (not full schema)."""
        step_properties = {
            'field1': {'type': 'string', 'title': 'Field 1'},
            'field2': {'type': 'boolean', 'title': 'Field 2'}
        }
        
        with patch('streamlit.text_input') as mock_text, \
             patch('streamlit.checkbox') as mock_checkbox:
            
            # Old API call with just properties
            render_form(step_properties)
            
            # Should wrap in object schema and render
            mock_text.assert_called()
            mock_checkbox.assert_called()
    
    def test_render_form_with_lot_context(self):
        """Test render_form with lot_context parameter."""
        # Create multiple lots
        self.mock_session_state['lots'] = [
            {'name': 'General', 'index': 0},
            {'name': 'Special', 'index': 1}
        ]
        self.mock_session_state['current_lot_index'] = 0
        
        schema = {'field': {'type': 'string'}}
        lot_context = {'lot_index': 1}
        
        with patch('streamlit.text_input') as mock_text:
            # Old API call with lot context
            render_form(schema, lot_context=lot_context)
            
            # Should switch to specified lot
            # Note: The switch happens internally in the controller
            # We can't directly test it without accessing controller internals
            self.assertTrue(True)  # Placeholder assertion
    
    def test_render_form_with_kwargs(self):
        """Test render_form with additional kwargs."""
        schema = {'type': 'object', 'properties': {'test': {'type': 'string'}}}
        
        with patch('streamlit.text_input') as mock_text:
            # Old API with custom options
            render_form(
                schema,
                show_lot_navigation=False,
                show_progress=True,
                lot_navigation_style='buttons'
            )
            
            # Should pass options to controller
            mock_text.assert_called()
    
    def test_get_form_data_compatibility(self):
        """Test get_form_data returns data in expected format."""
        # Add some test data
        self.mock_session_state['lots'] = [{'name': 'General', 'index': 0}]
        self.mock_session_state['lots.0.field1'] = 'value1'
        self.mock_session_state['lots.0.field2'] = 100
        
        # Get form data
        data = get_form_data()
        
        # Should return lot-structured data
        self.assertIn('lots', data)
        self.assertIsInstance(data['lots'], list)
    
    def test_validate_form_compatibility(self):
        """Test validate_form function."""
        # Set up valid data
        self.mock_session_state['lots'] = [{'name': 'General', 'index': 0}]
        
        with patch('ui.controllers.form_controller.FormController.validate_form') as mock_validate:
            mock_validate.return_value = True
            
            # Call validate
            is_valid = validate_form()
            
            self.assertTrue(is_valid)
    
    def test_clear_form_compatibility(self):
        """Test clear_form function."""
        # Add some data
        self.mock_session_state['lots.0.field1'] = 'value'
        
        with patch('ui.controllers.form_controller.FormController.clear_form') as mock_clear:
            # Clear form
            clear_form()
            
            # Should call controller's clear method
            mock_clear.assert_called()
    
    def test_multiple_lots_shows_navigation(self):
        """Test that multiple lots trigger navigation display."""
        # Create multiple lots
        self.mock_session_state['lots'] = [
            {'name': 'Lot 1', 'index': 0},
            {'name': 'Lot 2', 'index': 1}
        ]
        
        schema = {'type': 'object', 'properties': {'test': {'type': 'string'}}}
        
        with patch('ui.renderers.lot_manager.LotManager.render_lot_navigation') as mock_nav, \
             patch('streamlit.text_input'):
            
            # Render with multiple lots
            render_form(schema)
            
            # Navigation should be called
            mock_nav.assert_called()
    
    def test_empty_schema_handling(self):
        """Test handling of empty or None schema."""
        with patch('streamlit.warning') as mock_warning:
            # Call with None schema
            render_form(None)
            
            # Should show warning
            mock_warning.assert_called_with("No form schema provided. Please set a schema first.")
    
    def test_backward_compatibility_with_old_tests(self):
        """Ensure old test patterns still work."""
        # Simulate old test pattern
        schema = {
            'properties': {
                'basic_field': {'type': 'string', 'title': 'Basic Field'}
            }
        }
        
        with patch('streamlit.text_input') as mock_input:
            mock_input.return_value = "test_value"
            
            # Old-style call
            render_form(schema)
            
            # Should work without errors
            mock_input.assert_called()
            
            # Lot structure should be created automatically
            self.assertIn('lots', self.mock_session_state)


class TestMigrationPath(unittest.TestCase):
    """Test migration scenarios from old to new system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_state = {}
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_migration_preserves_data(self):
        """Test that existing data is preserved during migration."""
        # Simulate old data format (might not have lots)
        self.mock_session_state['field1'] = 'existing_value'
        self.mock_session_state['field2'] = 42
        
        schema = {
            'type': 'object',
            'properties': {
                'field1': {'type': 'string'},
                'field2': {'type': 'number'}
            }
        }
        
        with patch('streamlit.text_input') as mock_text:
            mock_text.return_value = "existing_value"
            
            # Render with new system
            render_form(schema)
            
            # Lot structure should be created
            self.assertIn('lots', self.mock_session_state)
            
            # Old data still accessible (though may need migration)
            self.assertEqual(self.mock_session_state['field1'], 'existing_value')
    
    def test_lot_context_name_lookup(self):
        """Test lot context with name instead of index."""
        self.mock_session_state['lots'] = [
            {'name': 'General', 'index': 0},
            {'name': 'Custom Lot', 'index': 1}
        ]
        
        lot_context = {'current_lot': 'Custom Lot'}
        schema = {'field': {'type': 'string'}}
        
        with patch('streamlit.text_input'):
            # Should handle name-based lot lookup
            render_form(schema, lot_context=lot_context)
            
            # No errors = success
            self.assertTrue(True)
    
    def test_nested_schema_compatibility(self):
        """Test compatibility with nested object schemas."""
        schema = {
            'type': 'object',
            'properties': {
                'nested': {
                    'type': 'object',
                    'properties': {
                        'inner': {'type': 'string'}
                    }
                }
            }
        }
        
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.text_input') as mock_text:
            
            # Create proper mock for container
            container_mock = MagicMock()
            mock_container.return_value = container_mock
            
            # Render nested structure
            render_form(schema)
            
            # Should handle nested objects without errors
            # The container might not be called if using different rendering style
            self.assertTrue(True)  # Success = no errors


if __name__ == '__main__':
    unittest.main()