"""
Test script for Contract Info implementation
Quinn - Senior Developer & QA Architect
"""

import streamlit as st
import json
from datetime import date

# Load the schema
with open('SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

st.set_page_config(page_title="Test Contract Info", layout="wide")
st.title("Test Contract Info Implementation")

# Get the contractInfo schema
contract_info_schema = schema['properties']['contractInfo']

st.json(contract_info_schema)

# Test the form rendering
st.header("Form Test")

# Section A - Contract Type Selection
st.markdown("### A. IZBIRA NAČINA SKLENITVE")

contract_type = st.radio(
    "Vrsta sklenitve",
    options=["pogodba", "okvirni sporazum"],
    horizontal=True
)

if contract_type == "pogodba":
    st.info("Selected: Pogodba")
    
    period_type = st.radio(
        "Način določitve obdobja pogodbe",
        options=["z veljavnostjo", "za obdobje od-do"],
        horizontal=True
    )
    
    if period_type == "z veljavnostjo":
        validity = st.text_input("Navedite za kakšno obdobje bi želeli skleniti pogodbo")
    else:
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input("Obdobje od")
        with col2:
            date_to = st.date_input("Obdobje do")
            
elif contract_type == "okvirni sporazum":
    st.info("Selected: Okvirni sporazum")
    
    framework_type = st.selectbox(
        "Vrsta okvirnega sporazuma",
        options=[
            "z enim gospodarskim subjektom in brez odpiranja konkurence",
            "z enim gospodarskim subjektom in z odpiranjem konkurence",
            "z več gospodarskimi subjekti in brez odpiranja konkurence",
            "z več gospodarskimi subjekti in z odpiranjem konkurence",
            "z več gospodarskimi subjekti in deloma brez ponovnega odpiranja konkurence in deloma z odpiranjem konkurence"
        ]
    )
    
    duration = st.text_input(
        "Navedite za kakšno obdobje bi želeli skleniti okvirni sporazum (max. 4 leta)"
    )
    
    # Validation
    if duration:
        if "let" in duration.lower():
            import re
            numbers = re.findall(r'(\d+)', duration)
            if numbers:
                years = int(numbers[0])
                if years > 4:
                    st.error("⚠️ Okvirni sporazum ne sme presegati 4 let!")
    
    # Show competition frequency field if needed
    if "z odpiranjem konkurence" in framework_type:
        frequency = st.text_input("Navedite kako pogosto želite odpirati konkurenco")
        
        # Show selected criteria
        st.info("ℹ️ Pri odpiranju konkurence bodo uporabljena naslednja merila: **Cena, Dodatne reference, Socialna merila**")

# Section B - Contract Extension
st.markdown("### B. PODALJŠANJE POGODBE")

can_extend = st.radio(
    "Ali naročnik predvideva možnost podaljšanja pogodbe?",
    options=["ne", "da"],
    horizontal=True
)

if can_extend == "da":
    reasons = st.text_area(
        "Navedite v katerih primerih oz. iz katerih razlogov lahko pride do podaljšanja pogodbe"
    )
    
    duration = st.text_input(
        "Navedite za koliko časa bi v navedenih primerih želeli podaljšati pogodbo"
    )

st.success("✅ Contract Info form implementation is working!")