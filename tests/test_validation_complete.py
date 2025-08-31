#!/usr/bin/env python3
"""Complete validation logic test suite."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.validations import (
    validate_criteria_selection, 
    check_cpv_requires_additional_criteria,
    get_validation_summary
)
from utils.validation_control import should_validate
from utils.criteria_suggestions import get_suggested_criteria_for_cpv
import database

def test_cpv_restrictions():
    """Test CPV code restriction detection."""
    print("\n=== Testing CPV Restrictions ===")
    
    # Test cases
    test_cases = [
        (["79000000"], True, "Business services should have restrictions"),
        (["79200000", "79400000"], True, "Multiple business services"),
        (["45000000"], False, "Construction work (no restriction expected)"),
        ([], False, "Empty list should have no restrictions"),
    ]
    
    for cpv_codes, expected_has_restrictions, description in test_cases:
        restricted = check_cpv_requires_additional_criteria(cpv_codes)
        has_restrictions = len(restricted) > 0
        
        status = "✓" if has_restrictions == expected_has_restrictions else "✗"
        print(f"{status} {description}")
        if restricted:
            print(f"  - Restricted codes: {list(restricted.keys())}")

def test_validation_logic():
    """Test validation with different criteria combinations."""
    print("\n=== Testing Validation Logic ===")
    
    # CPV codes that require additional criteria
    cpv_with_restrictions = ["79000000", "79200000"]
    
    test_cases = [
        (
            {"price": True},
            False,
            "Only price selected - should FAIL"
        ),
        (
            {"price": True, "additionalTechnicalRequirements": True},
            True,
            "Price + technical requirements - should PASS"
        ),
        (
            {"price": True, "environmentalCriteria": True, "socialCriteria": True},
            True,
            "Price + multiple criteria - should PASS"
        ),
        (
            {},
            True,
            "No criteria selected - should PASS with warning"
        ),
        (
            {"additionalTechnicalRequirements": True},
            True,
            "Only non-price criteria - should PASS"
        ),
    ]
    
    for criteria, expected_valid, description in test_cases:
        result = validate_criteria_selection(cpv_with_restrictions, criteria)
        status = "✓" if result.is_valid == expected_valid else "✗"
        print(f"{status} {description}")
        if result.messages:
            print(f"  - Message: {result.messages[0][:80]}...")

def test_validation_control():
    """Test validation control logic."""
    print("\n=== Testing Validation Control ===")
    
    # Simulate different session states
    test_cases = [
        (
            {"validation_disabled": True, "step_1_validation_enabled": False},
            1,
            False,
            "Master disabled, step disabled - NO validation"
        ),
        (
            {"validation_disabled": False, "step_1_validation_enabled": False},
            1,
            True,
            "Master enabled, step disabled - YES validation"
        ),
        (
            {"validation_disabled": True, "step_1_validation_enabled": True},
            1,
            True,
            "Master disabled, step enabled - YES validation (override)"
        ),
        (
            {"validation_disabled": False, "step_1_validation_enabled": True},
            1,
            True,
            "Master enabled, step enabled - YES validation"
        ),
    ]
    
    for session_state, step_num, expected_validate, description in test_cases:
        # Mock session state
        import streamlit as st
        if 'session_state' not in dir(st):
            st.session_state = type('obj', (object,), {})()
        
        for key, value in session_state.items():
            setattr(st.session_state, key, value)
        
        result = should_validate(step_num)
        status = "✓" if result == expected_validate else "✗"
        print(f"{status} {description}")

def test_suggestions():
    """Test criteria suggestions based on CPV codes."""
    print("\n=== Testing Criteria Suggestions ===")
    
    test_cases = [
        (["79000000"], "Business services"),  # Should suggest references + technical
        (["45000000"], "Construction works"),  # Should suggest deadline + warranty
        (["90000000"], "Environmental services"),  # Should suggest environmental
        (["85000000"], "Social services"),  # Should suggest social criteria
    ]
    
    for cpv_codes, category in test_cases:
        suggestions = get_suggested_criteria_for_cpv(cpv_codes)
        print(f"\n{category} ({cpv_codes[0]}):")
        print(f"  - Suggested criteria: {suggestions['suggested_criteria']}")
        if suggestions.get('explanation'):
            print(f"  - Explanation: {suggestions['explanation'][:100]}...")

def test_validation_summary():
    """Test validation summary generation."""
    print("\n=== Testing Validation Summary ===")
    
    # Test with restricted CPV codes
    cpv_codes = ["79000000", "79200000", "79400000"]
    summary = get_validation_summary(cpv_codes)
    
    print(f"CPV codes: {cpv_codes}")
    print(f"Has restrictions: {summary['has_restrictions']}")
    print(f"Restricted count: {summary['restricted_count']}")
    print(f"Rules: {summary['rules']}")

def run_all_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("VALIDATION LOGIC TEST SUITE")
    print("=" * 60)
    
    # Initialize database
    database.init_db()
    
    # Run tests
    test_cpv_restrictions()
    test_validation_logic()
    test_validation_control()
    test_suggestions()
    test_validation_summary()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()