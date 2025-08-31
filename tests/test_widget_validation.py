#!/usr/bin/env python3
"""Test validation with Streamlit widget keys."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.controllers.form_controller import FormController

def test_widget_validation():
    """Test that validation works with widget keys."""
    
    print("Testing Validation with Widget Keys")
    print("=" * 60)
    
    # Initialize
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize controller
    controller = FormController()
    
    # Test 1: Simulate how Streamlit actually stores data
    print("\n1. Simulating Streamlit widget data storage...")
    
    # Set up lots
    st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
    st.session_state['current_lot_index'] = 0
    st.session_state['clientInfo.isSingleClient'] = True
    
    # Simulate widget storage (as Streamlit does)
    # When user types in field, Streamlit stores in widget key
    st.session_state['widget_lots.0.clientInfo.singleClientName'] = 'OŠ Bistrica'
    st.session_state['widget_lots.0.clientInfo.singleClientStreetAddress'] = 'Kovorska cesta 1'
    st.session_state['widget_lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['widget_lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. FikFak Mafelda'
    
    # Also store in regular lot keys (as FieldRenderer should do)
    st.session_state['lots.0.clientInfo.singleClientName'] = 'OŠ Bistrica'
    st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Kovorska cesta 1'
    st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. FikFak Mafelda'
    st.session_state['lots.0.clientInfo.isSingleClient'] = True
    
    print("  Stored in both widget and lot keys")
    
    # Test 2: Validate with both keys present
    print("\n2. Testing validation with dual storage...")
    
    is_valid, errors = controller.validation_manager.validate_screen_1_customers()
    
    print(f"  Validation result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test 3: Test with ONLY widget keys (simulating sync failure)
    print("\n3. Testing with ONLY widget keys (no lot keys)...")
    
    # Clear lot keys but keep widget keys
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('lots.0.clientInfo.single')]
    for key in keys_to_remove:
        del st.session_state[key]
    
    # Keep only widget keys
    st.session_state['widget_lots.0.clientInfo.singleClientName'] = 'OŠ Bistrica'
    st.session_state['widget_lots.0.clientInfo.singleClientStreetAddress'] = 'Kovorska cesta 1'
    st.session_state['widget_lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['widget_lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. FikFak Mafelda'
    
    is_valid, errors = controller.validation_manager.validate_screen_1_customers()
    
    print(f"  Validation result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"  Errors: {errors[:2]}...")
    
    # Test 4: Debug what ValidationManager sees
    print("\n4. Debug: What ValidationManager sees...")
    
    vm = controller.validation_manager
    test_keys = [
        'clientInfo.singleClientName',
        'clientInfo.singleClientStreetAddress',
        'clientInfo.singleClientPostalCode',
        'clientInfo.singleClientLegalRepresentative'
    ]
    
    for key in test_keys:
        value = vm.session_state.get(key)
        print(f"  {key}: {value if value else 'NOT FOUND'}")
    
    # Test 5: Check all possible key patterns
    print("\n5. Checking all key patterns in session_state...")
    
    patterns = [
        'clientInfo.singleClientName',
        'lots.0.clientInfo.singleClientName',
        'widget_lots.0.clientInfo.singleClientName',
        'widget_clientInfo.singleClientName',
        'general.clientInfo.singleClientName'
    ]
    
    for pattern in patterns:
        if pattern in st.session_state:
            print(f"  ✅ Found: {pattern} = {st.session_state[pattern]}")
        else:
            print(f"  ❌ Missing: {pattern}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    if is_valid:
        print("✅ Validation works with widget keys!")
        print("\nKey findings:")
        print("- Widget keys are checked by ValidationAdapter")
        print("- Both widget and lot keys are supported")
        print("- Validation can find data in either location")
        return True
    else:
        print("❌ Validation still failing with widget keys")
        print("\nIssues found:")
        print("- Widget keys may not be properly checked")
        print("- Sync between widget and lot keys may be broken")
        print("- Need to investigate actual production key patterns")
        return False


if __name__ == "__main__":
    try:
        success = test_widget_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)