#!/usr/bin/env python3
"""Test script to verify social criteria 'Drugo' (Other) validation fix."""

import sys
import os
import streamlit as st
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.validations import ValidationManager

def test_social_criteria_validation():
    """Test social criteria validation with 'Drugo' option."""
    
    print("=" * 60)
    print("Testing Social Criteria 'Drugo' Validation Fix")
    print("=" * 60)
    
    # Test Case 1: Without lots - Drugo selected with description
    print("\n1. Testing WITHOUT lots - 'Drugo' selected with description:")
    session_state = {
        'selectionCriteria.price': True,  # Add main price criterion
        'selectionCriteria.priceRatio': 50,
        'selectionCriteria.socialCriteria': True,
        'selectionCriteria.socialCriteriaOptions.otherSocial': True,
        'selectionCriteria.socialCriteriaOptions.otherSocialDescription': 'Zaposlovanje lokalnega prebivalstva',
        'selectionCriteria.socialCriteriaOtherRatio': 15
    }
    
    # Debug: Show what keys are being searched
    print(f"Session state keys: {list(session_state.keys())}")
    
    validator = ValidationManager(session_state)
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        print(f"❌ FAILED - Errors found: {errors}")
    else:
        print(f"✅ PASSED - No validation errors")
    
    
    # Test Case 2: With lots - Drugo selected with description
    print("\n2. Testing WITH lots (lot_0) - 'Drugo' selected with description:")
    session_state = {
        'lot_mode': 'multiple',
        'current_lot_index': 0,
        'lot_0_selectionCriteria.price': True,
        'lot_0_selectionCriteria.priceRatio': 50,
        'lot_0_selectionCriteria.socialCriteria': True,
        'lot_0_selectionCriteria.socialCriteriaOptions.otherSocial': True,
        'lot_0_selectionCriteria.socialCriteriaOptions.otherSocialDescription': 'Zaposlovanje lokalnega prebivalstva',
        'lot_0_selectionCriteria.socialCriteriaOtherRatio': 15
    }
    
    validator = ValidationManager(session_state)
    is_valid, errors = validator.validate_merila('lot_0_selectionCriteria')
    
    if errors:
        print(f"❌ FAILED - Errors found: {errors}")
    else:
        print(f"✅ PASSED - No validation errors")
    
    
    # Test Case 3: Without lots - Drugo selected WITHOUT description (should fail)
    print("\n3. Testing WITHOUT lots - 'Drugo' selected WITHOUT description:")
    session_state = {
        'selectionCriteria.price': True,
        'selectionCriteria.priceRatio': 50,
        'selectionCriteria.socialCriteria': True,
        'selectionCriteria.socialCriteriaOptions.otherSocial': True,
        # Missing: 'selectionCriteria.socialCriteriaOptions.otherSocialDescription'
        'selectionCriteria.socialCriteriaOtherRatio': 15
    }
    
    validator = ValidationManager(session_state)
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        print(f"✅ PASSED - Expected error found: {errors}")
    else:
        print(f"❌ FAILED - Should have validation error for missing description")
    
    
    # Test Case 4: With other social options selected (not Drugo)
    print("\n4. Testing WITHOUT lots - Other social options (not 'Drugo'):")
    session_state = {
        'selectionCriteria.price': True,
        'selectionCriteria.priceRatio': 50,
        'selectionCriteria.socialCriteria': True,
        'selectionCriteria.socialCriteriaOptions.youngEmployeesShare': True,
        'selectionCriteria.socialCriteriaYoungRatio': 20
    }
    
    validator = ValidationManager(session_state)
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        print(f"❌ FAILED - Errors found: {errors}")
    else:
        print(f"✅ PASSED - No validation errors")
    
    
    # Test Case 5: Complex case - Multiple criteria including Drugo
    print("\n5. Testing complex case - Multiple criteria including 'Drugo':")
    session_state = {
        'selectionCriteria.price': True,
        'selectionCriteria.priceRatio': 60,
        'selectionCriteria.socialCriteria': True,
        'selectionCriteria.socialCriteriaOptions.youngEmployeesShare': True,
        'selectionCriteria.socialCriteriaYoungRatio': 10,
        'selectionCriteria.socialCriteriaOptions.otherSocial': True,
        'selectionCriteria.socialCriteriaOptions.otherSocialDescription': 'Lokalno zaposlovanje',
        'selectionCriteria.socialCriteriaOtherRatio': 10,
        'selectionCriteria.shorterDeadline': True,
        'selectionCriteria.shorterDeadlineRatio': 20
    }
    
    validator = ValidationManager(session_state)
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        print(f"❌ FAILED - Errors found: {errors}")
    else:
        print(f"✅ PASSED - No validation errors")
    
        
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_social_criteria_validation()