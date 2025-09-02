"""Utilities for lot-aware form management."""
import streamlit as st


def get_current_lot_context(current_step_keys):
    """
    Determine the lot context for the current step.
    Returns: dict with 'mode', 'lot_index', 'lot_name', 'is_lot_context'
    """
    context = {
        'mode': 'general',  # 'general' or 'lots'
        'lot_index': None,  # Index of current lot (0-based)
        'lot_name': None,   # Display name of current lot
        'is_lot_context': False,  # True if this is a lot context step
        'original_keys': []  # Original field keys without lot prefix
    }
    
    # Check if any of the current step keys are lot-specific
    for key in current_step_keys:
        if key.startswith('lot_context_'):
            # This is a lot context step
            context['is_lot_context'] = True
            context['mode'] = 'lots'
            context['lot_index'] = int(key.split('_')[2])
            lots = st.session_state.get("lots", [])
            if context['lot_index'] < len(lots):
                context['lot_name'] = lots[context['lot_index']].get("name", f"Sklop {context['lot_index'] + 1}")
            break
        elif key.startswith('lot_'):
            # This is a lot-specific field step
            context['mode'] = 'lots'
            parts = key.split('_', 2)  # lot_0_orderType -> ['lot', '0', 'orderType']
            if len(parts) >= 3:
                context['lot_index'] = int(parts[1])
                context['original_keys'].append(parts[2])
                lots = st.session_state.get("lots", [])
                if context['lot_index'] < len(lots):
                    context['lot_name'] = lots[context['lot_index']].get("name", f"Sklop {context['lot_index'] + 1}")
    
    # If no lot-specific keys found, check if lots exist to determine mode
    if context['mode'] == 'general':
        has_lots = st.session_state.get("lotsInfo.hasLots", False)
        lots = st.session_state.get("lots", [])
        if has_lots and len(lots) > 0:
            context['mode'] = 'lots'
        context['original_keys'] = current_step_keys
    
    return context


def get_lot_scoped_key(field_key, lot_index=None):
    """
    Get the session state key for a field, scoped to a lot if needed.
    
    Args:
        field_key: Original field key (e.g., 'orderType.type')
        lot_index: Lot index (None for general mode)
        
    Returns:
        Scoped key (e.g., 'lot_0.orderType.type' or 'general.orderType.type')
    """
    if lot_index is not None:
        return f"lot_{lot_index}.{field_key}"
    else:
        return f"general.{field_key}"


def get_lot_data(lot_index=None):
    """
    Get all data for a specific lot or general mode.
    
    Args:
        lot_index: Lot index (None for general mode)
        
    Returns:
        Dictionary of data for the lot
    """
    if lot_index is not None:
        key_prefix = f"lot_{lot_index}."
    else:
        key_prefix = "general."
    
    lot_data = {}
    for key, value in st.session_state.items():
        if key.startswith(key_prefix):
            # Remove the prefix to get the field key
            field_key = key[len(key_prefix):]
            lot_data[field_key] = value
    
    return lot_data


def initialize_lot_session_state():
    """
    Initialize lot-related session state variables.
    """
    if "lot_mode" not in st.session_state:
        # UNIFIED LOT ARCHITECTURE: Default to 'single', never 'none'
        st.session_state.lot_mode = "single"
    
    if "current_lot_index" not in st.session_state:
        st.session_state.current_lot_index = None


def migrate_existing_data_to_lot_structure():
    """
    Migrate existing session data to lot-aware structure.
    This helps with backward compatibility.
    """
    # List of fields that should be moved to lot-scoped keys
    lot_specific_fields = [
        "orderType", "technicalSpecifications", "executionDeadline", 
        "priceInfo", "inspectionInfo", "negotiationsInfo",
        "participationAndExclusion", "participationConditions", 
        "financialGuarantees", "variantOffers", "selectionCriteria"
    ]
    
    has_lots = st.session_state.get("lotsInfo.hasLots", False)
    lots = st.session_state.get("lots", [])
    
    if not has_lots or len(lots) == 0:
        # Migrate to general structure
        for field in lot_specific_fields:
            if field in st.session_state:
                general_key = f"general.{field}"
                if general_key not in st.session_state:
                    st.session_state[general_key] = st.session_state[field]
    else:
        # If lots exist but data is in old structure, we need to decide
        # For now, we'll leave existing data and let users re-enter per lot
        pass


def get_lot_progress_info():
    """
    Get information about lot completion progress.
    
    Returns:
        Dictionary with progress information
    """
    has_lots = st.session_state.get("lotsInfo.hasLots", False)
    lots = st.session_state.get("lots", [])
    
    if not has_lots or len(lots) == 0:
        return {
            'mode': 'general',
            'total_lots': 1,
            'current_lot': 1,
            'lot_name': 'Splošni sklop'
        }
    else:
        # Determine current lot from current step
        current_step_keys = st.session_state.get("current_step_keys", [])
        context = get_current_lot_context(current_step_keys)
        
        # Check if we're actually on a lot-specific step
        is_lot_specific = context.get('mode') == 'lots' and context.get('lot_index') is not None
        
        if not is_lot_specific:
            # We have lots but we're on general steps (base steps)
            return {
                'mode': 'general',
                'total_lots': len(lots),
                'current_lot': 1,
                'lot_name': 'Splošni podatki'  # General data that applies to all lots
            }
        
        current_lot_index = context.get('lot_index') or 0
        
        return {
            'mode': 'lots',
            'total_lots': len(lots),
            'current_lot': current_lot_index + 1,
            'lot_name': lots[current_lot_index].get("name", f"Sklop {current_lot_index + 1}") if current_lot_index is not None and current_lot_index < len(lots) else "Unknown"
        }


def render_lot_context_step(lot_index):
    """
    Render the lot context information step.
    
    Args:
        lot_index: Index of the lot to show context for
    """
    lots = st.session_state.get("lots", [])
    if lot_index < len(lots):
        lot = lots[lot_index]
        lot_name = lot.get("name", f"Sklop {lot_index + 1}")
        
        # Use a cleaner, simpler design
        st.markdown(f"""
        ### 📦 Vnos podatkov za sklop
        
        ## **{lot_name}**
        """)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"""
            Sedaj boste izpolnili vse podatke o javnem naročilu za ta sklop.  
            Vsi naslednji koraki se bodo nanašali izključno na ta sklop.
            """)
        
        with col2:
            st.metric("Napredek", f"{lot_index + 1}/{len(lots)} sklopov")
        
        st.divider()
        
        # If this is not the first lot, show what's been completed
        if lot_index > 0:
            with st.expander("✅ Dokončani sklopi"):
                for i in range(lot_index):
                    completed_lot = lots[i]
                    st.write(f"• **{completed_lot.get('name', f'Sklop {i+1}')}**")
    else:
        st.error(f"Sklop {lot_index + 1} ni najden.")