#!/usr/bin/env python3
"""Test saving and loading inspection dates."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st
from datetime import datetime, date
from utils.schema_utils import get_form_data_from_session
from database import update_procurement

# Mock session with inspection dates
st.session_state.clear()

with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    st.session_state['schema'] = json.load(f)

# Basic procurement info
st.session_state['edit_mode'] = True
st.session_state['editing_procurement_id'] = 8
st.session_state['lot_mode'] = 'multiple'
st.session_state['num_lots'] = 2
st.session_state['lotsInfo.hasLots'] = True
st.session_state['lot_names'] = ['Operacijske mize', 'Oprema za operacijske mize']

# Add inspection info for lot 0
st.session_state['lot_0.inspectionInfo.hasInspection'] = True
st.session_state['lot_0.inspectionInfo.inspectionDates'] = [
    {
        'date': '2024-12-15',
        'time': '10:00',
        'location': 'UKC Ljubljana, Zaloška 2',
        'contactPerson': 'Janez Novak',
        'notes': 'Obvezna prisotnost'
    },
    {
        'date': '2024-12-16', 
        'time': '14:00',
        'location': 'UKC Ljubljana, Zaloška 2',
        'contactPerson': 'Marija Kovač',
        'notes': 'Dodatni termin'
    }
]

# Add inspection info for lot 1
st.session_state['lot_1.inspectionInfo.hasInspection'] = True
st.session_state['lot_1.inspectionInfo.inspectionDates'] = [
    {
        'date': '2024-12-17',
        'time': '09:00',
        'location': 'UKC Ljubljana, Zaloška 2',
        'contactPerson': 'Peter Kranjc',
        'notes': ''
    }
]

print("=" * 60)
print("SAVING INSPECTION DATES")
print("=" * 60)

# Get form data
form_data = get_form_data_from_session()

# Check what's in form_data
print("\nInspection dates in form_data:")
for key in sorted(form_data.keys()):
    if 'inspection' in key.lower():
        print(f"  {key}: {form_data[key]}")

# Check lots array
if 'lots' in form_data:
    for i, lot in enumerate(form_data['lots']):
        if isinstance(lot, dict) and 'inspectionInfo' in lot:
            print(f"\nLot {i} inspection info:")
            print(json.dumps(lot['inspectionInfo'], indent=2, ensure_ascii=False))

# Now test loading back
print("\n" + "=" * 60)
print("LOADING BACK TO SESSION")
print("=" * 60)

# Clear session
for key in list(st.session_state.keys()):
    if key != 'schema':
        del st.session_state[key]

# Simulate loading the form_data back
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
                                else:
                                    item_key = f"{full_key}[{j}]"
                                    st.session_state[item_key] = item
                        else:
                            st.session_state[full_key] = field_value
                set_lot_fields(lot, f'lot_{i}')
    else:
        st.session_state[key] = value

print("\nInspection dates in session after loading:")
for key in sorted(st.session_state.keys()):
    if 'inspection' in key.lower():
        value = st.session_state[key]
        if isinstance(value, list) and len(value) > 0:
            print(f"  {key}: {len(value)} dates")
            for item in value:
                if isinstance(item, dict):
                    print(f"    - {item.get('date', 'no date')} at {item.get('time', 'no time')}")
        else:
            print(f"  {key}: {value}")