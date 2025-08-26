"""Utilities for handling JSON schema and session data."""
import json
import streamlit as st


def load_json_schema(file_path):
    """Load JSON schema from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_schema_ref(schema, ref_path):
    """Resolve a $ref in the schema.
    
    Args:
        schema: The full schema dictionary
        ref_path: The $ref path (e.g., '#/$defs/orderTypeProperties')
    
    Returns:
        The resolved schema section
    """
    if not ref_path.startswith('#/'):
        return None
    
    path_parts = ref_path[2:].split('/')  # Remove '#/' and split
    current = schema
    
    for part in path_parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


def update_session_state(key, value):
    """Update session state for form field changes."""
    st.session_state[key] = value


def get_form_data_from_session():
    """
    Reconstructs the nested form data dictionary from Streamlit's flat session_state.
    Handles both regular fields and lot-specific fields.
    """
    form_data = {}
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    if not schema_properties:
        return {}

    # Process regular fields
    for key, value in st.session_state.items():
        # Skip file info keys - they contain binary data that can't be serialized
        if '_file_info' in key:
            continue
            
        top_level_key = key.split('.')[0]
        
        # Handle regular schema properties
        if top_level_key in schema_properties:
            parts = key.split('.')
            d = form_data
            for part in parts[:-1]:
                # Ensure d is a dictionary before calling setdefault
                if not isinstance(d, dict):
                    break
                d = d.setdefault(part, {})
            else:
                # Only set the final value if we successfully navigated the structure
                if isinstance(d, dict):
                    d[parts[-1]] = value
        
        # Handle general lot fields (general.fieldname)
        elif top_level_key == 'general':
            parts = key.split('.')
            if len(parts) > 1:
                field_parts = parts[1:]  # Remove 'general' prefix
                d = form_data
                for part in field_parts[:-1]:
                    # Ensure d is a dictionary before calling setdefault
                    if not isinstance(d, dict):
                        break
                    d = d.setdefault(part, {})
                else:
                    # Only set the final value if we successfully navigated the structure
                    if isinstance(d, dict):
                        d[field_parts[-1]] = value
    
    # Handle lot-specific data
    lot_mode = st.session_state.get('lot_mode', 'none')
    if lot_mode == 'multiple':
        # Include lot names
        form_data['lot_names'] = st.session_state.get('lot_names', [])
        
        # Include structured lot data
        lots_data = []
        lots = st.session_state.get('lots', [])
        
        for i, lot in enumerate(lots):
            # Handle case where lot might be a list or other type instead of dict
            if isinstance(lot, dict):
                lot_data = {'name': lot.get('name', f'Sklop {i+1}')}
            else:
                # If lot is not a dict, create a default structure
                lot_data = {'name': f'Sklop {i+1}'}
            
            # Collect all lot-specific fields
            lot_prefix = f'lot_{i}.'
            for key, value in st.session_state.items():
                # Skip file info keys - they contain binary data that can't be serialized
                if '_file_info' in key:
                    continue
                if key.startswith(lot_prefix):
                    field_name = key[len(lot_prefix):]
                    # Build nested structure
                    parts = field_name.split('.')
                    d = lot_data
                    for part in parts[:-1]:
                        # Ensure d is a dictionary before calling setdefault
                        if not isinstance(d, dict):
                            # Skip this field if we can't build nested structure
                            break
                        d = d.setdefault(part, {})
                    else:
                        # Only set the final value if we successfully navigated the structure
                        if isinstance(d, dict):
                            d[parts[-1]] = value
            
            lots_data.append(lot_data)
        
        if lots_data:
            form_data['lots'] = lots_data
    
    # Include lot configuration metadata
    if 'lotsInfo.hasLots' in st.session_state:
        if 'lotsInfo' not in form_data:
            form_data['lotsInfo'] = {}
        form_data['lotsInfo']['hasLots'] = st.session_state['lotsInfo.hasLots']
    
    return form_data


def clear_form_data():
    """
    Clear all form data from session state.
    Preserves navigation and schema data.
    """
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    keys_to_remove = []
    
    # Clear current draft ID since we're starting fresh
    if 'current_draft_id' in st.session_state:
        del st.session_state['current_draft_id']
    
    # Identify all form-related keys
    for key in st.session_state.keys():
        top_level_key = key.split('.')[0]
        if top_level_key in schema_properties:
            keys_to_remove.append(key)
        # Also remove widget keys
        if key.startswith('widget_'):
            keys_to_remove.append(key)
        # Remove lot-specific keys
        if key.startswith('lot_') or key.startswith('general.'):
            keys_to_remove.append(key)
        # Remove lot configuration keys
        if key in ['lot_names', 'lots', 'current_lot_index', 'lot_mode']:
            keys_to_remove.append(key)
    
    # Remove the identified keys
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any tracking data
    if '_last_loaded_data' in st.session_state:
        del st.session_state['_last_loaded_data']
    if 'unsaved_changes' in st.session_state:
        del st.session_state['unsaved_changes']