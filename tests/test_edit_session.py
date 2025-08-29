#!/usr/bin/env python3
"""Test what happens in session state when editing procurement 8."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import sqlite3
import streamlit as st
from ui.dashboard import load_procurement_to_form

def test_edit_load():
    """Test loading procurement 8 into session state."""
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Load schema
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        st.session_state['schema'] = json.load(f)
    
    # Simulate edit mode
    st.session_state['edit_mode'] = True
    st.session_state['editing_procurement_id'] = 8
    
    print("=" * 80)
    print("BEFORE LOADING PROCUREMENT 8:")
    print("=" * 80)
    print(f"Session state keys: {len(st.session_state.keys())}")
    
    # Call the actual load function with procurement ID
    load_procurement_to_form(8)
    
    print("\n" + "=" * 80)
    print("AFTER LOADING PROCUREMENT 8:")
    print("=" * 80)
    
    # Check lot configuration
    print(f"\nlot_mode: {st.session_state.get('lot_mode')}")
    print(f"num_lots: {st.session_state.get('num_lots')}")
    print(f"lotsInfo.hasLots: {st.session_state.get('lotsInfo.hasLots')}")
    
    # Check lot names
    lot_names = st.session_state.get('lot_names', [])
    print(f"\nlot_names ({len(lot_names)} items):")
    for i, name in enumerate(lot_names):
        print(f"  {i}: {name}")
    
    # Check critical lot-specific values
    print("\n" + "=" * 80)
    print("CRITICAL LOT-SPECIFIC VALUES IN SESSION STATE:")
    print("=" * 80)
    
    for i in range(2):  # We know there are 2 lots
        est_value_key = f'lot_{i}.orderType.estimatedValue'
        cofinancers_key = f'lot_{i}.orderType.cofinancers'
        
        est_value = st.session_state.get(est_value_key, 'NOT FOUND')
        cofinancers = st.session_state.get(cofinancers_key, 'NOT FOUND')
        
        print(f"\nLot {i} ({lot_names[i] if i < len(lot_names) else 'Unknown'}):")
        
        if est_value == 'NOT FOUND':
            print(f"  ❌ {est_value_key}: NOT FOUND")
        else:
            print(f"  ✅ {est_value_key}: €{est_value:,.2f}")
        
        if cofinancers == 'NOT FOUND':
            print(f"  ❌ {cofinancers_key}: NOT FOUND")
        elif isinstance(cofinancers, list):
            print(f"  ✅ {cofinancers_key}: {len(cofinancers)} cofinancers")
            for j, cof in enumerate(cofinancers):
                if isinstance(cof, dict):
                    name = cof.get('cofinancerName', 'NO NAME')
                    print(f"      {j+1}. {name}")
        else:
            print(f"  ⚠️ {cofinancers_key}: {cofinancers}")
    
    # Check if widgets would display correctly
    print("\n" + "=" * 80)
    print("WIDGET KEY CHECK (what form_renderer would use):")
    print("=" * 80)
    
    # These are the widget keys that would be created by form_renderer
    widget_keys = [
        'widget_lot_0.orderType.estimatedValue',
        'widget_lot_1.orderType.estimatedValue'
    ]
    
    for key in widget_keys:
        value = st.session_state.get(key, 'NOT SET')
        print(f"  {key}: {value}")
    
    # Show total lot fields
    print("\n" + "=" * 80)
    print("ALL LOT FIELDS IN SESSION STATE:")
    print("=" * 80)
    
    lot_fields = sorted([k for k in st.session_state.keys() if k.startswith('lot_')])
    print(f"Total lot fields: {len(lot_fields)}")
    
    # Show only important ones
    for key in lot_fields:
        if 'estimatedValue' in key or 'cofinancer' in key.lower():
            value = st.session_state[key]
            if isinstance(value, (int, float)):
                print(f"  {key}: €{value:,.2f}")
            elif isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
            else:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    test_edit_load()