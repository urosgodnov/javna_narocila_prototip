"""
Test that new directory structure and imports work correctly.
This verifies Story 40.3 completion.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def test_renderer_imports():
    """Test that all renderer components can be imported"""
    from ui.renderers import FieldRenderer, SectionRenderer, LotManager
    
    # Verify classes exist
    assert FieldRenderer is not None
    assert SectionRenderer is not None
    assert LotManager is not None
    

def test_controller_imports():
    """Test that controller components can be imported"""
    from ui.controllers import FormController
    
    # Verify class exists
    assert FormController is not None
    

def test_form_helper_imports():
    """Test that form helper utilities can be imported"""
    from utils.form_helpers import (
        FormContext,
        migrate_flat_to_lot_structure,
        cleanup_session_state,
        export_lot_data
    )
    
    # Verify all components exist
    assert FormContext is not None
    assert migrate_flat_to_lot_structure is not None
    assert cleanup_session_state is not None
    assert export_lot_data is not None
    

def test_renderer_instantiation():
    """Test that renderer classes can be instantiated"""
    from ui.renderers import FieldRenderer, SectionRenderer, LotManager
    from utils.form_helpers import FormContext
    
    # Create mock session state
    mock_session_state = {}
    
    # Create context
    context = FormContext(mock_session_state)
    
    # Instantiate renderers
    field_renderer = FieldRenderer(context)
    section_renderer = SectionRenderer(context, field_renderer)
    lot_manager = LotManager(context)
    
    # Verify instances created
    assert field_renderer is not None
    assert section_renderer is not None
    assert lot_manager is not None
    

def test_form_context_lot_structure():
    """Test that FormContext creates lot structure automatically"""
    from utils.form_helpers import FormContext
    
    # Start with empty session state
    mock_session_state = {}
    
    # Create context
    context = FormContext(mock_session_state)
    
    # Verify lot structure was created
    assert 'lots' in mock_session_state
    assert len(mock_session_state['lots']) == 1
    assert mock_session_state['lots'][0]['name'] == 'General'
    assert mock_session_state['lots'][0]['index'] == 0
    assert mock_session_state['current_lot_index'] == 0
    

def test_form_context_key_generation():
    """Test that FormContext generates correct lot-scoped keys"""
    from utils.form_helpers import FormContext
    
    mock_session_state = {}
    context = FormContext(mock_session_state)
    
    # Test regular field key
    key = context.get_field_key("test_field")
    assert key == "lots.0.test_field"
    
    # Test global field key
    global_key = context.get_field_key("global_field", force_global=True)
    assert global_key == "global_field"
    

def test_form_controller_instantiation():
    """Test that FormController can be instantiated"""
    from ui.controllers import FormController
    
    mock_session_state = {}
    controller = FormController(mock_session_state)
    
    assert controller is not None
    assert controller.session_state == mock_session_state
    

def test_field_renderer_method_exists():
    """Test that FieldRenderer has required methods"""
    from ui.renderers import FieldRenderer
    from utils.form_helpers import FormContext
    
    mock_session_state = {}
    context = FormContext(mock_session_state)
    field_renderer = FieldRenderer(context)
    
    # Check required methods exist
    assert hasattr(field_renderer, 'render_field')
    assert callable(field_renderer.render_field)
    

def test_lot_manager_methods_exist():
    """Test that LotManager has required methods"""
    from ui.renderers import LotManager
    from utils.form_helpers import FormContext
    
    mock_session_state = {}
    context = FormContext(mock_session_state)
    lot_manager = LotManager(context)
    
    # Check required methods exist
    assert hasattr(lot_manager, 'render_lot_navigation')
    assert hasattr(lot_manager, 'add_lot')
    assert hasattr(lot_manager, 'remove_lot')
    

def test_form_state_utilities():
    """Test form state utility functions"""
    from utils.form_helpers import export_lot_data
    
    # Create mock session state with lot data
    mock_session_state = {
        'lots': [{'name': 'Test Lot', 'index': 0}],
        'lots.0.field1': 'value1',
        'lots.0.field2': 'value2',
        'lots.1.field1': 'value3',
        'other_key': 'other_value'
    }
    
    # Export lot 0 data
    lot_0_data = export_lot_data(mock_session_state, 0)
    
    assert 'field1' in lot_0_data
    assert 'field2' in lot_0_data
    assert lot_0_data['field1'] == 'value1'
    assert lot_0_data['field2'] == 'value2'
    assert 'other_key' not in lot_0_data
    

if __name__ == "__main__":
    pytest.main([__file__, "-v"])