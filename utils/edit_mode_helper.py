"""Helper functions for edit mode functionality."""
import streamlit as st
from typing import Dict, Any, List
import logging


def mark_completed_steps_for_edit(form_data: Dict[str, Any]) -> None:
    """
    Mark all steps as completed when loading data for editing.
    This ensures the sidebar shows all available steps.
    """
    from config import get_dynamic_form_steps
    
    # Get all possible steps - pass session_state as required
    steps = get_dynamic_form_steps(st.session_state)
    
    # Initialize completed_steps if not exists
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = {}
    
    # Mark each step as completed based on whether it has data
    for idx, step_fields in enumerate(steps):
        has_data = False
        
        # Check if any field in this step has data
        for field_key in step_fields:
            # Check various possible keys
            if field_key in form_data:
                if form_data[field_key]:
                    has_data = True
                    break
            
            # Check nested fields
            for key in form_data.keys():
                if key.startswith(f"{field_key}."):
                    if form_data[key]:
                        has_data = True
                        break
            
            # Check session state directly
            if field_key in st.session_state:
                if st.session_state[field_key]:
                    has_data = True
                    break
            
            # Check for fields with dots
            for key in st.session_state.keys():
                if key.startswith(f"{field_key}."):
                    if st.session_state[key]:
                        has_data = True
                        break
        
        # Mark step as completed if it has data
        if has_data:
            st.session_state.completed_steps[idx] = True
            logging.info(f"[mark_completed_steps_for_edit] Marked step {idx} as completed (has data)")
    
    # Also check for lot-specific completed steps
    if st.session_state.get('lot_mode') == 'multiple':
        if 'lot_completed_steps' not in st.session_state:
            st.session_state.lot_completed_steps = {}
        
        # Mark lot steps as completed if they have data
        num_lots = len(st.session_state.get('lots', []))
        for lot_idx in range(num_lots):
            lot_key = f"lot_{lot_idx}"
            if lot_key not in st.session_state.lot_completed_steps:
                st.session_state.lot_completed_steps[lot_key] = {}
            
            # Check each step for this lot
            for step_idx, step_fields in enumerate(steps):
                has_lot_data = False
                
                for field_key in step_fields:
                    # Check for lot-prefixed fields
                    lot_field_key = f"lot_{lot_idx}.{field_key}"
                    if lot_field_key in st.session_state and st.session_state[lot_field_key]:
                        has_lot_data = True
                        break
                
                if has_lot_data:
                    st.session_state.lot_completed_steps[lot_key][step_idx] = True
    
    logging.info(f"[mark_completed_steps_for_edit] Final completed_steps: {st.session_state.completed_steps}")