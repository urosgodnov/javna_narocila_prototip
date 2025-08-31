#!/usr/bin/env python3
"""Test complete save/load cycle with unified lot architecture."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from ui.controllers.form_controller import FormController
from utils.data_persistence_adapter import DataPersistenceAdapter

def test_save_load_cycle():
    """Test that data survives a complete save/load cycle."""
    
    print("Testing Save/Load Cycle with Unified Lot Architecture")
    print("=" * 60)
    
    # Initialize
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    controller = FormController()
    adapter = DataPersistenceAdapter()
    
    # Test 1: Single lot save/load
    print("\n1. Testing single lot save/load...")
    
    # Set up test data
    st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
    st.session_state['current_lot_index'] = 0
    st.session_state['current_step'] = 5
    st.session_state['completed_steps'] = [0, 1, 2, 3, 4]
    
    # Add form data in new format
    st.session_state['lots.0.clientInfo.singleClientName'] = 'Osnovna šola Test'
    st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Testna ulica 123'
    st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '1000 Ljubljana'
    st.session_state['lots.0.legalBasis.lawReference'] = 'ZJN-3'
    st.session_state['lots.0.technicalSpecs.description'] = 'Tehnične specifikacije'
    
    # Extract data
    form_data = adapter.extract_form_data_from_session()
    
    print(f"  Extracted data with {len(form_data['lots'])} lot(s)")
    print(f"  First lot name: {form_data['lots'][0]['name']}")
    print(f"  Data fields: {len(form_data['lots'][0]['data'])} fields")
    
    # Save to file
    filename = 'test_save_load.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(form_data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Saved to {filename}")
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    print("  ✓ Cleared session state")
    
    # Load back
    with open(filename, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    adapter.load_form_data_to_session(loaded_data)
    
    print("  ✓ Loaded data back to session")
    
    # Verify data
    test_passed = True
    expected_values = {
        'lots.0.clientInfo.singleClientName': 'Osnovna šola Test',
        'lots.0.clientInfo.singleClientStreetAddress': 'Testna ulica 123',
        'lots.0.clientInfo.singleClientPostalCode': '1000 Ljubljana',
        'lots.0.legalBasis.lawReference': 'ZJN-3',
        'lots.0.technicalSpecs.description': 'Tehnične specifikacije'
    }
    
    for key, expected in expected_values.items():
        actual = st.session_state.get(key)
        if actual != expected:
            print(f"  ✗ {key}: expected '{expected}', got '{actual}'")
            test_passed = False
    
    if test_passed:
        print("  ✅ All data correctly restored!")
    
    # Test 2: Multiple lots with pre-lot data sync
    print("\n2. Testing multiple lots with pre-lot data sync...")
    
    # Clear and set up multiple lots
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.session_state['lots'] = [
        {'name': 'Splošni sklop', 'index': 0},
        {'name': 'Tehnični sklop', 'index': 1},
        {'name': 'Programski sklop', 'index': 2}
    ]
    
    # Set pre-lot data (should apply to ALL lots)
    pre_lot_data = {
        'clientInfo.singleClientName': 'Skupni naročnik',
        'legalBasis.lawReference': 'ZJN-3',
        'projectInfo.projectTitle': 'Skupni projekt'
    }
    
    # Set data for lot 0
    for field, value in pre_lot_data.items():
        st.session_state[f'lots.0.{field}'] = value
    
    # Sync pre-lot data
    adapter.ensure_pre_lot_data_synced(['clientInfo', 'legalBasis', 'projectInfo'])
    
    # Add lot-specific data
    st.session_state['lots.0.technicalSpecs.specific'] = 'Lot 0 specific'
    st.session_state['lots.1.technicalSpecs.specific'] = 'Lot 1 specific'
    st.session_state['lots.2.technicalSpecs.specific'] = 'Lot 2 specific'
    
    # Extract and save
    form_data = adapter.extract_form_data_from_session()
    
    print(f"  Extracted data with {len(form_data['lots'])} lots")
    
    # Verify pre-lot data is in all lots
    sync_test_passed = True
    for i in range(3):
        lot_data = form_data['lots'][i]['data']
        for field, expected in pre_lot_data.items():
            if lot_data.get(field) != expected:
                print(f"  ✗ Lot {i} missing synced field {field}")
                sync_test_passed = False
    
    if sync_test_passed:
        print("  ✅ Pre-lot data synced to all lots!")
    
    # Verify lot-specific data is different
    specific_values = [
        form_data['lots'][i]['data'].get('technicalSpecs.specific')
        for i in range(3)
    ]
    
    if len(set(specific_values)) == 3:
        print("  ✅ Lot-specific data remains separate!")
    else:
        print("  ✗ Lot-specific data not properly separated")
        test_passed = False
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass
    
    print("\n" + "=" * 60)
    if test_passed and sync_test_passed:
        print("✅ SAVE/LOAD CYCLE TEST PASSED!")
        return True
    else:
        print("❌ SAVE/LOAD CYCLE TEST FAILED")
        return False


if __name__ == "__main__":
    try:
        success = test_save_load_cycle()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)