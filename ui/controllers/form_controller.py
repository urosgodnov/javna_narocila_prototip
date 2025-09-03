"""
Main form controller for orchestrating form rendering.
Coordinates all components with unified lot architecture.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from utils.form_helpers import FormContext
from ui.renderers.field_renderer import FieldRenderer
from ui.renderers.section_renderer import SectionRenderer
from ui.renderers.lot_manager import LotManager
from ui.renderers.validation_renderer import ValidationRenderer
from utils.validations import ValidationManager
from utils.validation_adapter import ValidationAdapter


class FormController:
    """
    Orchestrates form rendering with unified lot architecture.
    Ensures ALL forms have lot structure.
    This is the main entry point for rendering forms.
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize form controller with guaranteed lot structure.
        
        Args:
            schema: Optional JSON schema for the form
        """
        # Create context with lot structure (automatically creates General lot)
        self.context = FormContext(st.session_state)
        
        # Initialize validation renderer first
        self.validation_renderer = ValidationRenderer(self.context)
        # Pass validation renderer to field renderer for dynamic requirements
        self.field_renderer = FieldRenderer(self.context, self.validation_renderer)
        
        # Check for existing validation errors from previous validation attempts
        self._check_existing_validation_errors()
        self.section_renderer = SectionRenderer(self.context, self.field_renderer)
        self.lot_manager = LotManager(self.context)
        
        # Store schema (can be set later with set_schema)
        self.schema = schema or {}
        
        # Create validation manager and apply unified lot adapter
        self.validation_manager = ValidationManager(self.schema, st.session_state)
        ValidationAdapter.update_validation_manager_for_unified_lots(self.validation_manager)
        
        # Initialize form metadata
        self._initialize_form_metadata()
    
    def _initialize_form_metadata(self) -> None:
        """Initialize form metadata in session state."""
        if 'form_metadata' not in st.session_state:
            st.session_state['form_metadata'] = {
                'form_id': None,
                'version': '1.0',
                'created_at': None,
                'last_modified': None,
                'validation_mode': 'standard',
                'submission_count': 0,
                'is_dirty': False
            }
    
    def _check_existing_validation_errors(self) -> None:
        """Check for existing validation errors from previous attempts and mark fields."""
        # Check if there are stored validation errors from a previous validation attempt
        if 'last_validation_errors' in st.session_state:
            errors = st.session_state.get('last_validation_errors', [])
            if errors:
                # Extract field names from error messages and mark them
                for error in errors:
                    # Try to identify which fields have errors
                    if "Zakoniti zastopnik" in error or "singleClientLegalRepresentative" in error:
                        self._mark_field_with_error('clientInfo.singleClientLegalRepresentative')
                        self._mark_field_with_error('singleClientLegalRepresentative')
                    
                    # Check for other common required fields
                    field_mappings = {
                        'Poštna številka': ['clientInfo.singleClientPostalCode', 'singleClientPostalCode'],
                        'Kraj': ['clientInfo.singleClientCity', 'singleClientCity'],
                        'Ulica': ['clientInfo.singleClientStreet', 'singleClientStreet'],
                        'Hišna številka': ['clientInfo.singleClientHouseNumber', 'singleClientHouseNumber'],
                        'Naziv': ['clientInfo.singleClientName', 'singleClientName'],
                        'CPV': ['projectInfo.cpvCodes', 'cpvCodes']
                    }
                    
                    for field_label, field_keys in field_mappings.items():
                        if field_label in error:
                            for field_key in field_keys:
                                self._mark_field_with_error(field_key)
    
    def _mark_field_with_error(self, field_key: str) -> None:
        """Mark a field as having a validation error."""
        # Add error to context so field renderer knows to show red border
        self.context.add_validation_error(field_key, 'Validation error')
        # Also use validation renderer to add styling
        self.validation_renderer.add_field_error_style(field_key)
    
    def set_schema(self, schema: Dict[str, Any]) -> None:
        """
        Set or update the form schema.
        
        Args:
            schema: JSON schema for the form
        """
        self.schema = schema
        # Update validation manager with new schema and apply adapter
        self.validation_manager = ValidationManager(schema, st.session_state)
        ValidationAdapter.update_validation_manager_for_unified_lots(self.validation_manager)
        # DO NOT overwrite the global schema in session state!
        # This is just a local schema for this form controller instance
        # st.session_state['schema'] = schema  # REMOVED - was overwriting global schema
    
    def render_form(self, 
                   schema: Optional[Dict[str, Any]] = None,
                   show_lot_navigation: bool = True,
                   lot_navigation_style: str = 'tabs',
                   show_progress: bool = False,
                   show_validation_summary: bool = True,
                   custom_css: Optional[str] = None) -> None:
        """
        Render complete form with unified lot architecture.
        
        Args:
            schema: Optional schema (uses stored schema if not provided)
            show_lot_navigation: Whether to show lot navigation UI
            lot_navigation_style: Style for lot navigation ('tabs', 'buttons', 'select')
            show_progress: Whether to show form completion progress
            show_validation_summary: Whether to show validation summary
            custom_css: Optional custom CSS for styling
        """
        # Use provided schema or stored schema
        if schema:
            self.set_schema(schema)
        
        if not self.schema:
            st.warning("No form schema provided. Please set a schema first.")
            return
        
        # Apply custom CSS if provided
        if custom_css:
            st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
        
        # Render lot navigation if enabled and multiple lots exist
        if show_lot_navigation and self.context.get_lot_count() > 1:
            self.lot_manager.render_lot_navigation(
                style=lot_navigation_style,
                allow_add=self.schema.get('allow_multiple_lots', True),
                allow_remove=self.schema.get('allow_lot_removal', True),
                max_lots=self.schema.get('max_lots')
            )
            st.divider()
        
        # Show progress if enabled
        if show_progress:
            self._render_progress()
        
        # Update dynamic requirements based on current form data
        form_data = self.get_form_data()
        self.validation_renderer.update_dynamic_requirements(form_data)
        
        # Get schema properties based on type
        if self.schema.get('type') == 'object':
            # Direct object schema
            self._render_object_form(self.schema)
        elif 'properties' in self.schema:
            # Schema with top-level properties
            self._render_properties_form(self.schema)
        elif 'steps' in self.schema:
            # Multi-step form
            self._render_stepped_form(self.schema)
        else:
            st.error("Invalid schema format. Schema must have 'properties' or 'steps'.")
        
        # Show validation summary if enabled
        if show_validation_summary and self.context.has_errors():
            self._render_validation_summary()
    
    def _render_object_form(self, schema: Dict[str, Any]) -> None:
        """Render form from object schema."""
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        # Group properties by section if defined
        sections = schema.get('sections', {})
        
        if sections:
            # Render by sections
            for section_name, section_config in sections.items():
                self._render_section(section_name, section_config, properties, required_fields)
        else:
            # Render all properties directly
            self._render_properties(properties, required_fields)
    
    def _render_properties_form(self, schema: Dict[str, Any]) -> None:
        """Render form with top-level properties."""
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        # Check for UI hints
        ui_schema = schema.get('ui:schema', {})
        order = ui_schema.get('ui:order', list(properties.keys()))
        
        # Render in specified order
        for prop_name in order:
            if prop_name in properties:
                prop_schema = properties[prop_name]
                self._render_property(prop_name, prop_schema, required_fields)
    
    def _render_stepped_form(self, schema: Dict[str, Any]) -> None:
        """Render multi-step form."""
        steps = schema.get('steps', [])
        
        # Get current step
        if 'current_step_index' not in st.session_state:
            st.session_state['current_step_index'] = 0
        
        current_step_index = st.session_state['current_step_index']
        
        if current_step_index >= len(steps):
            current_step_index = 0
            st.session_state['current_step_index'] = 0
        
        # Render step navigation
        self._render_step_navigation(steps, current_step_index)
        
        # Render current step
        current_step = steps[current_step_index]
        st.subheader(current_step.get('title', f'Step {current_step_index + 1}'))
        
        if current_step.get('description'):
            st.caption(current_step['description'])
        
        # Render step properties
        step_properties = current_step.get('properties', {})
        step_required = current_step.get('required', [])
        self._render_properties(step_properties, step_required)
        
        # Step navigation buttons
        self._render_step_buttons(steps, current_step_index)
    
    def _render_step_navigation(self, steps: List[Dict], current_index: int) -> None:
        """Render step progress indicator."""
        progress_cols = st.columns(len(steps))
        
        for idx, (step, col) in enumerate(zip(steps, progress_cols)):
            with col:
                if idx < current_index:
                    st.success(f"✅ {step.get('title', f'Step {idx + 1}')}")
                elif idx == current_index:
                    st.info(f"👉 {step.get('title', f'Step {idx + 1}')}")
                else:
                    st.text(f"⏳ {step.get('title', f'Step {idx + 1}')}")
    
    def _render_step_buttons(self, steps: List[Dict], current_index: int) -> None:
        """Render navigation buttons for steps."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if current_index > 0:
                if st.button("⬅️ Previous", key="prev_step"):
                    st.session_state['current_step_index'] = current_index - 1
                    st.rerun()
        
        with col3:
            if current_index < len(steps) - 1:
                if st.button("Next ➡️", key="next_step"):
                    # Validate current step before proceeding
                    if self._validate_current_step(steps[current_index]):
                        st.session_state['current_step_index'] = current_index + 1
                        st.rerun()
                    # If validation failed, errors are already displayed by _validate_current_step
            else:
                if st.button("✅ Submit", key="submit_form", type="primary"):
                    if self.validate_form():
                        self._handle_submission()
    
    def _render_section(self, 
                       section_name: str, 
                       section_config: Dict,
                       all_properties: Dict,
                       all_required: List) -> None:
        """Render a section of properties."""
        # Get section properties
        section_props = section_config.get('properties', [])
        
        # Create section UI
        with st.container():
            if section_config.get('title'):
                st.subheader(section_config['title'])
            
            if section_config.get('description'):
                st.caption(section_config['description'])
            
            # Render each property in the section
            for prop_name in section_props:
                if prop_name in all_properties:
                    prop_schema = all_properties[prop_name]
                    self._render_property(prop_name, prop_schema, all_required)
    
    def _render_properties(self, properties: Dict, required_fields: List) -> None:
        """Render a set of properties."""
        for prop_name, prop_schema in properties.items():
            self._render_property(prop_name, prop_schema, required_fields)
    
    def _render_property(self, 
                        prop_name: str, 
                        prop_schema: Dict,
                        required_fields: List) -> None:
        """Render a single property using appropriate renderer."""
        prop_type = prop_schema.get('type')
        is_required = prop_name in required_fields
        
        # Check if property should be rendered (conditional rendering)
        if not self._should_render_property(prop_schema):
            return
        
        if prop_type == 'object':
            # Use section renderer for objects
            # Pass required fields from the object's schema
            object_required = prop_schema.get('required', [])
            self.section_renderer.render_section(
                prop_name, prop_schema, parent_key="", level=0, required_fields=object_required
            )
        elif prop_type == 'array' and prop_schema.get('items', {}).get('type') == 'object':
            # Use section renderer for arrays of objects
            # Arrays of objects might have required fields in items schema
            items_required = prop_schema.get('items', {}).get('required', [])
            self.section_renderer.render_section(
                prop_name, prop_schema, parent_key="", level=0, required_fields=items_required
            )
        else:
            # Use field renderer for simple fields
            self.field_renderer.render_field(
                prop_name, prop_schema, parent_key="", required=is_required
            )
    
    def _should_render_property(self, prop_schema: Dict) -> bool:
        """Check if property should be rendered based on conditions."""
        # This duplicates logic from SectionRenderer but needed at top level
        if 'render_if' in prop_schema:
            condition = prop_schema['render_if']
            if not self._check_condition(condition):
                return False
        
        if 'render_if_any' in prop_schema:
            conditions = prop_schema['render_if_any']
            if not any(self._check_condition(c) for c in conditions):
                return False
        
        if 'render_if_all' in prop_schema:
            conditions = prop_schema['render_if_all']
            if not all(self._check_condition(c) for c in conditions):
                return False
        
        return True
    
    def _check_condition(self, condition: Dict) -> bool:
        """Check a render condition."""
        field = condition.get('field')
        expected_value = condition.get('value')
        
        if not field:
            return True
        
        actual_value = self.context.get_field_value(field)
        return actual_value == expected_value
    
    def _render_progress(self) -> None:
        """Render form completion progress."""
        total_fields = self._count_total_fields()
        completed_fields = self._count_completed_fields()
        
        if total_fields > 0:
            progress = completed_fields / total_fields
            st.progress(progress, text=f"Form completion: {completed_fields}/{total_fields} fields")
    
    def _render_validation_summary(self) -> None:
        """Render validation error summary."""
        errors = self.context.validation_errors
        
        if errors:
            with st.expander("⚠️ Validation Issues", expanded=True):
                for field_key, field_errors in errors.items():
                    for error in field_errors:
                        st.error(f"• {error}")
    
    def _count_total_fields(self) -> int:
        """Count total number of fields in the form."""
        # Simplified count - would need recursive counting for nested structures
        if 'properties' in self.schema:
            return len(self.schema['properties'])
        return 0
    
    def _count_completed_fields(self) -> int:
        """Count number of completed fields."""
        count = 0
        if 'properties' in self.schema:
            for prop_name in self.schema['properties']:
                if self.context.field_exists(prop_name):
                    value = self.context.get_field_value(prop_name)
                    if value not in [None, "", [], {}]:
                        count += 1
        return count
    
    def _validate_current_step(self, step: Dict) -> bool:
        """Validate fields in the current step using enhanced validation."""
        # Get current step name and properties
        step_name = step.get('name', '')
        step_properties = step.get('properties', {})
        step_keys = list(step_properties.keys())
        
        # Clear previous validation errors
        self.validation_renderer.clear_field_errors()
        
        # Get form data and determine required fields
        form_data = self.get_form_data()
        required_fields = self.validation_renderer.get_required_fields_for_step(
            step_name, form_data
        )
        
        # Validate with enhanced visual display
        step_data = form_data.get(step_name, {})
        is_valid, visual_errors = self.validation_renderer.validate_and_display_errors(
            step_data, required_fields
        )
        
        # Also run original ValidationManager validation
        current_step_index = st.session_state.get('current_step', 0)
        manager_valid, manager_errors = self.validation_manager.validate_step(
            step_keys,
            current_step_index
        )
        
        # Combine results
        all_valid = is_valid and manager_valid
        all_errors = visual_errors + (manager_errors if manager_errors else [])
        
        # Display validation summary if there are errors
        if not all_valid and all_errors:
            self.validation_renderer.display_validation_summary(all_errors)
        
        return all_valid
    
    def validate_form(self) -> bool:
        """
        Validate entire form using ValidationManager.
        
        Returns:
            True if valid, False otherwise
        """
        # Clear previous validation errors
        self.context.clear_validation_errors()
        all_valid = True
        all_errors = []
        
        # Validate all steps/screens using ValidationManager
        # Get all form fields from schema
        if self.schema and 'properties' in self.schema:
            all_keys = list(self.schema['properties'].keys())
            
            # Use ValidationManager's validate_step for comprehensive validation
            is_valid, errors = self.validation_manager.validate_step(all_keys)
            
            if not is_valid:
                all_valid = False
                all_errors.extend(errors)
        
        # Add errors to context
        for error in all_errors:
            self.context.add_validation_error('form', error)
        
        return all_valid
    
    def get_form_data(self) -> Dict[str, Any]:
        """
        Get all form data in structured format.
        
        Returns:
            Dictionary with lot-structured data
        """
        return self.context.get_all_form_data()
    
    def clear_form(self) -> None:
        """Clear all form data while preserving lot structure."""
        # Clear data for all lots
        for lot in self.context.get_all_lots():
            self.context.clear_lot_data(lot['index'])
        
        # Reset validation errors
        self.context.clear_validation_errors()
        
        # Reset step index if using stepped form
        if 'current_step_index' in st.session_state:
            st.session_state['current_step_index'] = 0
    
    def _handle_submission(self) -> None:
        """Handle form submission."""
        # Get all form data
        form_data = self.get_form_data()
        
        # Update metadata
        import datetime
        st.session_state['form_metadata']['last_modified'] = datetime.datetime.now().isoformat()
        st.session_state['form_metadata']['submission_count'] += 1
        
        # Show success message
        st.success("✅ Form submitted successfully!")
        
        # Display submitted data (for debugging)
        with st.expander("Submitted Data", expanded=False):
            st.json(form_data)
        
        # Here you would typically:
        # 1. Send data to backend API
        # 2. Save to database
        # 3. Trigger workflows
        # 4. Send notifications
        
        # Optional: Clear form after submission
        if self.schema.get('clear_after_submit', False):
            self.clear_form()
            st.rerun()
    
    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Load existing data into the form.
        
        Args:
            data: Dictionary with form data (can be lot-structured or flat)
        """
        if 'lots' in data:
            # Lot-structured data
            for lot_data in data['lots']:
                lot_index = lot_data.get('index', 0)
                
                # Ensure lot exists
                while self.context.get_lot_count() <= lot_index:
                    self.context.add_lot()
                
                # Switch to lot and load data
                self.context.switch_to_lot(lot_index)
                
                for field_name, value in lot_data.get('data', {}).items():
                    self.context.set_field_value(field_name, value)
        else:
            # Flat data - load into current lot
            for field_name, value in data.items():
                if field_name not in ['schema', 'form_metadata']:
                    self.context.set_field_value(field_name, value)