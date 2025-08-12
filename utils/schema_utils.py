"""Utilities for handling JSON schema and session data."""
import json
import streamlit as st


def load_json_schema(file_path):
    """Load JSON schema from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_session_state(key, value):
    """Update session state for form field changes."""
    st.session_state[key] = value


def get_form_data_from_session():
    """
    Reconstructs the nested form data dictionary from Streamlit's flat session_state.
    """
    form_data = {}
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    if not schema_properties:
        return {}

    for key, value in st.session_state.items():
        top_level_key = key.split('.')[0]
        if top_level_key in schema_properties:
            parts = key.split('.')
            d = form_data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value
    return form_data


def clear_form_data():
    """
    Clear all form data from session state.
    Preserves navigation and schema data.
    """
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    keys_to_remove = []
    
    # Identify all form-related keys
    for key in st.session_state.keys():
        top_level_key = key.split('.')[0]
        if top_level_key in schema_properties:
            keys_to_remove.append(key)
        # Also remove widget keys
        if key.startswith('widget_'):
            keys_to_remove.append(key)
    
    # Remove the identified keys
    for key in keys_to_remove:
        del st.session_state[key]
    
    # Clear any tracking data
    if '_last_loaded_data' in st.session_state:
        del st.session_state['_last_loaded_data']
    if 'unsaved_changes' in st.session_state:
        del st.session_state['unsaved_changes']