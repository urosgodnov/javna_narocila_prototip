#!/usr/bin/env python3
"""Minimal test app for validation."""

import streamlit as st
from utils.criteria_validation import validate_criteria_selection, check_cpv_requires_additional_criteria
from utils.validation_control import should_validate, render_master_validation_toggle, render_step_validation_toggle

st.title("Validation Test App")

# Test validation control
st.header("1. Validation Control Test")
render_master_validation_toggle()

st.write("Master validation disabled:", st.session_state.get('validation_disabled', True))
st.write("Should validate (step 1):", should_validate(1))

render_step_validation_toggle(1)
st.write("Step 1 validation enabled:", st.session_state.get('step_1_validation_enabled', False))

# Test CPV validation
st.header("2. CPV Validation Test")

# Test CPV codes that require additional criteria
test_cpv_codes = ["79000000", "79200000", "79400000"]  # Business services
st.write("Testing CPV codes:", test_cpv_codes)

# Check which codes have restrictions
restricted = check_cpv_requires_additional_criteria(test_cpv_codes)
st.write("Restricted CPV codes:", restricted)

# Test validation with different criteria selections
st.subheader("Test Case 1: Only price selected (should fail)")
criteria1 = {"price": True}
result1 = validate_criteria_selection(test_cpv_codes, criteria1)
st.write("- Valid:", result1.is_valid)
if result1.messages:
    st.error(result1.messages[0])

st.subheader("Test Case 2: Price + another criterion (should pass)")
criteria2 = {"price": True, "additionalTechnicalRequirements": True}
result2 = validate_criteria_selection(test_cpv_codes, criteria2)
st.write("- Valid:", result2.is_valid)
if result2.is_valid:
    st.success("Validation passed!")

st.subheader("Test Case 3: No criteria selected")
criteria3 = {}
result3 = validate_criteria_selection(test_cpv_codes, criteria3)
st.write("- Valid:", result3.is_valid)
if result3.messages:
    st.warning(result3.messages[0])

# Interactive test
st.header("3. Interactive Test")

selected_cpv = st.text_input("Enter CPV code to test:", value="79000000")
if selected_cpv:
    st.write("Checking restrictions for:", selected_cpv)
    restricted = check_cpv_requires_additional_criteria([selected_cpv])
    if restricted:
        st.warning(f"This CPV code requires additional criteria: {restricted}")
    else:
        st.info("No restrictions for this CPV code")

st.markdown("---")
st.write("Session state:", dict(st.session_state))