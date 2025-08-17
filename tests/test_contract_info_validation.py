#!/usr/bin/env python3
"""
Test script to verify contract info validation is using correct fields.
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

def test_contract_info_validation():
    """Test the contract info validation with correct field names."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)
    
    print("Testing Contract Info Validation")
    print("=" * 50)
    
    # Test 1: Framework agreement without required fields
    print("\n✓ Test 1: Framework agreement - missing fields")
    session.data['contractInfo.type'] = 'okvirni sporazum'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Should NOT have errors about start/end dates anymore
    assert not any("začetni datum" in e for e in errors), "Should not ask for start date"
    assert not any("končni datum" in e for e in errors), "Should not ask for end date"
    # Should have errors about duration and type
    assert any("Obdobje okvirnega sporazuma je obvezno" in e for e in errors)
    assert any("Vrsta okvirnega sporazuma je obvezna" in e for e in errors)
    print("  ✅ Correct validation messages!")
    
    # Test 2: Framework agreement with correct fields
    print("\n✓ Test 2: Framework agreement - with correct fields")
    session.data['contractInfo.frameworkDuration'] = '4 leta'
    session.data['contractInfo.frameworkType'] = 'Z enim gospodarskim subjektom in brez odpiranja konkurence'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    assert is_valid, "Should be valid with duration and type filled"
    print("  ✅ Valid with correct fields!")
    
    # Test 3: Framework with competition reopening
    print("\n✓ Test 3: Framework with competition reopening")
    session.data['contractInfo.frameworkType'] = 'Z enim gospodarskim subjektom in z odpiranjem konkurence'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    # Should require frequency
    assert any("Pogostost odpiranja konkurence" in e for e in errors)
    print("  ✅ Correctly requires frequency for competition reopening!")
    
    # Test 4: Add frequency
    print("\n✓ Test 4: Add competition frequency")
    session.data['contractInfo.competitionFrequency'] = 'Kvartalno'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    assert is_valid, "Should be valid with frequency added"
    print("  ✅ Valid with frequency!")
    
    # Test 5: Contract (not framework) - should not require framework fields
    print("\n✓ Test 5: Regular contract (not framework)")
    session.data = {}  # Clear
    session.data['contractInfo.type'] = 'pogodba'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    # Should not have any framework-related errors
    assert not any("okvirn" in e.lower() for e in errors), "Should not have framework errors"
    assert is_valid, "Regular contract should be valid without framework fields"
    print("  ✅ No framework validation for regular contract!")
    
    # Test 6: Contract extension
    print("\n✓ Test 6: Contract extension validation")
    session.data['contractInfo.canBeExtended'] = 'da'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    # Should require extension details
    assert any("razloge za možnost podaljšanja" in e for e in errors)
    assert any("trajanje podaljšanja" in e for e in errors)
    
    # Add extension details
    session.data['contractInfo.extensionReasons'] = 'Dodatne storitve'
    session.data['contractInfo.extensionDuration'] = '6 mesecev'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  After adding extension details - Valid: {is_valid}")
    assert is_valid, "Should be valid with extension details"
    print("  ✅ Extension validation works correctly!")
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("\nThe validation now correctly:")
    print("- Uses frameworkDuration instead of date fields")
    print("- Requires frameworkType for framework agreements")
    print("- Only requires frequency when competition reopening is selected")
    print("- Doesn't apply framework validation to regular contracts")
    print("- Properly validates contract extensions")

if __name__ == "__main__":
    test_contract_info_validation()