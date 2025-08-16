#!/usr/bin/env python3
"""Test the social criteria validation fix."""

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
print("TESTING SOCIAL CRITERIA VALIDATION FIX")
print("="*60)

# Test 1: Social criteria with elderly employees sub-option and points
print("\n📋 Test 1: Social Criteria with Elderly Employees (20 points)")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.price': True,
    'selectionCriteria.priceRatio': '10',
    'selectionCriteria.socialCriteria': True,
    'selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare': True,
    'selectionCriteria.socialCriteriaElderlyRatio': '20'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Session state (relevant keys):")
print(f"  - price: True, priceRatio: 10")
print(f"  - socialCriteria: True")
print(f"  - elderlyEmployeesShare: True, elderlyRatio: 20")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
print(f"Warnings: {validator.get_warnings()}")

assert is_valid, "Should be valid with social criteria points and sub-option"
assert not any("ne smejo biti 0" in e for e in errors), "Should not have zero points error for social"
assert not any("vsaj eno možnost" in e for e in errors), "Should not have sub-option error"
print("✅ Social criteria with elderly employees works")

# Test 2: Social criteria with multiple sub-options
print("\n📋 Test 2: Social Criteria with Multiple Sub-options")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.socialCriteria': True,
    'selectionCriteria.socialCriteriaOptions.youngEmployeesShare': True,
    'selectionCriteria.socialCriteriaYoungRatio': '30',
    'selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare': True,
    'selectionCriteria.socialCriteriaElderlyRatio': '20',
    'selectionCriteria.socialCriteriaOptions.registeredStaffEmployed': True,
    'selectionCriteria.socialCriteriaStaffRatio': '50'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Total social points: 30 + 20 + 50 = 100")
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")

assert is_valid, "Should be valid with multiple social sub-options"
print("✅ Multiple social sub-options work")

# Test 3: Social criteria without sub-options (should error)
print("\n📋 Test 3: Social Criteria without Sub-options")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.socialCriteria': True,
    # No sub-options selected, no points assigned
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Valid: {is_valid}")
print(f"Errors: {errors}")

assert not is_valid, "Should be invalid without sub-options"
assert any("vsaj eno možnost" in e for e in errors), "Should have sub-option error"
print("✅ Correctly detects missing sub-options")

# Test 4: Test with general.selectionCriteria prefix
print("\n📋 Test 4: General Prefix Pattern")
print("-" * 40)

st.session_state.data = {
    'general.selectionCriteria.price': True,
    'general.selectionCriteria.priceRatio': '80',
    'general.selectionCriteria.socialCriteria': True,
    'general.selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare': True,
    'general.selectionCriteria.socialCriteriaElderlyRatio': '20'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
print(f"Warnings: {validator.get_warnings()}")

assert is_valid, "Should work with general prefix"
print("✅ General prefix pattern works")

# Test 5: Points only in ratio fields (no checkbox)
print("\n📋 Test 5: Points in Ratio Fields Counts as Sub-option")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.socialCriteria': True,
    # No checkbox for elderly, but has points
    'selectionCriteria.socialCriteriaElderlyRatio': '100'
}

validator = ValidationManager(schema, st.session_state)
is_valid, errors = validator.validate_merila('selectionCriteria')

print(f"Valid: {is_valid}")
print(f"Errors: {errors}")

assert is_valid, "Should be valid - points in ratio field counts as sub-option"
assert not any("vsaj eno možnost" in e for e in errors), "Should not have sub-option error"
print("✅ Points in ratio fields count as sub-option selection")

# Summary
print("\n" + "="*60)
print("SOCIAL CRITERIA FIX SUMMARY")
print("="*60)
print("✅ Social criteria with individual sub-option points - WORKS")
print("✅ Multiple social sub-options - WORKS")
print("✅ Missing sub-options detection - WORKS")
print("✅ General prefix pattern - WORKS")
print("✅ Points as sub-option indicator - WORKS")
print("\n🎉 SOCIAL CRITERIA VALIDATION FIXED!")
print("\nThe validation now correctly:")
print("• Sums points from individual social criteria ratio fields")
print("• Detects sub-options via checkboxes OR points > 0")
print("• Handles all key patterns (standard, general, lot-specific)")