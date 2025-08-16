#!/usr/bin/env python3
"""Debug script to understand validation key issues."""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit session state
class MockSessionState:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=''):
        result = self.data.get(key, default)
        print(f"  Session get: '{key}' -> '{result}'")
        return result
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data.get(key, '')

# Mock streamlit
import streamlit as st
st.session_state = MockSessionState()

# Import the validation manager
from utils.validations import ValidationManager

# Load schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("\n" + "="*60)
print("DEBUG: Validation Key Structure")
print("="*60)

# Simulate selecting price with 0 points
print("\n1. Setting up session state with price selected:")
st.session_state.data = {
    'selectionCriteria.price': True,
    'selectionCriteria.priceRatio': '0'
}
print(f"  Session state: {st.session_state.data}")

print("\n2. Creating validator and running validate_merila:")
validator = ValidationManager(schema, st.session_state)

print("\n3. Checking _get_selected_criteria:")
criteria = validator._get_selected_criteria('selectionCriteria')
print(f"  Selected criteria: {criteria}")

print("\n4. Running full validation:")
is_valid, errors = validator.validate_merila()
print(f"  Valid: {is_valid}")
print(f"  Errors: {errors}")

print("\n5. Checking expanded keys from validate_step:")
expanded = validator._expand_step_keys(['selectionCriteria'])
print(f"  Expanded keys (first 5): {expanded[:5]}")

print("\n6. Testing with different key patterns:")
# Try different key patterns that might be used in the actual form
test_patterns = [
    'selectionCriteria.price',
    'general.selectionCriteria.price', 
    'price',
    'lot_1_selectionCriteria.price'
]

for pattern in test_patterns:
    st.session_state.data = {pattern: True}
    print(f"\n  Testing pattern: {pattern}")
    criteria = validator._get_selected_criteria('selectionCriteria')
    print(f"    Result: price={criteria.get('price', False)}")