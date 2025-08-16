"""
Test script to verify dashboard functionality
"""

import streamlit as st
import database
from ui.dashboard import render_dashboard
from utils.schema_utils import load_json_schema, clear_form_data

st.set_page_config(layout="wide", page_title="Test Dashboard")

# Initialize navigation state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'edit_record_id' not in st.session_state:
    st.session_state.edit_record_id = None
if 'schema' not in st.session_state:
    st.session_state['schema'] = load_json_schema('SEZNAM_POTREBNIH_PODATKOV.json')
if "current_step" not in st.session_state:
    st.session_state.current_step = 0

# Initialize database
database.init_db()

# Render dashboard
render_dashboard()

# Add some test data button for demonstration
if st.sidebar.button("Add Test Data"):
    test_data = {
        'projectInfo': {'projectName': 'Test Javno Naročilo'},
        'orderType': {'type': 'blago', 'estimatedValue': 50000},
        'submissionProcedure': {'procedure': 'odprti postopek'}
    }
    new_id = database.create_procurement(test_data)
    st.success(f"Created test procurement with ID: {new_id}")
    st.rerun()