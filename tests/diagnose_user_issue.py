#!/usr/bin/env python3
"""Diagnose what's happening with the user's form data."""

import streamlit as st

st.set_page_config(page_title="Diagnose User Issue")

st.write("# Diagnosing User's Validation Issue")

st.write("""
## The User's Scenario:
1. User selected "Socialna merila" (Social criteria)
2. Under social criteria, user selected "Drugo" with description "rad imeti krompir" and 50 points
3. User thinks they also selected "Drugo, imam predlog" with 70 points
4. Validation complains about missing description for "otherCriteriaCustom"
""")

st.write("## Analysis:")

# Simulate what might be happening
st.write("### Possibility 1: User accidentally selected main 'Drugo merilo' criterion")
st.code("""
# User might have:
selectionCriteria.otherCriteriaCustom = True  # Main criterion "Drugo merilo"
selectionCriteria.otherCriteriaCustomRatio = 70  # Points for main criterion

# This REQUIRES a description in otherCriteriaDescription field!
""")

st.write("### Possibility 2: Form doesn't have 'Drugo, imam predlog' as social sub-option")
st.code("""
# JSON schema only defines these social sub-options:
- youngEmployeesShare (Delež zaposlenih mladih)
- elderlyEmployeesShare (Delež zaposlenih starejših) 
- registeredStaffEmployed (Priglašeni kader je zaposlen pri ponudniku)
- averageSalary (Povprečna plača priglašenega kadra)
- otherSocial (Drugo) - only this "Drugo" option exists!

# There is NO 'otherSocialCustom' or 'otherSocialAI' in the schema!
""")

st.write("### The Real Problem:")
st.error("""
The user mentioned there should be 7 social sub-options including:
- Drugo
- Drugo, imam predlog  
- Drugo, prosim predlog AI

But the JSON schema only defines 5 social sub-options, with only ONE "Drugo" option!
The fields 'socialCriteriaCustomRatio' and 'socialCriteriaAIRatio' don't exist in the form!
""")

st.write("### What's Actually Happening:")
st.info("""
When the user enters 70 points in what they think is "Drugo, imam predlog" under social criteria,
they're actually filling in "Drugo merilo" (otherCriteriaCustom) which is a MAIN criterion that
requires a description in the otherCriteriaDescription field.
""")

st.write("## Solution:")
st.success("""
Either:
1. Add the missing social sub-options to the JSON schema, OR
2. Help the user understand that "Drugo merilo" is not a social sub-option
""")

# Show current JSON structure
st.write("### Current Form Structure (from SEZNAM_POTREBNIH_PODATKOV.json):")
st.code("""
selectionCriteria:
  - price (with priceRatio)
  - socialCriteria (with sub-options):
      * youngEmployeesShare (with socialCriteriaYoungRatio)
      * elderlyEmployeesShare (with socialCriteriaElderlyRatio)
      * registeredStaffEmployed (with socialCriteriaStaffRatio)
      * averageSalary (with socialCriteriaSalaryRatio)
      * otherSocial (with socialCriteriaOtherRatio + otherSocialDescription)
  - otherCriteriaCustom (with otherCriteriaCustomRatio + otherCriteriaDescription)
  - [other main criteria...]
""")