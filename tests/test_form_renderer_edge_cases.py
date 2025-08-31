"""
Edge case tests for form_renderer.py baseline
These tests capture additional corner cases and critical behaviors.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import streamlit as st
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime
import json

from ui.form_renderer import (
    render_form,
    format_number_with_dots,
    parse_formatted_number,
    get_selected_criteria_labels,
    _should_render,
    _get_default_value,
    display_criteria_ratios_total
)


class TestEdgeCaseNumberFormatting:
    """Test edge cases in number formatting"""
    
    def test_format_very_large_numbers(self):
        """Test formatting of very large numbers"""
        assert format_number_with_dots(1000000000) == "1.000.000.000"
        assert format_number_with_dots(999999999999.99) == "999.999.999.999.99"
        
    def test_format_negative_numbers(self):
        """Test formatting of negative numbers"""
        assert format_number_with_dots(-1000) == "-1.000"
        assert format_number_with_dots(-1500.50) == "-1.500.50"
        
    def test_format_zero_variants(self):
        """Test different representations of zero"""
        assert format_number_with_dots(0) == "0"
        assert format_number_with_dots(0.0) == "0"
        assert format_number_with_dots(0.00) == "0"
        
    def test_parse_edge_cases(self):
        """Test parsing edge cases"""
        assert parse_formatted_number("") == 0.0
        assert parse_formatted_number("   ") == 0.0
        assert parse_formatted_number("0") == 0.0
        # Note: parse_formatted_number treats dots as decimal points for negative numbers
        assert parse_formatted_number("-1.000") == -1.0  # Not -1000.0!
        

class TestComplexConditionalRendering:
    """Test complex conditional rendering scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if 'session_state' not in st.__dict__:
            st.session_state = {}
        st.session_state.clear()
        
    def test_nested_render_if_conditions(self):
        """Test nested conditional rendering"""
        st.session_state['level1'] = 'show'
        st.session_state['level2'] = 'hide'
        
        # First level condition true, second false
        prop_details_1 = {
            'render_if': {
                'field': 'level1',
                'value': 'show'
            }
        }
        assert _should_render(prop_details_1) == True
        
        # Both conditions would need to be checked
        prop_details_2 = {
            'render_if': {
                'field': 'level2',
                'value': 'show'
            }
        }
        assert _should_render(prop_details_2) == False
        
    def test_render_if_all_conditions(self):
        """Test render_if_all with multiple conditions"""
        st.session_state['field1'] = 'yes'
        st.session_state['field2'] = 'yes'
        st.session_state['field3'] = 'no'
        
        prop_details = {
            'render_if_all': [
                {'field': 'field1', 'value': 'yes'},
                {'field': 'field2', 'value': 'yes'},
                {'field': 'field3', 'value': 'yes'}
            ]
        }
        
        # Should NOT render if ALL conditions are not true
        # Note: Check if render_if_all is actually implemented
        # If not implemented, this documents current behavior
        result = _should_render(prop_details)
        # Current implementation might not have render_if_all
        assert result == True  # Document actual behavior
        

class TestLotScopedKeys:
    """Test lot-scoped key generation edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if 'session_state' not in st.__dict__:
            st.session_state = {}
        st.session_state.clear()
        st.session_state['lots'] = [
            {'name': 'Lot 1', 'index': 0},
            {'name': 'Lot 2', 'index': 1},
            {'name': 'Lot 3', 'index': 2}
        ]
        
    def test_global_field_bypasses_lot_scoping(self):
        """Test that global fields don't get lot-scoped"""
        schema = {
            "globalField": {
                "type": "string",
                "title": "Global Field",
                "is_global": True  # If this property exists
            }
        }
        
        lot_context = {'mode': 'lots', 'lot_index': 1}
        
        with patch('streamlit.text_input') as mock_input:
            mock_input.return_value = "test"
            
            # Check if is_global property is respected
            render_form(schema, lot_context=lot_context)
            
            # Document current behavior
            mock_input.assert_called()
            

