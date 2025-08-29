#!/usr/bin/env python3
"""Test the complete save flow for estimatedValue and cofinancers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import sqlite3
from database import create_procurement, get_procurement_by_id
from utils.schema_utils import get_form_data_from_session
import streamlit as st

# Mock session state with test data
class MockSessionState(dict):
    def __init__(self):
        super().__init__()
        # Load the schema
        with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
            self['schema'] = json.load(f)
        
        # Basic data
        self['lot_mode'] = 'none'
        self['projectInfo.projectName'] = 'Test Project with EstimatedValue'
        self['orderType.type'] = 'blago'
        
        # THE CRITICAL VALUE WE'RE TESTING
        self['orderType.estimatedValue'] = 1500000.0
        
        # Add widget key too (as the form would create)
        self['widget_orderType.estimatedValue_text'] = '1.500.000,00'
        
        # Cofinancers data
        self['orderType.isCofinanced'] = True
        self['orderType.cofinancers'] = [
            {
                'cofinancerName': 'EU Funds Test',
                'cofinancerStreetAddress': 'Brussels 1',
                'cofinancerPostalCode': '1000',
                'programName': 'Horizon Europe',
                'programArea': 'Research',
                'programCode': 'HE2024'
            }
        ]
        
        # Individual cofinancer fields as form would set them
        self['orderType.cofinancers.0.cofinancerName'] = 'EU Funds Test'
        self['orderType.cofinancers.0.cofinancerStreetAddress'] = 'Brussels 1'
        self['orderType.cofinancers.0.cofinancerPostalCode'] = '1000'
        self['orderType.cofinancers.0.programName'] = 'Horizon Europe'
        self['orderType.cofinancers.0.programArea'] = 'Research'
        self['orderType.cofinancers.0.programCode'] = 'HE2024'

# Set mock session state
st.session_state = MockSessionState()

print("=" * 80)
print("TESTING COMPLETE SAVE FLOW")
print("=" * 80)

# Step 1: Get form data from session
print("\n1. Getting form data from session...")
form_data = get_form_data_from_session()

print("\nForm data structure:")
print(json.dumps(form_data, indent=2, ensure_ascii=False))

# Check critical values
print("\n" + "=" * 80)
print("CHECKING CRITICAL VALUES BEFORE SAVE:")
print("=" * 80)

estimated_value = form_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
cofinancers = form_data.get('orderType', {}).get('cofinancers', 'NOT FOUND')

print(f"1. estimatedValue: {estimated_value}")
print(f"2. cofinancers: {cofinancers}")

if estimated_value == 'NOT FOUND' or estimated_value == 0:
    print("\n❌ ERROR: estimatedValue is missing or 0 BEFORE save!")
else:
    print(f"\n✅ Good: estimatedValue = {estimated_value}")

if cofinancers == 'NOT FOUND' or not cofinancers:
    print("❌ ERROR: cofinancers missing BEFORE save!")
else:
    print(f"✅ Good: Found {len(cofinancers)} cofinancers")

# Step 2: Save to database
print("\n" + "=" * 80)
print("2. Saving to database...")
procurement_id = create_procurement(form_data)
print(f"Created procurement with ID: {procurement_id}")

# Step 3: Load back from database
print("\n3. Loading back from database...")
loaded_procurement = get_procurement_by_id(procurement_id)

if loaded_procurement:
    print(f"\nLoaded procurement:")
    print(f"  ID: {loaded_procurement['id']}")
    print(f"  Naziv: {loaded_procurement['naziv']}")
    print(f"  Vrednost (from DB column): {loaded_procurement['vrednost']}")
    
    # Parse the JSON data
    loaded_form_data = json.loads(loaded_procurement['form_data_json'])
    
    print("\n" + "=" * 80)
    print("CHECKING CRITICAL VALUES AFTER RELOAD:")
    print("=" * 80)
    
    reloaded_estimated = loaded_form_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
    reloaded_cofinancers = loaded_form_data.get('orderType', {}).get('cofinancers', 'NOT FOUND')
    
    print(f"1. estimatedValue in reloaded data: {reloaded_estimated}")
    print(f"2. cofinancers in reloaded data: {reloaded_cofinancers}")
    
    # Final check
    print("\n" + "=" * 80)
    print("FINAL VERDICT:")
    print("=" * 80)
    
    if reloaded_estimated == 1500000.0:
        print("✅ SUCCESS: estimatedValue saved and loaded correctly!")
    else:
        print(f"❌ FAILURE: estimatedValue lost! Expected 1500000.0, got {reloaded_estimated}")
        
    if reloaded_cofinancers and len(reloaded_cofinancers) > 0:
        print("✅ SUCCESS: cofinancers saved and loaded correctly!")
    else:
        print(f"❌ FAILURE: cofinancers lost! Got {reloaded_cofinancers}")
else:
    print("❌ ERROR: Could not load procurement back from database!")

print("\n" + "=" * 80)