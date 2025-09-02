"""
CRITICAL FIX: Eliminate all sources of lot_mode='none'
=====================================================

Problem: AI suggestions not working for negotiations fields because lot_mode='none' 
prevents proper data access in the unified lot architecture.

Root Cause: Multiple files defaulted to 'none' when lot_mode wasn't in session state,
violating the unified lot architecture principle that ALL forms must have at least one lot.

Solution: Changed ALL defaults from 'none' to 'single' and added startup safeguards.

Files Fixed:
1. app.py - Added startup safeguard to force lot_mode='single'
2. utils/lot_utils.py - Changed default from 'none' to 'single' 
3. ui/renderers/lots_info_renderer.py - Never allows lot_mode='none'
4. utils/lot_field_manager.py - Changed default to 'single'
5. utils/schema_utils.py - Changed default to 'single'
6. utils/validations.py - Changed default to 'single' and updated conditions
7. utils/form_helpers/form_context.py - Force correction in __post_init__

Applied on: 2025-01-02
"""

import streamlit as st
import logging

def apply_lot_mode_fix():
    """
    Apply the lot_mode fix to ensure it's never 'none'.
    This function can be called at startup to ensure proper state.
    """
    
    # CRITICAL: Force lot_mode to never be 'none'
    if 'lot_mode' not in st.session_state or st.session_state.get('lot_mode') == 'none':
        st.session_state['lot_mode'] = 'single'
        logging.warning("[LOT_MODE_FIX] Forced lot_mode from 'none' to 'single'")
    
    # Ensure lots structure exists
    if 'lots' not in st.session_state or not st.session_state.get('lots'):
        st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
        logging.info("[LOT_MODE_FIX] Created default lot structure")
    
    # Ensure current_lot_index is valid
    if 'current_lot_index' not in st.session_state:
        st.session_state['current_lot_index'] = 0
    elif st.session_state['current_lot_index'] >= len(st.session_state['lots']):
        st.session_state['current_lot_index'] = 0
        
    logging.info(f"[LOT_MODE_FIX] Final state: lot_mode={st.session_state.get('lot_mode')}, lots={len(st.session_state.get('lots', []))}, current_lot_index={st.session_state.get('current_lot_index')}")
    
    return True

def verify_lot_mode_consistency():
    """
    Verify that lot_mode is consistent and valid.
    Returns True if valid, False if issues found.
    """
    lot_mode = st.session_state.get('lot_mode')
    lots = st.session_state.get('lots', [])
    
    issues = []
    
    if lot_mode == 'none':
        issues.append("lot_mode is 'none' - should be 'single' or 'multiple'")
    
    if lot_mode == 'single' and len(lots) != 1:
        issues.append(f"lot_mode is 'single' but {len(lots)} lots exist")
    
    if lot_mode == 'multiple' and len(lots) <= 1:
        issues.append(f"lot_mode is 'multiple' but only {len(lots)} lot(s) exist")
    
    if len(lots) == 0:
        issues.append("No lots exist - at least one lot is required")
    
    if issues:
        for issue in issues:
            logging.error(f"[LOT_MODE_VERIFY] {issue}")
        return False
    
    logging.info(f"[LOT_MODE_VERIFY] Valid: lot_mode={lot_mode}, lots={len(lots)}")
    return True

# Auto-apply fix when patch is imported
if __name__ != "__main__":
    apply_lot_mode_fix()