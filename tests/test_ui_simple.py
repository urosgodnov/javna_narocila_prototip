#!/usr/bin/env python3
"""Simple UI test with validation."""

import streamlit as st
from utils.validations import validate_criteria_selection, check_cpv_requires_additional_criteria
from utils.validation_control import render_master_validation_toggle, render_step_validation_toggle, should_validate

st.set_page_config(page_title="Validation Test", layout="wide")
st.title("🧪 Test Validation Logic")

# Master validation toggle
col1, col2 = st.columns([1, 2])
with col1:
    st.header("1️⃣ Validation Control")
    render_master_validation_toggle()
    
with col2:
    st.header("Current State")
    st.info(f"Master disabled: {st.session_state.get('validation_disabled', True)}")
    st.info(f"Should validate step 1: {should_validate(1)}")

st.markdown("---")

# Step validation toggle
st.header("2️⃣ Step Validation")
render_step_validation_toggle(1)

st.markdown("---")

# CPV and criteria selection
st.header("3️⃣ CPV & Criteria Test")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Select CPV Codes")
    
    # Hardcode some CPV codes with restrictions
    cpv_options = {
        "79000000-4": "Business services (HAS RESTRICTIONS)",
        "79200000-6": "Accounting services (HAS RESTRICTIONS)", 
        "45000000-7": "Construction work (NO RESTRICTIONS)",
        "33000000-0": "Medical equipment (NO RESTRICTIONS)"
    }
    
    selected_cpv = st.multiselect(
        "Choose CPV codes:",
        options=list(cpv_options.keys()),
        format_func=lambda x: f"{x}: {cpv_options[x]}",
        default=["79000000-4"]
    )
    
    if selected_cpv:
        # Check restrictions
        restricted = check_cpv_requires_additional_criteria(selected_cpv)
        if restricted:
            st.warning(f"⚠️ {len(restricted)} CPV codes require additional criteria!")
            for code, info in restricted.items():
                st.write(f"- {code}: {info['restriction']}")
        else:
            st.success("✅ No restrictions for selected CPV codes")

with col2:
    st.subheader("Select Criteria")
    
    # Criteria checkboxes
    criteria = {}
    criteria['price'] = st.checkbox("💰 Cena (Price)", value=True)
    criteria['additionalReferences'] = st.checkbox("📋 Dodatne reference", value=False)
    criteria['additionalTechnicalRequirements'] = st.checkbox("🔧 Dodatne tehnične zahteve", value=False)
    criteria['shorterDeadline'] = st.checkbox("⏱️ Krajši rok izvedbe", value=False)
    criteria['longerWarranty'] = st.checkbox("🛡️ Daljša garancijska doba", value=False)
    criteria['environmentalCriteria'] = st.checkbox("🌿 Okoljska merila", value=False)
    criteria['socialCriteria'] = st.checkbox("👥 Socialna merila", value=False)
    
    # Show selected criteria
    selected_criteria = {k: v for k, v in criteria.items() if v}
    if selected_criteria:
        st.info(f"Selected criteria: {list(selected_criteria.keys())}")

st.markdown("---")

# Validation result
st.header("4️⃣ Validation Result")

if st.button("🔍 Validate Selection", type="primary"):
    if should_validate(1):
        result = validate_criteria_selection(selected_cpv, selected_criteria)
        
        if result.is_valid:
            st.success("✅ Validation PASSED!")
        else:
            st.error("❌ Validation FAILED!")
            for msg in result.messages:
                st.error(msg)
            
            if result.required_criteria:
                st.warning("Required criteria:")
                for req in result.required_criteria:
                    st.write(f"- {req}")
    else:
        st.info("⏭️ Validation is disabled for this step")

# Debug info
with st.expander("🐛 Debug Info"):
    st.write("Session State:", dict(st.session_state))
    st.write("Selected CPV:", selected_cpv)
    st.write("Selected Criteria:", selected_criteria)