#!/usr/bin/env python3
"""Test complete round trip for inspection dates."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st
from utils.schema_utils import get_form_data_from_session

# Start fresh
st.session_state.clear()

with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    st.session_state['schema'] = json.load(f)

# Set lot configuration
st.session_state['lot_mode'] = 'multiple'
st.session_state['lotsInfo.hasLots'] = True
st.session_state['lots'] = [{'name': 'Operacijske mize'}]
st.session_state['lot_names'] = ['Operacijske mize']

# Set inspection data as individual keys (how form creates them)
st.session_state['lot_0.inspectionInfo.hasInspection'] = True
st.session_state['lot_0.inspectionInfo.inspectionDates.0.date'] = '2024-12-15'
st.session_state['lot_0.inspectionInfo.inspectionDates.0.time'] = '10:00'
st.session_state['lot_0.inspectionInfo.inspectionDates.0.location'] = 'UKC Ljubljana, Zaloška 2'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.date'] = '2024-12-16'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.time'] = '14:00'
st.session_state['lot_0.inspectionInfo.inspectionDates.1.location'] = 'UKC Ljubljana, Zaloška 2'

print("=" * 60)
print("STEP 1: INITIAL DATA IN SESSION")
print("=" * 60)
inspection_keys = sorted([k for k in st.session_state.keys() if 'inspection' in k.lower()])
for key in inspection_keys:
    print(f"  {key}: {st.session_state[key]}")

# Get form data (simulating save)
form_data = get_form_data_from_session()

print("\n" + "=" * 60)
print("STEP 2: FORM DATA (WHAT GETS SAVED)")
print("=" * 60)
if 'lots' in form_data and len(form_data['lots']) > 0:
    lot = form_data['lots'][0]
    if 'inspectionInfo' in lot:
        print("Inspection info in lot 0:")
        print(json.dumps(lot['inspectionInfo'], indent=2, ensure_ascii=False))

# Clear session (simulating new edit session)
for key in list(st.session_state.keys()):
    if key != 'schema':
        del st.session_state[key]

print("\n" + "=" * 60)
print("STEP 3: LOADING BACK TO SESSION")
print("=" * 60)

# Load the form_data back (simulating load_procurement_to_form)
for key, value in form_data.items():
    if key == 'lots' and isinstance(value, list):
        # Process lots array - convert to lot_X fields
        for i, lot in enumerate(value):
            if isinstance(lot, dict):
                def set_lot_fields(lot_data, prefix):
                    for field_key, field_value in lot_data.items():
                        full_key = f'{prefix}.{field_key}'
                        if isinstance(field_value, dict):
                            set_lot_fields(field_value, full_key)
                        elif isinstance(field_value, list):
                            st.session_state[full_key] = field_value
                            # Also set individual array items
                            for j, item in enumerate(field_value):
                                if isinstance(item, dict):
                                    for item_key, item_val in item.items():
                                        item_full_key = f"{full_key}.{j}.{item_key}"
                                        st.session_state[item_full_key] = item_val
                                        print(f"  Setting: {item_full_key} = {item_val}")
                                else:
                                    item_key = f"{full_key}[{j}]"
                                    st.session_state[item_key] = item
                        else:
                            st.session_state[full_key] = field_value
                            if 'inspection' in full_key.lower():
                                print(f"  Setting: {full_key} = {field_value}")
                set_lot_fields(lot, f'lot_{i}')
    else:
        st.session_state[key] = value

print("\n" + "=" * 60)
print("STEP 4: FINAL STATE (READY FOR FORM)")
print("=" * 60)
inspection_keys = sorted([k for k in st.session_state.keys() if 'inspection' in k.lower()])
for key in inspection_keys:
    value = st.session_state[key]
    if isinstance(value, list):
        print(f"  {key}: {len(value)} items")
    else:
        print(f"  {key}: {value}")

print("\n✅ COMPLETE ROUND TRIP TEST:")
original_date = '2024-12-15'
final_date = st.session_state.get('lot_0.inspectionInfo.inspectionDates.0.date', 'NOT FOUND')
if final_date == original_date:
    print(f"  SUCCESS: Date preserved ({original_date})")
else:
    print(f"  FAILED: Expected {original_date}, got {final_date}")