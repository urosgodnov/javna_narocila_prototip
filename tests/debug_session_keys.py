#!/usr/bin/env python3
"""Debug tool to show what keys are in session state for selection criteria."""

import streamlit as st
import json

st.set_page_config(page_title="Debug Session Keys", layout="wide")

st.title("🔍 Debug: Selection Criteria Session Keys")

# Load the form and navigate to Merila step to populate session state
if st.button("Load Main App First"):
    st.info("Please run the main app.py first and navigate to the Merila step, then come back here")

# Show all session keys related to selection criteria
st.header("Session State Keys")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Selection Criteria Keys")
    criteria_keys = [k for k in st.session_state.keys() if 'selection' in k.lower() or 'criteria' in k.lower()]
    for key in sorted(criteria_keys):
        value = st.session_state[key]
        if value and value != 0 and value != False:
            st.success(f"✓ {key}: {value}")
        else:
            st.text(f"  {key}: {value}")

with col2:
    st.subheader("Ratio/Points Keys")
    ratio_keys = [k for k in st.session_state.keys() if 'ratio' in k.lower() or 'point' in k.lower()]
    for key in sorted(ratio_keys):
        value = st.session_state[key]
        if value and value != 0:
            st.success(f"✓ {key}: {value}")
        else:
            st.text(f"  {key}: {value}")

st.divider()

# Show social criteria specific keys
st.header("Social Criteria Keys")

social_keys = [k for k in st.session_state.keys() if 'social' in k.lower()]
for key in sorted(social_keys):
    value = st.session_state[key]
    if value and value != 0 and value != False:
        st.success(f"✓ {key}: {value}")
    else:
        st.text(f"  {key}: {value}")

st.divider()

# Show widget keys (Streamlit creates these automatically)
st.header("Widget Keys")
widget_keys = [k for k in st.session_state.keys() if k.startswith('widget_')]
for key in sorted(widget_keys):
    value = st.session_state[key]
    if value and value != 0 and value != False:
        st.success(f"✓ {key}: {value}")
    else:
        st.text(f"  {key}: {value}")

st.divider()

# Show lot-specific keys if any
st.header("Lot-Specific Keys")
lot_keys = [k for k in st.session_state.keys() if 'lot_' in k]
if lot_keys:
    for key in sorted(lot_keys):
        value = st.session_state[key]
        if value and value != 0 and value != False:
            st.success(f"✓ {key}: {value}")
        else:
            st.text(f"  {key}: {value}")
else:
    st.info("No lot-specific keys found (running in general mode)")

# Export button
if st.button("Export All Keys to File"):
    with open("session_keys_debug.json", "w") as f:
        # Convert session state to serializable format
        serializable = {}
        for k, v in st.session_state.items():
            try:
                json.dumps(v)  # Test if serializable
                serializable[k] = v
            except:
                serializable[k] = str(v)
        json.dump(serializable, f, indent=2)
    st.success("Exported to session_keys_debug.json")