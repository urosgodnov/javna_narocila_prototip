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
        st.session_state.lot_mode = "general"
    
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
        "exclusionReasons", "participationConditions", 
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
        
        current_lot_index = context.get('lot_index') or 0  # Handle None properly
        
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
        
        st.markdown(f"""
        <div class="lot-card" style="background: linear-gradient(135deg, var(--primary-900) 0%, var(--primary-700) 100%); 
                    color: white; padding: 2rem; border-radius: var(--radius-lg); margin-bottom: 2rem;
                    box-shadow: var(--shadow-xl); position: relative; overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                                    linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                                    linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                                    linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%);
                        background-size: 20px 20px; opacity: 0.3; pointer-events: none;"></div>
            <div style="position: relative; z-index: 1;">
                <h2 style="margin: 0 0 1rem 0; font-size: 2rem; font-weight: 700; color: white;">🎯 {lot_name}</h2>
                <p style="margin: 0 0 0.75rem 0; font-size: 1.125rem; line-height: 1.6; opacity: 0.95;">
                    Sedaj boste izpolnili podatke za ta sklop. Vsi naslednji koraki se nanašajo na ta sklop.
                </p>
                <div style="background: rgba(255,255,255,0.2); padding: 0.75rem 1.25rem; border-radius: var(--radius-md); 
                           display: inline-block; margin-top: 0.5rem;">
                    <strong style="font-weight: 600;">Sklop {lot_index + 1} od {len(lots)}</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show lot-specific order type if it exists
        if "orderType" in lot:
            order_type = lot["orderType"]
            if order_type:
                st.info(f"ℹ️ Vrsta naročila za ta sklop: {order_type.get('type', 'Ni določeno')}")
    else:
        st.error(f"Sklop {lot_index + 1} ni najden.")