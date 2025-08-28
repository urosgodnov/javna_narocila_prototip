#!/usr/bin/env python3
"""Test script to verify multiple clients validation fix."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager

print("Testing Multiple Clients Validation Fix")
print("=" * 50)

# Test 1: No multiple client selection (default single client)
print("\n✅ Test 1: Default single client mode (no validation should trigger)")
session_state_1 = {
    'clientInfo.name': 'Test Company',
    'clientInfo.streetAddress': 'Test Street 1',
    'clientInfo.postalCode': '1000 Ljubljana',
    # Note: isSingleClient NOT explicitly set, defaults to True
}

validator_1 = ValidationManager(session_state_1, {})
validator_1._validate_multiple_entries()
if validator_1.errors:
    print(f"❌ FAILED: Got errors: {validator_1.errors}")
else:
    print("✅ PASSED: No validation errors for single client mode")

# Test 2: Multiple clients selected but no data entered yet
print("\n✅ Test 2: Multiple clients selected but no data (no validation should trigger)")
session_state_2 = {
    'clientInfo.isSingleClient': False,  # Multiple clients selected
    'clientInfo.clients': []  # But no data entered yet
}

validator_2 = ValidationManager(session_state_2, {})
validator_2._validate_multiple_entries()
if validator_2.errors:
    print(f"❌ FAILED: Got errors: {validator_2.errors}")
else:
    print("✅ PASSED: No validation errors when no client data entered")

# Test 3: Multiple clients with only one client filled
print("\n✅ Test 3: Multiple clients with only one complete (should trigger validation)")
session_state_3 = {
    'clientInfo.isSingleClient': False,
    'clientInfo.clients': [
        {
            'name': 'Client 1',
            'streetAddress': 'Street 1',
            'postalCode': '1000 Ljubljana',
            'legalRepresentative': 'John Doe'
        }
    ]
}

validator_3 = ValidationManager(session_state_3, {})
validator_3._validate_multiple_entries()
if validator_3.errors:
    print(f"✅ PASSED: Got expected error: {validator_3.errors[0]}")
else:
    print("❌ FAILED: Should have validation error for only 1 client")

# Test 4: Multiple clients with two complete clients
print("\n✅ Test 4: Multiple clients with two complete (should pass)")
session_state_4 = {
    'clientInfo.isSingleClient': False,
    'clientInfo.clients': [
        {
            'name': 'Client 1',
            'streetAddress': 'Street 1',
            'postalCode': '1000 Ljubljana',
            'legalRepresentative': 'John Doe'
        },
        {
            'name': 'Client 2',
            'streetAddress': 'Street 2',
            'postalCode': '2000 Maribor',
            'legalRepresentative': 'Jane Smith'
        }
    ]
}

validator_4 = ValidationManager(session_state_4, {})
validator_4._validate_multiple_entries()
if validator_4.errors:
    print(f"❌ FAILED: Got errors: {validator_4.errors}")
else:
    print("✅ PASSED: No validation errors with 2 complete clients")

# Test 5: Multiple clients with incomplete second client
print("\n✅ Test 5: Multiple clients with incomplete second client (should show specific errors)")
session_state_5 = {
    'clientInfo.isSingleClient': False,
    'clientInfo.clients': [
        {
            'name': 'Client 1',
            'streetAddress': 'Street 1',
            'postalCode': '1000 Ljubljana',
            'legalRepresentative': 'John Doe'
        },
        {
            'name': 'Client 2',
            'streetAddress': '',  # Missing
            'postalCode': '2000 Maribor',
            'legalRepresentative': ''  # Missing
        }
    ]
}

validator_5 = ValidationManager(session_state_5, {})
validator_5._validate_multiple_entries()
if validator_5.errors:
    print(f"✅ PASSED: Got expected errors:")
    for error in validator_5.errors:
        print(f"  - {error}")
else:
    print("❌ FAILED: Should have validation errors for incomplete client")

print("\n" + "=" * 50)
print("✨ Multiple Clients Validation Fix Test Complete!")
print("\nThe fix ensures that:")
print("1. No validation when isSingleClient is not explicitly set")
print("2. No validation when multiple clients selected but no data entered")
print("3. Proper validation only when data is actually being entered")
print("4. Clear error messages for incomplete clients")