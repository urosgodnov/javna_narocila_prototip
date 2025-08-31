"""
Test Story 40.10: Verify ALL forms use unified lot structure.
No special handling for different form types.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from ui.controllers.form_controller import FormController
from ui.form_renderer_compat import render_form


class TestUnifiedFormArchitecture(unittest.TestCase):
    """Test that ALL forms use the unified lot architecture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_state = {}
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_simple_form_has_general_lot(self):
        """Test that simple forms automatically get General lot."""
        # List of simple forms that previously had no lots
        simple_forms = [
            {'clientInfo': {'type': 'object', 'properties': {'name': {'type': 'string'}}}},
            {'projectInfo': {'type': 'object', 'properties': {'title': {'type': 'string'}}}},
            {'submissionInfo': {'type': 'object', 'properties': {'deadline': {'type': 'string'}}}},
            {'legalBasis': {'type': 'object', 'properties': {'law': {'type': 'string'}}}}
        ]
        
        for form_schema in simple_forms:
            # Clear session state
            self.mock_session_state.clear()
            
            # Create controller
            controller = FormController()
            controller.set_schema({'type': 'object', 'properties': form_schema})
            
            # Verify General lot was created
            self.assertIn('lots', self.mock_session_state)
            self.assertEqual(len(self.mock_session_state['lots']), 1)
            self.assertEqual(self.mock_session_state['lots'][0]['name'], 'General')
            self.assertEqual(self.mock_session_state['lots'][0]['index'], 0)
    
    def test_complex_form_supports_multiple_lots(self):
        """Test that complex forms can have multiple lots."""
        # Complex form schema
        complex_schema = {
            'type': 'object',
            'properties': {
                'lotsConfiguration': {'type': 'object'},
                'technicalRequirements': {'type': 'object'},
                'selectionCriteria': {'type': 'object'}
            },
            'allow_multiple_lots': True
        }
        
        controller = FormController(complex_schema)
        
        # Start with General lot
        self.assertEqual(controller.context.get_lot_count(), 1)
        
        # Add more lots
        controller.context.add_lot('Technical Lot')
        controller.context.add_lot('Financial Lot')
        
        # Verify multiple lots
        self.assertEqual(controller.context.get_lot_count(), 3)
        lots = controller.context.get_all_lots()
        self.assertEqual(lots[0]['name'], 'General')
        self.assertEqual(lots[1]['name'], 'Technical Lot')
        self.assertEqual(lots[2]['name'], 'Financial Lot')
    
    def test_all_data_is_lot_scoped(self):
        """Test that ALL form data uses lot-scoped keys."""
        schema = {
            'type': 'object',
            'properties': {
                'field1': {'type': 'string'},
                'field2': {'type': 'number'},
                'nested': {
                    'type': 'object',
                    'properties': {
                        'inner': {'type': 'string'}
                    }
                }
            }
        }
        
        controller = FormController(schema)
        
        # Set some field values
        controller.context.set_field_value('field1', 'test')
        controller.context.set_field_value('field2', 42)
        controller.context.set_field_value('nested.inner', 'nested_value')
        
        # Check all data keys
        for key in self.mock_session_state.keys():
            # Skip metadata keys
            if key in ['lots', 'current_lot_index', 'form_metadata', 'schema']:
                continue
            
            # All other keys MUST be lot-scoped
            self.assertTrue(
                key.startswith('lots.'),
                f"Key '{key}' is not lot-scoped! All data must use lots.X.field pattern"
            )
    
    def test_no_has_lots_conditionals(self):
        """Test that there are no legacy has_lots conditionals in new code."""
        # This test verifies the architecture doesn't check for has_lots
        controller = FormController()
        
        # These attributes/methods should not exist
        self.assertFalse(hasattr(controller, 'has_lots'))
        self.assertFalse(hasattr(controller.context, 'has_lots'))
        
        # The context should always have lot structure
        self.assertTrue(hasattr(controller.context, 'lot_index'))
        self.assertIsNotNone(controller.context.get_all_lots())
    
    def test_compatibility_wrapper_handles_all_forms(self):
        """Test that compatibility wrapper works for all form types."""
        test_cases = [
            # Simple form (no explicit lots)
            {
                'schema': {'field': {'type': 'string'}},
                'expected_lots': 1
            },
            # Object form
            {
                'schema': {
                    'type': 'object',
                    'properties': {'name': {'type': 'string'}}
                },
                'expected_lots': 1
            },
            # Form with lot_context (legacy)
            {
                'schema': {'field': {'type': 'string'}},
                'lot_context': {'mode': 'general'},
                'expected_lots': 1
            }
        ]
        
        for case in test_cases:
            self.mock_session_state.clear()
            
            with patch('streamlit.text_input'):
                # Call through compatibility wrapper
                if 'lot_context' in case:
                    render_form(case['schema'], lot_context=case['lot_context'])
                else:
                    render_form(case['schema'])
                
                # Verify lot structure
                self.assertIn('lots', self.mock_session_state)
                self.assertEqual(len(self.mock_session_state['lots']), case['expected_lots'])
    
    def test_lot_switching_preserves_data(self):
        """Test that switching between lots preserves data."""
        controller = FormController()
        
        # Add data to General lot
        controller.context.set_field_value('field1', 'general_value')
        
        # Add second lot
        controller.context.add_lot('Second Lot')
        controller.context.switch_to_lot(1)
        
        # Add data to second lot
        controller.context.set_field_value('field1', 'second_value')
        
        # Switch back to General
        controller.context.switch_to_lot(0)
        
        # Verify data preserved
        self.assertEqual(controller.context.get_field_value('field1'), 'general_value')
        
        # Switch to second lot
        controller.context.switch_to_lot(1)
        self.assertEqual(controller.context.get_field_value('field1'), 'second_value')
    
    def test_form_data_retrieval_unified(self):
        """Test that form data retrieval is unified for all forms."""
        controller = FormController()
        
        # Add data to multiple lots
        controller.context.set_field_value('name', 'John Doe')
        controller.context.add_lot('Additional')
        controller.context.switch_to_lot(1)
        controller.context.set_field_value('name', 'Jane Doe')
        
        # Get all form data
        form_data = controller.get_form_data()
        
        # Verify structure
        self.assertIn('lots', form_data)
        self.assertEqual(len(form_data['lots']), 2)
        
        # Verify data is lot-structured
        self.assertIn('lots.0.name', self.mock_session_state)
        self.assertIn('lots.1.name', self.mock_session_state)
        self.assertEqual(self.mock_session_state['lots.0.name'], 'John Doe')
        self.assertEqual(self.mock_session_state['lots.1.name'], 'Jane Doe')
    
    def test_no_mode_checks_in_new_architecture(self):
        """Test that new architecture doesn't check for 'mode'."""
        controller = FormController()
        
        # Check session state doesn't have lot mode fields
        for key in self.mock_session_state:
            if key == 'form_metadata':
                continue  # Skip metadata which has validation_mode
            # Check for lot mode patterns
            if isinstance(self.mock_session_state[key], str):
                self.assertNotIn('general_mode', self.mock_session_state[key])
                self.assertNotIn('lots_mode', self.mock_session_state[key])
        
        # Lot context should not have mode
        current_lot = controller.context.get_current_lot()
        self.assertNotIn('mode', current_lot)
    
    def test_field_keys_always_lot_scoped(self):
        """Test that field keys are always lot-scoped, never plain."""
        controller = FormController()
        
        test_fields = ['simple_field', 'nested.field', 'array.0.item']
        
        for field in test_fields:
            # Get the actual key that would be used
            actual_key = controller.context.get_field_key(field)
            
            # Must always be lot-scoped
            self.assertTrue(
                actual_key.startswith('lots.'),
                f"Field '{field}' produced non-lot-scoped key: {actual_key}"
            )
            
            # Should include lot index
            self.assertIn('.0.', actual_key, "Should include lot index 0")


