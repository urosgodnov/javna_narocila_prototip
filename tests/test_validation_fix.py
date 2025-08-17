#!/usr/bin/env python3
"""
Test script to verify validation fixes for participation and exclusion fields.
"""

import streamlit as st
from utils.validations import ValidationManager

def test_participation_validation():
    """Test the participation and exclusion validation with correct field names."""
    
    # Create a mock session state
    class MockSessionState:
        def __init__(self):
            self.data = {}
        
        def get(self, key, default=None):
            return self.data.get(key, default)
        
        def __contains__(self, key):
            return key in self.data
    
    session = MockSessionState()
    validator = ValidationManager(session, {})
    
    print("Testing Participation and Exclusion Validation")
    print("=" * 50)
    
    # Test 1: No fields set - should show errors
    print("\nTest 1: No fields set")
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should be invalid when no fields are set"
    assert any("Prosimo označite vse neobvezne razloge za izključitev" in e for e in errors)
    assert any("Ali želite vključiti pogoje za sodelovanje je obvezno" in e for e in errors)
    
    # Test 2: Set exclusion reasons field with correct name
    print("\nTest 2: Set exclusion reasons with correct field name")
    session.data['participationAndExclusion.exclusionReasonsSelection'] = 'vse razloge'
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    # Should no longer have exclusion error
    assert not any("Prosimo označite vse neobvezne razloge za izključitev" in e for e in errors)
    
    # Test 3: Set participation conditions with correct name
    print("\nTest 3: Set participation conditions with correct field name")
    session.data['participationConditions.participationSelection'] = 'ne, ne želimo postaviti posebnih pogojev'
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    # Should be valid now
    assert is_valid, "Should be valid when both fields are set"
    assert len(errors) == 0
    
    # Test 4: Test with specific reasons selected
    print("\nTest 4: Test with specific exclusion reasons")
    session.data['participationAndExclusion.exclusionReasonsSelection'] = 'specifični razlogi'
    # Without specific reasons selected - should error
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid
    assert any("Pri specifičnih razlogih morate izbrati najmanj eno možnost" in e for e in errors)
    
    # Add a specific reason
    session.data['participationAndExclusion.criminalConviction'] = True
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid after adding specific reason: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should be valid with specific reason selected"
    
    # Test 5: Test with specific participation conditions
    print("\nTest 5: Test with specific participation conditions")
    session.data['participationConditions.participationSelection'] = 'da, specifični pogoji'
    # Without specific conditions - should error
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid
    assert any("Pri specifičnih pogojih morate izbrati najmanj eno možnost" in e for e in errors)
    
    # Add a specific condition
    session.data['participationConditions.economicCondition'] = True
    session.data['participationConditions.economicDescription'] = 'Test economic description'
    is_valid, errors = validator.validate_participation_conditions()
    print(f"Valid after adding specific condition: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should be valid with specific condition and description"
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    

if __name__ == "__main__":
    test_participation_validation()