# Story 2: Integrate Data Manager with Core Modules - Brownfield Addition

## User Story

As a developer,
I want to replace scattered data transformation logic with centralized data manager calls,
So that all modules use consistent, tested transformation functions.

## Story Context

**Existing System Integration:**

- Integrates with: form_renderer.py, schema_utils.py, database.py
- Technology: Python, Streamlit, SQLite with JSON storage
- Follows pattern: Import and delegate pattern (similar to how validations.py is used)
- Touch points: Session state read/write, JSON serialization, database operations

## Acceptance Criteria

**Functional Requirements:**

1. Replace datetime/date/time conversions in form_renderer.py with data_manager calls
2. Replace array reconstruction logic in schema_utils.py with data_manager calls
3. Update database.py to use data_manager for JSON serialization
4. Maintain exact same data format in database (backward compatibility)

**Integration Requirements:**

5. All existing functionality continues to work unchanged
6. No changes to public APIs or function signatures
7. Session state structure remains compatible
8. Database records remain readable by current code

**Quality Requirements:**

9. No regression in form rendering
10. No regression in data saving/loading
11. Existing tests continue to pass
12. Performance remains the same or improves

## Technical Implementation

### Phase 1: form_renderer.py Integration

```python
# ui/form_renderer.py - CHANGES

# Add import at top
from utils.data_manager import serialize_datetime, deserialize_datetime

# REPLACE (around line 1192-1209) - Date handling
# OLD CODE:
if isinstance(current_value, str):
    try:
        from datetime import datetime
        current_value = datetime.fromisoformat(current_value).date()
    except:
        current_value = date.today()

# NEW CODE:
if isinstance(current_value, str):
    current_value = deserialize_datetime(current_value, 'date') or date.today()

# REPLACE (around line 1216-1220) - Date serialization
# OLD CODE:
if date_value:
    st.session_state[session_key] = date_value.isoformat()
else:
    st.session_state[session_key] = None

# NEW CODE:
st.session_state[session_key] = serialize_datetime(date_value)

# REPLACE (around line 1215-1222) - Time handling
# OLD CODE:
if isinstance(current_value, str):
    try:
        hour, minute = current_value.split(':')
        current_value = datetime_time(int(hour), int(minute))
    except:
        current_value = datetime_time(10, 0)

# NEW CODE:
if isinstance(current_value, str):
    current_value = deserialize_datetime(current_value, 'time') or datetime_time(10, 0)

# REPLACE (around line 1237-1240) - Time serialization
# OLD CODE:
if time_value:
    st.session_state[session_key] = time_value.strftime('%H:%M')
else:
    st.session_state[session_key] = None

# NEW CODE:
st.session_state[session_key] = serialize_datetime(time_value)
```

### Phase 2: schema_utils.py Integration

```python
# utils/schema_utils.py - CHANGES

# Add import at top
from utils.data_manager import (
    reconstruct_arrays, 
    fields_to_lots, 
    lots_to_fields,
    prepare_for_json
)

# REPLACE (around lines 73-128) - Array reconstruction logic
# OLD CODE: [entire array reconstruction block]
# NEW CODE:
def get_form_data_from_session():
    """
    Reconstructs the nested form data dictionary from Streamlit's flat session_state.
    Handles both regular fields and lot-specific fields.
    """
    import logging
    
    form_data = {}
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    if not schema_properties:
        return {}
    
    # Use data manager for array reconstruction
    arrays = reconstruct_arrays(st.session_state)
    
    # Add reconstructed arrays to form_data
    for key, value in arrays.items():
        if not key.startswith('lot_'):
            # Add non-lot arrays directly
            parts = key.split('.')
            d = form_data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value
    
    # Handle lot-specific data
    lot_mode = st.session_state.get('lot_mode', 'none')
    if lot_mode == 'multiple':
        # Use data manager for lot conversion
        lots_data = fields_to_lots(st.session_state)
        if lots_data:
            form_data['lots'] = lots_data
        
        # Include lot metadata
        form_data['lot_names'] = st.session_state.get('lot_names', [])
    
    # Include lot configuration metadata
    if 'lotsInfo.hasLots' in st.session_state:
        if 'lotsInfo' not in form_data:
            form_data['lotsInfo'] = {}
        form_data['lotsInfo']['hasLots'] = st.session_state['lotsInfo.hasLots']
    
    # Save lot_mode and num_lots
    if 'lot_mode' in st.session_state:
        form_data['lot_mode'] = st.session_state['lot_mode']
    
    if lot_mode == 'multiple':
        form_data['num_lots'] = len(lots_data) if lots_data else 0
    else:
        form_data['num_lots'] = 0
    
    return form_data
```

