"""
Adapter for data persistence with unified lot architecture.
Handles conversion between old format (general., lot_0.) and new format (lots.0.).
"""

import streamlit as st
from typing import Dict, Any, List
import logging

class DataPersistenceAdapter:
    """
    Adapter to handle data persistence with unified lot architecture.
    
    Key responsibilities:
    1. Convert old format to new format when loading
    2. Ensure data is saved in new format
    3. Handle pre-lot screens that apply to ALL lots
    """
    
    @staticmethod
    def extract_form_data_from_session() -> Dict[str, Any]:
        """
        Extract form data from session state in unified lot format.
        
        Returns:
            Dictionary with form data in new lot-structured format
        """
        form_data = {
            'lots': [],
            'current_step': st.session_state.get('current_step', 0),
            'completed_steps': st.session_state.get('completed_steps', [])
        }
        
        # Get lots structure
        lots = st.session_state.get('lots', [])
        if not lots:
            # Create default lot if none exists
            lots = [{'name': 'Splošni sklop', 'index': 0}]
        
        # Pre-lot configuration screens (apply to ALL lots)
        pre_lot_screens = [
            'clientInfo',
            'projectInfo',
            'legalBasis',
            'submissionProcedure',
            'lotsInfo'
        ]
        
        # Process each lot
        for lot in lots:
            lot_index = lot.get('index', 0)
            lot_data = {
                'name': lot.get('name', f'Sklop {lot_index + 1}'),
                'index': lot_index,
                'data': {}
            }
            
            # Collect all data for this lot
            lot_prefix = f'lots.{lot_index}.'
            
            for key in st.session_state.keys():
                # Skip special keys
                if key in ['lots', 'current_step', 'completed_steps', 'current_lot_index', 'schema']:
                    continue
                
                # Check if this key belongs to this lot
                if key.startswith(lot_prefix):
                    # Extract the field name without lot prefix
                    field_name = key[len(lot_prefix):]
                    lot_data['data'][field_name] = st.session_state[key]
                    logging.debug(f"Extracted {field_name} = {st.session_state[key]} for lot {lot_index}")
            
            form_data['lots'].append(lot_data)
        
        # Add any global metadata
        form_data['form_metadata'] = st.session_state.get('form_metadata', {})
        
        logging.info(f"Extracted form data with {len(form_data['lots'])} lots")
        return form_data
    
    @staticmethod
    def load_form_data_to_session(form_data: Dict[str, Any]) -> None:
        """
        Load form data into session state using unified lot format.
        
        Args:
            form_data: Dictionary with form data (can be old or new format)
        """
        # Clear existing form data
        keys_to_clear = [k for k in st.session_state.keys() 
                         if k.startswith('lots.') or k.startswith('lot_') or k.startswith('general.')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Detect format
        if 'lots' in form_data and isinstance(form_data['lots'], list):
            # New format - load directly
            DataPersistenceAdapter._load_new_format(form_data)
        else:
            # Old format - convert and load
            DataPersistenceAdapter._convert_and_load_old_format(form_data)
        
        # Set metadata
        st.session_state['current_step'] = form_data.get('current_step', 0)
        st.session_state['completed_steps'] = form_data.get('completed_steps', [])
        st.session_state['form_metadata'] = form_data.get('form_metadata', {})
        
        logging.info("Form data loaded to session state")
    
    @staticmethod
    def _load_new_format(form_data: Dict[str, Any]) -> None:
        """Load data that's already in new format."""
        lots_data = form_data.get('lots', [])
        
        # Set up lots structure
        lots = []
        for lot_data in lots_data:
            lots.append({
                'name': lot_data.get('name', f"Sklop {lot_data['index'] + 1}"),
                'index': lot_data['index']
            })
            
            # Load lot data
            lot_index = lot_data['index']
            for field_name, value in lot_data.get('data', {}).items():
                key = f'lots.{lot_index}.{field_name}'
                st.session_state[key] = value
                logging.debug(f"Loaded {key} = {value}")
        
        st.session_state['lots'] = lots
        st.session_state['current_lot_index'] = 0
    
    @staticmethod
    def _convert_and_load_old_format(form_data: Dict[str, Any]) -> None:
        """Convert old format to new format and load."""
        # Determine number of lots
        has_lots = form_data.get('lotsInfo.hasLots', False)
        lot_names = form_data.get('lot_names', [])
        
        if not has_lots or not lot_names:
            # Single lot mode
            lots = [{'name': 'Splošni sklop', 'index': 0}]
            
            # Convert all general. and plain keys to lots.0.
            for key, value in form_data.items():
                if key in ['current_step', 'completed_steps', 'form_metadata']:
                    continue
                
                # Remove prefixes and convert to lot-scoped
                if key.startswith('general.'):
                    field_name = key[8:]  # Remove 'general.'
                elif not key.startswith('lot_'):
                    field_name = key
                else:
                    continue  # Skip lot_ keys in single lot mode
                
                new_key = f'lots.0.{field_name}'
                st.session_state[new_key] = value
                logging.debug(f"Converted {key} -> {new_key}")
        else:
            # Multiple lots mode
            lots = []
            for i, lot_name in enumerate(lot_names):
                lots.append({'name': lot_name, 'index': i})
            
            # Process lot-specific data
            for key, value in form_data.items():
                if key in ['current_step', 'completed_steps', 'form_metadata', 'lot_names']:
                    continue
                
                if key.startswith('lot_'):
                    # Extract lot index and field name
                    # Format: lot_0.field.name
                    parts = key.split('.', 1)
                    if len(parts) >= 2:
                        lot_part = parts[0]  # e.g., 'lot_0'
                        field_name = parts[1]  # e.g., 'field.name'
                        
                        try:
                            lot_index = int(lot_part.split('_')[1])
                            new_key = f'lots.{lot_index}.{field_name}'
                            st.session_state[new_key] = value
                            logging.debug(f"Converted {key} -> {new_key}")
                        except (IndexError, ValueError):
                            logging.warning(f"Could not parse lot key: {key}")
                
                elif key.startswith('general.'):
                    # General fields apply to lot 0 in new format
                    field_name = key[8:]
                    new_key = f'lots.0.{field_name}'
                    st.session_state[new_key] = value
                    logging.debug(f"Converted {key} -> {new_key}")
        
        st.session_state['lots'] = lots
        st.session_state['current_lot_index'] = 0
    
    @staticmethod
    def ensure_pre_lot_data_synced(pre_lot_screens: List[str]) -> None:
        """
        Ensure pre-lot configuration data is synced across all lots.
        
        Args:
            pre_lot_screens: List of screen names that apply to all lots
        """
        lots = st.session_state.get('lots', [])
        if len(lots) <= 1:
            return  # No need to sync for single lot
        
        # For each pre-lot screen, copy data from lot 0 to all other lots
        for screen in pre_lot_screens:
            # Find all keys for this screen in lot 0
            lot0_prefix = f'lots.0.{screen}.'
            screen_data = {}
            
            for key in st.session_state.keys():
                if key.startswith(lot0_prefix):
                    field_name = key[len(lot0_prefix):]
                    screen_data[field_name] = st.session_state[key]
            
            # Copy to all other lots
            for i in range(1, len(lots)):
                for field_name, value in screen_data.items():
                    target_key = f'lots.{i}.{screen}.{field_name}'
                    st.session_state[target_key] = value
                    logging.debug(f"Synced {screen}.{field_name} to lot {i}")
        
        logging.info(f"Synced pre-lot data across {len(lots)} lots")