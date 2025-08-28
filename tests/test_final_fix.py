#!/usr/bin/env python3
"""Test the fix for social criteria sub-options."""

import streamlit as st
st.set_page_config(page_title="Test Final Fix")

st.write("# Testing Social Criteria Fix")
st.write("This test simulates the user's exact scenario with the new social sub-options.")

# Set up the user's scenario
st.session_state['selectionCriteria.price'] = True
st.session_state['selectionCriteria.priceRatio'] = 100.0

# Social criteria selected
st.session_state['selectionCriteria.socialCriteria'] = True

# Social sub-option 1: "Drugo" with description
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocial'] = True
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocialDescription'] = 'rad imeti krompir'
st.session_state['selectionCriteria.socialCriteriaOtherRatio'] = 50.0

# Social sub-option 2: "Drugo, imam predlog" with description  
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocialCustom'] = True
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocialCustomDescription'] = 'kakovost krompirja'
st.session_state['selectionCriteria.socialCriteriaCustomRatio'] = 70.0

st.write("## Session State")
st.write("**Selected criteria:**")
criteria_keys = sorted([k for k in st.session_state.keys() if 'criteria' in k.lower()])
for key in criteria_keys:
    val = st.session_state[key]
    if val and val != 0:
        st.write(f"- `{key}`: {val}")

from utils.validations import ValidationManager

validator = ValidationManager(session_state=st.session_state)

st.write("\n## Validation Check")

# Test _has_social_suboptions
has_social = validator._has_social_suboptions('selectionCriteria')
if has_social:
    st.success(f"✅ Social sub-options detected: {has_social}")
else:
    st.error(f"❌ Social sub-options NOT detected")

# Test full validation
is_valid, errors = validator.validate_merila('selectionCriteria')

st.write("\n## Validation Results")
if is_valid:
    st.success("✅ Validation PASSED! No errors.")
else:
    st.error("❌ Validation failed:")
    for error in errors:
        st.write(f"- {error}")

# Show warnings if any
warnings = validator.get_warnings()
if warnings:
    st.warning("⚠️ Warnings:")
    for warning in warnings:
        st.write(f"- {warning}")

# Calculate total points
total_points = (
    st.session_state.get('selectionCriteria.priceRatio', 0) +
    st.session_state.get('selectionCriteria.socialCriteriaOtherRatio', 0) +
    st.session_state.get('selectionCriteria.socialCriteriaCustomRatio', 0)
)
st.info(f"**Total points:** {total_points} (100 + 50 + 70 = 220)")

st.write("\n## Summary")
st.write("""
The fix adds three "Drugo" variants as SOCIAL SUB-OPTIONS:
1. **Drugo** - requires description
2. **Drugo, imam predlog** - requires description  
3. **Drugo, prosim predlog AI** - no description needed

These are now correctly part of Social Criteria, not separate main criteria.
""")