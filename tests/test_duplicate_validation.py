#!/usr/bin/env python3
"""
Test script to verify that duplicate validation messages are fixed.
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

def test_merila_validation_no_duplicates():
    """Test that Merila validation doesn't produce duplicate messages."""
    
    session = MockSessionState()
    validator = ValidationManager({}, session)
    
    print("Testing Merila Validation - No Duplicates")
    print("=" * 50)
    
    # Test 1: Price with 0 points - should only show error once
    print("\n✓ Test 1: Price selected with 0 points")
    session.data['selectionCriteria.price'] = True
    session.data['selectionCriteria.priceRatio'] = 0
    
    # Simulate what validate_step does for step 12
    step_keys = ['selectionCriteria']
    
    # First clear errors and warnings
    validator.errors = []
    validator.warnings = []
    
    # Call validate_step like app.py does
    # This simulates the lambda call in step 12
    selection_key = validator._find_selection_criteria_key(step_keys)
    is_valid, errors = validator.validate_merila(selection_key)
    
    print(f"  Valid: {is_valid}")
    print(f"  Errors count: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Count how many times the "0 points" error appears
    zero_points_errors = [e for e in errors if "ne smejo biti 0" in e]
    print(f"\n  '0 points' error count: {len(zero_points_errors)}")
    
    if len(zero_points_errors) == 1:
        print("  ✅ SUCCESS: Error appears only once!")
    else:
        print(f"  ❌ FAIL: Error appears {len(zero_points_errors)} times (should be 1)")
    
    # Test 2: Multiple criteria with 0 points
    print("\n✓ Test 2: Multiple criteria with 0 points")
    session.data['selectionCriteria.price'] = True
    session.data['selectionCriteria.priceRatio'] = 0
    session.data['selectionCriteria.quality'] = True
    session.data['selectionCriteria.qualityRatio'] = 0
    
    validator.errors = []
    validator.warnings = []
    is_valid, errors = validator.validate_merila(selection_key)
    
    print(f"  Valid: {is_valid}")
    print(f"  Errors count: {len(errors)}")
    for error in errors:
        print(f"    - {error}")
    
    # Check for unique errors
    unique_errors = list(set(errors))
    if len(unique_errors) == len(errors):
        print("  ✅ SUCCESS: No duplicate errors!")
    else:
        print(f"  ❌ FAIL: Found duplicates ({len(errors) - len(unique_errors)} duplicates)")
    
    # Test 3: With warnings
    print("\n✓ Test 3: Price as sole criterion (should generate warning)")
    session.data = {}  # Clear
    session.data['selectionCriteria.price'] = True
    session.data['selectionCriteria.priceRatio'] = 100
    
    validator.errors = []
    validator.warnings = []
    is_valid, errors = validator.validate_merila(selection_key)
    warnings = validator.get_warnings()
    
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    for warning in warnings:
        print(f"    ℹ️ {warning}")
    
    # Check for unique warnings
    unique_warnings = list(set(warnings))
    if len(unique_warnings) == len(warnings):
        print("  ✅ SUCCESS: No duplicate warnings!")
    else:
        print(f"  ❌ FAIL: Found duplicate warnings")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("The validation should now produce each error/warning only once.")
    print("This was fixed by removing the duplicate validate_merila call in app.py")

if __name__ == "__main__":
    test_merila_validation_no_duplicates()