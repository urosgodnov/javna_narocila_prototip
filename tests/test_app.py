#!/usr/bin/env python3
"""Simple test app to verify validation is blocking navigation."""

import streamlit as st
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

from utils.criteria_validation import validate_criteria_selection, check_cpv_requires_social_criteria

st.title("Test CPV Validation")

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state['orderType.cpvCodes'] = '50700000-2 - Repair and maintenance'
    st.session_state['selectionCriteria.price'] = False
    st.session_state['selectionCriteria.socialCriteria'] = False

# Show current step
st.info(f"Current step: {st.session_state.step}")

if st.session_state.step == 0:
    st.header("Step 1: Configure CPV")
    cpv = st.text_input("CPV Code", value=st.session_state['orderType.cpvCodes'])
    st.session_state['orderType.cpvCodes'] = cpv
    
elif st.session_state.step == 1:
    st.header("Step 2: Selection Criteria")
    
    # Show checkboxes
    price = st.checkbox("Cena (Price)", value=st.session_state['selectionCriteria.price'])
    social = st.checkbox("Socialna merila (Social criteria)", value=st.session_state['selectionCriteria.socialCriteria'])
    
    # Update session state
    st.session_state['selectionCriteria.price'] = price
    st.session_state['selectionCriteria.socialCriteria'] = social
    
    # Show validation status
    cpv_codes_raw = st.session_state['orderType.cpvCodes']
    cpv_codes = []
    if cpv_codes_raw:
        for code in cpv_codes_raw.split(','):
            code = code.strip()
            if ' - ' in code:
                code = code.split(' - ')[0].strip()
            if code:
                cpv_codes.append(code)
    
    if cpv_codes:
        social_required = check_cpv_requires_social_criteria(cpv_codes)
        if social_required:
            st.warning(f"⚠️ CPV code {cpv_codes[0]} requires social criteria")
        
        selected_criteria = {
            'price': price,
            'socialCriteria': social,
        }
        
        validation_result = validate_criteria_selection(cpv_codes, selected_criteria)
        
        if validation_result.is_valid:
            st.success("✅ Validation passed")
        else:
            st.error("❌ Validation failed")
            for msg in validation_result.messages:
                st.error(msg)

else:
    st.header("Step 3: Complete")
    st.success("You made it to step 3!")

# Navigation buttons
col1, col2 = st.columns(2)

with col1:
    if st.session_state.step > 0:
        if st.button("← Back"):
            logging.info(f"Back button clicked at step {st.session_state.step}")
            st.session_state.step -= 1
            st.rerun()

with col2:
    if st.session_state.step < 2:
        if st.button("Next →"):
            logging.info(f"Next button clicked at step {st.session_state.step}")
            
            # Validate if on criteria step
            if st.session_state.step == 1:
                # Get CPV codes
                cpv_codes_raw = st.session_state['orderType.cpvCodes']
                cpv_codes = []
                if cpv_codes_raw:
                    for code in cpv_codes_raw.split(','):
                        code = code.strip()
                        if ' - ' in code:
                            code = code.split(' - ')[0].strip()
                        if code:
                            cpv_codes.append(code)
                
                # Get selected criteria
                selected_criteria = {
                    'price': st.session_state['selectionCriteria.price'],
                    'socialCriteria': st.session_state['selectionCriteria.socialCriteria'],
                }
                
                logging.info(f"CPV codes: {cpv_codes}")
                logging.info(f"Selected criteria: {selected_criteria}")
                
                # Validate
                validation_result = validate_criteria_selection(cpv_codes, selected_criteria)
                logging.info(f"Validation result: is_valid={validation_result.is_valid}")
                
                if validation_result.is_valid:
                    logging.info("Validation passed - allowing navigation")
                    st.session_state.step += 1
                    st.rerun()
                else:
                    logging.info("Validation failed - blocking navigation")
                    st.error("Cannot proceed - validation failed!")
                    for msg in validation_result.messages:
                        st.error(msg)
            else:
                # No validation for other steps
                st.session_state.step += 1
                st.rerun()