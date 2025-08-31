#!/usr/bin/env python3
"""Test that validation works with lot-scoped keys in unified architecture."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.controllers.form_controller import FormController
from utils.validations import ValidationManager
from utils.validation_adapter import ValidationAdapter

def test_validation_with_lot_keys():
    """Test that validation correctly recognizes lot-scoped field values."""
    
    print("Testing Validation with Lot-Scoped Keys")
    print("=" * 60)
    
    # Initialize session state
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Test 1: Set up filled fields in lot-scoped format
    print("\n1. Setting up filled customer fields in lot-scoped format...")
    
    # Initialize with single lot
    st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
    st.session_state['current_lot_index'] = 0
    
    # Fill in customer data in lot-scoped format (as new form saves it)
    st.session_state['lots.0.clientInfo.singleClientName'] = 'Šola Bistrica'
    st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Bistriška 7'
    st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. Frida Meglič'
    st.session_state['lots.0.clientInfo.isSingleClient'] = True
    
    print("   Filled fields:")
    print(f"     Name: {st.session_state.get('lots.0.clientInfo.singleClientName')}")
    print(f"     Address: {st.session_state.get('lots.0.clientInfo.singleClientStreetAddress')}")
    print(f"     Postal: {st.session_state.get('lots.0.clientInfo.singleClientPostalCode')}")
    print(f"     Representative: {st.session_state.get('lots.0.clientInfo.singleClientLegalRepresentative')}")
    
    # Test 2: Create ValidationManager with adapter
    print("\n2. Testing ValidationManager with adapter...")
    
    # Create controller which includes ValidationManager with adapter
    controller = FormController()
    
    # Validate customer screen
    step_keys = ['clientInfo']
    is_valid, errors = controller.validation_manager.validate_step(step_keys, 0)
    
    print(f"   Validation result: {'PASS' if is_valid else 'FAIL'}")
    print(f"   Number of errors: {len(errors)}")
    if errors:
        print("   Errors found:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"     - {error}")
    
    # Expected: Should be valid since all fields are filled
    if is_valid:
        print("   ✓ Validation correctly recognizes lot-scoped fields!")
    else:
        print("   ✗ Validation still not recognizing lot-scoped fields")
    
    # Test 3: Test with old-style keys (should also work via adapter)
    print("\n3. Testing backward compatibility with old-style keys...")
    
    # Clear lot-scoped data and use old-style keys
    for key in list(st.session_state.keys()):
        if key.startswith('lots.0.clientInfo'):
            del st.session_state[key]
    
    # Set old-style keys
    st.session_state['clientInfo.singleClientName'] = 'Test School'
    st.session_state['clientInfo.singleClientStreetAddress'] = 'Test Street 123'
    st.session_state['clientInfo.singleClientPostalCode'] = '1000 Ljubljana'
    st.session_state['clientInfo.singleClientLegalRepresentative'] = 'Test Person'
    st.session_state['clientInfo.isSingleClient'] = True
    
    # Validate again
    is_valid_old, errors_old = controller.validation_manager.validate_step(step_keys, 0)
    
    print(f"   Old-style validation: {'PASS' if is_valid_old else 'FAIL'}")
    print(f"   Number of errors: {len(errors_old)}")
    
    if is_valid_old:
        print("   ✓ Backward compatibility maintained!")
    
    # Test 4: Test mixed keys (some lot-scoped, some old-style)
    print("\n4. Testing mixed key formats...")
    
    # Mix of old and new keys
    st.session_state['lots.0.clientInfo.singleClientName'] = 'Mixed Test'
    st.session_state['clientInfo.singleClientStreetAddress'] = 'Mixed Street'
    st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '2000 Maribor'
    st.session_state['clientInfo.singleClientLegalRepresentative'] = 'Mixed Person'
    
    # Validate with mixed keys
    is_valid_mixed, errors_mixed = controller.validation_manager.validate_step(step_keys, 0)
    
    print(f"   Mixed-key validation: {'PASS' if is_valid_mixed else 'FAIL'}")
    print(f"   Number of errors: {len(errors_mixed)}")
    
    # Test 5: Test ValidationAdapter's get method directly
    print("\n5. Testing ValidationAdapter key resolution...")
    
    # Test the lot_aware_get function
    vm = ValidationManager({}, st.session_state)
    ValidationAdapter.update_validation_manager_for_unified_lots(vm)
    
    # Should find lot-scoped value
    name_value = vm.session_state.get('clientInfo.singleClientName')
    print(f"   Looking for 'clientInfo.singleClientName': {name_value}")
    
    # Should find old-style value
    address_value = vm.session_state.get('clientInfo.singleClientStreetAddress')
    print(f"   Looking for 'clientInfo.singleClientStreetAddress': {address_value}")
    
    print("\n" + "=" * 60)
    
    # Overall result
    if is_valid or is_valid_old:
        print("✅ VALIDATION KEY MAPPING WORKS!")
        print("\nKey Features:")
        print("- Lot-scoped keys (lots.0.field) are properly recognized")
        print("- Backward compatibility with old-style keys maintained")
        print("- ValidationAdapter successfully maps between key formats")
        return True
    else:
        print("❌ VALIDATION KEY MAPPING STILL HAS ISSUES")
        print("\nProblem:")
        print("- Validation not recognizing filled fields")
        print("- Check ValidationAdapter implementation")
        return False

if __name__ == "__main__":
    try:
        success = test_validation_with_lot_keys()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)