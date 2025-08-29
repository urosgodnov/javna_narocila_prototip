# utils/data_manager.py
"""
Centralized data transformation module for handling all data conversions.
Provides consistent, testable transformations between different data formats.
"""

from datetime import datetime, date, time
from typing import Any, Dict, List, Optional, Union, Tuple
import json

# ============= Type Conversions =============

def serialize_datetime(obj: Union[datetime, date, time, None]) -> Optional[str]:
    """Convert datetime/date/time objects to JSON-serializable strings."""
    if obj is None:
        return None
    # Check datetime before date since datetime is a subclass of date
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    else:  # isinstance(obj, time)
        return obj.strftime('%H:%M:%S')

def deserialize_datetime(value: str, target_type: str) -> Union[datetime, date, time, None]:
    """Convert string back to datetime/date/time objects."""
    if not value:
        return None
    
    try:
        if target_type == 'datetime':
            return datetime.fromisoformat(value)
        elif target_type == 'date':
            # Handle both date-only and datetime strings
            if 'T' in value:
                return datetime.fromisoformat(value).date()
            else:
                return date.fromisoformat(value)
        elif target_type == 'time':
            # Handle both HH:MM:SS and HH:MM formats
            parts = value.split(':')
            if len(parts) == 2:
                return time(int(parts[0]), int(parts[1]))
            elif len(parts) == 3:
                return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError):
        return None
    return None

def prepare_for_json(data: Any) -> Any:
    """Recursively convert all non-JSON-serializable objects in a data structure."""
    if isinstance(data, dict):
        return {key: prepare_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [prepare_for_json(item) for item in data]
    elif isinstance(data, (datetime, date, time)):
        return serialize_datetime(data)
    else:
        return data

# ============= Structure Transformations =============

def flatten_nested_dict(nested: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Convert nested dictionary to flat dictionary with dot notation.
    Example: {'a': {'b': 1}} -> {'a.b': 1}
    """
    items: List[Tuple[str, Any]] = []
    for key, value in nested.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict) and value:  # Non-empty dict
            items.extend(flatten_nested_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

def unflatten_dict(flat: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Convert flat dictionary with dot notation to nested dictionary.
    Example: {'a.b': 1} -> {'a': {'b': 1}}
    """
    nested: Dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(sep)
        d = nested
        for part in parts[:-1]:
            # Only use setdefault if d is a dict
            if not isinstance(d, dict):
                # Cannot navigate further - skip this key
                break
            d = d.setdefault(part, {})
        else:
            # Only set value if we successfully navigated
            if isinstance(d, dict):
                d[parts[-1]] = value
    return nested

def lots_to_fields(lots_array: List[Dict[str, Any]], prefix: str = 'lot') -> Dict[str, Any]:
    """
    Convert lots array to individual lot fields.
    Example: [{'name': 'Lot1', 'value': 100}] -> {'lot_0.name': 'Lot1', 'lot_0.value': 100}
    """
    result = {}
    for i, lot in enumerate(lots_array):
        if isinstance(lot, dict):
            flat_lot = flatten_nested_dict(lot)
            for key, value in flat_lot.items():
                result[f"{prefix}_{i}.{key}"] = value
    return result

def fields_to_lots(session_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract lot fields from session state and convert to lots array.
    Example: {'lot_0.name': 'Lot1', 'lot_0.value': 100} -> [{'name': 'Lot1', 'value': 100}]
    Only includes contiguous lots starting from lot_0.
    """
    lots_data: Dict[int, Dict[str, Any]] = {}
    
    for key, value in session_state.items():
        if key.startswith('lot_') and '.' in key:
            # Parse lot_X.field pattern
            parts = key.split('.', 1)
            lot_part = parts[0]  # e.g., 'lot_0'
            field_path = parts[1]  # e.g., 'orderType.estimatedValue'
            
            if '_' in lot_part:
                lot_idx_str = lot_part.split('_')[1]
                if lot_idx_str.isdigit():
                    lot_idx = int(lot_idx_str)
                    if lot_idx not in lots_data:
                        lots_data[lot_idx] = {}
                    
                    # Handle nested field paths
                    field_parts = field_path.split('.')
                    d = lots_data[lot_idx]
                    navigation_failed = False
                    
                    for part in field_parts[:-1]:
                        # Only use setdefault if d is a dict
                        if not isinstance(d, dict):
                            navigation_failed = True
                            break
                        d = d.setdefault(part, {})
                    
                    # Only set value if we successfully navigated
                    if not navigation_failed and isinstance(d, dict):
                        d[field_parts[-1]] = value
    
    # Convert to sorted list, only including contiguous lots from 0
    if lots_data:
        # Find the highest contiguous index starting from 0
        max_contiguous = -1
        for i in range(100):  # Reasonable upper limit
            if i in lots_data:
                max_contiguous = i
            else:
                break
        
        # Return only contiguous lots
        if max_contiguous >= 0:
            return [lots_data.get(i, {}) for i in range(max_contiguous + 1)]
    return []

# ============= Array Reconstruction =============

def reconstruct_arrays(session_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconstruct arrays from individual indexed fields.
    Example: {'field.0.name': 'A', 'field.1.name': 'B'} -> {'field': [{'name': 'A'}, {'name': 'B'}]}
    """
    arrays: Dict[str, Dict[int, Any]] = {}
    processed_keys = set()
    
    for key, value in session_state.items():
        # Skip widget keys
        if key.startswith('widget_'):
            continue
            
        if any(part.isdigit() for part in key.split('.')):
            parts = key.split('.')
            for i, part in enumerate(parts):
                if part.isdigit():
                    array_key = '.'.join(parts[:i])
                    index = int(part)
                    field_path = '.'.join(parts[i+1:]) if i+1 < len(parts) else None
                    
                    if array_key not in arrays:
                        arrays[array_key] = {}
                    if index not in arrays[array_key]:
                        arrays[array_key][index] = {}
                    
                    if field_path:
                        # Navigate nested structure
                        d = arrays[array_key][index]
                        field_parts = field_path.split('.')
                        navigation_failed = False
                        
                        for fp in field_parts[:-1]:
                            # Only use setdefault if d is a dict
                            if not isinstance(d, dict):
                                navigation_failed = True
                                break
                            d = d.setdefault(fp, {})
                        
                        # Only set value if we successfully navigated
                        if not navigation_failed and isinstance(d, dict):
                            d[field_parts[-1]] = value
                    else:
                        arrays[array_key][index] = value
                    
                    processed_keys.add(key)
                    break
    
    # Convert to proper arrays
    result = {}
    for array_key, indices_dict in arrays.items():
        max_index = max(indices_dict.keys()) if indices_dict else -1
        array_list = [indices_dict.get(i, {}) for i in range(max_index + 1)]
        result[array_key] = array_list
    
    # Add non-array fields
    for key, value in session_state.items():
        if key not in processed_keys and not key.startswith('widget_'):
            result[key] = value
    
    return result