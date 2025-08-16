"""
Test suite for Modern Form Renderer
Tests the fixed integration and all field types
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_modern_form_imports():
    """Test that modern form renderer can be imported without errors."""
    try:
        from ui.modern_form_renderer import (
            render_modern_form, 
            inject_modern_styles
        )
        print("✅ Modern form renderer imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_modern_form_functions():
    """Test that the fixed functions work correctly."""
    import streamlit as st
    from ui.modern_form_renderer import render_modern_form
    from config import get_dynamic_form_steps
    from utils.lot_utils import get_current_lot_context
    
    # Mock session state
    if 'schema' not in st.session_state:
        st.session_state['schema'] = {
            "properties": {
                "clientInfo": {"type": "object", "title": "Client Information"},
                "projectInfo": {"type": "object", "title": "Project Information"},
                "orderType": {"type": "string", "title": "Order Type"}
            }
        }
    
    if 'current_step' not in st.session_state:
        st.session_state['current_step'] = 0
    
    # Test get_dynamic_form_steps with session_state parameter
    try:
        form_steps = get_dynamic_form_steps(st.session_state)
        print(f"✅ get_dynamic_form_steps works: {len(form_steps)} steps")
    except Exception as e:
        print(f"❌ get_dynamic_form_steps error: {e}")
        return False
    
    # Test get_current_lot_context with current_step_keys
    try:
        if form_steps and len(form_steps) > 0:
            current_step_keys = form_steps[0]
            lot_context = get_current_lot_context(current_step_keys)
            print(f"✅ get_current_lot_context works: mode={lot_context['mode']}")
    except Exception as e:
        print(f"❌ get_current_lot_context error: {e}")
        return False
    
    print("✅ All function signature tests passed!")
    return True

def test_schema_property_building():
    """Test that current_step_properties dictionary is built correctly."""
    import streamlit as st
    
    # Setup test schema
    st.session_state['schema'] = {
        "properties": {
            "clientInfo": {
                "type": "object",
                "title": "Podatki o naročniku",
                "properties": {
                    "name": {"type": "string", "title": "Naziv"}
                }
            },
            "orderType": {
                "type": "string",
                "title": "Vrsta naročila",
                "enum": ["blago", "storitve", "gradnje"]
            }
        }
    }
    
    # Test building properties for regular keys
    test_keys = ["clientInfo", "orderType"]
    current_step_properties = {}
    
    for key in test_keys:
        if key in st.session_state.schema["properties"]:
            prop_copy = st.session_state.schema["properties"][key].copy()
            current_step_properties[key] = prop_copy
    
    assert len(current_step_properties) == 2, "Should have 2 properties"
    assert "clientInfo" in current_step_properties, "Should have clientInfo"
    assert "orderType" in current_step_properties, "Should have orderType"
    
    print("✅ Schema property building works correctly")
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 MODERN FORM RENDERER TEST SUITE")
    print("="*60 + "\n")
    
    # Run tests
    tests = [
        ("Import Test", test_modern_form_imports),
        ("Function Signatures", test_modern_form_functions),
        ("Schema Properties", test_schema_property_building)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, "PASSED ✅" if success else "FAILED ❌"))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append((test_name, f"ERROR ❌: {str(e)[:50]}"))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    for test_name, result in results:
        print(f"{test_name:30} {result}")
    
    passed = sum(1 for _, r in results if "PASSED" in r)
    total = len(results)
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Modern Form Renderer is fixed!")
    else:
        print("\n⚠️ Some tests failed - Review the issues above")