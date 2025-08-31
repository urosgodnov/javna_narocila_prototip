# UI Renderers

## Purpose
This directory contains specialized renderer components that handle the presentation layer of form fields, sections, and lots.

## Unified Lot Architecture
All renderers in this directory assume that EVERY form has lot structure. Forms without explicit lots are treated as having a single "General" lot. This eliminates conditional logic and special cases.

## Components

### FieldRenderer (`field_renderer.py`)
- Renders individual form fields (string, number, boolean, date, etc.)
- Handles field validation and formatting
- Always uses lot-scoped keys through FormContext

### SectionRenderer (`section_renderer.py`)
- Renders complex sections and nested objects
- Manages container layouts and visual grouping
- Handles conditional rendering logic

### LotManager (`lot_manager.py`)
- Manages lot navigation and switching
- Handles lot creation and deletion
- Provides lot-specific UI elements (tabs, navigation buttons)

## Usage Example
```python
from ui.renderers import FieldRenderer, SectionRenderer, LotManager
from utils.form_helpers import FormContext

# All components work with FormContext
context = FormContext(st.session_state)
field_renderer = FieldRenderer(context)
section_renderer = SectionRenderer(context, field_renderer)
lot_manager = LotManager(context)

# Render a field (always lot-scoped)
field_renderer.render_field("field_name", field_schema)

# Render a section
section_renderer.render_section("section_name", section_schema)

# Manage lots
lot_manager.render_lot_navigation()
```

## Design Principles
1. **Separation of Concerns**: Each renderer has a single responsibility
2. **Dependency Injection**: Renderers receive context and dependencies via constructor
3. **No Global State**: All state managed through FormContext
4. **Testability**: Each renderer can be tested in isolation

## Visual Preservation
These renderers maintain the EXACT visual design of the current form_renderer.py:
- Container borders: `st.container(border=True)`
- Column ratios: `[5, 1]` for header/remove buttons
- Icons: 🗑️ (delete), ➕ (add), 📦 (lot), ⬅️/➡️ (navigation)
- Number formatting with dots: 1.000.000,00

## Dependencies
- streamlit: For UI components
- utils.form_helpers.FormContext: For state management
- localization: For text translations