class TestArrayEdgeCases:
    """Test edge cases in array handling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if 'session_state' not in st.__dict__:
            st.session_state = {}
        st.session_state.clear()
        
    def test_empty_array_initialization(self):
        """Test rendering empty array"""
        schema = {
            "items": {
                "type": "array",
                "title": "Items",
                "items": {
                    "type": "string",
                    "enum": ["Option1", "Option2", "Option3"]  # Need enum for multiselect
                }
            }
        }
        
        # Don't initialize array in session state
        with patch('streamlit.multiselect') as mock_multi:
            mock_multi.return_value = []
            
            render_form(schema)
            
            mock_multi.assert_called()
            
    def test_array_with_max_items(self):
        """Test array with maxItems constraint"""
        schema = {
            "items": {
                "type": "array",
                "title": "Items",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        # Initialize with max items
        st.session_state['items'] = [
            {"name": "Item 1"},
            {"name": "Item 2"},
            {"name": "Item 3"}
        ]
        
        with patch('streamlit.button') as mock_button:
            with patch('streamlit.container'):
                with patch('streamlit.text_input'):
                    render_form(schema)
                    
                    # Check if add button is disabled/hidden at max
                    # Document current behavior
                    assert mock_button.called
                    

class TestFinancialFieldHandling:
    """Test financial field specific handling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if 'session_state' not in st.__dict__:
            st.session_state = {}
        st.session_state.clear()
        
    def test_estimated_value_field(self):
        """Test estimatedValue field gets special formatting"""
        schema = {
            "estimatedValue": {
                "type": "number",
                "title": "Estimated Value"
            }
        }
        
        with patch('streamlit.text_input') as mock_input:
            with patch('streamlit.columns') as mock_cols:
                mock_input.return_value = "1.000.000"
                mock_cols.return_value = [MagicMock(), MagicMock()]
                
                render_form(schema)
                
                # Financial fields use columns for EUR symbol
                mock_cols.assert_called()
                
    def test_guarantee_amount_fields(self):
        """Test guarantee amount fields in different contexts"""
        schema = {
            "financialGuarantees": {
                "type": "object",
                "properties": {
                    "fzSeriousness": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "title": "Amount"
                            }
                        }
                    }
                }
            }
        }
        
        with patch('streamlit.text_input') as mock_input:
            with patch('streamlit.columns') as mock_cols:
                mock_input.return_value = "50.000"
                mock_cols.return_value = [MagicMock(), MagicMock()]
                
                render_form(schema)
                
                # Guarantee amounts should also use financial formatting
                mock_cols.assert_called()
                

class TestValidationIntegration:
    """Test validation integration with form rendering"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if 'session_state' not in st.__dict__:
            st.session_state = {}
        st.session_state.clear()
        
    def test_required_field_validation(self):
        """Test required field validation"""
        schema = {
            "requiredField": {
                "type": "string",
                "title": "Required Field",
                "required": True
            }
        }
        
        # Set empty value
        st.session_state['requiredField'] = ""
        
        with patch('streamlit.text_input') as mock_input:
            mock_input.return_value = ""
            
            # Render and check validation
            render_form(schema)
            
            # Document how validation errors are shown
            mock_input.assert_called()
            

class TestDeepNesting:
    """Test deeply nested structures"""
    
    def test_three_level_nesting(self):
        """Test 3+ levels of object nesting"""
        schema = {
            "level1": {
                "type": "object",
                "title": "Level 1",
                "properties": {
                    "level2": {
                        "type": "object",
                        "title": "Level 2",
                        "properties": {
                            "level3": {
                                "type": "object",
                                "title": "Level 3",
                                "properties": {
                                    "deepField": {
                                        "type": "string",
                                        "title": "Deep Field"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        with patch('streamlit.subheader') as mock_header:
            with patch('streamlit.text_input') as mock_input:
                render_form(schema)
                
                # Verify nested headers are created
                assert mock_header.call_count >= 3
                mock_input.assert_called()
                

if __name__ == "__main__":
    pytest.main([__file__, "-v"])