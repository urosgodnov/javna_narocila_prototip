#!/usr/bin/env python3
"""Test how session data is converted to form data for saving."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st
from utils.schema_utils import get_form_data_from_session

# Mock session state simulating lot mode with values
class MockLotSession(dict):
    def __init__(self):
        super().__init__()
        with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
            self['schema'] = json.load(f)
        
        # Lot configuration
        self['lot_mode'] = 'multiple'
        self['num_lots'] = 2
        self['lotsInfo.hasLots'] = True
        self['lots'] = [
            {'name': 'Operacijske mize'},
            {'name': 'Oprema za operacijske mize'}
        ]
        
        # Lot-specific values as they would be in form
        self['lot_0.orderType.estimatedValue'] = 1000000.0
        self['lot_0.orderType.type'] = 'blago'
        
        self['lot_1.orderType.estimatedValue'] = 500000.0
        self['lot_1.orderType.type'] = 'blago'
        
        # Cofinancers for lot 0
        self['lot_0.orderType.isCofinanced'] = True
        self['lot_0.orderType.cofinancers'] = [
            {
                'cofinancerName': 'EU Funds for Lot 0',
                'programName': 'Program A'
            }
        ]
        
        # General data
        self['projectInfo.projectName'] = 'Test Lot Project'

st.session_state = MockLotSession()

print("=" * 80)
print("TESTING SESSION TO FORM DATA CONVERSION FOR LOTS")
print("=" * 80)

print("\nSession state (lot-specific fields):")
for key in sorted(st.session_state.keys()):
    if key.startswith('lot_'):
        print(f"  {key}: {st.session_state[key]}")

form_data = get_form_data_from_session()

print("\n" + "=" * 80)
print("RESULT form_data:")
print("=" * 80)
print(json.dumps(form_data, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("CHECKING CRITICAL VALUES:")
print("=" * 80)

# Check if lot_X fields are preserved
lot_0_value = form_data.get('lot_0.orderType.estimatedValue', 'NOT FOUND')
lot_1_value = form_data.get('lot_1.orderType.estimatedValue', 'NOT FOUND')

print(f"lot_0.orderType.estimatedValue: {lot_0_value}")
print(f"lot_1.orderType.estimatedValue: {lot_1_value}")

if lot_0_value == 'NOT FOUND':
    print("\n❌ ERROR: lot_0 values NOT in form_data!")
else:
    print(f"\n✅ lot_0 value found: {lot_0_value}")

# Check lots array
if 'lots' in form_data:
    print(f"\nLots array has {len(form_data['lots'])} items")
    for i, lot in enumerate(form_data['lots']):
        if isinstance(lot, dict):
            print(f"  Lot {i}: {lot}")