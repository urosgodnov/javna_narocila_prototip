#!/usr/bin/env python3
"""
Test script to verify CPV code validation for social criteria.
This script sets CPV code 50700000-2 in session state for testing.
"""

import streamlit as st
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.criteria_validation import check_cpv_requires_social_criteria, validate_criteria_selection
from utils.criteria_manager import get_criteria_for_cpv

def main():
    st.title("Test CPV Validation for Social Criteria")
    
    # Test CPV code that requires social criteria
    test_cpv = "50700000-2"
    
    st.write(f"Testing CPV code: {test_cpv}")
    st.write("Description: Repair and maintenance services of building installations")
    
    # Check database for criteria requirements
    st.subheader("Database Check")
    criteria = get_criteria_for_cpv(test_cpv)
    if criteria:
        st.success(f"✅ CPV code {test_cpv} has criteria requirements in database:")
        for c in criteria:
            st.write(f"- {c['name']}: {c['description']}")
    else:
        st.error(f"❌ No criteria requirements found for CPV {test_cpv}")
    
    # Check social criteria requirement
    st.subheader("Social Criteria Check")
    social_cpv = check_cpv_requires_social_criteria([test_cpv])
    if social_cpv:
        st.success("✅ Social criteria are required for this CPV code")
        for code, info in social_cpv.items():
            st.write(f"- Code: {info['code']}")
            st.write(f"- Description: {info['description']}")
            st.write(f"- Restriction: {info['restriction']}")
    else:
        st.error("❌ No social criteria requirement found")
    
    # Test validation scenarios
    st.subheader("Validation Test Scenarios")
    
    # Scenario 1: Only price selected (should fail)
    st.write("**Scenario 1:** Only 'Cena' (price) selected")
    selected_criteria_1 = {
        'price': True,
        'additionalReferences': False,
        'additionalTechnicalRequirements': False,
        'shorterDeadline': False,
        'longerWarranty': False,
        'environmentalCriteria': False,
        'socialCriteria': False
    }
    result_1 = validate_criteria_selection([test_cpv], selected_criteria_1)
    if not result_1.is_valid:
        st.error(f"❌ Validation failed (as expected): {result_1.messages}")
    else:
        st.warning("⚠️ Validation passed (unexpected)")
    
    # Scenario 2: Price and social criteria selected (should pass)
    st.write("**Scenario 2:** 'Cena' and 'Socialna merila' selected")
    selected_criteria_2 = {
        'price': True,
        'additionalReferences': False,
        'additionalTechnicalRequirements': False,
        'shorterDeadline': False,
        'longerWarranty': False,
        'environmentalCriteria': False,
        'socialCriteria': True
    }
    result_2 = validate_criteria_selection([test_cpv], selected_criteria_2)
    if result_2.is_valid:
        st.success("✅ Validation passed (as expected)")
    else:
        st.error(f"❌ Validation failed (unexpected): {result_2.messages}")
    
    # Set CPV code in session state for the main app
    if st.button("Set CPV code in session state for main app"):
        st.session_state['orderType.cpvCodes'] = f"{test_cpv} - Repair and maintenance services"
        st.success(f"✅ Set CPV code {test_cpv} in session state")
        st.write("You can now navigate to step 13 in the main app to test validation")

if __name__ == "__main__":
    main()