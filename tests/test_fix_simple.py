#!/usr/bin/env python3
"""Simple test for the social criteria fix."""

import sys
sys.path.insert(0, '.')

# Mock streamlit session state
class MockSessionState:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def keys(self):
        return self.data.keys()

# Create mock session state
session_state = MockSessionState()

# Set up the user's scenario
session_state['selectionCriteria.price'] = True
session_state['selectionCriteria.priceRatio'] = 100.0

# Social criteria selected
session_state['selectionCriteria.socialCriteria'] = True

# Social sub-option 1: "Drugo" with description
session_state['selectionCriteria.socialCriteriaOptions.otherSocial'] = True
session_state['selectionCriteria.socialCriteriaOptions.otherSocialDescription'] = 'rad imeti krompir'
session_state['selectionCriteria.socialCriteriaOtherRatio'] = 50.0

# Social sub-option 2: "Drugo, imam predlog" with description  
session_state['selectionCriteria.socialCriteriaOptions.otherSocialCustom'] = True
session_state['selectionCriteria.socialCriteriaOptions.otherSocialCustomDescription'] = 'kakovost krompirja'
session_state['selectionCriteria.socialCriteriaCustomRatio'] = 70.0

print("=" * 60)
print("Testing Social Criteria Fix")
print("=" * 60)

print("\n1. Session State Setup:")
for key in sorted([k for k in session_state.keys() if 'criteria' in k.lower()]):
    val = session_state[key]
    if val and val != 0:
        print(f"   {key}: {val}")

from utils.validations import ValidationManager

validator = ValidationManager(session_state=session_state)

print("\n2. Testing _has_social_suboptions:")
has_social = validator._has_social_suboptions('selectionCriteria')
print(f"   Result: {has_social}")
print(f"   Expected: True")

print("\n3. Testing _get_selected_criteria:")
selected = validator._get_selected_criteria('selectionCriteria')
print("   Selected criteria:")
for crit, is_sel in selected.items():
    if is_sel:
        print(f"   - {crit}: {is_sel}")

print("\n4. Testing full validation:")
is_valid, errors = validator.validate_merila('selectionCriteria')

if is_valid:
    print("   ✅ VALIDATION PASSED!")
else:
    print("   ❌ Validation failed with errors:")
    for error in errors:
        print(f"      - {error}")

warnings = validator.get_warnings()
if warnings:
    print("\n   ⚠️ Warnings:")
    for warning in warnings:
        print(f"      - {warning}")

# Calculate total points
total_points = (
    session_state.get('selectionCriteria.priceRatio', 0) +
    session_state.get('selectionCriteria.socialCriteriaOtherRatio', 0) +
    session_state.get('selectionCriteria.socialCriteriaCustomRatio', 0)
)

print(f"\n5. Total points: {total_points} (100 + 50 + 70)")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)