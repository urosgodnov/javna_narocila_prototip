#!/usr/bin/env python3
"""Simple validation test with Streamlit."""

import streamlit as st
import sys
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

from utils.criteria_validation import validate_criteria_selection

st.title("Simple Validation Test")

# Set test data
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.price = True
    st.session_state.social = False

# Show checkboxes
price = st.checkbox("Price", value=st.session_state.price)
social = st.checkbox("Social", value=st.session_state.social)

st.session_state.price = price
st.session_state.social = social

# Validate button
if st.button("Validate"):
    cpv_codes = ['50700000-2']
    selected = {
        'price': price,
        'socialCriteria': social
    }
    
    result = validate_criteria_selection(cpv_codes, selected)
    
    if result.is_valid:
        st.success("Valid!")
    else:
        st.error("Invalid!")
        for msg in result.messages:
            st.error(msg)
            
# Navigation test
col1, col2 = st.columns(2)
with col2:
    if st.button("Next →"):
        cpv_codes = ['50700000-2']
        selected = {
            'price': st.session_state.price,
            'socialCriteria': st.session_state.social
        }
        
        result = validate_criteria_selection(cpv_codes, selected)
        
        if result.is_valid:
            st.success("Navigation allowed")
        else:
            st.error("Navigation blocked!")
            for msg in result.messages:
                st.error(msg)