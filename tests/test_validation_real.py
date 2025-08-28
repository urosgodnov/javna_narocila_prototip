#!/usr/bin/env python3
"""Test validation with actual Streamlit session state."""

import streamlit as st

# Initialize Streamlit
st.set_page_config(page_title="Validation Test")

# Set up the REAL session state as the user would have it
st.session_state['selectionCriteria.price'] = True
st.session_state['selectionCriteria.priceRatio'] = 100.0

# Social criteria selected
st.session_state['selectionCriteria.socialCriteria'] = True

# Social sub-option "Drugo"
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocial'] = True
st.session_state['selectionCriteria.socialCriteriaOptions.otherSocialDescription'] = 'rad imeti krompir'
st.session_state['selectionCriteria.socialCriteriaOtherRatio'] = 50.0

# Social sub-option "Drugo, imam predlog" - THIS IS NOT otherCriteriaCustom!
st.session_state['selectionCriteria.socialCriteriaCustomRatio'] = 70.0

# DO NOT SET THIS - it's the confusion source!
# st.session_state['selectionCriteria.otherCriteriaCustom'] = True

st.write("# Validation Test")
st.write("Testing social criteria sub-options WITHOUT setting otherCriteriaCustom")

st.write("\n## Session State")
criteria_keys = sorted([k for k in st.session_state.keys() if 'criteria' in k.lower()])
for key in criteria_keys:
    st.write(f"- `{key}`: {st.session_state[key]}")

from utils.validations import ValidationManager

validator = ValidationManager(session_state=st.session_state)

st.write("\n## Validation Results")

# Check selected criteria
selected = validator._get_selected_criteria('selectionCriteria')
st.write("### Selected Criteria")
for crit, is_selected in selected.items():
    if is_selected:
        st.write(f"- ✅ {crit}")
    else:
        st.write(f"- ❌ {crit}")

# Check social sub-options
has_social = validator._has_social_suboptions('selectionCriteria')
st.write(f"\n**Has social sub-options:** {has_social}")

# Run full validation
is_valid, errors = validator.validate_merila('selectionCriteria')

st.write("\n### Validation Result")
if is_valid:
    st.success("✅ Validation passed!")
else:
    st.error("❌ Validation failed with errors:")
    for error in errors:
        st.write(f"- {error}")

# Calculate total points
total_points = (
    st.session_state.get('selectionCriteria.priceRatio', 0) +
    st.session_state.get('selectionCriteria.socialCriteriaOtherRatio', 0) +
    st.session_state.get('selectionCriteria.socialCriteriaCustomRatio', 0)
)
st.info(f"Total points: {total_points} (100 + 50 + 70)")