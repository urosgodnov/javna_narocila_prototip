#!/usr/bin/env python3
"""Test to simulate actual form behavior."""

import streamlit as st
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Load schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

st.title("Test Merila Validation")

# Get selectionCriteria properties from schema
criteria_props = {}
if 'selectionCriteria' in schema.get('properties', {}):
    sc = schema['properties']['selectionCriteria']
    if '$ref' in sc:
        ref_path = sc['$ref'].replace('#/$defs/', '')
        if '$defs' in schema and ref_path in schema['$defs']:
            criteria_props = schema['$defs'][ref_path].get('properties', {})

# Render checkboxes exactly as the form would
st.header("A. IZBIRA MERIL")

# Price checkbox
price_key = 'selectionCriteria.price'
if st.checkbox("Cena", key=price_key):
    ratio_key = 'selectionCriteria.priceRatio'
    points = st.number_input("→ točke", min_value=0, max_value=100, value=0, key=ratio_key)

# Debug: Show session state
st.sidebar.header("Debug Info")
st.sidebar.write("Session state keys related to criteria:")
for key in st.session_state:
    if 'selectionCriteria' in key or 'price' in key.lower():
        st.sidebar.write(f"- {key}: {st.session_state[key]}")

# Validation button
if st.button("Validate (Naprej)"):
    from utils.validations import ValidationManager
    
    # Log session state
    logging.info("=== Validation Button Clicked ===")
    logging.info(f"Price checkbox value: {st.session_state.get(price_key)}")
    logging.info(f"Price ratio value: {st.session_state.get('selectionCriteria.priceRatio')}")
    
    validator = ValidationManager(schema, st.session_state)
    is_valid, errors = validator.validate_merila('selectionCriteria')
    
    if errors:
        for error in errors:
            st.error(f"⚠️ {error}")
    else:
        st.success("✅ Validation passed!")
    
    # Show warnings
    for warning in validator.get_warnings():
        st.warning(f"ℹ️ {warning}")