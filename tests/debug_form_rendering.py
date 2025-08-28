#!/usr/bin/env python3
"""Debug what's actually being rendered in the form."""

import json
import streamlit as st

st.set_page_config(page_title="Debug Form Rendering")

st.title("Debug: Merila Form Structure")

# Load the JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema_data = f.read()
    schema = json.loads(schema_data)

# Find selectionCriteria section
selection_criteria_props = None
for section in schema:
    if isinstance(section, dict) and 'properties' in section:
        if 'selectionCriteria' in section['properties']:
            selection_criteria_props = section['properties']['selectionCriteria']['properties']
            break

if not selection_criteria_props:
    st.error("Could not find selectionCriteria in schema")
else:
    st.success("Found selectionCriteria section")
    
    # Show main boolean criteria
    st.header("Main Criteria (Boolean fields)")
    main_criteria = []
    for key, value in selection_criteria_props.items():
        if isinstance(value, dict) and value.get('type') == 'boolean':
            if 'Options' not in key and 'Header' not in key:
                title = value.get('title', key)
                main_criteria.append(f"- **{key}**: {title}")
    
    st.markdown("\n".join(main_criteria))
    
    # Show social sub-options
    st.header("Social Sub-Options")
    social_options = selection_criteria_props.get('socialCriteriaOptions', {}).get('properties', {})
    social_list = []
    for key, value in social_options.items():
        if isinstance(value, dict) and value.get('type') == 'boolean':
            title = value.get('title', key)
            social_list.append(f"- **{key}**: {title}")
    
    st.markdown("\n".join(social_list))
    
    # Check for duplicates
    st.header("Duplicate Check")
    
    # Get all titles
    main_titles = []
    social_titles = []
    
    for key, value in selection_criteria_props.items():
        if isinstance(value, dict) and value.get('type') == 'boolean':
            if 'Options' not in key and 'Header' not in key:
                main_titles.append(value.get('title', key))
    
    for key, value in social_options.items():
        if isinstance(value, dict) and value.get('type') == 'boolean':
            social_titles.append(value.get('title', key))
    
    # Find exact duplicates
    all_titles = main_titles + social_titles
    seen = set()
    duplicates = []
    for title in all_titles:
        if title in seen:
            duplicates.append(title)
        seen.add(title)
    
    if duplicates:
        st.error(f"Found duplicate titles: {duplicates}")
    else:
        st.success("No exact duplicate titles found")
    
    # Show similar titles
    st.header("Similar Titles (potential confusion)")
    for main in main_titles:
        for social in social_titles:
            if 'Drugo' in main and 'Drugo' in social and main != social:
                st.warning(f"Main: '{main}' vs Social: '{social}'")