class TestPerformanceUnified(unittest.TestCase):
    """Test performance of unified architecture."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_state = {}
        self.session_patcher = patch('streamlit.session_state', self.mock_session_state)
        self.session_patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        self.session_patcher.stop()
    
    def test_simple_form_performance(self):
        """Test that simple forms (with General lot) perform well."""
        import time
        
        schema = {
            'type': 'object',
            'properties': {
                f'field_{i}': {'type': 'string'}
                for i in range(50)  # 50 fields
            }
        }
        
        start = time.time()
        
        controller = FormController(schema)
        # Set values for all fields
        for i in range(50):
            controller.context.set_field_value(f'field_{i}', f'value_{i}')
        
        # Get all values
        for i in range(50):
            value = controller.context.get_field_value(f'field_{i}')
            self.assertEqual(value, f'value_{i}')
        
        elapsed = time.time() - start
        
        # Should be fast (< 100ms for 50 fields)
        self.assertLess(elapsed, 0.1, f"Simple form too slow: {elapsed:.3f}s")
    
    def test_multi_lot_performance(self):
        """Test performance with multiple lots."""
        import time
        
        schema = {
            'type': 'object',
            'properties': {
                f'field_{i}': {'type': 'string'}
                for i in range(20)
            }
        }
        
        start = time.time()
        
        controller = FormController(schema)
        
        # Add 5 lots
        for i in range(1, 5):
            controller.context.add_lot(f'Lot {i+1}')
        
        # Add data to each lot
        for lot_idx in range(5):
            controller.context.switch_to_lot(lot_idx)
            for field_idx in range(20):
                controller.context.set_field_value(
                    f'field_{field_idx}',
                    f'lot_{lot_idx}_value_{field_idx}'
                )
        
        elapsed = time.time() - start
        
        # Should handle multiple lots efficiently (< 200ms)
        self.assertLess(elapsed, 0.2, f"Multi-lot form too slow: {elapsed:.3f}s")


class TestNoLegacyCodePaths(unittest.TestCase):
    """Verify no legacy code paths remain."""
    
    def test_no_forbidden_patterns_in_controller(self):
        """Test that FormController has no legacy patterns."""
        import inspect
        from ui.controllers.form_controller import FormController
        
        # Get source code
        source = inspect.getsource(FormController)
        
        # Forbidden patterns that indicate legacy code
        forbidden_patterns = [
            'if has_lots',
            'if lot_context',
            'mode == "general"',
            'mode == "lots"',
            'mode == \'general\'',
            'mode == \'lots\'',
            'has_lots =',
            'check_has_lots'
        ]
        
        for pattern in forbidden_patterns:
            self.assertNotIn(
                pattern.lower(),
                source.lower(),
                f"Found forbidden legacy pattern in FormController: {pattern}"
            )
    
    def test_no_forbidden_patterns_in_context(self):
        """Test that FormContext has no legacy patterns."""
        import inspect
        from utils.form_helpers import FormContext
        
        source = inspect.getsource(FormContext)
        
        forbidden_patterns = [
            'has_lots',
            'mode =',
            'general_mode',
            'lots_mode'
        ]
        
        for pattern in forbidden_patterns:
            self.assertNotIn(
                pattern.lower(),
                source.lower(),
                f"Found forbidden legacy pattern in FormContext: {pattern}"
            )


if __name__ == '__main__':
    unittest.main()