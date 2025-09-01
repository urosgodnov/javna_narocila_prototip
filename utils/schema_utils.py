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
    import logging
    
    form_data = {}
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    if not schema_properties:
        return {}
    
    # Debug: Check if clients data exists in session state
    if 'clientInfo.clients' in st.session_state:
        logging.info(f"[get_form_data_from_session] clientInfo.clients found: {st.session_state['clientInfo.clients']}")
    else:
        logging.info("[get_form_data_from_session] clientInfo.clients NOT in session state")
    
    # Debug: Check for any client-related keys
    client_keys = [k for k in st.session_state.keys() if 'client' in k.lower()]
    if client_keys:
        logging.info(f"[get_form_data_from_session] All client-related keys: {client_keys}")
        for key in client_keys:
            value = st.session_state[key]
            if isinstance(value, list):
                logging.info(f"  {key} = list with {len(value)} items")
                if value:
                    logging.info(f"    First item: {value[0]}")
            else:
                logging.info(f"  {key} = {value}")

    # First, reconstruct array objects from nested keys (e.g., clientInfo.clients.0.name)
    array_data = {}  # Track array items
    
    for key in st.session_state.keys():
        # Skip widget keys
        if key.startswith('widget_'):
            continue
            
        # Handle regular, general-prefixed, AND lot-prefixed array keys
        actual_key = key
        original_prefix = ''
        
        if key.startswith('general.'):
            # For processing, we'll use the key without general prefix
            # but remember it has the prefix for proper reconstruction
            actual_key = key[8:]  # Remove 'general.' prefix
            original_prefix = 'general.'
        elif key.startswith('lot_'):
            # Check if this is a lot-prefixed key with array pattern
            # e.g., lot_0.inspectionInfo.inspectionDates.0.date
            # We keep the lot prefix for now since we'll handle it specially
            actual_key = key
            # Extract lot prefix (e.g., 'lot_0.')
            if '.' in key:
                lot_part = key.split('.')[0]
                if '_' in lot_part and lot_part.split('_')[1].isdigit():
                    original_prefix = lot_part + '.'
                    actual_key = key  # Keep full key for lot processing
            
        # Pattern: parentKey.arrayName.index.field (e.g., clientInfo.clients.0.name or orderType.cofinancers.0.cofinancerName)
        if '.' in actual_key and any(part.isdigit() for part in actual_key.split('.')):
            parts = actual_key.split('.')
            # Find array index
            for i, part in enumerate(parts):
                if part.isdigit():
                    # This is an array element
                    array_key = '.'.join(parts[:i])  # e.g., clientInfo.clients or orderType.cofinancers
                    index = int(part)
                    field_path = '.'.join(parts[i+1:]) if i+1 < len(parts) else None
                    
                    if array_key not in array_data:
                        array_data[array_key] = {}
                    if index not in array_data[array_key]:
                        array_data[array_key][index] = {}
                    
                    if field_path:
                        # Navigate nested structure
                        d = array_data[array_key][index]
                        field_parts = field_path.split('.')
                        for fp in field_parts[:-1]:
                            # Only use setdefault if d is a dict
                            if not isinstance(d, dict):
                                # Cannot navigate further - skip this key
                                break
                            d = d.setdefault(fp, {})
                        else:
                            # Only set value if we successfully navigated
                            if isinstance(d, dict):
                                d[field_parts[-1]] = st.session_state[key]
                    else:
                        # Direct value
                        array_data[array_key][index] = st.session_state[key]
                    break
    
    # Convert array_data to proper arrays
    lot_arrays = {}  # Store lot-prefixed arrays separately
    
    for array_key, indices_dict in array_data.items():
        # Sort by index and create array
        max_index = max(indices_dict.keys()) if indices_dict else -1
        array_list = []
        for i in range(max_index + 1):
            if i in indices_dict:
                array_list.append(indices_dict[i])
            else:
                array_list.append({})  # Fill gaps with empty objects
        
        # Check if this is a lot-prefixed array
        if array_key.startswith('lot_'):
            # Store it for later processing with lot data
            lot_arrays[array_key] = array_list
            logging.info(f"[get_form_data_from_session] Storing lot array {array_key} with {len(array_list)} items for later")
        else:
            # Set non-lot arrays in form_data
            parts = array_key.split('.')
            d = form_data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = array_list
            
            logging.info(f"[get_form_data_from_session] Reconstructed array {array_key} with {len(array_list)} items")
            
            # Special logging for cofinancers
            if 'cofinancers' in array_key:
                logging.info(f"[COFINANCERS] Reconstructed {array_key}: {array_list}")
    
    # Process regular fields
    for key, value in st.session_state.items():
        # Skip file info keys - they contain binary data that can't be serialized
        if '_file_info' in key:
            continue
        
        # Skip array element keys (already processed above)
        if '.' in key and any(part.isdigit() for part in key.split('.')):
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
                    # Don't overwrite arrays we just reconstructed
                    if parts[-1] not in d or not isinstance(d[parts[-1]], list):
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
                        # Special logging for estimatedValue
                        if 'estimatedValue' in key:
                            logging.info(f"[ESTIMATED_VALUE] Setting in form_data: {'.'.join(field_parts)} = {value}")
    
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
            lot_double_prefix = f'lot_{i}.lot_{i}_'  # Handle double-prefixed keys
            
            for key, value in st.session_state.items():
                # Skip file info keys - they contain binary data that can't be serialized
                if '_file_info' in key:
                    continue
                    
                # Skip widget keys
                if key.startswith('widget_'):
                    continue
                    
                if key.startswith(lot_prefix):
                    # Remove the lot prefix
                    field_name = key[len(lot_prefix):]
                    
                    # Check if this has double prefix pattern (lot_0.lot_0_orderType)
                    if field_name.startswith(f'lot_{i}_'):
                        # Remove the redundant prefix
                        field_name = field_name[len(f'lot_{i}_'):]
                    
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
            
            # Add any arrays that belong to this lot
            for array_key, array_value in lot_arrays.items():
                if array_key.startswith(f'lot_{i}.'):
                    # Remove the lot prefix to get the field path
                    field_path = array_key[len(f'lot_{i}.'):]
                    parts = field_path.split('.')
                    
                    # Navigate to the correct position in lot_data
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
                            d[parts[-1]] = array_value
                    
                    logging.info(f"[get_form_data_from_session] Added lot array {array_key} to lot {i}")
            
            lots_data.append(lot_data)
        
        if lots_data:
            form_data['lots'] = lots_data
    
    # Include lot configuration metadata
    if 'lotsInfo.hasLots' in st.session_state:
        if 'lotsInfo' not in form_data:
            form_data['lotsInfo'] = {}
        form_data['lotsInfo']['hasLots'] = st.session_state['lotsInfo.hasLots']
    
    # Save lot_mode and num_lots for proper value calculation
    if 'lot_mode' in st.session_state:
        form_data['lot_mode'] = st.session_state['lot_mode']
    
    # Calculate and save num_lots
    if lot_mode == 'multiple':
        # Count actual number of lots
        lot_indices = set()
        for key in st.session_state.keys():
            if key.startswith('lot_') and '.' in key:
                lot_part = key.split('.')[0]
                if '_' in lot_part:
                    idx = lot_part.split('_')[1]
                    if idx.isdigit():
                        lot_indices.add(int(idx))
        form_data['num_lots'] = len(lot_indices)
    else:
        form_data['num_lots'] = 0
    
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
    
    # Clear edit data loaded flag
    if 'edit_data_loaded' in st.session_state:
        del st.session_state['edit_data_loaded']
    
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