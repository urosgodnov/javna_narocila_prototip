#!/usr/bin/env python3
"""Debug why get_form_data_from_session doesn't see the value."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st

# Mock session state
class DebugSessionState(dict):
    def __init__(self):
        super().__init__()
        with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
            self['schema'] = json.load(f)
        
        self['lot_mode'] = 'none'
        self['orderType.estimatedValue'] = 1500000.0  # This SHOULD be found
        self['orderType.type'] = 'blago'

st.session_state = DebugSessionState()

# Check what schema properties are
schema_properties = st.session_state.get('schema', {}).get('properties', {})
print("Schema top-level properties:")
for prop in schema_properties.keys():
    print(f"  - {prop}")

print("\nChecking 'orderType.estimatedValue':")
key = 'orderType.estimatedValue'
top_level_key = key.split('.')[0]
print(f"  Top level key: '{top_level_key}'")
print(f"  Is in schema properties? {top_level_key in schema_properties}")

# Now test the actual function
from utils.schema_utils import get_form_data_from_session
form_data = get_form_data_from_session()

print("\nResult from get_form_data_from_session:")
print(json.dumps(form_data, indent=2, ensure_ascii=False))