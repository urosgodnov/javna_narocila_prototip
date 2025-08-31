# UI Controllers

## Purpose
This directory contains the orchestration layer that coordinates between renderers, manages form flow, and handles high-level form logic.

## Unified Lot Architecture
The FormController assumes ALL forms have lot structure. It initializes forms with at least one "General" lot if no lots are explicitly defined. This ensures uniform behavior across all form types.

## Components

### FormController (`form_controller.py`)
- Main orchestrator for form rendering
- Coordinates between FieldRenderer, SectionRenderer, and LotManager
- Handles form initialization and submission
- Manages validation flow
- Controls the overall form lifecycle

## Usage Example
```python
from ui.controllers import FormController
import streamlit as st

# Initialize controller (handles all setup internally)
controller = FormController(st.session_state)

# Render entire form with unified lot architecture
controller.render_form(
    schema=form_schema,
    data=existing_data,  # Optional
    validation_mode='strict'  # Optional
)

# Get form data (always lot-structured)
form_data = controller.get_form_data()

# Validate form
is_valid = controller.validate_form()
errors = controller.get_validation_errors()
```

## Architecture Flow
```
FormController
    ├── Initializes FormContext
    ├── Creates renderer instances
    ├── Ensures lot structure exists
    ├── Orchestrates rendering:
    │   ├── LotManager.render_navigation()
    │   ├── For each field/section:
    │   │   ├── Check conditions
    │   │   ├── Call appropriate renderer
    │   │   └── Handle validation
    │   └── LotManager.render_lot_controls()
    └── Collects and returns data
```

## Key Responsibilities
1. **Initialization**: Set up form structure with lots
2. **Orchestration**: Coordinate between different renderers
3. **State Management**: Ensure consistent state through FormContext
4. **Validation**: Coordinate validation across all fields and lots
5. **Data Collection**: Gather form data in structured format

## Design Patterns
- **Facade Pattern**: Provides simple interface to complex rendering system
- **Strategy Pattern**: Different validation strategies can be plugged in
- **Observer Pattern**: Responds to state changes in FormContext

## Configuration
The controller accepts configuration for:
- Validation mode (strict, lenient, custom)
- Layout options (columns, containers, expanders)
- Lot behavior (auto-add, max-lots, lot-naming)

## Dependencies
- ui.renderers: All renderer components
- utils.form_helpers: FormContext and state management
- streamlit: UI framework