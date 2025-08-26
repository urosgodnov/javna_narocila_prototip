"""Lot navigation utilities for handling lot iteration and actions."""
import streamlit as st
from utils.schema_utils import get_form_data_from_session


def handle_lot_action(action):
    """
    Handle lot navigation actions.
    
    Args:
        action: Action type ('save', 'start_current_lot', 'next_lot', 'new_lot', 'submit')
    """
    if action == 'save':
        # Save current lot data
        save_current_lot_data()
        st.success("✅ Podatki za trenutni sklop so bili shranjeni.")
    
    elif action == 'start_current_lot':
        # Mark current lot data entry as started and proceed
        current_lot_index = st.session_state.get('current_lot_index', 0)
        if current_lot_index is None:
            current_lot_index = 0
            st.session_state.current_lot_index = 0
        
        st.session_state[f"lot_{current_lot_index}_data_started"] = True
        st.session_state.current_step += 1
        lot_names = st.session_state.get('lot_names', [])
        if current_lot_index < len(lot_names):
            st.success(f"✅ Začetek vnosa za sklop: {lot_names[current_lot_index]}")
        st.rerun()
        
    elif action == 'next_lot':
        # Save current lot and move to next
        save_current_lot_data()
        
        # Increment lot index
        current_lot_index = st.session_state.get('current_lot_index', 0)
        if current_lot_index is None:
            current_lot_index = 0
        lot_names = st.session_state.get('lot_names', [])
        
        if current_lot_index < len(lot_names) - 1:
            st.session_state.current_lot_index = current_lot_index + 1
            
            # Reset the data_started flag for the new lot
            new_lot_index = current_lot_index + 1
            if f"lot_{new_lot_index}_data_started" in st.session_state:
                del st.session_state[f"lot_{new_lot_index}_data_started"]
            
            # Find the step for lot configuration
            lot_config_step = find_lot_configuration_step()
            if lot_config_step is not None:
                # Jump to first step after lot configuration
                st.session_state.current_step = lot_config_step + 1
            
            st.success(f"✅ Prehod na sklop: {lot_names[current_lot_index + 1]}")
            st.rerun()
    
    elif action == 'new_lot':
        # Save current lot and create a new one
        save_current_lot_data()
        
        # Add a new lot
        lot_names = st.session_state.get('lot_names', [])
        new_lot_name = f"Sklop {len(lot_names) + 1}"
        lot_names.append(new_lot_name)
        st.session_state.lot_names = lot_names
        
        # Add to lots array
        if 'lots' not in st.session_state:
            st.session_state.lots = []
        st.session_state.lots.append({'name': new_lot_name})
        
        # Set current lot index to the new lot
        st.session_state.current_lot_index = len(lot_names) - 1
        
        # Jump back to lot configuration step
        lot_config_step = find_lot_configuration_step()
        if lot_config_step is not None:
            st.session_state.current_step = lot_config_step
        
        st.success(f"✅ Dodan nov sklop: {new_lot_name}")
        st.rerun()
    
    elif action == 'submit':
        # Save current lot and submit the entire form
        save_current_lot_data()
        
        # Get all form data including all lots
        final_form_data = get_form_data_from_session()
        
        # Check if we're in edit mode
        if st.session_state.get('edit_mode', False):
            import database
            # Update existing procurement
            record_id = st.session_state.get('edit_record_id')
            if database.update_procurement(record_id, final_form_data):
                st.success(f"✅ Naročilo ID {record_id} uspešno posodobljeno!")
                # Clear edit mode and return to dashboard
                st.session_state.edit_mode = False
                st.session_state.edit_record_id = None
                st.session_state.current_page = 'dashboard'
                clear_form_data_with_lots()
                st.rerun()
            else:
                st.error("❌ Napaka pri posodabljanju naročila")
        else:
            import database
            # Create new procurement
            new_id = database.create_procurement(final_form_data)
            if new_id:
                st.success(f"✅ Osnutek uspešno shranjen! ID: {new_id}")
                # Return to dashboard
                st.session_state.current_page = 'dashboard'
                clear_form_data_with_lots()
                st.rerun()
            else:
                st.error("❌ Napaka pri ustvarjanju naročila")


def save_current_lot_data():
    """Save data for the current lot being edited."""
    current_lot_index = st.session_state.get('current_lot_index', 0)
    if current_lot_index is None:
        current_lot_index = 0
    
    if 'lots' not in st.session_state:
        st.session_state.lots = []
    
    # Ensure we have enough lot entries
    while len(st.session_state.lots) <= current_lot_index:
        st.session_state.lots.append({})
    
    # Get all lot-scoped data for current lot
    lot_data = {}
    prefix = f"lot_{current_lot_index}."
    
    for key, value in st.session_state.items():
        if key.startswith(prefix):
            # Remove prefix to get field name
            field_name = key[len(prefix):]
            lot_data[field_name] = value
    
    # Update the lot data
    st.session_state.lots[current_lot_index].update(lot_data)
    
    # Keep the lot name
    lot_names = st.session_state.get('lot_names', [])
    if current_lot_index < len(lot_names):
        st.session_state.lots[current_lot_index]['name'] = lot_names[current_lot_index]


def find_lot_configuration_step():
    """Find the step index for lot configuration."""
    from config_refactored import get_dynamic_form_steps_refactored
    steps = get_dynamic_form_steps_refactored(st.session_state)
    
    for i, step_fields in enumerate(steps):
        if 'lotConfiguration' in step_fields:
            return i
        # Also check for lot context steps
        if any(field.startswith('lot_context_') for field in step_fields):
            return i - 1  # Return the step before the first lot context
    
    return None


def clear_form_data_with_lots():
    """Clear all form data including lot-specific data."""
    from utils.schema_utils import clear_form_data
    
    # Clear standard form data
    clear_form_data()
    
    # Clear lot-specific session state
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('lot_') or key in ['lot_names', 'lots', 'current_lot_index', 'lot_mode']:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]