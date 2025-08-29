#!/usr/bin/env python3
"""Test the real-world scenario with formatted numbers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st
from utils.schema_utils import get_form_data_from_session
from ui.form_renderer import parse_formatted_number

# Mock session state simulating ACTUAL user input
class RealWorldSessionState(dict):
    def __init__(self):
        super().__init__()
        # Load the schema
        with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
            self['schema'] = json.load(f)
        
        self['lot_mode'] = 'none'
        self['projectInfo.projectName'] = 'Nove operacijske hale'
        self['orderType.type'] = 'gradnje'
        
        # CRITICAL: This is what actually happens when user types in form
        # The widget stores the formatted value
        self['widget_orderType.estimatedValue_text'] = '1.500.000,00'
        # The session key might still have old value if not properly updated
        self['orderType.estimatedValue'] = 0.0  # This is the bug!
        
        # Let's also check general prefix version
        self['general.orderType.estimatedValue'] = 0.0
        self['widget_general.orderType.estimatedValue_text'] = '1.500.000,00'

# Set mock session state
st.session_state = RealWorldSessionState()

print("=" * 80)
print("REAL-WORLD TEST: User types '1.500.000,00' in form")
print("=" * 80)

# Test 1: Parse the formatted number
formatted = st.session_state.get('widget_orderType.estimatedValue_text')
parsed = parse_formatted_number(formatted)
print(f"\n1. Widget value: '{formatted}'")
print(f"   Parsed to: {parsed}")

# Test 2: What does get_form_data_from_session see?
print("\n2. Getting form data (BEFORE fix)...")
form_data = get_form_data_from_session()

estimated_before = form_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
print(f"   estimatedValue in form_data: {estimated_before}")

# Test 3: Simulate what SHOULD happen in form_renderer.py
print("\n3. Simulating the FIX in form_renderer.py...")
# When rendering number field, it should update session from widget
widget_key = 'widget_orderType.estimatedValue_text'
session_key = 'orderType.estimatedValue'

if widget_key in st.session_state:
    widget_value = st.session_state[widget_key]
    parsed_value = parse_formatted_number(widget_value)
    st.session_state[session_key] = parsed_value
    print(f"   Updated {session_key} = {parsed_value}")

# Test 4: Check again after fix
print("\n4. Getting form data (AFTER fix)...")
form_data_fixed = get_form_data_from_session()
estimated_after = form_data_fixed.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
print(f"   estimatedValue in form_data: {estimated_after}")

print("\n" + "=" * 80)
print("CONCLUSION:")
if estimated_after == 1500000.0:
    print("✅ Fix works! Value is correctly saved.")
else:
    print(f"❌ Still broken! Got {estimated_after} instead of 1500000.0")
    
# Check all session keys with estimatedValue
print("\n" + "=" * 80)
print("DEBUG: All estimatedValue-related keys in session:")
for key in st.session_state.keys():
    if 'estimatedvalue' in key.lower():
        print(f"  {key}: {st.session_state[key]}")