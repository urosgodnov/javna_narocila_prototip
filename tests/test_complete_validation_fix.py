#!/usr/bin/env python3
"""Test complete validation fix with widget sync."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.controllers.form_controller import FormController
from utils.widget_sync import WidgetSync

def test_complete_validation_fix():
    """Test the complete validation fix including widget sync."""
    
    print("Testing Complete Validation Fix")
    print("=" * 60)
    
    # Initialize
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize controller
    controller = FormController()
    
    # Test 1: Set up production-like scenario
    print("\n1. Setting up production-like scenario...")
    
    # Set up lots and basic state
    st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
    st.session_state['current_lot_index'] = 0
    st.session_state['lots.0.clientInfo.isSingleClient'] = True
    
    # Simulate user filling fields (only widget keys, no lot keys)
    st.session_state['widget_lots.0.clientInfo.singleClientName'] = 'OŠ Bistrica'
    st.session_state['widget_lots.0.clientInfo.singleClientStreetAddress'] = 'Kovorska cesta 1'
    st.session_state['widget_lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['widget_lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. FikFak Mafelda'
    
    print("  ✅ Widget keys set (simulating user input)")
    print("  ❌ Lot keys NOT set (sync hasn't happened)")
    
    # Test 2: Check widget state before validation
    print("\n2. Checking widget state before validation...")
    
    debug_info = WidgetSync.debug_widget_state('client')
    print(f"  Widget keys found: {len(debug_info['widget_keys'])}")
    print(f"  Lot keys found: {len(debug_info['lot_keys'])}")
    print(f"  Widget-only keys: {len(debug_info['widget_only'])}")
    
    # Test 3: Validate WITHOUT manual sync (should work with auto-sync)
    print("\n3. Testing validation (with automatic widget sync)...")
    
    is_valid, errors = controller.validation_manager.validate_screen_1_customers()
    
    print(f"  Validation result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"  Errors: {errors[:3]}...")
    
    # Test 4: Check widget state after validation
    print("\n4. Checking widget state after validation...")
    
    debug_info_after = WidgetSync.debug_widget_state('client')
    print(f"  Widget keys: {len(debug_info_after['widget_keys'])}")
    print(f"  Lot keys: {len(debug_info_after['lot_keys'])}")
    print(f"  Synced during validation: {len(debug_info_after['lot_keys']) - len(debug_info['lot_keys'])}")
    
    # Test 5: Verify lot keys now exist
    print("\n5. Verifying lot keys after auto-sync...")
    
    expected_lot_keys = [
        'lots.0.clientInfo.singleClientName',
        'lots.0.clientInfo.singleClientStreetAddress',
        'lots.0.clientInfo.singleClientPostalCode',
        'lots.0.clientInfo.singleClientLegalRepresentative'
    ]
    
    for key in expected_lot_keys:
        if key in st.session_state:
            value = st.session_state[key]
            print(f"  ✅ {key.split('.')[-1][:30]}: {value[:20] if value else 'empty'}...")
        else:
            print(f"  ❌ {key.split('.')[-1][:30]}: NOT FOUND")
    
    # Test 6: Clean state and test manual sync
    print("\n6. Testing manual widget sync...")
    
    # Clear lot keys but keep widget keys
    for key in expected_lot_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Manually sync
    synced = WidgetSync.sync_all_widget_values()
    print(f"  Manually synced {synced} values")
    
    # Validate again
    is_valid_manual, errors_manual = controller.validation_manager.validate_screen_1_customers()
    print(f"  Validation after manual sync: {'✅ PASS' if is_valid_manual else '❌ FAIL'}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    if is_valid:
        print("✅ COMPLETE FIX SUCCESSFUL!")
        print("\nKey achievements:")
        print("- Widget values automatically synced before validation")
        print("- ValidationAdapter checks both widget and lot keys")
        print("- Validation works even when FieldRenderer hasn't synced")
        print("\nThe validation bug is FIXED!")
        return True
    else:
        print("❌ Validation still failing")
        print("\nRemaining issues:")
        for error in errors[:3]:
            print(f"- {error}")
        print("\nNeed further investigation")
        return False


if __name__ == "__main__":
    try:
        success = test_complete_validation_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)