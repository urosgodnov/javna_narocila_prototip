#!/usr/bin/env python3
"""Test validation with exact user scenario."""

import streamlit as st
st.set_page_config(page_title="Test")

# Set up session state exactly as user described
st.session_state['selectionCriteria.price'] = True
st.session_state['selectionCriteria.priceRatio'] = 100.0

st.session_state['selectionCriteria.socialCriteria'] = True
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocial'] = True
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocialDescription'] = 'rad imeti krompir'
st.session_state['selectionCriteria.socialCriteriaOtherRatio'] = 50.0

st.session_state['selectionCriteria.otherCriteriaCustom'] = True
st.session_state['selectionCriteria.otherCriteriaDescription'] = 'kakovost krompirja'
st.session_state['selectionCriteria.otherCriteriaCustomRatio'] = 70.0

st.write("## Testing Validation")
st.write("Session state keys related to criteria:")

# Show all criteria-related keys
criteria_keys = [k for k in st.session_state.keys() if 'criteria' in k.lower()]
for key in sorted(criteria_keys):
    st.write(f"- `{key}`: {st.session_state[key]}")

from utils.validations import ValidationManager

st.write("\n## Validation Test")

validator = ValidationManager(session_state=st.session_state)

# Test _has_social_suboptions
has_social = validator._has_social_suboptions('selectionCriteria')
st.write(f"Has social suboptions: **{has_social}**")

# Test full validation
is_valid, errors = validator.validate_merila('selectionCriteria')
st.write(f"Is valid: **{is_valid}**")

if errors:
    st.error("Validation errors:")
    for error in errors:
        st.write(f"- {error}")
else:
    st.success("No validation errors!")

# Show what the validator sees for selected criteria
selected = validator._get_selected_criteria('selectionCriteria')
st.write("\n## Selected Criteria (as seen by validator):")
for crit, val in selected.items():
    if val:
        st.write(f"- {crit}: {val}")