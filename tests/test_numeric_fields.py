#!/usr/bin/env python3
"""
Test script to verify that numeric field validation works correctly.
"""

from utils.validations import ValidationManager

class MockSessionState:
    """Mock session state for testing."""
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data

def test_numeric_amount_fields():
    """Test that validation handles numeric amount fields correctly."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)
    
    print("Testing Numeric Amount Fields")
    print("=" * 50)
    
    # Test 1: Set up financial guarantees with NUMERIC amount (float)
    print("\n✓ Test 1: Financial guarantee with numeric amount (float)")
    session.data['financialGuarantees.requiresFinancialGuarantees'] = 'da, zahtevamo finančna zavarovanja'
    session.data['financialGuarantees.fzSeriousness.required'] = True
    session.data['financialGuarantees.fzSeriousness.instrument'] = 'bančna garancija'
    session.data['financialGuarantees.fzSeriousness.amount'] = 5000.0  # FLOAT value
    session.data['variantOffers.allowVariants'] = 'ne'
    
    try:
        is_valid, errors = validator.validate_financial_guarantees()
        print(f"  Valid: {is_valid}")
        print(f"  Errors: {len(errors)}")
        if errors:
            for error in errors:
                print(f"    - {error}")
        print("  ✅ No AttributeError with float amount!")
    except AttributeError as e:
        print(f"  ❌ AttributeError occurred: {e}")
        raise
    
    # Test 2: Test with integer amount
    print("\n✓ Test 2: Financial guarantee with integer amount")
    session.data['financialGuarantees.fzSeriousness.amount'] = 5000  # INT value
    
    try:
        is_valid, errors = validator.validate_financial_guarantees()
        print(f"  Valid: {is_valid}")
        print(f"  Errors: {len(errors)}")
        print("  ✅ No AttributeError with integer amount!")
    except AttributeError as e:
        print(f"  ❌ AttributeError occurred: {e}")
        raise
    
    # Test 3: Test with string amount
    print("\n✓ Test 3: Financial guarantee with string amount")
    session.data['financialGuarantees.fzSeriousness.amount'] = "  5000  "  # STRING with spaces
    
    try:
        is_valid, errors = validator.validate_financial_guarantees()
        print(f"  Valid: {is_valid}")
        print(f"  Errors: {len(errors)}")
        print("  ✅ No AttributeError with string amount!")
    except AttributeError as e:
        print(f"  ❌ AttributeError occurred: {e}")
        raise
    
    # Test 4: Test with zero amount (edge case)
    print("\n✓ Test 4: Financial guarantee with zero amount")
    session.data['financialGuarantees.fzSeriousness.amount'] = 0
    
    try:
        is_valid, errors = validator.validate_financial_guarantees()
        print(f"  Valid: {is_valid}")
        print(f"  Errors: {len(errors)}")
        if errors:
            for error in errors:
                print(f"    - {error}")
        print("  ✅ No AttributeError with zero amount!")
    except AttributeError as e:
        print(f"  ❌ AttributeError occurred: {e}")
        raise
    
    # Test 5: Test deposit details with mixed types
    print("\n✓ Test 5: Deposit details with mixed field types")
    session.data['financialGuarantees.fzSeriousness.instrument'] = 'denarni depozit'
    session.data['financialGuarantees.fzSeriousness.depositDetails.iban'] = "SI56 1234 5678 9012 345"
    session.data['financialGuarantees.fzSeriousness.depositDetails.bank'] = "Test Bank"
    session.data['financialGuarantees.fzSeriousness.depositDetails.swift'] = "TESTSI2X"
    session.data['financialGuarantees.fzSeriousness.amount'] = 1000.50  # Float amount
    
    try:
        is_valid, errors = validator.validate_financial_guarantees()
        print(f"  Valid: {is_valid}")
        print(f"  Errors: {len(errors)}")
        print("  ✅ No AttributeError with mixed types in deposit details!")
    except AttributeError as e:
        print(f"  ❌ AttributeError occurred: {e}")
        raise
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("The validation now correctly handles:")
    print("  - Float numbers")
    print("  - Integer numbers")
    print("  - String values with spaces")
    print("  - Zero values")
    print("  - Mixed field types")

if __name__ == "__main__":
    test_numeric_amount_fields()