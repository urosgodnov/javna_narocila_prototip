"""Manager for lot-aware field rendering and data management."""
import streamlit as st
from typing import Any, Dict, Optional


class LotFieldManager:
    """Manages field keys and values in lot-aware context."""
    
    def __init__(self, lot_index: Optional[int] = None):
        """
        Initialize the field manager.
        
        Args:
            lot_index: Current lot index (None for general/no-lot mode)
        """
        self.lot_index = lot_index
        self.prefix = self._get_prefix()
    
    def _get_prefix(self) -> str:
        """Get the appropriate prefix for field keys."""
        if self.lot_index is not None:
            return f"lot_{self.lot_index}"
        return "general"
    
    def get_field_key(self, field_name: str) -> str:
        """
        Get the properly scoped session state key for a field.
        
        Args:
            field_name: Original field name (e.g., 'orderType.type')
            
        Returns:
            Scoped key (e.g., 'lot_0.orderType.type' or 'general.orderType.type')
        """
        return f"{self.prefix}.{field_name}"
    
    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """
        Get the value of a field from session state.
        
        Args:
            field_name: Original field name
            default: Default value if not found
            
        Returns:
            Field value or default
        """
        key = self.get_field_key(field_name)
        return st.session_state.get(key, default)
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """
        Set the value of a field in session state.
        
        Args:
            field_name: Original field name
            value: Value to set
        """
        key = self.get_field_key(field_name)
        st.session_state[key] = value
    
    def get_all_lot_data(self) -> Dict[str, Any]:
        """
        Get all data for the current lot.
        
        Returns:
            Dictionary of all fields for this lot
        """
        data = {}
        prefix_with_dot = f"{self.prefix}."
        
        for key, value in st.session_state.items():
            if key.startswith(prefix_with_dot):
                # Remove prefix to get original field name
                field_name = key[len(prefix_with_dot):]
                data[field_name] = value
        
        return data
    
    def copy_from_lot(self, source_lot_index: int, field_patterns: Optional[list] = None) -> None:
        """
        Copy field values from another lot.
        
        Args:
            source_lot_index: Index of the lot to copy from
            field_patterns: List of field patterns to copy (None = copy all)
        """
        source_prefix = f"lot_{source_lot_index}."
        dest_prefix = f"{self.prefix}."
        
        for key, value in st.session_state.items():
            if key.startswith(source_prefix):
                field_name = key[len(source_prefix):]
                
                # Check if this field should be copied
                if field_patterns is None or any(field_name.startswith(p) for p in field_patterns):
                    dest_key = f"{dest_prefix}{field_name}"
                    st.session_state[dest_key] = value
    
    def clear_lot_data(self) -> None:
        """Clear all data for the current lot."""
        prefix_with_dot = f"{self.prefix}."
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith(prefix_with_dot)]
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def get_current_lot_index() -> Optional[int]:
        """
        Determine the current lot index from session state.
        
        Returns:
            Current lot index or None if not in lot mode
        """
        # Check if we're in lot mode
        # UNIFIED LOT ARCHITECTURE: Default to 'single', never 'none'
        lot_mode = st.session_state.get("lot_mode", "single")
        if lot_mode == "single" and not st.session_state.get("lotsInfo.hasLots", False):
            # Single implicit lot mode - return 0 for the default lot
            return 0
        
        # Check for explicit current lot index
        if "current_lot_index" in st.session_state:
            return st.session_state.current_lot_index
        
        # Try to determine from current step keys
        current_step_keys = st.session_state.get("current_step_keys", [])
        for key in current_step_keys:
            if key.startswith("lot_") and "_" in key[4:]:
                parts = key.split("_", 2)
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1])
        
        return 0  # Default to first lot


def create_lot_aware_field(
    field_name: str,
    field_type: str,
    label: str,
    lot_manager: LotFieldManager,
    **kwargs
) -> Any:
    """
    Create a Streamlit input field that's lot-aware.
    
    Args:
        field_name: Original field name
        field_type: Type of Streamlit widget (text_input, selectbox, etc.)
        label: Field label
        lot_manager: LotFieldManager instance
        **kwargs: Additional arguments for the Streamlit widget
        
    Returns:
        The created widget's return value
    """
    # Get the properly scoped key
    key = lot_manager.get_field_key(field_name)
    
    # Get current value
    current_value = lot_manager.get_field_value(field_name, kwargs.get('value', ''))
    
    # Remove 'value' from kwargs if present
    kwargs.pop('value', None)
    
    # Get the appropriate Streamlit function
    widget_func = getattr(st, field_type)
    
    # Create the widget with the scoped key
    result = widget_func(
        label,
        value=current_value,
        key=key,
        **kwargs
    )
    
    return result