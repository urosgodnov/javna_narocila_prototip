"""
Integration tests for FormController with all components.
Tests the complete flow: FormContext → FormController → Renderers → UI.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from ui.controllers.form_controller import FormController
from utils.form_helpers import FormContext


class TestFormControllerIntegration(unittest.TestCase):
    """Test FormController integration with all components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock streamlit session state
        self.mock_session_state = {}
        
        # Patch st.session_state
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
        
        # Create controller
        self.controller = FormController()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_initialization_creates_lot_structure(self):
        """Test that initialization guarantees lot structure."""
        # Verify lots were created
        self.assertIn('lots', self.mock_session_state)
        self.assertEqual(len(self.mock_session_state['lots']), 1)
        self.assertEqual(self.mock_session_state['lots'][0]['name'], 'General')
        self.assertEqual(self.mock_session_state['lots'][0]['index'], 0)
        
        # Verify current_lot_index is set (FormContext uses this name)
        self.assertIn('current_lot_index', self.mock_session_state)
        self.assertEqual(self.mock_session_state['current_lot_index'], 0)
    
    def test_simple_object_form_rendering(self):
        """Test rendering a simple object-based form."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'title': 'Name'},
                'age': {'type': 'number', 'title': 'Age'},
                'active': {'type': 'boolean', 'title': 'Active'}
            },
            'required': ['name']
        }
        
        with patch('streamlit.text_input') as mock_text, \
             patch('streamlit.checkbox') as mock_checkbox:
            
            mock_text.return_value = "John"
            mock_checkbox.return_value = True
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify field renderers were called
            # Note: number fields use text_input for formatting support
            self.assertEqual(mock_text.call_count, 2)  # name + age
            mock_checkbox.assert_called()
    
    def test_nested_object_rendering(self):
        """Test rendering nested objects."""
        schema = {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'object',
                    'title': 'User Details',
                    'properties': {
                        'firstName': {'type': 'string', 'title': 'First Name'},
                        'lastName': {'type': 'string', 'title': 'Last Name'},
                        'contact': {
                            'type': 'object',
                            'title': 'Contact Info',
                            'properties': {
                                'email': {'type': 'string', 'format': 'email'},
                                'phone': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
        
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.text_input') as mock_text:
            
            mock_container.return_value.__enter__ = Mock(return_value=None)
            mock_container.return_value.__exit__ = Mock(return_value=None)
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify nested structure was created
            mock_container.assert_called()
            mock_subheader.assert_called()
    
    def test_array_of_objects_rendering(self):
        """Test rendering arrays of objects."""
        schema = {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'title': 'Items',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'quantity': {'type': 'number'}
                        }
                    }
                }
            }
        }
        
        # Add some array data
        self.mock_session_state['lots.0.items'] = [
            {'name': 'Item 1', 'quantity': 5},
            {'name': 'Item 2', 'quantity': 10}
        ]
        
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.text_input') as mock_text, \
             patch('streamlit.number_input') as mock_number:
            
            mock_container.return_value.__enter__ = Mock(return_value=None)
            mock_container.return_value.__exit__ = Mock(return_value=None)
            mock_button.return_value = False
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify array items were rendered
            self.assertTrue(mock_container.called)
            # Verify add button was created
            add_button_calls = [c for c in mock_button.call_args_list 
                              if '➕' in str(c)]
            self.assertTrue(len(add_button_calls) > 0)
    
    def test_multi_step_form_navigation(self):
        """Test multi-step form with navigation."""
        schema = {
            'steps': [
                {
                    'title': 'Personal Info',
                    'properties': {
                        'name': {'type': 'string', 'title': 'Name'},
                        'email': {'type': 'string', 'format': 'email'}
                    },
                    'required': ['name']
                },
                {
                    'title': 'Address',
                    'properties': {
                        'street': {'type': 'string', 'title': 'Street'},
                        'city': {'type': 'string', 'title': 'City'}
                    }
                },
                {
                    'title': 'Confirmation',
                    'properties': {
                        'agree': {'type': 'boolean', 'title': 'I agree'}
                    }
                }
            ]
        }
        
        # Set initial step
        self.mock_session_state['current_step_index'] = 0
        
        with patch('streamlit.columns') as mock_cols, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.text_input') as mock_text, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.text') as mock_st_text:
            
            # Create proper mock columns with context manager support
            col_mocks = [MagicMock() for _ in range(3)]
            mock_cols.return_value = col_mocks
            mock_button.return_value = False
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify step navigation was rendered
            mock_subheader.assert_called_with('Personal Info')
            
            # Verify navigation buttons
            button_calls = [str(c) for c in mock_button.call_args_list]
            next_button = any('Next' in s for s in button_calls)
            self.assertTrue(next_button)
    
    def test_lot_navigation_with_multiple_lots(self):
        """Test lot navigation when multiple lots exist."""
        # Add second lot
        self.mock_session_state['lots'].append({'name': 'Lot 2', 'index': 1})
        
        schema = {
            'type': 'object',
            'properties': {
                'value': {'type': 'number', 'title': 'Value'}
            },
            'allow_multiple_lots': True
        }
        
        with patch.object(self.controller.lot_manager, 'render_lot_navigation') as mock_nav:
            # Render form with multiple lots
            self.controller.render_form(schema, show_lot_navigation=True)
            
            # Verify lot navigation was called
            mock_nav.assert_called_once_with(
                style='tabs',
                allow_add=True,
                allow_remove=True,
                max_lots=None
            )
    
    def test_conditional_rendering(self):
        """Test conditional field rendering."""
        schema = {
            'type': 'object',
            'properties': {
                'hasPhone': {'type': 'boolean', 'title': 'Has Phone'},
                'phoneNumber': {
                    'type': 'string',
                    'title': 'Phone Number',
                    'render_if': {'field': 'hasPhone', 'value': True}
                }
            }
        }
        
        # Test with condition false
        self.mock_session_state['lots.0.hasPhone'] = False
        
        with patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.text_input') as mock_text:
            
            mock_checkbox.return_value = False
            
            # Render form
            self.controller.render_form(schema)
            
            # Phone field should not be rendered
            text_calls = [c for c in mock_text.call_args_list 
                         if 'Phone' in str(c)]
            self.assertEqual(len(text_calls), 0)
        
        # Test with condition true
        self.mock_session_state['lots.0.hasPhone'] = True
        
        with patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.text_input') as mock_text:
            
            mock_checkbox.return_value = True
            
            # Render form
            self.controller.render_form(schema)
            
            # Phone field should be rendered
            mock_text.assert_called()
    
    def test_form_validation(self):
        """Test form validation across lots."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'title': 'Name'},
                'email': {'type': 'string', 'format': 'email', 'title': 'Email'}
            },
            'required': ['name', 'email']
        }
        
        # Set schema
        self.controller.set_schema(schema)
        
        # Test with missing required fields
        self.mock_session_state['lots.0.name'] = ''
        self.mock_session_state['lots.0.email'] = ''
        
        is_valid = self.controller.validate_form()
        
        self.assertFalse(is_valid)
        self.assertTrue(self.controller.context.has_errors())
        
        # Test with valid data
        self.mock_session_state['lots.0.name'] = 'John'
        self.mock_session_state['lots.0.email'] = 'john@example.com'
        
        is_valid = self.controller.validate_form()
        
        self.assertTrue(is_valid)
    
    def test_form_submission(self):
        """Test form submission flow."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'title': 'Name'},
                'value': {'type': 'number', 'title': 'Value'}
            }
        }
        
        self.controller.set_schema(schema)
        
        # Set form data
        self.mock_session_state['lots.0.name'] = 'Test'
        self.mock_session_state['lots.0.value'] = 100
        
        with patch('streamlit.success') as mock_success, \
             patch('streamlit.expander') as mock_expander, \
             patch('streamlit.json') as mock_json:
            
            mock_expander.return_value.__enter__ = Mock(return_value=None)
            mock_expander.return_value.__exit__ = Mock(return_value=None)
            
            # Trigger submission (normally via button)
            self.controller._handle_submission()
            
            # Verify success message
            mock_success.assert_called_with("✅ Form submitted successfully!")
            
            # Verify data display
            mock_json.assert_called()
            call_args = mock_json.call_args[0][0]
            self.assertIn('lots', call_args)
    
    def test_load_data_into_form(self):
        """Test loading existing data into form."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'items': {
                    'type': 'array',
                    'items': {'type': 'object'}
                }
            }
        }
        
        self.controller.set_schema(schema)
        
        # Load lot-structured data
        data = {
            'lots': [
                {
                    'index': 0,
                    'name': 'General',
                    'data': {
                        'name': 'John Doe',
                        'items': [{'id': 1}, {'id': 2}]
                    }
                },
                {
                    'index': 1,
                    'name': 'Special',
                    'data': {
                        'name': 'Jane Doe',
                        'items': [{'id': 3}]
                    }
                }
            ]
        }
        
        self.controller.load_data(data)
        
        # Verify data was loaded
        self.assertEqual(self.mock_session_state['lots.0.name'], 'John Doe')
        self.assertEqual(len(self.mock_session_state['lots.0.items']), 2)
        
        # Verify second lot was created
        self.assertEqual(len(self.mock_session_state['lots']), 2)
        self.assertEqual(self.mock_session_state['lots.1.name'], 'Jane Doe')
    
    def test_financial_field_formatting(self):
        """Test financial field with special formatting."""
        schema = {
            'type': 'object',
            'properties': {
                'estimatedValue': {
                    'type': 'number',
                    'title': 'Estimated Value',
                    'format': 'financial'
                }
            }
        }
        
        with patch('streamlit.columns') as mock_cols, \
             patch('streamlit.text_input') as mock_text, \
             patch('streamlit.markdown') as mock_markdown:
            
            # Create proper mock columns with context manager support
            col_mocks = [MagicMock(), MagicMock()]
            mock_cols.return_value = col_mocks
            mock_text.return_value = "1000000.50"
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify EUR symbol was rendered
            markdown_calls = [str(c) for c in mock_markdown.call_args_list]
            eur_symbol = any('€' in s for s in markdown_calls)
            self.assertTrue(eur_symbol)
    
    def test_clear_form_functionality(self):
        """Test clearing form data."""
        # Add some data
        self.mock_session_state['lots.0.field1'] = 'value1'
        self.mock_session_state['lots.0.field2'] = 100
        self.mock_session_state['current_step_index'] = 2
        
        # Add validation errors
        self.controller.context.add_validation_error('field1', 'Test error')
        
        # Clear form
        self.controller.clear_form()
        
        # Verify data was cleared
        self.assertNotIn('lots.0.field1', self.mock_session_state)
        self.assertNotIn('lots.0.field2', self.mock_session_state)
        
        # Verify step was reset
        self.assertEqual(self.mock_session_state.get('current_step_index'), 0)
        
        # Verify errors were cleared
        self.assertFalse(self.controller.context.has_errors())
    
    def test_schema_sections_rendering(self):
        """Test rendering form with defined sections."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'age': {'type': 'number'},
                'city': {'type': 'string'}
            },
            'sections': {
                'personal': {
                    'title': 'Personal Information',
                    'description': 'Enter your personal details',
                    'properties': ['name', 'age']
                },
                'contact': {
                    'title': 'Contact Information',
                    'properties': ['email', 'city']
                }
            }
        }
        
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.caption') as mock_caption:
            
            mock_container.return_value.__enter__ = Mock(return_value=None)
            mock_container.return_value.__exit__ = Mock(return_value=None)
            
            # Render form
            self.controller.render_form(schema)
            
            # Verify sections were created
            subheader_calls = [c[0][0] for c in mock_subheader.call_args_list]
            self.assertIn('Personal Information', subheader_calls)
            self.assertIn('Contact Information', subheader_calls)
            
            # Verify description
            caption_calls = [c[0][0] for c in mock_caption.call_args_list]
            self.assertIn('Enter your personal details', caption_calls)


class TestFormControllerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_state = {}
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
        self.controller = FormController()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_render_without_schema(self):
        """Test rendering without providing schema."""
        with patch('streamlit.warning') as mock_warning:
            self.controller.render_form()
            mock_warning.assert_called_with("No form schema provided. Please set a schema first.")
    
    def test_invalid_schema_format(self):
        """Test handling of invalid schema format."""
        schema = {'invalid': 'schema'}  # No properties or steps
        
        with patch('streamlit.error') as mock_error:
            self.controller.render_form(schema)
            mock_error.assert_called_with("Invalid schema format. Schema must have 'properties' or 'steps'.")
    
    def test_deeply_nested_structure(self):
        """Test handling deeply nested object structures."""
        schema = {
            'type': 'object',
            'properties': {
                'level1': {
                    'type': 'object',
                    'use_container': True,
                    'properties': {
                        'level2': {
                            'type': 'object',
                            'use_container': True,
                            'properties': {
                                'level3': {
                                    'type': 'object',
                                    'use_container': True,
                                    'properties': {
                                        'deepField': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.text_input') as mock_text, \
             patch('streamlit.markdown') as mock_markdown:
            
            # Create a proper mock with context manager support
            container_mock = MagicMock()
            mock_container.return_value = container_mock
            
            # Should handle without errors
            self.controller.render_form(schema)
            
            # Verify nested containers were created (one for each nested object with use_container=True)
            self.assertTrue(mock_container.call_count >= 3)
    
    def test_empty_array_handling(self):
        """Test handling of empty arrays."""
        schema = {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {'type': 'object'}
                }
            }
        }
        
        # Ensure array is empty
        self.mock_session_state['lots.0.items'] = []
        
        with patch('streamlit.button') as mock_button:
            mock_button.return_value = False
            
            # Should render without errors
            self.controller.render_form(schema)
            
            # Verify add button was rendered
            add_calls = [c for c in mock_button.call_args_list if '➕' in str(c)]
            self.assertTrue(len(add_calls) > 0)
    
    def test_lot_limit_enforcement(self):
        """Test max_lots limit enforcement."""
        schema = {
            'type': 'object',
            'properties': {'field': {'type': 'string'}},
            'max_lots': 3,
            'allow_multiple_lots': True
        }
        
        # Add lots up to limit
        self.mock_session_state['lots'] = [
            {'name': 'Lot 1', 'index': 0},
            {'name': 'Lot 2', 'index': 1},
            {'name': 'Lot 3', 'index': 2}
        ]
        
        with patch.object(self.controller.lot_manager, 'render_lot_navigation') as mock_nav:
            self.controller.render_form(schema)
            
            # Verify max_lots was passed
            mock_nav.assert_called_with(
                style='tabs',
                allow_add=True,
                allow_remove=True,
                max_lots=3
            )


if __name__ == '__main__':
    unittest.main()