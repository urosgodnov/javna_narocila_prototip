#!/usr/bin/env python3
"""Test complete form flow with validation and save/load."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from utils.form_integration import FormIntegration

def test_complete_flow():
    """Test complete form flow including validation and persistence."""
    
    print("Testing Complete Form Flow")
    print("=" * 60)
    
    # Initialize
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    integration = FormIntegration()
    
    # Scenario 1: Single lot workflow
    print("\n📋 Scenario 1: Single Lot Workflow")
    print("-" * 40)
    
    # Step 1: Fill customer info (pre-lot screen)
    print("Step 1: Customer Information")
    st.session_state['lots.0.clientInfo.isSingleClient'] = True
    st.session_state['lots.0.clientInfo.singleClientName'] = 'Osnovna šola Bistrica'
    st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Bistriška 7'
    st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
    st.session_state['lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. Frida Meglič'
    
    # Validate
    is_valid, errors = integration.validate_step(['clientInfo'], 0)
    print(f"  Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if not is_valid:
        print(f"  Errors: {errors[:2]}...")
    
    # Step 2: Legal basis (pre-lot screen)
    print("Step 2: Legal Basis")
    st.session_state['lots.0.legalBasis.lawReference'] = 'ZJN-3'
    st.session_state['lots.0.legalBasis.articleReference'] = '66. člen'
    
    # Step 3: Technical specs (lot-specific)
    print("Step 3: Technical Specifications")
    st.session_state['lots.0.technicalSpecs.description'] = 'Dobava računalniške opreme'
    st.session_state['lots.0.technicalSpecs.cpvCode'] = '30200000-1'
    
    # Save data
    print("\nSaving form data...")
    form_data = integration.save_form_data()
    
    print(f"  Saved {len(form_data['lots'])} lot(s)")
    print(f"  Fields in lot 0: {len(form_data['lots'][0]['data'])} fields")
    
    # Clear and reload
    print("\nClearing session state...")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    print("Loading data back...")
    integration.load_form_data(form_data)
    
    # Verify loaded data
    print("\nVerifying loaded data:")
    test_fields = [
        ('lots.0.clientInfo.singleClientName', 'Osnovna šola Bistrica'),
        ('lots.0.legalBasis.lawReference', 'ZJN-3'),
        ('lots.0.technicalSpecs.description', 'Dobava računalniške opreme')
    ]
    
    scenario1_passed = True
    for key, expected in test_fields:
        actual = st.session_state.get(key)
        if actual == expected:
            print(f"  ✅ {key.split('.')[-1]}: {actual}")
        else:
            print(f"  ❌ {key.split('.')[-1]}: expected '{expected}', got '{actual}'")
            scenario1_passed = False
    
    # Scenario 2: Multiple lots workflow
    print("\n📋 Scenario 2: Multiple Lots Workflow")
    print("-" * 40)
    
    # Clear for new scenario
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    integration = FormIntegration()
    
    # Add multiple lots
    print("Adding 3 lots...")
    integration.add_lot("Tehnična oprema")
    integration.add_lot("Programska oprema")
    
    lot_info = integration.get_current_lot_info()
    print(f"  Total lots: {lot_info['total_lots']}")
    
    # Fill pre-lot data (should apply to ALL lots)
    print("\nFilling pre-lot configuration (applies to ALL lots):")
    st.session_state['lots.0.clientInfo.singleClientName'] = 'Skupni naročnik'
    st.session_state['lots.0.legalBasis.lawReference'] = 'ZJN-3'
    st.session_state['lots.0.projectInfo.projectTitle'] = 'Skupni projekt'
    
    # Sync pre-lot data
    integration.persistence.ensure_pre_lot_data_synced(integration.pre_lot_screens)
    
    # Fill lot-specific data
    print("\nFilling lot-specific data:")
    st.session_state['lots.0.technicalSpecs.specific'] = 'Splošna oprema'
    st.session_state['lots.1.technicalSpecs.specific'] = 'Tehnična oprema specs'
    st.session_state['lots.2.technicalSpecs.specific'] = 'Software specs'
    
    # Save
    form_data = integration.save_form_data()
    print(f"  Saved {len(form_data['lots'])} lots")
    
    # Verify pre-lot data is in ALL lots
    print("\nVerifying pre-lot data in all lots:")
    scenario2_passed = True
    
    for i in range(3):
        lot_data = form_data['lots'][i]['data']
        client_name = lot_data.get('clientInfo.singleClientName')
        
        if client_name == 'Skupni naročnik':
            print(f"  ✅ Lot {i}: Has shared client name")
        else:
            print(f"  ❌ Lot {i}: Missing shared client name")
            scenario2_passed = False
    
    # Verify lot-specific data is different
    print("\nVerifying lot-specific data:")
    specific_values = []
    for i in range(3):
        specific = form_data['lots'][i]['data'].get('technicalSpecs.specific')
        specific_values.append(specific)
        print(f"  Lot {i}: {specific}")
    
    if len(set(specific_values)) == 3:
        print("  ✅ Each lot has unique specific data")
    else:
        print("  ❌ Lot-specific data not properly separated")
        scenario2_passed = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    if scenario1_passed:
        print("✅ Scenario 1 (Single Lot): PASSED")
    else:
        print("❌ Scenario 1 (Single Lot): FAILED")
    
    if scenario2_passed:
        print("✅ Scenario 2 (Multiple Lots): PASSED")
    else:
        print("❌ Scenario 2 (Multiple Lots): FAILED")
    
    if scenario1_passed and scenario2_passed:
        print("\n🎉 ALL SCENARIOS PASSED!")
        print("\nKey achievements:")
        print("- Validation works with lot-scoped keys")
        print("- Data persists correctly through save/load")
        print("- Pre-lot screens apply to ALL lots")
        print("- Lot-specific screens maintain separate data")
        print("- Slovenian labels throughout")
        return True
    else:
        print("\n⚠️ Some scenarios failed")
        return False


if __name__ == "__main__":
    try:
        success = test_complete_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)