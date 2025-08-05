"""Form rendering components for the main application form."""
import streamlit as st
from datetime import date


def _get_default_value(full_key, prop_details):
    """Get appropriate default value for form field."""
    if prop_details.get("type") == "number":
        return st.session_state.get(full_key, 0.0)
    elif prop_details.get("format") == "date":
        return st.session_state.get(full_key, date.today())
    elif prop_details.get("type") == "array":
        return st.session_state.get(full_key, [])
    else:
        return st.session_state.get(full_key, "")


def _render_string_field(label, full_key, current_value, prop_details):
    """Render string-type form fields based on format."""
    if prop_details.get("format") == "textarea":
        st.text_area(label, value=current_value, key=full_key)
    elif prop_details.get("format") == "date":
        st.date_input(label, value=current_value, key=full_key)
    elif prop_details.get("format") == "file":
        st.file_uploader(label, key=full_key)
    else:
        st.text_input(label, value=current_value, key=full_key)


def render_form_section(schema_properties, parent_key=""):
    """Render form fields based on JSON schema properties."""
    for prop_name, prop_details in schema_properties.items():
        full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
        label = prop_details.get("title", prop_name)
        
        # Get current value from session_state with appropriate defaults
        current_value = _get_default_value(full_key, prop_details)

        # Render appropriate form element based on property type
        if prop_details.get("type") == "object":
            st.subheader(label)
            render_form_section(prop_details.get("properties", {}), parent_key=full_key)
        elif prop_details.get("type") == "array" and "enum" in prop_details:
            st.multiselect(label, options=prop_details["enum"], default=current_value, key=full_key)
        elif prop_details.get("type") == "string" and "enum" in prop_details:
            index = prop_details["enum"].index(current_value) if current_value in prop_details["enum"] else 0
            st.selectbox(label, options=prop_details["enum"], index=index, key=full_key)
        elif prop_details.get("type") == "string":
            _render_string_field(label, full_key, current_value, prop_details)
        elif prop_details.get("type") == "number":
            st.number_input(label, value=current_value, key=full_key)