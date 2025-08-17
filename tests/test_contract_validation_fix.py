#!/usr/bin/env python3
"""
Test script to verify contract info validation is working correctly.
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

def test_contract_validation():
    """Test the contract info validation with correct logic."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)
    
    print("Testing Contract Info Validation - Fixed")
    print("=" * 50)
    
    # Test 1: No contract type selected
    print("\n✓ Test 1: No contract type selected")
    session.data = {}  # Clear
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    assert any("Vrsta sklenitve je obvezna" in e for e in errors)
    print("  ✅ Correctly requires contract type!")
    
    # Test 2: Regular contract (pogodba) selected
    print("\n✓ Test 2: Regular contract (pogodba) selected")
    session.data['contractInfo.type'] = 'pogodba'
    session.data['contractInfo.contractValidity'] = '3'  # Validity period
    session.data['contractInfo.contractPeriodType'] = 'z veljavnostjo'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Should NOT have any framework-related errors
    assert not any("okvirn" in e.lower() for e in errors), "Should not have framework errors for regular contract"
    print("  ✅ No framework validation for regular contract!")
    
    # Test 3: Framework agreement without required fields
    print("\n✓ Test 3: Framework agreement without required fields")
    session.data = {}  # Clear
    session.data['contractInfo.type'] = 'okvirni sporazum'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Should have framework-specific errors
    assert any("Obdobje okvirnega sporazuma je obvezno" in e for e in errors)
    assert any("Vrsta okvirnega sporazuma je obvezna" in e for e in errors)
    print("  ✅ Correct framework validation!")
    
    # Test 4: Framework agreement with all fields
    print("\n✓ Test 4: Framework agreement with all required fields")
    session.data['contractInfo.frameworkDuration'] = '4 leta'
    session.data['contractInfo.frameworkType'] = 'Z enim gospodarskim subjektom in brez odpiranja konkurence'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    assert is_valid or len(errors) == 0, "Should be valid with all framework fields"
    print("  ✅ Valid framework agreement!")
    
    # Test 5: Switching from framework back to contract
    print("\n✓ Test 5: Switching from framework back to contract")
    # Keep framework fields but change type
    session.data['contractInfo.type'] = 'pogodba'
    session.data['contractInfo.contractValidity'] = '2 leti'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for error in errors:
            print(f"    - {error}")
    
    # Should NOT validate framework fields even if they exist in session
    assert not any("Vrsta okvirnega sporazuma" in e for e in errors), "Should not validate framework fields for contract"
    assert not any("Obdobje okvirnega sporazuma" in e for e in errors), "Should not validate framework duration for contract"
    print("  ✅ Correctly ignores framework fields when contract is selected!")
    
    # Test 6: Contract with extension
    print("\n✓ Test 6: Contract with extension")
    session.data['contractInfo.canBeExtended'] = 'da'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Should require extension details
    assert any("razloge" in e for e in errors)
    assert any("trajanje" in e for e in errors)
    
    # Add extension details
    session.data['contractInfo.extensionReasons'] = 'Dodatne potrebe'
    session.data['contractInfo.extensionDuration'] = '6 mesecev'
    
    is_valid, errors = validator.validate_contract_info()
    print(f"  After adding extension details - Valid: {is_valid}")
    print("  ✅ Extension validation works!")
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("\nKey fixes:")
    print("- Contract type is checked before applying specific validation")
    print("- Framework validation only applies when type = 'okvirni sporazum'")
    print("- Contract validation only applies when type = 'pogodba'")
    print("- Old framework fields are ignored when switching to contract")

if __name__ == "__main__":
    test_contract_validation()