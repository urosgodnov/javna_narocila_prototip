#!/usr/bin/env python3
"""Debug script to check actual session state during validation."""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.validations import ValidationManager

# This will help us understand what's actually in session state
def debug_session_state():
    print("=" * 80)
    print("DEBUG: Session State Analysis")
    print("=" * 80)
    
    # Find all social criteria related keys
    social_keys = [k for k in st.session_state.keys() if 'social' in k.lower()]
    print(f"\nFound {len(social_keys)} keys with 'social':")
    for key in sorted(social_keys):
        value = st.session_state[key]
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Find all selection criteria keys
    criteria_keys = [k for k in st.session_state.keys() if 'criteria' in k.lower()]
    print(f"\nFound {len(criteria_keys)} keys with 'criteria':")
    for key in sorted(criteria_keys):
        value = st.session_state[key]
        if 'social' not in key.lower():  # Don't repeat social ones
            print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Check specific problematic keys
    print("\n" + "=" * 80)
    print("Checking specific keys that should work:")
    
    test_keys = [
        'selectionCriteria.socialCriteria',
        'selectionCriteria.socialCriteriaOptions.otherSocial',
        'selectionCriteria.socialCriteriaOptions.otherSocialDescription',
        'selectionCriteria.socialCriteriaOtherRatio',
        'selectionCriteria.otherCriteriaCustom',
        'selectionCriteria.otherCriteriaDescription'
    ]
    
    for key in test_keys:
        value = st.session_state.get(key, "NOT FOUND")
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("Testing ValidationManager with actual session state:")
    
    # Create validator with actual session state
    validator = ValidationManager(session_state=st.session_state)
    
    # Test _has_social_suboptions
    result = validator._has_social_suboptions('selectionCriteria')
    print(f"\n_has_social_suboptions result: {result}")
    
    # Test _get_selected_criteria
    selected = validator._get_selected_criteria('selectionCriteria')
    print(f"\n_get_selected_criteria result: {selected}")
    
    # Test full validation
    is_valid, errors = validator.validate_merila('selectionCriteria')
    print(f"\nvalidate_merila result: is_valid={is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")

if __name__ == "__main__":
    # Initialize minimal session state if needed
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 11
    
    debug_session_state()