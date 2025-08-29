#!/usr/bin/env python3
"""Find all time objects in session state."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import streamlit as st
from datetime import date, time, datetime

# Mock session
st.session_state.clear()

# Add some test data with time objects
st.session_state['test_time'] = time(10, 30)
st.session_state['test_date'] = date.today()
st.session_state['test_string'] = "10:30"
st.session_state['nested.time'] = time(14, 0)

print("Session state contents:")
print("-" * 40)

# Find all time/date objects
problematic_keys = []
for key, value in st.session_state.items():
    if isinstance(value, (date, time, datetime)):
        print(f"❌ {key}: {value} (type: {type(value).__name__})")
        problematic_keys.append(key)
    else:
        print(f"✅ {key}: {value} (type: {type(value).__name__})")

print("\n" + "=" * 40)
print("Testing JSON serialization:")
print("=" * 40)

# Try to serialize
try:
    json_str = json.dumps(dict(st.session_state))
    print("✅ JSON serialization successful")
except Exception as e:
    print(f"❌ JSON serialization failed: {e}")
    
    # Find the exact problematic key
    for key, value in st.session_state.items():
        try:
            json.dumps({key: value})
        except:
            print(f"   Problem key: {key} = {value} (type: {type(value).__name__})")