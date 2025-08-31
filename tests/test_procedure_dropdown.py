#!/usr/bin/env python3
"""Test procedure dropdown with new option."""

import streamlit as st
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.form_renderer_compat import render_form
from utils.schema_utils import load_json_schema

# Initialize Streamlit
st.set_page_config(page_title="Test Procedure Dropdown", layout="wide")
st.title("Test Procedure Dropdown")

# Load schema
schema = load_json_schema('json_files/SEZNAM_POTREBNIH_PODATKOV.json')

# Initialize session state
if 'schema' not in st.session_state:
    st.session_state['schema'] = schema
if 'current_lot' not in st.session_state:
    st.session_state.current_lot = None

# Get the submission procedure properties
procedure_props = schema['properties']['submissionProcedure']['properties']

st.write("## Testing Procedure Dropdown")
st.write("This test verifies that the new procedure option appears in the dropdown with the correct legal reference.")

# Create columns for before/after comparison
col1, col2 = st.columns(2)

with col1:
    st.write("### JSON Schema Values:")
    procedures = procedure_props['procedure']['enum']
    for i, proc in enumerate(procedures, 1):
        if "postopek s pogajanji z objavo" in proc:
            st.write(f"**{i}. {proc}** ← New procedure")
        else:
            st.write(f"{i}. {proc}")

with col2:
    st.write("### Dropdown Display Values:")
    st.info("What users will see in the dropdown (with legal references):")
    
# Render just the procedure field
with st.expander("Live Dropdown Test", expanded=True):
    st.write("#### Select a procedure:")
    
    # Initialize session state for the procedure field
    if 'submissionProcedure.procedure' not in st.session_state:
        st.session_state['submissionProcedure.procedure'] = procedures[0]
    
    # Render the actual form field
    render_form(
        {'procedure': procedure_props['procedure']}, 
        parent_key='submissionProcedure',
        lot_context=None
    )
    
    # Show selected value
    selected = st.session_state.get('submissionProcedure.procedure', '')
    if selected:
        st.success(f"Selected value in session state: **{selected}**")
        if "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)" == selected:
            st.balloons()
            st.success("✅ New procedure is working correctly!")

st.write("---")
st.write("### Expected Result:")
st.write("The dropdown should show 9 options, with the new procedure at position 6:")
st.write('- **"postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju) (45. člen ZJN-3)"**')
st.write("")
st.info("Run this test with: `streamlit run tests/test_procedure_dropdown.py`")