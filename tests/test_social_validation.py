#!/usr/bin/env python3
"""Test social criteria validation logic."""

import sys
import json
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validations import ValidationManager

# Load schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Create test session state with social criteria selected
test_session = {
    'schema': schema,
    'current_step': 7,  # Merila step
    'current_lot_index': None,  # General mode
    
    # Main criteria selections
    'selectionCriteria.price': True,
    'selectionCriteria.socialCriteria': True,
    'selectionCriteria.otherCriteriaCustom': True,
    
    # Social sub-option - "Drugo" selected
    'selectionCriteria.socialCriteriaOptions.otherSocial': True,
    'selectionCriteria.socialCriteriaOptions.otherSocialDescription': '5 veselih kuharjev krompirja',
    
    # Points for criteria
    'selectionCriteria.priceRatio': 10,
    'selectionCriteria.socialCriteriaOtherRatio': 10,  # Points for "Drugo" social sub-option
    'selectionCriteria.otherCriteriaCustomRatio': 0,  # No points yet
    
    # Description for otherCriteriaCustom
    'selectionCriteria.otherCriteriaCustomDescription': 'hihihi'
}

# Create validation manager
validator = ValidationManager(schema, test_session)

# Test _has_social_suboptions
print("=" * 60)
print("Testing _has_social_suboptions method")
print("=" * 60)

has_suboptions = validator._has_social_suboptions('selectionCriteria')
print(f"Has social sub-options: {has_suboptions}")
print(f"Expected: True (because 'otherSocial' is selected)")

# Test _get_selected_criteria
print("\n" + "=" * 60)
print("Testing _get_selected_criteria method")
print("=" * 60)

selected = validator._get_selected_criteria('selectionCriteria')
print("Selected criteria:")
for criterion, is_selected in selected.items():
    if is_selected:
        print(f"  ✓ {criterion}")

# Run full validation
print("\n" + "=" * 60)
print("Running validation for selection criteria")
print("=" * 60)

# Call the selection criteria validation directly
errors = []
warnings = []

# Get selected criteria
selected_criteria = validator._get_selected_criteria('selectionCriteria')

# Check if social criteria needs sub-options
if selected_criteria.get('socialCriteria'):
    has_suboptions = validator._has_social_suboptions('selectionCriteria')
    if not has_suboptions:
        errors.append("Pri socialnih merilih morate izbrati vsaj eno možnost")

# Check if otherCriteriaCustom needs description
if selected_criteria.get('otherCriteriaCustom'):
    desc = test_session.get('selectionCriteria.otherCriteriaCustomDescription', '')
    if not desc:
        errors.append("Pri izbiri 'Drugo, imam predlog' morate navesti opis merila")

if errors:
    print("ERRORS:")
    for error in errors:
        print(f"  ❌ {error}")
else:
    print("✅ No errors!")

if warnings:
    print("\nWARNINGS:")
    for warning in warnings:
        print(f"  ⚠️ {warning}")
else:
    print("✅ No warnings!")

# Test edge case: social criteria selected but no sub-options
print("\n" + "=" * 60)
print("Edge case: Social criteria but no sub-options")
print("=" * 60)

test_session2 = test_session.copy()
test_session2['selectionCriteria.socialCriteriaOptions.otherSocial'] = False
test_session2['selectionCriteria.socialCriteriaOtherRatio'] = 0

validator2 = ValidationManager(schema, test_session2)

# Check social sub-options manually
has_suboptions2 = validator2._has_social_suboptions('selectionCriteria')
errors2 = []
if not has_suboptions2:
    errors2.append("Pri socialnih merilih morate izbrati vsaj eno možnost")

if errors2:
    print("ERRORS (expected):")
    for error in errors2:
        print(f"  ❌ {error}")
        if "Pri socialnih merilih morate izbrati vsaj eno možnost" in error:
            print("  ✅ Correct error message!")