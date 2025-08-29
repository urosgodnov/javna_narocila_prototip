#!/usr/bin/env python3
"""Test script to debug estimatedValue and cofinancers saving issue."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.schema_utils import get_form_data_from_session
import json

# Simulate session state with test data
class MockSessionState(dict):
    def __init__(self):
        super().__init__()
        # Set schema
        with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
            self['schema'] = json.load(f)
        
        # Test data - simulate what would be in session after user enters data
        # For general mode (no lots)
        self['lot_mode'] = 'none'
        
        # EstimatedValue - multiple possible locations
        self['general.orderType.estimatedValue'] = 1500000.0
        self['orderType.estimatedValue'] = 1500000.0
        
        # Cofinancers array - as it would be after form entry
        self['orderType.cofinancers'] = [
            {
                'cofinancerName': 'EU Funds',
                'cofinancerStreetAddress': 'Brussels 1',
                'cofinancerPostalCode': '1000 Brussels',
                'programName': 'Horizon',
                'programArea': 'Research',
                'programCode': 'H2020'
            }
        ]
        self['general.orderType.cofinancers'] = self['orderType.cofinancers']
        
        # Individual cofinancer fields (as form would create them)
        self['orderType.cofinancers.0.cofinancerName'] = 'EU Funds'
        self['orderType.cofinancers.0.cofinancerStreetAddress'] = 'Brussels 1'
        self['orderType.cofinancers.0.cofinancerPostalCode'] = '1000 Brussels'
        self['orderType.cofinancers.0.programName'] = 'Horizon'
        self['orderType.cofinancers.0.programArea'] = 'Research'
        self['orderType.cofinancers.0.programCode'] = 'H2020'
        
        self['general.orderType.cofinancers.0.cofinancerName'] = 'EU Funds'
        self['general.orderType.cofinancers.0.cofinancerStreetAddress'] = 'Brussels 1'
        self['general.orderType.cofinancers.0.cofinancerPostalCode'] = '1000 Brussels'
        self['general.orderType.cofinancers.0.programName'] = 'Horizon'
        self['general.orderType.cofinancers.0.programArea'] = 'Research'
        self['general.orderType.cofinancers.0.programCode'] = 'H2020'
        
        # Other required fields
        self['general.projectInfo.projectName'] = 'Test Project'
        self['projectInfo.projectName'] = 'Test Project'
        self['general.orderType.type'] = 'blago'
        self['orderType.type'] = 'blago'
        self['general.orderType.isCofinanced'] = True
        self['orderType.isCofinanced'] = True

# Mock streamlit session state
st.session_state = MockSessionState()

# Test the function
print("Testing get_form_data_from_session...")
print("=" * 60)

form_data = get_form_data_from_session()

print("\nGenerated form_data structure:")
print(json.dumps(form_data, indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
print("Checking critical values:")
print(f"1. estimatedValue in orderType: {form_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')}")
print(f"2. cofinancers in orderType: {form_data.get('orderType', {}).get('cofinancers', 'NOT FOUND')}")

if form_data.get('orderType', {}).get('estimatedValue', 0) == 0:
    print("\n❌ ERROR: estimatedValue is 0 or missing!")
else:
    print(f"\n✅ SUCCESS: estimatedValue = {form_data.get('orderType', {}).get('estimatedValue')}")

if not form_data.get('orderType', {}).get('cofinancers'):
    print("❌ ERROR: cofinancers array is empty or missing!")
else:
    print(f"✅ SUCCESS: Found {len(form_data.get('orderType', {}).get('cofinancers', []))} cofinancers")