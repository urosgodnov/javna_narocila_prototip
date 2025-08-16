#!/usr/bin/env python3
"""
Interactive UI test for validation control feature.
Run with: streamlit run tests/test_ui_validation_control.py
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validation_control import (
    should_validate, 
    render_master_validation_toggle,
    render_step_validation_toggle,
    get_validation_status_message
)

st.set_page_config(page_title="Test Validation Control", layout="wide")

st.title("🧪 Test Validation Control System")
st.markdown("Interactive test for Epic 22: Granular Validation Control")

# Simulate form steps
total_steps = 5
step_names = [
    "Korak 1: Osnovni podatki",
    "Korak 2: Podatki projekta", 
    "Korak 3: Opis naročila",
    "Korak 4: Merila izbora",
    "Korak 5: Sklepanje pogodbe"
]

# Initialize current step
if 'test_current_step' not in st.session_state:
    st.session_state.test_current_step = 0

current_step = st.session_state.test_current_step

# Navigation
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if current_step > 0:
        if st.button("⬅️ Nazaj"):
            st.session_state.test_current_step -= 1
            st.rerun()

with col2:
    st.markdown(f"### {step_names[current_step]}")
    progress = (current_step + 1) / total_steps
    st.progress(progress)

with col3:
    if current_step < total_steps - 1:
        if st.button("Naprej ➡️"):
            st.session_state.test_current_step += 1
            st.rerun()

st.markdown("---")

# Render master toggle on first step
if current_step == 0:
    render_master_validation_toggle()

# Main content area
st.markdown("### 📝 Vsebina obrazca")
st.info("Tukaj bi bila polja obrazca za ta korak...")

# Example form fields
with st.container():
    if current_step == 0:
        st.text_input("Ime organizacije", key="org_name")
        st.text_input("Naslov", key="address")
    elif current_step == 1:
        st.text_input("Naziv projekta", key="project_name")
        st.text_area("Opis projekta", key="project_desc")
    elif current_step == 2:
        st.text_input("CPV koda", key="cpv_code")
        st.number_input("Ocenjena vrednost", key="value")
    elif current_step == 3:
        st.checkbox("Cena", key="price_criteria")
        st.checkbox("Dodatne reference", key="ref_criteria")
    else:
        st.selectbox("Vrsta pogodbe", ["Enkratna", "Okvirni sporazum"], key="contract_type")

# Render per-step validation toggle
render_step_validation_toggle(current_step)

# Validation Status Display
st.markdown("---")
st.markdown("### 📊 Status validacije")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Trenutni korak")
    status_msg = get_validation_status_message(current_step)
    if should_validate(current_step):
        st.success(status_msg)
        st.markdown("✅ Validacija **BO** izvedena na tem koraku")
    else:
        st.warning(status_msg)
        st.markdown("⏭️ Validacija **NE BO** izvedena na tem koraku")

with col2:
    st.markdown("#### Globalne nastavitve")
    
    master_disabled = st.session_state.get('validation_disabled', True)
    step_enabled = st.session_state.get(f'step_{current_step}_validation_enabled', False)
    
    if master_disabled:
        st.info("🔴 Master: IZKLOPLJENA (privzeto)")
    else:
        st.success("🟢 Master: VKLOPLJENA")
    
    if step_enabled:
        st.success(f"🟢 Korak {current_step}: VKLOPLJENA")
    else:
        st.info(f"⚪ Korak {current_step}: Uporablja master")

# Logic explanation
with st.expander("🔍 Razlaga logike", expanded=False):
    st.markdown("""
    ### Kako deluje validacija:
    
    1. **Master toggle** (na prvem koraku):
       - ☑️ Označeno = validacija IZKLOPLJENA (privzeto)
       - ☐ Neoznačeno = validacija VKLOPLJENA
    
    2. **Per-step toggle** (na vsakem koraku):
       - ☐ Neoznačeno = uporablja master nastavitev (privzeto)
       - ☑️ Označeno = VKLOPI validacijo za ta korak
    
    3. **Logika**:
       - Validacija se izvede če: master je IZKLOPLJEN (unchecked) ALI korak je VKLOPLJEN (checked)
       - Formula: `validate = (NOT master_disabled) OR step_enabled`
    
    ### Primeri:
    - Master ☑️ + Korak ☐ = **Ni validacije**
    - Master ☑️ + Korak ☑️ = **Validacija (korak override)**
    - Master ☐ + Korak ☐ = **Validacija (globalna)**
    - Master ☐ + Korak ☑️ = **Validacija**
    """)

# Test all steps status
with st.expander("📋 Status vseh korakov", expanded=False):
    st.markdown("### Pregled validacije za vse korake:")
    
    for i in range(total_steps):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{step_names[i]}**")
        
        with col2:
            step_key = f'step_{i}_validation_enabled'
            if st.session_state.get(step_key, False):
                st.success("Korak: ON")
            else:
                st.info("Korak: OFF")
        
        with col3:
            if should_validate(i):
                st.success("✓ Validacija")
            else:
                st.warning("○ Preskočeno")

st.markdown("---")
st.caption("Test interface for Validation Control feature - Epic 22")