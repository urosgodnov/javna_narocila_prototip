#!/usr/bin/env python3
"""Debug what's happening with inspection dates."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st

# Mock session with inspection dates as array
st.session_state.clear()

with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    st.session_state['schema'] = json.load(f)

# Set lot configuration
st.session_state['lot_mode'] = 'multiple'
st.session_state['lotsInfo.hasLots'] = True
st.session_state['lots'] = [{'name': 'Test Lot 1'}]
st.session_state['lot_names'] = ['Test Lot 1']

# Set inspection data as it would be in the form
st.session_state['lot_0.inspectionInfo.hasInspection'] = True

# Check how the data is stored - as an array or as individual keys?
# Try setting as individual keys (how form_renderer creates them)
st.session_state['lot_0.inspectionInfo.inspectionDates.0.date'] = '2024-12-15'
st.session_state['lot_0.inspectionInfo.inspectionDates.0.time'] = '10:00'
st.session_state['lot_0.inspectionInfo.inspectionDates.0.location'] = 'UKC Ljubljana'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.date'] = '2024-12-16'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.time'] = '14:00'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.location'] = 'UKC Ljubljana'

print("Session state keys with inspection:")
for key in sorted(st.session_state.keys()):
    if 'inspection' in key.lower():
        print(f"  {key}: {st.session_state[key]}")

# Now get form data
from utils.schema_utils import get_form_data_from_session

form_data = get_form_data_from_session()

print("\nForm data keys:")
for key in sorted(form_data.keys()):
    print(f"  {key}")

if 'lots' in form_data:
    print(f"\nLots array has {len(form_data['lots'])} items")
    for i, lot in enumerate(form_data['lots']):
        print(f"\n  Lot {i} keys:")
        if isinstance(lot, dict):
            for key in sorted(lot.keys()):
                print(f"    {key}")
                if key == 'inspectionInfo':
                    print(f"      inspectionInfo content: {lot[key]}")