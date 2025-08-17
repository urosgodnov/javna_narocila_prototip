#!/usr/bin/env python3
"""
Test script to verify financial guarantees and variant offers validation fixes.
"""

import sys
from utils.validations import ValidationManager

class MockSessionState:
    """Mock session state for testing."""
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data

def test_financial_guarantees_validation():
    """Test the financial guarantees and variant offers validation."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)  # schema first, then session_state
    
    print("=" * 60)
    print("TESTING FINANCIAL GUARANTEES AND VARIANT OFFERS VALIDATION")
    print("=" * 60)
    
    # Test 1: No fields set - should show errors
    print("\n✓ Test 1: No fields set")
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Expected errors: 2")
    print(f"  Actual errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    assert not is_valid
    assert any("Ali zahtevate finančna zavarovanja je obvezno" in e for e in errors)
    assert any("Ali dopuščate predložitev variantnih ponudb je obvezno" in e for e in errors)
    
    # Test 2: Set financial guarantees with correct field name
    print("\n✓ Test 2: Set financial guarantees = 'da, zahtevamo finančna zavarovanja'")
    session.data['financialGuarantees.requiresFinancialGuarantees'] = 'da, zahtevamo finančna zavarovanja'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    # Should have error about selecting at least one type
    assert not is_valid
    assert any("Pri finančnih zavarovanjih morate izbrati najmanj eno vrsto" in e for e in errors)
    
    # Test 3: Add a specific guarantee type
    print("\n✓ Test 3: Add fzSeriousness guarantee")
    session.data['financialGuarantees.fzSeriousness.required'] = True
    session.data['financialGuarantees.fzSeriousness.instrument'] = 'bančna garancija'
    session.data['financialGuarantees.fzSeriousness.amount'] = '5000'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    # Should only have variant offers error now
    assert not is_valid
    assert not any("finančna zavarovanja" in e.lower() and "obvezno" in e for e in errors)
    
    # Test 4: Set variant offers with correct field name
    print("\n✓ Test 4: Set variant offers = 'ne'")
    session.data['variantOffers.allowVariants'] = 'ne'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    # Should be valid now
    assert is_valid, f"Should be valid but got errors: {errors}"
    
    # Test 5: Test variant offers = 'da' requires minimal requirements
    print("\n✓ Test 5: Set variant offers = 'da' without requirements")
    session.data['variantOffers.allowVariants'] = 'da'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    assert not is_valid
    assert any("minimalne zahteve" in e for e in errors)
    
    # Test 6: Add minimal requirements
    print("\n✓ Test 6: Add minimal requirements for variant offers")
    session.data['variantOffers.minimalRequirements'] = 'Test minimal requirements'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    assert is_valid, f"Should be valid but got errors: {errors}"
    
    # Test 7: Test deposit details validation
    print("\n✓ Test 7: Test deposit details validation")
    session.data['financialGuarantees.fzSeriousness.instrument'] = 'denarni depozit'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    # Should have errors about missing deposit details
    assert not is_valid
    assert any("IBAN" in e for e in errors)
    
    # Test 8: Add deposit details
    print("\n✓ Test 8: Add complete deposit details")
    session.data['financialGuarantees.fzSeriousness.depositDetails.iban'] = 'SI56 1234 5678 9012 345'
    session.data['financialGuarantees.fzSeriousness.depositDetails.bank'] = 'Test Bank'
    session.data['financialGuarantees.fzSeriousness.depositDetails.swift'] = 'TESTSI2X'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    assert is_valid, f"Should be valid but got errors: {errors}"
    
    # Test 9: Test 'ne, naročnik ne zahteva' option
    print("\n✓ Test 9: Set financial guarantees = 'ne, naročnik ne zahteva finančnih zavarovanj'")
    session.data = {}  # Clear all data
    session.data['financialGuarantees.requiresFinancialGuarantees'] = 'ne, naročnik ne zahteva finančnih zavarovanj'
    session.data['variantOffers.allowVariants'] = 'ne'
    is_valid, errors = validator.validate_financial_guarantees()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    assert is_valid, f"Should be valid but got errors: {errors}"
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
    print("\nSummary:")
    print("- Financial guarantees field name: requiresFinancialGuarantees")
    print("- Valid values: 'da, zahtevamo finančna zavarovanja' / 'ne, naročnik ne zahteva finančnih zavarovanj'")
    print("- Guarantee types: fzSeriousness, fzPerformance, fzWarranty")
    print("- Variant offers field name: allowVariants")
    print("- Valid values: 'da' / 'ne'")
    print("- Minimal requirements field: minimalRequirements")

if __name__ == "__main__":
    test_financial_guarantees_validation()