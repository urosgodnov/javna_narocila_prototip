#!/usr/bin/env python3
"""Test what should be shown in merila step."""

import json
import streamlit as st

st.set_page_config(page_title="Test Merila Structure")

st.title("🔍 Merila Step - Expected Structure")

# Load the JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get selectionCriteria properties
sel_crit_props = data.get('$defs', {}).get('selectionCriteriaProperties', {}).get('properties', {})

st.header("✅ What SHOULD be shown:")

st.subheader("A. IZBIRA MERIL (Main Criteria)")
main_criteria = []
for key, val in sel_crit_props.items():
    if val.get('type') == 'boolean' and 'Options' not in key:
        title = val.get('title', key)
        main_criteria.append(f"☐ {title}")

for item in main_criteria:
    st.write(item)

# Check for social criteria options
if 'socialCriteriaOptions' in sel_crit_props:
    social_props = sel_crit_props['socialCriteriaOptions'].get('properties', {})
    
    st.write("")  # Space
    st.subheader("→ Izberite socialna merila: (Social Sub-options)")
    st.write("*(Only shown when 'Socialna merila' is checked)*")
    
    social_options = []
    for key, val in social_props.items():
        if val.get('type') == 'boolean':
            title = val.get('title', key)
            social_options.append(f"☐ {title}")
    
    for item in social_options:
        st.write(f"  {item}")

st.divider()

st.header("❌ What should NOT be shown:")

# Check for fields from other sections that might be bleeding through
other_sections = ['participationAndExclusion', 'participationConditions']
wrong_fields = []

for section_name in other_sections:
    # Find this section in the schema
    section_props = data.get('properties', {}).get(section_name, {})
    if '$ref' in section_props:
        # Resolve reference
        ref_path = section_props['$ref'].split('/')
        ref_props = data
        for part in ref_path:
            if part and part != '#':
                ref_props = ref_props.get(part, {})
        section_props = ref_props
    
    if 'properties' in section_props:
        # Look for any AI or custom fields
        for key, val in section_props['properties'].items():
            if isinstance(val, dict) and 'properties' in val:
                # Check nested properties
                for nested_key, nested_val in val['properties'].items():
                    if nested_val.get('type') == 'boolean':
                        title = nested_val.get('title', '')
                        if 'AI' in nested_key or 'prosim' in title.lower() or 'predlog' in title.lower():
                            wrong_fields.append(f"☐ {title} (from {section_name}.{key})")

if wrong_fields:
    st.error("These fields from OTHER sections should NOT appear in merila:")
    for field in wrong_fields:
        st.write(field)
else:
    st.success("No fields from other sections found")

st.divider()

st.header("📋 Summary")
st.info("""
**Correct structure:**
1. Main criteria (8 checkboxes including "Socialna merila")
2. When "Socialna merila" is checked → show 7 social sub-options
3. "Drugo, imam predlog" and "Drugo, prosim predlog AI" should ONLY appear as social sub-options

**Common issues:**
- Fields from participationAndExclusion appearing in merila step
- Social sub-options appearing as main criteria
- Duplicate checkboxes with similar names
""")