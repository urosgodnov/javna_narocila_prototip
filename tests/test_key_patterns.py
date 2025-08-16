#!/usr/bin/env python3
"""Test the fixed validation with different key patterns."""

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
        return self.data.get(key, default)
    
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
print("TESTING KEY PATTERN FIXES")
print("="*60)

# Test 1: Standard pattern (selectionCriteria.price)
print("\n📋 Test 1: Standard Pattern")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.price': True,
    'selectionCriteria.priceRatio': '0'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Session state: {st.session_state.data}")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
assert not is_valid, "Should be invalid with 0 points"
assert any("ne smejo biti 0" in e for e in errors), "Should have zero points error"
print("✅ Standard pattern works")

# Test 2: General lot pattern (general.selectionCriteria.price)
print("\n📋 Test 2: General Lot Pattern")
print("-" * 40)

st.session_state.data = {
    'general.selectionCriteria.price': True,
    'general.selectionCriteria.priceRatio': '0'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Session state: {st.session_state.data}")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
assert not is_valid, "Should be invalid with 0 points"
assert any("ne smejo biti 0" in e for e in errors), "Should have zero points error"
print("✅ General lot pattern works")

# Test 3: Specific lot pattern (lot_1_selectionCriteria.price)
print("\n📋 Test 3: Specific Lot Pattern")
print("-" * 40)

st.session_state.data = {
    'lot_1_selectionCriteria.price': True,
    'lot_1_selectionCriteria.priceRatio': '0'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Session state: {st.session_state.data}")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
assert not is_valid, "Should be invalid with 0 points"
assert any("ne smejo biti 0" in e for e in errors), "Should have zero points error"
print("✅ Specific lot pattern works")

# Test 4: Calling with prefixed step_key
print("\n📋 Test 4: Prefixed Step Key")
print("-" * 40)

st.session_state.data = {
    'general.selectionCriteria.price': True,
    'general.selectionCriteria.priceRatio': '50',
    'general.selectionCriteria.longerWarranty': True,
    'general.selectionCriteria.longerWarrantyRatio': '50'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('general.selectionCriteria')

print(f"Session state: {st.session_state.data}")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
assert is_valid, "Should be valid with proper points"
print("✅ Prefixed step key works")

# Test 5: Mixed patterns (shouldn't happen but test robustness)
print("\n📋 Test 5: Mixed Patterns")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.price': False,
    'general.selectionCriteria.price': True,  # This should be found
    'general.selectionCriteria.priceRatio': '100'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Session state: {st.session_state.data}")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
assert is_valid, "Should find the general.selectionCriteria.price"
print("✅ Mixed patterns handled correctly")

# Summary
print("\n" + "="*60)
print("KEY PATTERN FIX SUMMARY")
print("="*60)
print("✅ Standard pattern (selectionCriteria.price) - WORKS")
print("✅ General lot pattern (general.selectionCriteria.price) - WORKS")
print("✅ Specific lot pattern (lot_1_selectionCriteria.price) - WORKS")
print("✅ Prefixed step key (general.selectionCriteria) - WORKS")
print("✅ Mixed patterns - HANDLED CORRECTLY")
print("\n🎉 KEY PATTERN ISSUE FIXED!")
print("\nThe validation now correctly handles:")
print("• Standard keys: selectionCriteria.price")
print("• General lot keys: general.selectionCriteria.price")
print("• Specific lot keys: lot_1_selectionCriteria.price")
print("• Prefixed step keys passed to validate_merila()")