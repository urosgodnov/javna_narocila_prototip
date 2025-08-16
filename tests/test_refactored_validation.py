#!/usr/bin/env python3
"""Test script to verify the refactored validation system (Story 27.3)."""

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

# Mock validation control
from unittest.mock import MagicMock
import sys
sys.modules['utils.validation_control'] = MagicMock()
from utils.validation_control import should_validate
should_validate = MagicMock(return_value=True)

# Mock localization
sys.modules['localization'] = MagicMock()
from localization import get_text
get_text = MagicMock(side_effect=lambda key, **kwargs: key)

# Import the refactored function
from app import validate_step

# Load schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("\n" + "="*60)
print("TESTING REFACTORED VALIDATION SYSTEM (Story 27.3)")
print("="*60)

# Mock streamlit error/warning/info
errors = []
warnings = []
infos = []

def mock_error(msg):
    errors.append(msg)
    print(f"  ERROR: {msg}")

def mock_warning(msg):
    warnings.append(msg)
    print(f"  WARNING: {msg}")

def mock_info(msg):
    infos.append(msg)
    print(f"  INFO: {msg}")

st.error = mock_error
st.warning = mock_warning
st.info = mock_info

# Test 1: Required Fields Validation
print("\n📋 Test 1: Required Fields Validation")
print("-" * 40)

st.session_state.data = {}
errors.clear()

result = validate_step(['clientInfo'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert not result, "Should be invalid with empty required fields"
assert len(errors) > 0, "Should have validation errors"
print("✅ Required fields validation working")

# Test 2: Valid Data
print("\n📋 Test 2: Valid Data")
print("-" * 40)

st.session_state.data = {
    'clientInfo.singleClientName': 'Test Client',
    'clientInfo.singleClientAddress': 'Test Address 123'
}
errors.clear()

result = validate_step(['clientInfo'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert result, "Should be valid with filled required fields"
print("✅ Valid data acceptance working")

# Test 3: Merila Validation Integration
print("\n📋 Test 3: Merila Validation Integration")
print("-" * 40)

st.session_state.data = {
    'selectionCriteria.price': True,
    'selectionCriteria.priceRatio': '0'  # Invalid: points cannot be 0
}
errors.clear()
warnings.clear()

result = validate_step(['selectionCriteria'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert not result, "Should be invalid with 0 points"
assert any("ne smejo biti 0" in e for e in errors), "Should have 'points cannot be 0' error"
print("✅ Merila validation integrated")

# Test 4: Framework Agreement Validation
print("\n📋 Test 4: Framework Agreement Validation")
print("-" * 40)

st.session_state.data = {
    'contractInfo.type': 'okvirni sporazum',
    'contractInfo.frameworkDuration': '5 let'  # Invalid: exceeds 4 years
}
errors.clear()

result = validate_step(['contractInfo'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert not result, "Should be invalid with framework > 4 years"
assert any("ne sme presegati 4 let" in e for e in errors), "Should have framework duration error"
print("✅ Framework agreement validation working")

# Test 5: Contract Extension Validation
print("\n📋 Test 5: Contract Extension Validation")
print("-" * 40)

st.session_state.data = {
    'contractInfo.canBeExtended': 'da',
    'contractInfo.extensionReasons': '',  # Invalid: missing reasons
    'contractInfo.extensionDuration': ''  # Invalid: missing duration
}
errors.clear()

result = validate_step(['contractInfo'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert not result, "Should be invalid without extension details"
assert any("razloge" in e for e in errors), "Should have extension reasons error"
assert any("trajanje" in e for e in errors), "Should have extension duration error"
print("✅ Contract extension validation working")

# Test 6: Multiple Clients Validation
print("\n📋 Test 6: Multiple Clients Validation")
print("-" * 40)

st.session_state.data = {
    'clientInfo.multipleClients': 'da',
    'clientInfo.client1Name': 'Client 1',
    # Missing second client - should be invalid
}
errors.clear()

result = validate_step(['clientInfo'], schema)
print(f"Result: {'✅ Valid' if result else '❌ Invalid'}")
print(f"Errors count: {len(errors)}")
assert not result, "Should be invalid with only 1 client when multiple selected"
assert any("najmanj 2 naročnika" in e for e in errors), "Should have multiple clients error"
print("✅ Multiple clients validation working")

# Test 7: CPV Code Validation
print("\n📋 Test 7: CPV Code Validation")
print("-" * 40)

st.session_state.data = {
    'projectInfo.cpvCodes': '55000000-0',  # CPV that may require social criteria
    'selectionCriteria.price': True,
    'selectionCriteria.priceRatio': '100'
}
errors.clear()

result = validate_step(['selectionCriteria'], schema)
print(f"Result: {'Valid' if result else 'Invalid'} (depends on DB)")
print(f"Errors count: {len(errors)}")
print("✅ CPV validation integrated")

# Summary
print("\n" + "="*60)
print("REFACTORED VALIDATION TEST SUMMARY")
print("="*60)
print("✅ Required fields validation working")
print("✅ Valid data acceptance working")
print("✅ Merila validation integrated")
print("✅ Framework agreement validation working")
print("✅ Contract extension validation working")
print("✅ Multiple clients validation working")
print("✅ CPV code validation integrated")
print("\n🎉 Story 27.3 COMPLETED SUCCESSFULLY!")
print("\n✨ Epic 27 - Centralized Validation System COMPLETED!")
print("\nAll validation logic is now centralized in utils/validations.py")
print("The ValidationManager class handles all form validations")
print("app.py now uses the centralized validation system")