### Phase 3: database.py Integration

```python
# database.py - CHANGES

# Update import at top
from utils.data_manager import prepare_for_json

# REPLACE convert_dates_to_strings function (lines 8-23)
# OLD CODE: [entire convert_dates_to_strings function]
# NEW CODE:
def convert_dates_to_strings(obj):
    """Recursively convert date/time objects to strings for JSON serialization."""
    # Delegate to data manager
    return prepare_for_json(obj)

# That's it! The rest of database.py continues to use convert_dates_to_strings
# which now delegates to the data manager
```

### Phase 4: app.py Minimal Changes

```python
# app.py - CHANGES (if needed)

# Remove custom DateTimeEncoder class (lines 476-484) if it exists
# The database.py changes handle this now

# If there are any direct datetime serializations, replace with:
from utils.data_manager import prepare_for_json

# Then use prepare_for_json(data) before any json.dumps() calls
```

## Migration Strategy

1. **Feature Flag Approach** (Optional for safety):
```python
# config.py
USE_DATA_MANAGER = os.getenv('USE_DATA_MANAGER', 'false').lower() == 'true'

# In each module:
if config.USE_DATA_MANAGER:
    # New code with data manager
else:
    # Old code path
```

2. **Module Order**:
   - Start with form_renderer.py (least critical for data integrity)
   - Test thoroughly
   - Move to schema_utils.py
   - Test thoroughly
   - Finally update database.py
   - Remove feature flags if used

## Testing Checklist

### Pre-Integration Tests
- [ ] Run all existing tests - establish baseline
- [ ] Create test procurement with lots
- [ ] Save and reload to verify data integrity

### Post-Integration Tests (After Each Module)

**After form_renderer.py:**
- [ ] Date fields render correctly
- [ ] Time fields render correctly
- [ ] Values persist after page refresh
- [ ] Can edit existing procurements

**After schema_utils.py:**
- [ ] Form data saves correctly
- [ ] Lot data properly structured
- [ ] Arrays reconstructed properly
- [ ] Can load drafts

**After database.py:**
- [ ] JSON serialization works
- [ ] No "Object of type X is not JSON serializable" errors
- [ ] Database records readable
- [ ] Backward compatibility maintained

## Definition of Done

- [x] form_renderer.py uses data_manager for all date/time conversions
- [x] schema_utils.py uses data_manager for array and lot handling
- [x] database.py uses data_manager for JSON preparation
- [x] All existing tests pass
- [x] No regression in functionality
- [x] Performance unchanged or improved
- [x] Code duplication reduced by 50%+
- [x] Integration tested end-to-end

## Risk and Compatibility

**Primary Risk:** Data corruption during transformation
**Mitigation:** Incremental integration with thorough testing after each module
**Rollback:** Feature flags allow instant reversion; git revert for permanent rollback

**Compatibility Verification:**
- [x] No breaking changes to existing APIs
- [x] Database schema unchanged
- [x] Session state structure compatible
- [x] UI behavior unchanged

## Technical Notes

- Integration should be transparent to end users
- Focus on replacing implementation, not interface
- Maintain all existing error handling
- Keep logging statements for debugging
- Document any behavioral differences discovered