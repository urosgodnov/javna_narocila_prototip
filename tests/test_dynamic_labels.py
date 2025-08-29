#!/usr/bin/env python3
"""Test script to verify dynamic labels in form arrays."""

import streamlit as st
import json
from ui.form_renderer import render_form
from utils.schema_utils import load_json_schema

def test_dynamic_labels():
    """Test dynamic label generation for array fields."""
    
    # Load schema
    schema = load_json_schema("json_files/SEZNAM_POTREBNIH_PODATKOV.json")
    
    # Set up test data in session state
    st.session_state['schema'] = schema
    
    # Test clients array
    st.session_state['clientInfo.clients'] = [
        {'name': 'UKC Ljubljana', 'email': 'info@ukc-lj.si'},
        {'name': 'UKC Maribor', 'email': 'info@ukc-mb.si'},
        {}  # Empty client to test fallback
    ]
    st.session_state['clientInfo.clients.0.name'] = 'UKC Ljubljana'
    st.session_state['clientInfo.clients.1.name'] = 'UKC Maribor'
    st.session_state['clientInfo.clients.2.name'] = ''
    
    # Test cofinancers array
    st.session_state['financialInfo.cofinancers'] = [
        {'name': 'EU Funds', 'percentage': 75},
        {'name': 'Ministry', 'percentage': 20},
        {}  # Empty cofinancer
    ]
    st.session_state['financialInfo.cofinancers.0.name'] = 'EU Funds'
    st.session_state['financialInfo.cofinancers.0.percentage'] = 75
    st.session_state['financialInfo.cofinancers.1.name'] = 'Ministry'
    st.session_state['financialInfo.cofinancers.1.percentage'] = 20
    
    # Test lots array
    st.session_state['lots'] = [
        {'name': 'Sklop A - Medicinski material'},
        {'name': 'Sklop B - Laboratorijska oprema'},
        {}  # Empty lot
    ]
    st.session_state['lots.0.name'] = 'Sklop A - Medicinski material'
    st.session_state['lots.1.name'] = 'Sklop B - Laboratorijska oprema'
    
    # Test inspection dates
    st.session_state['submissionProcedure.inspectionDates'] = [
        {'date': '2025-02-15', 'time': '10:00'},
        {'date': '2025-02-20', 'time': ''},
        {}  # Empty date
    ]
    st.session_state['submissionProcedure.inspectionDates.0.date'] = '2025-02-15'
    st.session_state['submissionProcedure.inspectionDates.0.time'] = '10:00'
    st.session_state['submissionProcedure.inspectionDates.1.date'] = '2025-02-20'
    
    # Test specification documents
    st.session_state['technicalSpecifications.specificationDocuments'] = [
        {'filename': 'technical_specs.pdf'},
        {'filename': ''},
    ]
    st.session_state['technicalSpecifications.specificationDocuments.0.filename'] = 'technical_specs.pdf'
    
    # Test mixed order components
    st.session_state['orderType.mixedOrderComponents'] = [
        {'description': 'Dobava medicinskih pripomočkov za intenzivno nego'},
        {'description': 'Vzdrževanje in servisiranje medicinske opreme v obdobju 3 let z možnostjo podaljšanja'},
        {}
    ]
    st.session_state['orderType.mixedOrderComponents.0.description'] = 'Dobava medicinskih pripomočkov za intenzivno nego'
    st.session_state['orderType.mixedOrderComponents.1.description'] = 'Vzdrževanje in servisiranje medicinske opreme v obdobju 3 let z možnostjo podaljšanja'
    
    st.title("Test dinamičnih oznak za array elemente")
    st.write("---")
    
    # Test each array type
    st.subheader("1. Naročniki (clients)")
    st.write("Pričakovano:")
    st.write("- UKC Ljubljana")
    st.write("- UKC Maribor")
    st.write("- Naročnik 3 (brez imena)")
    
    st.subheader("2. Sofinancerji (cofinancers)")
    st.write("Pričakovano:")
    st.write("- EU Funds (75%)")
    st.write("- Ministry (20%)")
    st.write("- Sofinancer 3 (brez imena)")
    
    st.subheader("3. Sklopi (lots)")
    st.write("Pričakovano:")
    st.write("- Sklop A - Medicinski material")
    st.write("- Sklop B - Laboratorijska oprema")
    st.write("- Sklop 3")
    
    st.subheader("4. Termini ogledov (inspectionDates)")
    st.write("Pričakovano:")
    st.write("- Ogled: 2025-02-15 ob 10:00")
    st.write("- Ogled: 2025-02-20")
    st.write("- Termin ogleda 3")
    
    st.subheader("5. Tehnični dokumenti (specificationDocuments)")
    st.write("Pričakovano:")
    st.write("- Dokument: technical_specs.pdf")
    st.write("- Dokument 2")
    
    st.subheader("6. Postavke mešanega naročila (mixedOrderComponents)")
    st.write("Pričakovano:")
    st.write("- Dobava medicinskih pripomočkov za intenzivno nego")
    st.write("- Vzdrževanje in servisiranje medicinske opreme v o... (skrajšano)")
    st.write("- Postavka 3")
    
    st.write("---")
    st.success("✅ Testni podatki pripravljeni. Sedaj preverite prikaz v glavni aplikaciji.")
    
    # Print actual session state for debugging
    if st.checkbox("Prikaži session state (za debugging)"):
        relevant_keys = [k for k in st.session_state.keys() 
                        if any(x in k for x in ['client', 'cofinanc', 'lot', 'inspection', 
                                               'specification', 'mixed'])]
        for key in sorted(relevant_keys):
            st.write(f"{key}: {st.session_state[key]}")

if __name__ == "__main__":
    test_dynamic_labels()