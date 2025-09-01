"""
Integration module for unified lot architecture.
Provides a single point of integration for app.py.
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

def render_warning_box(title: str, content: str):
    """Render a consistent warning box with yellow/orange styling."""
    # Remove any existing warning prefixes from content
    content = content.replace("⚠️", "").replace("ℹ️", "").replace("**Opozorilo:**", "").replace("**OPOZORILO:**", "").strip()
    
    # Create custom HTML for warning box
    warning_html = f"""
    <div style="
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    ">
        <div style="
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
        ">
            <span style="font-size: 1.2rem;">⚠️</span>
            <div style="flex: 1;">
                <strong style="color: #856404; font-size: 1rem;">{title}</strong>
                <div style="color: #856404; margin-top: 0.5rem; line-height: 1.5;">
                    {content}
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)

from ui.controllers.form_controller import FormController
from utils.validation_adapter import ValidationAdapter
from utils.data_persistence_adapter import DataPersistenceAdapter


class FormIntegration:
    """
    Main integration class for unified lot architecture.
    Use this in app.py for all form operations.
    """
    
    def __init__(self):
        """Initialize integration with all adapters."""
        self.controller = FormController()
        self.persistence = DataPersistenceAdapter()
        
        # Pre-lot screens that apply to ALL lots
        self.pre_lot_screens = [
            'clientInfo',
            'projectInfo',
            'legalBasis', 
            'submissionProcedure',
            'lotsInfo'
        ]
        
        # Initialize session state if needed
        if 'lots' not in st.session_state:
            st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
            st.session_state['current_lot_index'] = 0
    
    def render_step(self, step_properties: Dict[str, Any], step_name: str = None) -> None:
        """
        Render a form step with proper lot handling.
        
        Args:
            step_properties: Properties/schema for the step
            step_name: Optional step name for context
        """
        # Determine if this is a pre-lot screen
        is_pre_lot = False
        if step_name:
            is_pre_lot = any(screen in step_name for screen in self.pre_lot_screens)
        
        # Set schema and render
        self.controller.set_schema({'properties': step_properties})
        
        # For pre-lot screens, show info that data applies to all lots
        if is_pre_lot and len(st.session_state.get('lots', [])) > 1:
            st.info(f"ℹ️ Ti podatki veljajo za vse sklope ({len(st.session_state['lots'])} sklopov)")
        
        # Render the form
        self.controller.render_form(
            show_lot_navigation=not is_pre_lot,  # Only show lot nav for lot-specific screens
            show_validation_summary=True
        )
        
        # Sync pre-lot data if needed
        if is_pre_lot:
            self._sync_pre_lot_data(step_name)
    
    def _sync_pre_lot_data(self, screen_name: str) -> None:
        """
        Sync pre-lot screen data across all lots.
        
        Args:
            screen_name: Name of the pre-lot screen
        """
        lots = st.session_state.get('lots', [])
        if len(lots) <= 1:
            return
        
        # Find the screen prefix
        screen_prefix = None
        for screen in self.pre_lot_screens:
            if screen in screen_name:
                screen_prefix = screen
                break
        
        if not screen_prefix:
            return
        
        # Sync data from lot 0 to all other lots
        lot0_prefix = f'lots.0.{screen_prefix}.'
        
        for key in st.session_state.keys():
            if key.startswith(lot0_prefix):
                field_name = key[len(lot0_prefix):]
                value = st.session_state[key]
                
                # Copy to all other lots
                for i in range(1, len(lots)):
                    target_key = f'lots.{i}.{screen_prefix}.{field_name}'
                    st.session_state[target_key] = value
        
        logging.debug(f"Synced {screen_prefix} data across {len(lots)} lots")
    
    def validate_step(self, step_keys: list, step_number: int = None) -> tuple:
        """
        Validate current step.
        
        Args:
            step_keys: Keys for the step to validate
            step_number: Optional step number
            
        Returns:
            Tuple of (is_valid, errors)
        """
        return self.controller.validation_manager.validate_step(step_keys, step_number)
    
    def save_form_data(self) -> Dict[str, Any]:
        """
        Extract and return form data for saving.
        
        Returns:
            Dictionary with form data in unified format
        """
        # Ensure pre-lot data is synced before saving
        self.persistence.ensure_pre_lot_data_synced(self.pre_lot_screens)
        
        # Extract and return data
        return self.persistence.extract_form_data_from_session()
    
    def load_form_data(self, form_data: Dict[str, Any]) -> None:
        """
        Load form data into session state.
        
        Args:
            form_data: Dictionary with form data (old or new format)
        """
        self.persistence.load_form_data_to_session(form_data)
        
        # Ensure pre-lot data is synced after loading
        self.persistence.ensure_pre_lot_data_synced(self.pre_lot_screens)
    
    def get_current_lot_info(self) -> Dict[str, Any]:
        """
        Get information about current lot.
        
        Returns:
            Dictionary with current lot info
        """
        lots = st.session_state.get('lots', [])
        current_index = st.session_state.get('current_lot_index', 0)
        
        if current_index < len(lots):
            return {
                'index': current_index,
                'name': lots[current_index].get('name', f'Sklop {current_index + 1}'),
                'total_lots': len(lots)
            }
        
        return {
            'index': 0,
            'name': 'Splošni sklop',
            'total_lots': 1
        }
    
    def add_lot(self, name: Optional[str] = None) -> int:
        """
        Add a new lot.
        
        Args:
            name: Optional lot name
            
        Returns:
            Index of the new lot
        """
        lots = st.session_state.get('lots', [])
        new_index = len(lots)
        
        if name is None:
            name = f"Sklop {new_index + 1}"
        
        lots.append({'name': name, 'index': new_index})
        st.session_state['lots'] = lots
        
        # Copy pre-lot data to new lot
        if new_index > 0:
            for screen in self.pre_lot_screens:
                lot0_prefix = f'lots.0.{screen}.'
                
                for key in st.session_state.keys():
                    if key.startswith(lot0_prefix):
                        field_name = key[len(lot0_prefix):]
                        value = st.session_state[key]
                        target_key = f'lots.{new_index}.{screen}.{field_name}'
                        st.session_state[target_key] = value
        
        logging.info(f"Added new lot: {name} at index {new_index}")
        return new_index
    
    def remove_lot(self, lot_index: int) -> bool:
        """
        Remove a lot.
        
        Args:
            lot_index: Index of lot to remove
            
        Returns:
            True if removed, False if cannot remove (e.g., last lot)
        """
        lots = st.session_state.get('lots', [])
        
        if len(lots) <= 1:
            logging.warning("Cannot remove last lot")
            return False
        
        if lot_index >= len(lots):
            logging.warning(f"Invalid lot index: {lot_index}")
            return False
        
        # Remove lot from list
        removed_lot = lots.pop(lot_index)
        
        # Re-index remaining lots
        for i, lot in enumerate(lots):
            lot['index'] = i
        
        st.session_state['lots'] = lots
        
        # Remove lot data from session state
        lot_prefix = f'lots.{lot_index}.'
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith(lot_prefix)]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Re-index data for lots after the removed one
        for i in range(lot_index + 1, len(lots) + 1):
            old_prefix = f'lots.{i}.'
            new_prefix = f'lots.{i-1}.'
            
            keys_to_move = [k for k in st.session_state.keys() if k.startswith(old_prefix)]
            for key in keys_to_move:
                new_key = new_prefix + key[len(old_prefix):]
                st.session_state[new_key] = st.session_state[key]
                del st.session_state[key]
        
        # Adjust current lot index if needed
        if st.session_state.get('current_lot_index', 0) >= len(lots):
            st.session_state['current_lot_index'] = len(lots) - 1
        
        logging.info(f"Removed lot: {removed_lot['name']}")
        return True