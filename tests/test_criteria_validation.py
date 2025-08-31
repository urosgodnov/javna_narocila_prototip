#!/usr/bin/env python3
"""Test script for criteria validation feature (Stories 21.1-21.3)"""

import sys
from utils.validations import (
    validate_criteria_selection,
    check_cpv_requires_additional_criteria,
    get_validation_summary
)
from utils.criteria_suggestions import (
    get_suggested_criteria_for_cpv,
    analyze_cpv_categories
)

def test_validation():
    """Test the validation logic"""
    print("=" * 60)
    print("TESTING CRITERIA VALIDATION (Story 21.1)")
    print("=" * 60)
    
    # Test 1: CPV codes with restrictions
    test_cpv_codes = ['71000000-8', '79000000-4']  # Architecture and Business services
    print(f"\n1. Testing CPV codes: {test_cpv_codes}")
    
    restricted = check_cpv_requires_additional_criteria(test_cpv_codes)
    print(f"   Restricted codes found: {len(restricted)}")
    for code, info in restricted.items():
        print(f"   - {code}: {info['description']}")
        print(f"     Restriction: {info['restriction']}")
    
    # Test 2: Validation with only price selected
    print("\n2. Testing validation with only price selected:")
    criteria_price_only = {'price': True}
    result = validate_criteria_selection(test_cpv_codes, criteria_price_only)
    print(f"   Valid: {result.is_valid}")
    if result.messages:
        print("   Messages:")
        for msg in result.messages:
            print(f"   - {msg}")
    
    # Test 3: Validation with additional criteria
    print("\n3. Testing validation with price + additional criteria:")
    criteria_with_additional = {
        'price': True,
        'additionalReferences': True,
        'additionalTechnicalRequirements': True
    }
    result = validate_criteria_selection(test_cpv_codes, criteria_with_additional)
    print(f"   Valid: {result.is_valid}")
    print(f"   Messages: {result.messages if result.messages else 'None (valid)'}")
    
    # Test 4: CPV codes without restrictions
    print("\n4. Testing CPV codes without restrictions:")
    unrestricted_codes = ['03000000-1']  # Agricultural products
    result = validate_criteria_selection(unrestricted_codes, criteria_price_only)
    print(f"   CPV codes: {unrestricted_codes}")
    print(f"   Valid with price only: {result.is_valid}")
    
    # Test 5: Validation summary
    print("\n5. Testing validation summary:")
    summary = get_validation_summary(test_cpv_codes)
    print(f"   Has restrictions: {summary['has_restrictions']}")
    print(f"   Rules: {summary['rules']}")
    print(f"   Restricted count: {summary['restricted_count']}")


def test_suggestions():
    """Test the suggestions logic"""
    print("\n" + "=" * 60)
    print("TESTING CRITERIA SUGGESTIONS (Story 21.3)")
    print("=" * 60)
    
    # Test different CPV categories
    test_cases = [
        (['71000000-8', '71200000-0'], "Architecture/Engineering"),
        (['45000000-7'], "Construction"),
        (['85000000-9'], "Health and Social"),
        (['79000000-4', '48000000-8'], "Business/Software"),
        (['90000000-7'], "Environmental")
    ]
    
    for cpv_codes, description in test_cases:
        print(f"\n{description} CPV codes: {cpv_codes}")
        
        # Analyze categories
        categories = analyze_cpv_categories(cpv_codes)
        print(f"Categories identified: {categories}")
        
        # Get suggestions
        suggestions = get_suggested_criteria_for_cpv(cpv_codes)
        print(f"Recommended criteria: {suggestions['recommended']}")
        print(f"Commonly used: {suggestions['commonly_used']}")
        print(f"Explanation: {suggestions['explanation']}")


def test_integration():
    """Test the full integration"""
    print("\n" + "=" * 60)
    print("TESTING FULL INTEGRATION")
    print("=" * 60)
    
    # Simulate a user selecting CPV codes and criteria
    print("\nScenario: User selects architecture CPV code (71000000-8)")
    cpv_codes = ['71000000-8']
    
    # Check restrictions
    restricted = check_cpv_requires_additional_criteria(cpv_codes)
    if restricted:
        print("✓ System detects restriction: Price cannot be the only criterion")
        
        # Get suggestions
        suggestions = get_suggested_criteria_for_cpv(cpv_codes)
        print(f"✓ System suggests: {suggestions['recommended']}")
        print(f"✓ Explanation: {suggestions['explanation']}")
        
        # User selects only price (invalid)
        print("\nUser selects only price...")
        result = validate_criteria_selection(cpv_codes, {'price': True})
        if not result.is_valid:
            print("✓ Validation fails as expected")
            print(f"  Message: {result.messages[0] if result.messages else 'No message'}")
        
        # User follows suggestion
        print("\nUser accepts suggestion and selects additional criteria...")
        criteria = {'price': True}
        for c in suggestions['recommended']:
            criteria[c] = True
        
        result = validate_criteria_selection(cpv_codes, criteria)
        if result.is_valid:
            print("✓ Validation passes!")
            print("✓ Form can be submitted")
        else:
            print("✗ Validation still fails (unexpected)")
    else:
        print("✗ No restrictions found (unexpected for this CPV code)")


if __name__ == "__main__":
    try:
        test_validation()
        test_suggestions()
        test_integration()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)