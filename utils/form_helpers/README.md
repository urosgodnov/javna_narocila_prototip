# Form Helpers

## Purpose
This directory contains shared utilities and helper classes that support the unified lot architecture. These are the foundational components used by both renderers and controllers.

## Unified Lot Architecture
The FormContext class is the cornerstone of the unified lot architecture. It ensures that ALL forms have a lot structure in session state, eliminating the need for conditional logic throughout the application.

## Components

### FormContext (`form_context.py`)
- Central state management for all form operations
- Ensures lot structure exists (creates "General" lot if needed)
- Provides lot-scoped key generation
- Manages current lot context
- Handles field value get/set operations

### FormState (`form_state.py`)
- Helper utilities for state manipulation
- State initialization helpers
- State cleanup utilities
- State migration tools (for backward compatibility during transition)

## Usage Example
```python
from utils.form_helpers import FormContext
import streamlit as st

# Initialize context (automatically ensures lot structure)
context = FormContext(st.session_state)

# Always get lot-scoped keys
key = context.get_field_key("field_name")  # Returns: "lots.0.field_name"

# Get/set values (always lot-scoped)
value = context.get_field_value("field_name", default="")
context.set_field_value("field_name", "new value")

# Switch lots
context.switch_to_lot(1)
key = context.get_field_key("field_name")  # Returns: "lots.1.field_name"

# Add new lot
new_lot_index = context.add_lot("Custom Lot Name")

# Get current lot info
current_lot = context.get_current_lot()  # {"name": "Lot 1", "index": 0}
```

## Key Concepts

### Lot Structure in Session State
```python
st.session_state = {
    "lots": [
        {"name": "General", "index": 0},  # Always exists
        {"name": "Lot 2", "index": 1},     # Additional lots
    ],
    "current_lot_index": 0,
    "lots.0.field1": "value1",  # Lot-scoped fields
    "lots.0.field2": "value2",
    "lots.1.field1": "value3",
    "lots.1.field2": "value4",
}
```

### Key Generation Rules
1. Regular fields: `lots.{lot_index}.{field_name}`
2. Nested fields: `lots.{lot_index}.{parent}.{field_name}`
3. Global fields: `{field_name}` (when force_global=True)

### Automatic Lot Creation
If FormContext detects no lot structure, it automatically creates:
```python
{
    "lots": [{"name": "General", "index": 0}],
    "current_lot_index": 0
}
```

## Design Principles
1. **Single Source of Truth**: All state management goes through FormContext
2. **Automatic Structure**: Lot structure created automatically if missing
3. **Consistent Keys**: All keys follow the same pattern
4. **Isolation**: Each lot's data is isolated from others
5. **Testability**: Can be tested with mock session state

## Migration Support
During the transition period, FormState provides utilities to:
- Migrate old flat keys to lot-scoped keys
- Convert existing data to lot structure
- Maintain backward compatibility (temporary)

## Dependencies
- streamlit: For session state access
- typing: For type hints
- json: For data serialization (if needed)