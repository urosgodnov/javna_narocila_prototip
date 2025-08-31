"""
Adapter for ValidationManager to work with unified lot architecture.
In the new system, everything is a lot - minimum one "Splošni sklop".
This adapter ensures validation works correctly with this principle.
"""

from typing import Any, Dict, List, Tuple, Optional
from utils.widget_sync import WidgetSync

class ValidationAdapter:
    """
    Adapts validation logic for the unified lot architecture.
    Key principles:
    1. Everything is a lot (minimum 1 "Splošni sklop")
    2. Screens before lot configuration apply to ALL lots
    3. Lot-specific screens validate individual lots
    """
    
    @staticmethod
    def get_lot_context_for_validation(session_state: Dict[str, Any], step_keys: List[str]) -> Dict[str, Any]:
        """
        Determine the lot context for validation based on current step.
        
        Args:
            session_state: Session state
            step_keys: Keys for current step
            
        Returns:
            Dict with lot_mode and current_lot_index
        """
        # In new architecture, we always have lots
        lots = session_state.get('lots', [])
        
        # Default to single lot mode (everything in lot 0)
        if len(lots) <= 1:
            return {
                'lot_mode': 'single',
                'current_lot_index': 0,
                'has_lots': False  # For backward compatibility
            }
        
        # Multiple lots
        # Check if we're on a lot-specific step
        is_lot_specific = any(
            key.startswith('lot_') or 
            key.startswith('lots.') 
            for key in step_keys
        )
        
        if is_lot_specific:
            # Get current lot index from session state
            current_lot = session_state.get('current_lot_index', 0)
            return {
                'lot_mode': 'multiple',
                'current_lot_index': current_lot,
                'has_lots': True
            }
        else:
            # General step that applies to all lots
            return {
                'lot_mode': 'multiple',
                'current_lot_index': None,  # Validate all lots
                'has_lots': True
            }
    
    @staticmethod
    def adapt_field_key(field_key: str, lot_index: int = 0) -> str:
        """
        Convert field key to lot-scoped key for new architecture.
        
        Args:
            field_key: Original field key
            lot_index: Lot index (default 0)
            
        Returns:
            Lot-scoped key
        """
        # Skip if already lot-scoped
        if field_key.startswith('lots.'):
            return field_key
        
        # Skip global fields
        global_fields = ['schema', 'current_step', 'lots', 'current_lot_index']
        if field_key in global_fields:
            return field_key
        
        # Convert to lot-scoped
        return f'lots.{lot_index}.{field_key}'
    
    @staticmethod
    def get_field_value_with_fallback(session_state: Dict[str, Any], 
                                     field_key: str, 
                                     lot_index: Optional[int] = None) -> Any:
        """
        Get field value with fallback for backward compatibility.
        
        Tries multiple key patterns:
        1. New lot-scoped: lots.{index}.{field}
        2. Old lot pattern: lot_{index}.{field}
        3. General pattern: general.{field}
        4. Plain key: {field}
        
        Args:
            session_state: Session state
            field_key: Field key to look for
            lot_index: Optional lot index
            
        Returns:
            Field value or None
        """
        # Try new lot-scoped pattern first
        if lot_index is not None:
            new_key = f'lots.{lot_index}.{field_key}'
            if new_key in session_state:
                return session_state[new_key]
            
            # Try old lot pattern
            old_key = f'lot_{lot_index}.{field_key}'
            if old_key in session_state:
                return session_state[old_key]
        
        # Try general pattern (for single lot / old system)
        general_key = f'general.{field_key}'
        if general_key in session_state:
            return session_state[general_key]
        
        # Try lot 0 (default lot in new system)
        lot0_key = f'lots.0.{field_key}'
        if lot0_key in session_state:
            return session_state[lot0_key]
        
        # Try plain key
        if field_key in session_state:
            return session_state[field_key]
        
        return None
    
    @staticmethod
    def validate_for_all_lots(validation_func, session_state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Run validation for all lots (for screens before lot configuration).
        
        Args:
            validation_func: Validation function to run
            session_state: Session state
            
        Returns:
            Tuple of (is_valid, errors)
        """
        lots = session_state.get('lots', [])
        all_valid = True
        all_errors = []
        
        # If no lots or single lot, validate as single
        if len(lots) <= 1:
            return validation_func()
        
        # Validate each lot
        original_lot_index = session_state.get('current_lot_index', 0)
        
        for i, lot in enumerate(lots):
            # Temporarily switch to this lot for validation
            session_state['current_lot_index'] = i
            
            # Run validation for this lot
            is_valid, errors = validation_func()
            
            if not is_valid:
                all_valid = False
                # Prefix errors with lot name for clarity
                lot_name = lot.get('name', f'Sklop {i+1}')
                prefixed_errors = [f"{lot_name}: {error}" for error in errors]
                all_errors.extend(prefixed_errors)
        
        # Restore original lot index
        session_state['current_lot_index'] = original_lot_index
        
        return all_valid, all_errors
    
    @staticmethod
    def update_validation_manager_for_unified_lots(validation_manager):
        """
        Monkey-patch ValidationManager methods to work with unified lot architecture.
        
        Args:
            validation_manager: ValidationManager instance to update
        """
        # Store original validate_step
        original_validate_step = validation_manager.validate_step
        
        # Create a wrapper class for session_state that maps keys
        class LotAwareSessionState:
            """Wrapper for session_state that automatically maps to lot-scoped keys."""
            
            def __init__(self, original_session_state):
                self._original = original_session_state
            
            def get(self, key, default=None):
                """Get value with automatic lot-scoping for unified architecture."""
                # Special handling for 'lots' and other global keys
                if key in ['lots', 'current_lot_index', 'current_step', 'schema']:
                    return self._original.get(key, default)
                
                # First check if the key already contains 'lots.' prefix
                if key.startswith('lots.'):
                    return self._original.get(key, default)
                
                # Try lot-scoped version FIRST (this is the new standard)
                current_lot = self._original.get('current_lot_index', 0)
                lot_key = f'lots.{current_lot}.{key}'
                if lot_key in self._original:
                    return self._original[lot_key]
                
                # CRITICAL: Also check widget keys!
                # Streamlit stores values in widget_lots.X.field format
                widget_lot_key = f'widget_lots.{current_lot}.{key}'
                if widget_lot_key in self._original:
                    return self._original[widget_lot_key]
                
                # Try widget key for lot 0
                if current_lot != 0:
                    widget_lot0_key = f'widget_lots.0.{key}'
                    if widget_lot0_key in self._original:
                        return self._original[widget_lot0_key]
                
                # Also try lot 0 explicitly (default lot)
                if current_lot != 0:
                    lot0_key = f'lots.0.{key}'
                    if lot0_key in self._original:
                        return self._original[lot0_key]
                
                # Try old widget format (widget_ prefix without lots)
                widget_key = f'widget_{key}'
                if widget_key in self._original:
                    return self._original[widget_key]
                
                # Finally try the original key (for backward compatibility)
                if key in self._original:
                    return self._original[key]
                
                # Debug logging when key not found (only for client fields during validation)
                if default is None and 'client' in key.lower():
                    import logging
                    logging.debug(f"ValidationAdapter: Key '{key}' not found. Tried: {lot_key}, {widget_lot_key}")
                
                return default
            
            def __getitem__(self, key):
                """Support dict-style access."""
                value = self.get(key, None)
                if value is None and key not in self._original:
                    raise KeyError(key)
                return value
            
            def __setitem__(self, key, value):
                """Support dict-style assignment."""
                self._original[key] = value
            
            def __contains__(self, key):
                """Support 'in' operator."""
                return self.get(key) is not None
            
            def __getattr__(self, name):
                """Forward other attributes to original session_state."""
                return getattr(self._original, name)
        
        # Replace session_state with wrapper
        validation_manager.session_state = LotAwareSessionState(validation_manager.session_state)
        
        def new_validate_step(step_keys: List[str], step_number: int = None) -> Tuple[bool, List[str]]:
            """Enhanced validate_step that handles unified lot architecture."""
            
            # CRITICAL: Sync widget values before validation
            # This ensures widget values are available in lot keys
            WidgetSync.ensure_validation_ready()
            
            # Determine if this is a pre-lot configuration screen
            # These screens apply to ALL lots
            pre_lot_screens = [
                'clientInfo', 'projectInfo', 'legalBasis', 
                'submissionProcedure', 'lotsInfo'
            ]
            
            is_pre_lot = any(key in pre_lot_screens for key in step_keys)
            
            if is_pre_lot and len(validation_manager.session_state.get('lots', [])) > 1:
                # Validate for all lots
                return ValidationAdapter.validate_for_all_lots(
                    lambda: original_validate_step(step_keys, step_number),
                    validation_manager.session_state
                )
            else:
                # Normal validation (current lot or single lot)
                return original_validate_step(step_keys, step_number)
        
        # Replace the method
        validation_manager.validate_step = new_validate_step
        
        return validation_manager