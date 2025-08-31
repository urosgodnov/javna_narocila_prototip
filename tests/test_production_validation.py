#!/usr/bin/env python3
"""Test validation in production-like scenario with widget keys."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.controllers.form_controller import FormController

def test_production_validation():
    """Test validation as it happens in production with widget keys."""
    
    print("Testing Production Validation Scenario")
    print("=" * 60)
    
    # Initialize
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize controller
    controller = FormController()
    
    # Test 1: Simulate EXACTLY how production stores data
    print("\n1. Simulating production data storage...")
    
    # Set up lots and basic state (as FormContext does)
    st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
    st.session_state['current_lot_index'] = 0
    st.session_state['lots.0.clientInfo.isSingleClient'] = True
    
    # CRITICAL: In production, when user types in a field:
    # 1. Streamlit stores value in widget key IMMEDIATELY
    # 2. FieldRenderer's update happens AFTER (on rerun)
    # 3. Validation might run BEFORE the sync
    
    # Simulate user typing in fields (Streamlit stores in widget keys)
    # The widget key format from FieldRenderer is: widget_{session_key}
    # where session_key = lots.0.clientInfo.singleClientName
    st.session_state['widget_lots.0.clientInfo.singleClientName'] = 'OŠ Bistrica'
    st.session_state['widget_lots.0.clientInfo.singleClientStreetAddress'] = 'Kovorska cesta 1'
    st.session_state['widget_lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['widget_lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. FikFak Mafelda'
    
    # NO lot keys yet (sync hasn't happened)
    print("  Stored ONLY in widget keys (before sync)")
    
    # Test 2: Validate BEFORE sync (this is the bug scenario)
    print("\n2. Testing validation BEFORE field sync...")
    
    is_valid, errors = controller.validation_manager.validate_screen_1_customers()
    
    print(f"  Validation result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"  Errors found: {len(errors)}")
        for error in errors[:3]:
            print(f"    - {error}")
    
    # Test 3: What does ValidationManager actually see?
    print("\n3. Debug: Keys ValidationManager checks...")
    
    vm = controller.validation_manager
    
    # Check what the wrapper sees
    test_keys = [
        'clientInfo.singleClientName',
        'clientInfo.singleClientStreetAddress',
        'clientInfo.singleClientPostalCode',
        'clientInfo.singleClientLegalRepresentative'
    ]
    
    for key in test_keys:
        # Direct check
        value = vm.session_state.get(key)
        print(f"  {key}: {value if value else 'NOT FOUND'}")
    
    # Test 4: Show ALL keys in session state
    print("\n4. All session state keys:")
    for key in sorted(st.session_state.keys()):
        if 'client' in key.lower():
            value = st.session_state[key]
            if isinstance(value, str) and len(value) > 30:
                value = value[:30] + "..."
            print(f"  {key} = {value}")
    
    # Test 5: Now simulate the sync (what FieldRenderer does after widget change)
    print("\n5. Simulating FieldRenderer sync...")
    
    # Copy widget values to lot keys (as FieldRenderer should do)
    for key in list(st.session_state.keys()):
        if key.startswith('widget_lots.'):
            # Extract the non-widget key
            non_widget_key = key.replace('widget_', '')
            st.session_state[non_widget_key] = st.session_state[key]
    
    print("  Synced widget values to lot keys")
    
    # Test 6: Validate AFTER sync
    print("\n6. Testing validation AFTER field sync...")
    
    is_valid_after, errors_after = controller.validation_manager.validate_screen_1_customers()
    
    print(f"  Validation result: {'✅ PASS' if is_valid_after else '❌ FAIL'}")
    if errors_after:
        print(f"  Errors found: {len(errors_after)}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("-" * 60)
    
    if not is_valid and is_valid_after:
        print("❌ PROBLEM CONFIRMED: Validation fails before sync!")
        print("\nRoot cause:")
        print("- Streamlit stores widget values immediately")
        print("- FieldRenderer sync happens on next rerun")
        print("- Validation runs before sync completes")
        print("\nSolution:")
        print("- ValidationAdapter must check widget keys FIRST")
        print("- Widget key pattern: widget_lots.{lot}.{field}")
        return False
    elif is_valid:
        print("✅ Validation works even before sync!")
        print("\nValidationAdapter is correctly checking:")
        print("- Widget keys (widget_lots.X.field)")
        print("- Lot keys (lots.X.field)")
        print("- Both patterns are supported")
        return True
    else:
        print("❌ Validation fails even after sync")
        print("\nPossible issues:")
        print("- Field names don't match")
        print("- Validation logic has other requirements")
        print("- Need to debug actual validation code")
        return False


if __name__ == "__main__":
    try:
        success = test_production_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)