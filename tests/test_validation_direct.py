#!/usr/bin/env python3
"""Direct test of validation with streamlit."""

import streamlit as st
import sys
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

from utils.validations import validate_criteria_selection, check_cpv_requires_social_criteria

st.title("Test CPV Validation")

# Set up test data
cpv_code = st.text_input("CPV Code", value="50700000-2")
price_selected = st.checkbox("Cena", value=True)
social_selected = st.checkbox("Socialna merila", value=False)

if st.button("Validate"):
    cpv_codes = [cpv_code]
    selected_criteria = {
        'price': price_selected,
        'socialCriteria': social_selected,
    }
    
    # Check if social is required
    social_cpv = check_cpv_requires_social_criteria(cpv_codes)
    if social_cpv:
        st.warning(f"CPV koda {cpv_code} zahteva socialna merila")
    
    # Validate
    validation_result = validate_criteria_selection(cpv_codes, selected_criteria)
    
    if validation_result.is_valid:
        st.success("✓ Validacija uspešna")
    else:
        st.error("✗ Validacija ni uspešna")
        for msg in validation_result.messages:
            st.error(msg)