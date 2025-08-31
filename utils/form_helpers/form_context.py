"""
Form context for unified lot architecture.
ALL forms have lot structure - no exceptions, no backward compatibility.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Fields that should never be lot-scoped
GLOBAL_FIELDS = [
    'schema', 
    'current_step', 
    'form_metadata',
    'lots',
    'current_lot_index',
    'validation_mode',
    'submission_timestamp'
]


@dataclass
class FormContext:
    """
    Unified form context where ALL forms have lot structure.
    No backward compatibility, no legacy support.
    This is the single source of truth for all form state management.
    """
    session_state: Any  # Streamlit session state reference
    lot_index: int = 0  # Current lot index (default 0 for "Splošni sklop")
    current_step: Optional[str] = None
    validation_errors: Dict[str, List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure lot structure exists immediately upon creation"""
        self.ensure_lot_structure()
        # Sync lot_index with session state
        self.lot_index = self.session_state.get('current_lot_index', 0)
    
    def ensure_lot_structure(self) -> None:
        """
        Guarantee lot structure exists for ALL forms.
        This is called automatically and ensures uniform behavior.
        """
        if 'lots' not in self.session_state:
            self.session_state['lots'] = [{
                'name': 'Splošni sklop',
                'index': 0
            }]
            self.session_state['current_lot_index'] = 0
        elif len(self.session_state.get('lots', [])) == 0:
            # Edge case: lots key exists but is empty
            self.session_state['lots'] = [{
                'name': 'Splošni sklop',
                'index': 0
            }]
            self.session_state['current_lot_index'] = 0
            
        # Ensure current_lot_index is valid
        if 'current_lot_index' not in self.session_state:
            self.session_state['current_lot_index'] = 0
        elif self.session_state['current_lot_index'] >= len(self.session_state['lots']):
            self.session_state['current_lot_index'] = 0
    
    def get_field_key(self, field_name: str, force_global: bool = False) -> str:
        """
        ALWAYS return lot-scoped key (except for explicitly global fields).
        
        Args:
            field_name: Name of the field (can include parent path like "parent.child")
            force_global: If True, return global key (not lot-scoped)
            
        Returns:
            Lot-scoped key like "lots.0.field_name" or global key
        """
        if force_global or field_name in GLOBAL_FIELDS:
            return field_name
        
        # EVERYTHING else is lot-scoped, no exceptions
        return f"lots.{self.lot_index}.{field_name}"
    
    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """
        Get field value from session state using lot-scoped key.
        
        Args:
            field_name: Name of the field
            default: Default value if not found
            
        Returns:
            Field value or default
        """
        key = self.get_field_key(field_name)
        return self.session_state.get(key, default)
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """
        Set field value in session state using lot-scoped key.
        
        Args:
            field_name: Name of the field
            value: Value to set
        """
        key = self.get_field_key(field_name)
        self.session_state[key] = value
    
    def delete_field_value(self, field_name: str) -> None:
        """
        Delete field value from session state.
        
        Args:
            field_name: Name of the field to delete
        """
        key = self.get_field_key(field_name)
        if key in self.session_state:
            del self.session_state[key]
    
    def field_exists(self, field_name: str) -> bool:
        """
        Check if a field exists in session state.
        
        Args:
            field_name: Name of the field
            
        Returns:
            True if field exists, False otherwise
        """
        key = self.get_field_key(field_name)
        return key in self.session_state
    
    # Lot Management Methods
    
    def get_current_lot(self) -> Dict[str, Any]:
        """
        Get current lot information.
        
        Returns:
            Dictionary with lot info {'name': str, 'index': int}
        """
        lots = self.session_state.get('lots', [])
        if self.lot_index < len(lots):
            return lots[self.lot_index]
        return {'name': 'Splošni sklop', 'index': 0}
    
    def get_all_lots(self) -> List[Dict[str, Any]]:
        """
        Get all lots.
        
        Returns:
            List of lot dictionaries
        """
        return self.session_state.get('lots', [])
    
    def get_lot_count(self) -> int:
        """
        Get number of lots.
        
        Returns:
            Number of lots (always at least 1)
        """
        return len(self.session_state.get('lots', []))
    
    def switch_to_lot(self, lot_index: int) -> bool:
        """
        Switch to a different lot.
        
        Args:
            lot_index: Index of lot to switch to
            
        Returns:
            True if switch successful, False if index invalid
        """
        lots = self.session_state.get('lots', [])
        if 0 <= lot_index < len(lots):
            self.lot_index = lot_index
            self.session_state['current_lot_index'] = lot_index
            return True
        return False
    
    def add_lot(self, name: Optional[str] = None) -> int:
        """
        Add a new lot.
        
        Args:
            name: Optional name for the lot (defaults to "Sklop N")
            
        Returns:
            Index of the newly created lot
        """
        lots = self.session_state.get('lots', [])
        new_index = len(lots)
        
        if name is None:
            name = f"Sklop {new_index + 1}"
            
        lots.append({
            'name': name,
            'index': new_index
        })
        
        self.session_state['lots'] = lots
        return new_index
    
    def remove_lot(self, lot_index: int) -> bool:
        """
        Remove a lot (if more than one exists).
        Cannot remove the last lot - there must always be at least one.
        
        Args:
            lot_index: Index of lot to remove
            
        Returns:
            True if removed, False if cannot remove
        """
        lots = self.session_state.get('lots', [])
        
        # Cannot remove if only one lot or invalid index
        if len(lots) <= 1 or lot_index < 0 or lot_index >= len(lots):
            return False
        
        # Clear all data for this lot
        self.clear_lot_data(lot_index)
        
        # Remove the lot
        lots.pop(lot_index)
        
        # Reindex remaining lots
        for i, lot in enumerate(lots):
            lot['index'] = i
            
        self.session_state['lots'] = lots
        
        # Adjust current lot if necessary
        if self.session_state['current_lot_index'] >= len(lots):
            self.session_state['current_lot_index'] = len(lots) - 1
            self.lot_index = self.session_state['current_lot_index']
            
        # Migrate data keys for lots after the removed one
        self._migrate_lot_keys_after_removal(lot_index)
        
        return True
    
    def rename_lot(self, lot_index: int, new_name: str) -> bool:
        """
        Rename a lot.
        
        Args:
            lot_index: Index of lot to rename
            new_name: New name for the lot
            
        Returns:
            True if renamed, False if index invalid
        """
        lots = self.session_state.get('lots', [])
        if 0 <= lot_index < len(lots):
            lots[lot_index]['name'] = new_name
            self.session_state['lots'] = lots
            return True
        return False
    
    def clear_lot_data(self, lot_index: int) -> None:
        """
        Clear all data for a specific lot.
        
        Args:
            lot_index: Index of lot to clear
        """
        prefix = f"lots.{lot_index}."
        keys_to_remove = [k for k in self.session_state.keys() 
                         if k.startswith(prefix)]
        for key in keys_to_remove:
            del self.session_state[key]
    
    def copy_lot_data(self, source_index: int, target_index: int) -> bool:
        """
        Copy all data from one lot to another.
        
        Args:
            source_index: Source lot index
            target_index: Target lot index
            
        Returns:
            True if copied, False if indices invalid
        """
        lots = self.session_state.get('lots', [])
        if (0 <= source_index < len(lots) and 
            0 <= target_index < len(lots) and
            source_index != target_index):
            
            source_prefix = f"lots.{source_index}."
            target_prefix = f"lots.{target_index}."
            
            # Find all source keys and copy to target
            for key in list(self.session_state.keys()):
                if key.startswith(source_prefix):
                    field_name = key[len(source_prefix):]
                    target_key = f"{target_prefix}{field_name}"
                    self.session_state[target_key] = self.session_state[key]
            
            return True
        return False
    
    def _migrate_lot_keys_after_removal(self, removed_index: int) -> None:
        """
        Migrate keys after removing a lot to maintain continuity.
        
        Args:
            removed_index: Index of the removed lot
        """
        # Collect all keys that need migration
        keys_to_migrate = {}
        
        for key in list(self.session_state.keys()):
            if key.startswith("lots."):
                parts = key.split(".", 2)
                if len(parts) >= 3:
                    lot_idx = int(parts[1])
                    if lot_idx > removed_index:
                        # This key needs to be migrated to idx-1
                        new_key = f"lots.{lot_idx - 1}.{parts[2]}"
                        keys_to_migrate[key] = new_key
        
        # Perform migration
        for old_key, new_key in keys_to_migrate.items():
            self.session_state[new_key] = self.session_state[old_key]
            del self.session_state[old_key]
    
    # Validation Methods
    
    def add_validation_error(self, field_name: str, error: str) -> None:
        """
        Add validation error for a field.
        
        Args:
            field_name: Name of the field
            error: Error message
        """
        key = self.get_field_key(field_name)
        if key not in self.validation_errors:
            self.validation_errors[key] = []
        if error not in self.validation_errors[key]:  # Avoid duplicates
            self.validation_errors[key].append(error)
    
    def get_validation_errors(self, field_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get validation errors.
        
        Args:
            field_name: If provided, get errors for specific field only
            
        Returns:
            Dictionary of errors or list of errors for specific field
        """
        if field_name:
            key = self.get_field_key(field_name)
            return self.validation_errors.get(key, [])
        return self.validation_errors
    
    def clear_validation_errors(self, field_name: Optional[str] = None) -> None:
        """
        Clear validation errors.
        
        Args:
            field_name: If provided, clear errors for specific field only
        """
        if field_name:
            key = self.get_field_key(field_name)
            if key in self.validation_errors:
                del self.validation_errors[key]
        else:
            self.validation_errors.clear()
    
    def has_errors(self, field_name: Optional[str] = None) -> bool:
        """
        Check if there are validation errors.
        
        Args:
            field_name: If provided, check specific field only
            
        Returns:
            True if there are errors, False otherwise
        """
        if field_name:
            key = self.get_field_key(field_name)
            return key in self.validation_errors and len(self.validation_errors[key]) > 0
        return len(self.validation_errors) > 0
    
    # Utility Methods
    
    def get_lot_data(self, lot_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all data for a specific lot.
        
        Args:
            lot_index: Lot index (uses current if not provided)
            
        Returns:
            Dictionary with all field values for the lot
        """
        if lot_index is None:
            lot_index = self.lot_index
            
        prefix = f"lots.{lot_index}."
        lot_data = {}
        
        for key, value in self.session_state.items():
            if key.startswith(prefix):
                field_name = key[len(prefix):]
                lot_data[field_name] = value
                
        return lot_data
    
    def get_all_form_data(self) -> Dict[str, Any]:
        """
        Get all form data across all lots in structured format.
        
        Returns:
            Dictionary with all lots and their data
        """
        result = {
            'lots': []
        }
        
        lots = self.session_state.get('lots', [])
        for lot in lots:
            lot_data = self.get_lot_data(lot['index'])
            result['lots'].append({
                'name': lot['name'],
                'index': lot['index'],
                'data': lot_data
            })
            
        # Add global fields
        for field in GLOBAL_FIELDS:
            if field in self.session_state and field != 'lots':
                result[field] = self.session_state[field]
                
        return result