#!/usr/bin/env python3
"""
Widget synchronization utilities for Streamlit.
Ensures widget values are properly synced to lot keys before validation.
"""

import streamlit as st
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class WidgetSync:
    """
    Handles synchronization between Streamlit widget keys and lot-scoped keys.
    
    Problem: Streamlit stores widget values in widget keys immediately,
    but the sync to lot keys happens on next rerun. This causes validation
    to fail if it runs before the sync.
    
    Solution: Provide explicit sync methods that can be called before validation.
    """
    
    @staticmethod
    def sync_all_widget_values():
        """
        Sync all widget values to their corresponding lot keys.
        Call this before validation to ensure all values are available.
        
        Returns:
            Number of values synced
        """
        synced_count = 0
        
        # Find all widget keys that need syncing
        widget_keys = [k for k in st.session_state.keys() if k.startswith('widget_')]
        
        for widget_key in widget_keys:
            # Skip non-lot widget keys
            if not widget_key.startswith('widget_lots.'):
                continue
            
            # Get corresponding lot key
            lot_key = widget_key.replace('widget_', '')
            
            # Sync if values differ or lot key doesn't exist
            widget_value = st.session_state[widget_key]
            lot_value = st.session_state.get(lot_key)
            
            if lot_value != widget_value:
                st.session_state[lot_key] = widget_value
                synced_count += 1
                logger.debug(f"Synced {widget_key} -> {lot_key}")
        
        return synced_count
    
    @staticmethod
    def sync_widget_for_field(field_name: str, lot_index: int = 0):
        """
        Sync a specific widget value to its lot key.
        
        Args:
            field_name: Field name (e.g., 'clientInfo.singleClientName')
            lot_index: Lot index (default 0)
        """
        lot_key = f'lots.{lot_index}.{field_name}'
        widget_key = f'widget_{lot_key}'
        
        if widget_key in st.session_state:
            widget_value = st.session_state[widget_key]
            if st.session_state.get(lot_key) != widget_value:
                st.session_state[lot_key] = widget_value
                logger.debug(f"Synced single field: {widget_key} -> {lot_key}")
    
    @staticmethod
    def ensure_validation_ready():
        """
        Ensure all data is ready for validation.
        This includes syncing widget values and checking lot structure.
        
        Call this at the beginning of any validation process.
        """
        # Ensure lot structure exists
        if 'lots' not in st.session_state or not st.session_state['lots']:
            st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
            st.session_state['current_lot_index'] = 0
        
        # Sync all widget values
        synced = WidgetSync.sync_all_widget_values()
        
        if synced > 0:
            logger.info(f"Synced {synced} widget values before validation")
        
        return synced
    
    @staticmethod
    def get_field_value_with_widget_fallback(field_name: str, lot_index: int = 0) -> Any:
        """
        Get field value, checking both lot key and widget key.
        
        Args:
            field_name: Field name
            lot_index: Lot index
            
        Returns:
            Field value or None
        """
        # Try lot key first
        lot_key = f'lots.{lot_index}.{field_name}'
        if lot_key in st.session_state:
            return st.session_state[lot_key]
        
        # Try widget key
        widget_key = f'widget_{lot_key}'
        if widget_key in st.session_state:
            # Also sync it for next time
            value = st.session_state[widget_key]
            st.session_state[lot_key] = value
            return value
        
        return None
    
    @staticmethod
    def debug_widget_state(field_pattern: str = 'client'):
        """
        Debug widget and lot key state for fields matching pattern.
        
        Args:
            field_pattern: Pattern to match in field names
            
        Returns:
            Dict with debug information
        """
        debug_info = {
            'widget_keys': [],
            'lot_keys': [],
            'mismatched': [],
            'widget_only': [],
            'lot_only': []
        }
        
        # Find all relevant keys
        for key in st.session_state.keys():
            if field_pattern.lower() not in key.lower():
                continue
            
            if key.startswith('widget_lots.'):
                debug_info['widget_keys'].append(key)
                # Check if lot key exists
                lot_key = key.replace('widget_', '')
                if lot_key not in st.session_state:
                    debug_info['widget_only'].append(key)
                elif st.session_state[key] != st.session_state[lot_key]:
                    debug_info['mismatched'].append({
                        'widget': key,
                        'lot': lot_key,
                        'widget_value': st.session_state[key],
                        'lot_value': st.session_state[lot_key]
                    })
            elif key.startswith('lots.') and field_pattern.lower() in key.lower():
                debug_info['lot_keys'].append(key)
                # Check if widget key exists
                widget_key = f'widget_{key}'
                if widget_key not in st.session_state:
                    debug_info['lot_only'].append(key)
        
        return debug_info


# Convenience function for integration
def prepare_for_validation():
    """
    Convenience function to prepare session state for validation.
    Call this before any validation to ensure data is synced.
    """
    return WidgetSync.ensure_validation_ready()