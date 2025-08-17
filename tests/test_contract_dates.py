#!/usr/bin/env python3
"""
Test script to verify contract date field validation is fixed.
"""

from datetime import date, datetime
from utils.validations import ValidationManager

class MockSessionState:
    """Mock session state for testing."""
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data

def test_contract_dates():
    """Test the contract date validation with correct field names."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)
    
    print("Testing Contract Date Fields Validation")
    print("=" * 50)
    
    # Test 1: Contract with date period - missing dates
    print("\n✓ Test 1: Contract with 'od-do' period - missing dates")
    session.data = {
        'contractInfo.type': 'pogodba',
        'contractInfo.contractPeriodType': 'za obdobje od-do'
    }
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Should ask for the correct field names now
    assert any("Obdobje od je obvezno" in e for e in errors), "Should ask for 'Obdobje od'"
    assert any("Obdobje do je obvezno" in e for e in errors), "Should ask for 'Obdobje do'"
    # Should NOT ask for old field names
    assert not any("Začetni datum pogodbe" in e for e in errors), "Should not use old field name"
    assert not any("Končni datum pogodbe" in e for e in errors), "Should not use old field name"
    print("  ✅ Correct error messages with proper field names!")
    
    # Test 2: Contract with dates filled (as date objects like Streamlit returns)
    print("\n✓ Test 2: Contract with dates filled (date objects)")
    session.data['contractInfo.contractDateFrom'] = date(2025, 8, 17)
    session.data['contractInfo.contractDateTo'] = date(2025, 8, 17)
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Should be valid or only have extension-related errors
    assert not any("Obdobje od" in e for e in errors), "Should not complain about start date"
    assert not any("Obdobje do" in e for e in errors), "Should not complain about end date"
    print("  ✅ Dates recognized correctly!")
    
    # Test 3: Test with invalid date order
    print("\n✓ Test 3: End date before start date")
    session.data['contractInfo.contractDateFrom'] = date(2025, 12, 31)
    session.data['contractInfo.contractDateTo'] = date(2025, 1, 1)
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    assert any("Končni datum ne more biti pred začetnim" in e for e in errors), "Should validate date order"
    print("  ✅ Date order validation works!")
    
    # Test 4: Contract with validity period instead of dates
    print("\n✓ Test 4: Contract with validity period")
    session.data = {
        'contractInfo.type': 'pogodba',
        'contractInfo.contractPeriodType': 'z veljavnostjo',
        'contractInfo.contractValidity': '2 leti'
    }
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Should not ask for dates when using validity period
    assert not any("Obdobje od" in e for e in errors), "Should not ask for dates with validity period"
    assert not any("Obdobje do" in e for e in errors), "Should not ask for dates with validity period"
    print("  ✅ Validity period works without dates!")
    
    # Test 5: Contract with dates as strings (ISO format)
    print("\n✓ Test 5: Contract with dates as strings")
    session.data = {
        'contractInfo.type': 'pogodba',
        'contractInfo.contractPeriodType': 'za obdobje od-do',
        'contractInfo.contractDateFrom': '2025-08-17',
        'contractInfo.contractDateTo': '2026-08-17'
    }
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Should handle string dates correctly
    assert not any("Obdobje" in e for e in errors), "Should handle string dates"
    print("  ✅ String dates handled correctly!")
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("\nKey fixes:")
    print("- Uses correct field names: contractDateFrom and contractDateTo")
    print("- Error messages match the form labels: 'Obdobje od' and 'Obdobje do'")
    print("- Handles both date objects and strings")
    print("- Validates date order")
    print("- Works with both validity period and date range options")

if __name__ == "__main__":
    test_contract_dates()