# Data Layer Refactoring - Brownfield Enhancement

## Epic Goal

Establish a centralized data layer to handle all data transformations, type conversions, and structure normalization, eliminating the current inconsistencies and repeated code patterns that cause frequent serialization and data handling errors.

## Epic Description

**Existing System Context:**

- Current relevant functionality: Form data handling across core modules (form_renderer.py, schema_utils.py, database.py, app.py)
- Technology stack: Python, Streamlit, SQLite with JSON storage
- Integration points: Session state management, form rendering, database operations, draft saving
- **Out of scope: Admin panel module**

**Enhancement Details:**

- What's being added/changed: Creating a central data management module that handles all data transformations for the main form system
- How it integrates: Becomes the single source of truth for form data operations, called by core modules only
- Success criteria: Zero serialization errors in form operations, consistent data structure across form handling, reduced code duplication by 50%

## Stories

### Story 1: Create Central Data Manager Module
- Create `utils/data_manager.py` with unified data transformation functions
- Implement type conversion handlers (datetime/date/time to string and back)
- Add consistent lot data structure handling (lot_X ↔ lots array conversion)
- **Scope: Form system only, exclude admin panel**

### Story 2: Integrate Data Manager with Core Form Modules
- Replace scattered conversion logic in form_renderer.py with data manager calls
- Update schema_utils.py to use central data transformations
- Modify database.py to use unified serialization (procurement operations only)
- **Exclude: admin_panel.py and its specific data handling**

### Story 3: Add Type Hints and Testing
- Add comprehensive type hints to data manager functions
- Ensure data manager integrates properly with existing `utils/validations.py`
- Create unit tests for all transformation functions
- **Note: Validation logic remains in `utils/validations.py` per project convention**

## Technical Details

### Current Problems Identified

1. **Inconsistent Data Structures**
   - `lot_0.orderType.estimatedValue` (flat session state)
   - `lots[0].orderType.estimatedValue` (nested array in JSON)
   - `general.orderType.estimatedValue` (general mode prefix)
   - No unified conversion pattern

2. **Type Serialization Issues**
   - Streamlit returns datetime/date/time objects
   - JSON requires string representation
   - Conversion logic scattered across multiple files
   - No centralized serialization handler

3. **Code Duplication**
   - Same conversion logic repeated in multiple modules
   - Each module handles its own edge cases
   - No single source of truth for data transformations

### Proposed Solution Architecture

```
utils/data_manager.py
├── Type Conversions
│   ├── datetime_to_string()
│   ├── string_to_datetime()
│   ├── serialize_for_json()
│   └── deserialize_from_json()
└── Structure Transformations
    ├── session_to_nested()  # flat session state → nested JSON
    ├── nested_to_session()  # nested JSON → flat session state
    ├── lots_array_to_fields()
    └── fields_to_lots_array()

utils/validations.py (existing, enhanced)
└── Data Validation (remains here)
    ├── validate_structure()
    ├── ensure_consistency()
    └── [all existing validation logic]
```

## Compatibility Requirements

- [x] Existing APIs remain unchanged
- [x] No database schema changes
- [x] UI changes follow existing patterns
- [x] Performance impact is minimal

## Risk Mitigation

- **Primary Risk:** Breaking existing data flow during refactoring
- **Mitigation:** Implement changes incrementally with feature flags, maintain old code paths initially
- **Rollback Plan:** Feature flag to revert to original data handling, all changes in isolated module

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Existing functionality verified through testing
- [ ] Integration points working correctly
- [ ] Documentation updated appropriately
- [ ] No regression in existing features
- [ ] All datetime serialization errors resolved
- [ ] Lot data handling consistent across all modules
- [ ] Code duplication reduced by at least 50%

## Implementation Notes

### Phase 1: Create Data Manager (Story 1)
1. Create new module without touching existing code
2. Implement all transformations with comprehensive tests
3. Validate against current data structures

### Phase 2: Integration (Story 2)
1. Start with least critical module (form_renderer.py)
2. Add feature flag for gradual rollout
3. Monitor for any data inconsistencies
4. Proceed to schema_utils.py, then database.py

### Phase 3: Type Hints & Testing (Story 3)
1. Add type hints progressively to data_manager.py
2. Create test suite covering all transformation edge cases
3. Verify integration with existing validations.py
4. Document all data transformation patterns

## Files to be Modified

### Core Files (In Scope)
- `utils/data_manager.py` (NEW)
- `ui/form_renderer.py`
- `utils/schema_utils.py`
- `database.py`
- `app.py` (minimal changes)

### Out of Scope
- `ui/admin_panel.py`
- `ui/dashboard.py` (unless critical)
- Any admin-specific modules

## Success Metrics

1. **Zero serialization errors** in production logs
2. **50% reduction** in conversion-related code lines
3. **100% test coverage** for data transformations
4. **Single source of truth** for all data operations
5. **Consistent data structure** across all modules

---

**Story Manager Handoff:**

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing system running Python/Streamlit/SQLite
- Integration points: Session state management, form rendering, database operations, draft saving
- Existing patterns to follow: Current module structure, Streamlit session state patterns
- Critical compatibility requirements: Must maintain backward compatibility with existing stored data
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering centralized, consistent data management that eliminates serialization errors and reduces code duplication."