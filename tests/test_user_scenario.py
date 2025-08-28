#!/usr/bin/env python3
"""Test the exact scenario reported by the user."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.validations import ValidationManager

def test_user_scenario():
    """Test the exact validation scenario reported by user."""
    
    print("=" * 60)
    print("Testing User's Validation Scenario")
    print("=" * 60)
    
    # Simulate the user's form data with social criteria "Drugo" selected
    session_state = {
        # Main criteria selections
        'selectionCriteria.price': True,  # Cena selected
        'selectionCriteria.priceRatio': 50,  # 50 points for price
        
        'selectionCriteria.socialCriteria': True,  # Social criteria selected
        
        # Social criteria sub-options - only "Drugo" selected
        'selectionCriteria.socialCriteriaOptions.otherSocial': True,  # "Drugo" checkbox
        'selectionCriteria.socialCriteriaOptions.otherSocialDescription': 'Zaposlovanje lokalnega prebivalstva',  # Description for "Drugo"
        'selectionCriteria.socialCriteriaOtherRatio': 20,  # 20 points for social "Drugo"
        
        # Other criteria selections  
        'selectionCriteria.shorterDeadline': True,
        'selectionCriteria.shorterDeadlineRatio': 30,
        
        'selectionCriteria.longerWarranty': True, 
        'selectionCriteria.longerWarrantyRatio': 40,
        
        'selectionCriteria.otherCriteriaCustom': True,  # "Druga merila" selected
        'selectionCriteria.otherCriteriaDescription': 'Dodatni pogoji za kvaliteto',  # Description for other criteria
        'selectionCriteria.otherCriteriaCustomRatio': 30
    }
    
    validator = ValidationManager(session_state)
    
    # Test the problematic methods
    print("\n1. Testing _has_social_suboptions:")
    has_social = validator._has_social_suboptions('selectionCriteria')
    print(f"   Result: {has_social}")
    print(f"   Expected: True (because 'Drugo' is selected with description)")
    
    print("\n2. Testing full validation:")
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        print(f"   ❌ Validation errors found:")
        for error in errors:
            print(f"      - {error}")
    else:
        print(f"   ✅ No validation errors")
    
    print("\n3. Checking specific issues:")
    
    # Check if social criteria points are recognized
    social_points = session_state.get('selectionCriteria.socialCriteriaOtherRatio', 0)
    print(f"   Social criteria 'Drugo' points: {social_points}")
    
    # Check total points
    total = (session_state.get('selectionCriteria.priceRatio', 0) +
             session_state.get('selectionCriteria.socialCriteriaOtherRatio', 0) +
             session_state.get('selectionCriteria.shorterDeadlineRatio', 0) +
             session_state.get('selectionCriteria.longerWarrantyRatio', 0) +
             session_state.get('selectionCriteria.otherCriteriaCustomRatio', 0))
    print(f"   Total points: {total} (user mentioned 170)")
    
    print("\n" + "=" * 60)
    
    # Now test with lots mode
    print("\nTesting with LOTS mode:")
    print("=" * 60)
    
    session_state_lots = {
        'lot_mode': 'multiple',
        'current_lot_index': 0,
        # Same data but with lot prefix
        'lot_0_selectionCriteria.price': True,
        'lot_0_selectionCriteria.priceRatio': 50,
        'lot_0_selectionCriteria.socialCriteria': True,
        'lot_0_selectionCriteria.socialCriteriaOptions.otherSocial': True,
        'lot_0_selectionCriteria.socialCriteriaOptions.otherSocialDescription': 'Zaposlovanje lokalnega prebivalstva',
        'lot_0_selectionCriteria.socialCriteriaOtherRatio': 20,
        'lot_0_selectionCriteria.otherCriteriaCustom': True,
        'lot_0_selectionCriteria.otherCriteriaDescription': 'Dodatni pogoji',
        'lot_0_selectionCriteria.otherCriteriaCustomRatio': 30
    }
    
    validator_lots = ValidationManager(session_state_lots)
    is_valid_lots, errors_lots = validator_lots.validate_merila('lot_0_selectionCriteria')
    
    if errors_lots:
        print(f"   ❌ Validation errors in lots mode:")
        for error in errors_lots:
            print(f"      - {error}")
    else:
        print(f"   ✅ No validation errors in lots mode")
    
    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_user_scenario()