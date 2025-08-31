#!/usr/bin/env python3
"""
Interactive test for the Merila validation UI.
Run with: streamlit run test_ui_validation.py
"""

import streamlit as st
import database
from utils.validations import (
    validate_criteria_selection,
    check_cpv_requires_additional_criteria,
    get_validation_summary
)
from utils.criteria_suggestions import (
    get_suggested_criteria_for_cpv,
    get_criteria_help_text,
    get_criteria_display_names
)

# Initialize database
database.init_db()

st.set_page_config(page_title="Test Merila Validation", layout="wide")

st.title("🧪 Test Merila (Criteria) Validation")
st.markdown("Test interface for Stories 21.1, 21.2, and 21.3")

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.header("1️⃣ Select CPV Codes")
    
    # Predefined test CPV codes
    test_cpv_options = {
        "71000000-8": "Architecture services (RESTRICTED)",
        "79000000-4": "Business services (RESTRICTED)",
        "48000000-8": "Software packages (RESTRICTED)",
        "45000000-7": "Construction work (NO RESTRICTION)",
        "03000000-1": "Agricultural products (NO RESTRICTION)",
        "90000000-7": "Environmental services (NO RESTRICTION)"
    }
    
    selected_cpv = st.multiselect(
        "Select CPV codes to test:",
        options=list(test_cpv_options.keys()),
        format_func=lambda x: f"{x} - {test_cpv_options[x]}",
        default=["71000000-8"]
    )
    
    if selected_cpv:
        # Check for restrictions
        restricted = check_cpv_requires_additional_criteria(selected_cpv)
        if restricted:
            st.warning(f"⚠️ {len(restricted)} CPV code(s) have criteria restrictions")
            for code, info in restricted.items():
                st.caption(f"• {code}: {info['restriction']}")
        else:
            st.success("✅ No restrictions for selected CPV codes")

with col2:
    st.header("2️⃣ Select Criteria")
    
    # Criteria checkboxes
    criteria_names = get_criteria_display_names()
    selected_criteria = {}
    
    for key, display_name in criteria_names.items():
        selected_criteria[key] = st.checkbox(display_name, key=f"criteria_{key}")
        
        # Show help text
        help_texts = get_criteria_help_text()
        if key in help_texts and selected_criteria[key]:
            with st.expander(f"ℹ️ About {display_name}", expanded=False):
                st.caption(help_texts[key])

st.markdown("---")

# Validation section
st.header("3️⃣ Validation Results")

if selected_cpv:
    # Run validation
    validation_result = validate_criteria_selection(selected_cpv, selected_criteria)
    
    col_result, col_suggestions = st.columns(2)
    
    with col_result:
        st.subheader("Validation Status")
        
        if validation_result.is_valid:
            st.success("✅ **VALID** - Criteria selection meets all requirements")
        else:
            st.error("❌ **INVALID** - Additional criteria required")
            
            if validation_result.messages:
                for msg in validation_result.messages:
                    st.warning(msg)
            
            if validation_result.restricted_cpv_codes:
                st.markdown("**Restricted CPV codes:**")
                for cpv in validation_result.restricted_cpv_codes:
                    st.markdown(f"• {cpv['code']} - {cpv['description']}")
        
        # Validation summary
        st.subheader("Summary")
        summary = get_validation_summary(selected_cpv)
        if summary['has_restrictions']:
            st.info(f"📊 {summary['rules'][0]}")
    
    with col_suggestions:
        st.subheader("Suggestions")
        
        # Get suggestions
        suggestions = get_suggested_criteria_for_cpv(selected_cpv)
        
        if suggestions['explanation']:
            st.info(f"💡 {suggestions['explanation']}")
        
        if suggestions['recommended']:
            st.markdown("**Recommended criteria:**")
            for criteria in suggestions['recommended']:
                if criteria in criteria_names:
                    st.markdown(f"• {criteria_names[criteria]}")
            
            # Auto-select button
            if st.button("✨ Auto-select recommended", type="primary"):
                st.info("In the real form, this would select the recommended criteria")
        
        if suggestions['commonly_used']:
            st.markdown("**Also commonly used:**")
            for criteria in suggestions['commonly_used']:
                if criteria in criteria_names:
                    st.markdown(f"• {criteria_names[criteria]}")

# Educational section
with st.expander("📚 Learn More", expanded=False):
    st.markdown("""
    ### Why Additional Criteria Are Required
    
    According to Slovenian Public Procurement Law (ZJN-3), certain types of services 
    cannot use price as the only selection criterion. This includes:
    
    - **Intellectual services** (architecture, engineering, consulting)
    - **Social services** (healthcare, education)
    - **Creative services** (design, marketing)
    - **Complex technical services** (specialized IT, research)
    
    The goal is to ensure quality and value, not just the lowest price.
    
    ### How It Works
    
    1. **CPV Code Selection** - When you select CPV codes, the system checks if any have restrictions
    2. **Validation** - If restricted codes are found and only price is selected, validation fails
    3. **Suggestions** - The system suggests appropriate additional criteria based on service type
    4. **Auto-select** - You can automatically select recommended criteria with one click
    5. **Override** - Advanced users can override warnings if needed (at their own risk)
    """)

st.markdown("---")
st.caption("Test interface for Merila validation feature - Stories 21.1, 21.2, and 21.3")