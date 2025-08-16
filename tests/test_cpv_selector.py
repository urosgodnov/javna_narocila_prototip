#!/usr/bin/env python3
"""Test script for CPV selector integration."""

import streamlit as st
from ui.components.cpv_selector import render_cpv_selector
from utils.cpv_manager import get_cpv_count

st.set_page_config(page_title="CPV Selector Test", layout="wide")

st.title("Test CPV Selector Component")

# Check if CPV codes are loaded
cpv_count = get_cpv_count()
st.info(f"CPV codes in database: {cpv_count}")

if cpv_count > 0:
    st.markdown("### Test CPV Selector")
    
    # Test basic selector
    st.markdown("#### Basic CPV Selector")
    cpv_value = render_cpv_selector(
        field_key="test_cpv_basic",
        field_schema={
            'title': 'CPV kode',
            'description': 'Izberite CPV kode'
        },
        current_value="",
        disabled=False
    )
    
    st.write(f"Selected CPV codes: {cpv_value}")
    
    # Test with pre-filled value
    st.markdown("#### CPV Selector with Pre-filled Values")
    cpv_value2 = render_cpv_selector(
        field_key="test_cpv_prefilled",
        field_schema={
            'title': 'CPV kode s predizpolnjenimi vrednostmi',
            'description': 'Test z obstoječimi vrednostmi'
        },
        current_value="30000000-9, 45000000-7",
        disabled=False
    )
    
    st.write(f"Selected CPV codes: {cpv_value2}")
    
    # Test disabled selector
    st.markdown("#### Disabled CPV Selector")
    cpv_value3 = render_cpv_selector(
        field_key="test_cpv_disabled",
        field_schema={
            'title': 'Onemogočen CPV izbor',
            'description': 'Test onemogočenega selectorja'
        },
        current_value="72000000-5",
        disabled=True
    )
    
    st.write(f"Selected CPV codes: {cpv_value3}")
else:
    st.warning("No CPV codes in database. Please import CPV codes first.")
    
    # Show import instructions
    st.markdown("""
    ### How to import CPV codes:
    1. Go to Admin Panel
    2. Navigate to CPV codes tab
    3. Click "Load sample CPV codes" or import from Excel file
    """)