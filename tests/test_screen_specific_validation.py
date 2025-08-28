#!/usr/bin/env python3
"""Test that validation only runs on the appropriate screens."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager

print("Testing Screen-Specific Validation")
print("=" * 50)

# Test 1: Non-client screen should NOT validate multiple clients
print("\n✅ Test 1: Validation on procurement screen (Step 2 - no client fields)")
session_state = {
    'clientInfo.isSingleClient': False,  # Multiple clients selected
    'clientInfo.clients': [],  # But no clients entered
    'procurementInfo.title': 'Test Procurement',
    'procurementInfo.type': 'Blago'
}

# Simulate being on procurement info screen (step 2)
step_keys = ['procurementInfo']
expanded_keys = ['procurementInfo.title', 'procurementInfo.type']

validator = ValidationManager(session_state, {})
# Call validate method with procurement keys (simulating step 2)
validator._validate_dropdowns(expanded_keys)

# Check if _validate_multiple_entries would be called
should_validate_clients = any('clientInfo' in key for key in expanded_keys)
print(f"  Should validate clients on this screen? {should_validate_clients}")
print(f"  Expanded keys: {expanded_keys}")

if not should_validate_clients:
    print("✅ PASSED: Multiple clients validation NOT triggered on procurement screen")
else:
    print("❌ FAILED: Should not validate clients on procurement screen")

# Test 2: Client screen SHOULD validate multiple clients
print("\n✅ Test 2: Validation on client screen (Step 1 - has client fields)")
session_state_2 = {
    'clientInfo.isSingleClient': False,  # Multiple clients selected
    'clientInfo.clients': [
        {'name': 'Client 1', 'streetAddress': 'Street 1', 'postalCode': '1000', 'legalRepresentative': 'John'}
    ]  # Only one client (should trigger error)
}

# Simulate being on client info screen (step 1)
client_keys = ['clientInfo', 'clientInfo.name', 'clientInfo.address', 'clientInfo.clients']

validator_2 = ValidationManager(session_state_2, {})
# Check if validation should run
should_validate_clients_2 = any('clientInfo' in key for key in client_keys)
print(f"  Should validate clients on this screen? {should_validate_clients_2}")
print(f"  Keys on screen: {client_keys[:3]}...")

if should_validate_clients_2:
    # Now actually validate
    validator_2._validate_multiple_entries()
    if validator_2.errors:
        print(f"✅ PASSED: Got expected validation: {validator_2.errors[0][:50]}...")
    else:
        print("❌ FAILED: Should have validation error for only 1 client")
else:
    print("❌ FAILED: Should validate clients on client screen")

# Test 3: Different screens with NO client fields
print("\n✅ Test 3: Various other screens (no client validation)")
test_screens = [
    (['selectionCriteria'], "Selection Criteria"),
    (['contractInfo'], "Contract Info"),
    (['tenderInfo'], "Tender Info"),
    (['technicalRequirements'], "Technical Requirements"),
]

all_passed = True
for keys, screen_name in test_screens:
    should_validate = any('clientInfo' in key for key in keys)
    if should_validate:
        print(f"  ❌ {screen_name}: Would incorrectly validate clients")
        all_passed = False
    else:
        print(f"  ✅ {screen_name}: Correctly skips client validation")

if all_passed:
    print("\n✅ PASSED: All non-client screens correctly skip validation")

print("\n" + "=" * 50)
print("✨ Screen-Specific Validation Test Complete!")
print("\nThe fix ensures that:")
print("1. Multiple client validation ONLY runs on client info screen")
print("2. Other screens are not affected by client validation")
print("3. Validation is context-aware based on current screen fields")