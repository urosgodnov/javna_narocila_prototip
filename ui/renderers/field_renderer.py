"""
Field renderer for basic form fields.
Preserves EXACT visual output and behavior from current form_renderer.py.
ALL fields are lot-scoped through FormContext.
"""

import streamlit as st
from typing import Any, Optional, List
from datetime import date, datetime
import logging

from utils.form_helpers import FormContext


class FieldRenderer:
    """
    Renders individual form fields with unified lot architecture.
    ALL fields are lot-scoped through FormContext.
    Preserves exact visual design from original form_renderer.
    """
    
    # Financial fields that need special formatting
    FINANCIAL_FIELDS = [
        "estimatedValue", 
        "guaranteedFunds", 
        "availableFunds", 
        "averageSalary"
    ]
    
    def __init__(self, context: FormContext):
        """
        Initialize field renderer.
        
        Args:
            context: FormContext instance for state management
        """
        self.context = context
        
    def render_field(self, 
                    field_name: str, 
                    field_schema: dict,
                    parent_key: str = "",
                    required: bool = False) -> Any:
        """
        Main entry point for field rendering.
        
        Args:
            field_name: Name of the field
            field_schema: JSON schema for the field
            parent_key: Parent key for nested fields
            required: Whether field is required
            
        Returns:
            Field value
        """
        field_type = field_schema.get('type')
        
        if field_type == 'string':
            return self._render_string_field(field_name, field_schema, parent_key, required)
        elif field_type == 'number':
            return self._render_number_field(field_name, field_schema, parent_key, required)
        elif field_type == 'boolean':
            return self._render_boolean_field(field_name, field_schema, parent_key, required)
        elif field_type == 'integer':
            return self._render_integer_field(field_name, field_schema, parent_key, required)
        elif field_type == 'array':
            return self._render_array_field(field_name, field_schema, parent_key, required)
        else:
            # Fallback to string for unknown types
            return self._render_string_field(field_name, field_schema, parent_key, required)
    
    def _get_full_key(self, field_name: str, parent_key: str) -> str:
        """Get full field key including parent path."""
        if parent_key:
            return f"{parent_key}.{field_name}"
        return field_name
    
    def _format_label(self, label: str, required: bool, field_key: str = "") -> str:
        """
        Format field label with required indicator.
        Story 1.2: Support for dynamic required indicators.
        """
        # Check if we have a validation renderer with dynamic requirements
        if hasattr(self.context, 'validation_renderer'):
            renderer = self.context.validation_renderer
            if hasattr(renderer, '_dynamic_required_fields') and field_key:
                dynamic_required = renderer._dynamic_required_fields.get(field_key, required)
                if dynamic_required:
                    return f"{label} *"
        
        if required:
            return f"{label} *"
        return label
    
    def _render_string_field(self, 
                            field_name: str, 
                            schema: dict, 
                            parent_key: str,
                            required: bool) -> Any:
        """Render string field with all its variations."""
        full_key = self._get_full_key(field_name, parent_key)
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        # Get field properties
        label = schema.get('title', field_name)
        help_text = schema.get('description')
        default = schema.get('default', '')
        
        # Initialize session state if needed
        if not self.context.field_exists(full_key):
            self.context.set_field_value(full_key, default)
        
        current_value = self.context.get_field_value(full_key, default)
        
        # Handle different string subtypes
        if schema.get('format') == 'date':
            return self._render_date_picker(
                full_key, label, help_text, required, current_value, schema
            )
        elif schema.get('format') == 'datetime':
            return self._render_datetime_picker(
                full_key, label, help_text, required, current_value
            )
        elif 'enum' in schema:
            return self._render_select_box(
                full_key, label, schema['enum'], help_text, required, current_value
            )
        elif schema.get('format') == 'textarea' or schema.get('widget') == 'textarea':
            return self._render_text_area(
                full_key, label, help_text, required, current_value
            )
        else:
            # Regular text input
            value = st.text_input(
                label=self._format_label(label, required, full_key),
                value=current_value,
                key=widget_key,
                help=help_text
            )
            
            # Update session state
            self.context.set_field_value(full_key, value)
            
            # Add validation error if required and empty
            if required and not value:
                self.context.add_validation_error(full_key, f"{label} is required")
            
            return value
    
    def _render_number_field(self, 
                            field_name: str, 
                            schema: dict, 
                            parent_key: str,
                            required: bool) -> Any:
        """
        Render number field with formatting support.
        Uses text_input for financial fields to support dot-formatted numbers.
        """
        full_key = self._get_full_key(field_name, parent_key)
        session_key = self.context.get_field_key(full_key)
        
        label = schema.get('title', field_name)
        help_text = schema.get('description')
        default = schema.get('default', 0.0)
        minimum = schema.get('minimum')
        maximum = schema.get('maximum')
        
        # Initialize session state if needed
        if not self.context.field_exists(full_key):
            self.context.set_field_value(full_key, float(default))
        
        current_value = self.context.get_field_value(full_key, default)
        
        # Check if this is a financial field
        is_financial = self._is_financial_field(field_name, parent_key)
        
        if is_financial:
            # Use text input with formatting for financial fields
            return self._render_financial_field(
                full_key, label, help_text, required, current_value
            )
        else:
            # Use text input for regular numbers (matching current behavior)
            widget_key = f"widget_{session_key}_text"
            current_str = str(current_value) if current_value != 0.0 else ""
            
            value_str = st.text_input(
                label=self._format_label(label, required, full_key),
                value=current_str,
                key=widget_key,
                help=help_text,
                placeholder="0.00"
            )
            
            # Parse and store number value
            try:
                if value_str and value_str.strip():
                    number_value = float(value_str.replace(',', '.'))
                else:
                    number_value = 0.0
                self.context.set_field_value(full_key, number_value)
                return number_value
            except ValueError:
                st.warning(f"'{value_str}' ni veljavna številka")
                self.context.set_field_value(full_key, 0.0)
                return 0.0
    
    def _render_integer_field(self, 
                             field_name: str, 
                             schema: dict, 
                             parent_key: str,
                             required: bool) -> Any:
        """Render integer field."""
        full_key = self._get_full_key(field_name, parent_key)
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        label = schema.get('title', field_name)
        help_text = schema.get('description')
        default = schema.get('default', 0)
        minimum = schema.get('minimum')
        maximum = schema.get('maximum')
        step = schema.get('step', 1)
        
        # Initialize session state if needed
        if not self.context.field_exists(full_key):
            self.context.set_field_value(full_key, int(default))
        
        current_value = self.context.get_field_value(full_key, default)
        
        value = st.number_input(
            label=self._format_label(label, required, full_key),
            value=int(current_value),
            min_value=minimum,
            max_value=maximum,
            step=step,
            key=widget_key,
            help=help_text
        )
        
        self.context.set_field_value(full_key, value)
        return value
    
    def _render_boolean_field(self, 
                             field_name: str, 
                             schema: dict, 
                             parent_key: str,
                             required: bool) -> Any:
        """Render boolean field as checkbox."""
        full_key = self._get_full_key(field_name, parent_key)
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        label = schema.get('title', field_name)
        help_text = schema.get('description')
        default = schema.get('default', False)
        
        # Initialize session state if needed
        if not self.context.field_exists(full_key):
            self.context.set_field_value(full_key, bool(default))
        
        current_value = self.context.get_field_value(full_key, default)
        
        value = st.checkbox(
            label=label,  # Checkboxes don't show required asterisk
            value=bool(current_value),
            key=widget_key,
            help=help_text
        )
        
        self.context.set_field_value(full_key, value)
        return value
    
    def _render_array_field(self, 
                           field_name: str, 
                           schema: dict, 
                           parent_key: str,
                           required: bool) -> Any:
        """Render array field (multiselect for enums, complex for objects)."""
        full_key = self._get_full_key(field_name, parent_key)
        items_schema = schema.get('items', {})
        
        # Check if it's an array of enums (multiselect)
        if 'enum' in items_schema:
            return self._render_multiselect(
                full_key, 
                schema.get('title', field_name),
                items_schema['enum'],
                schema.get('description'),
                required
            )
        else:
            # Complex array handling will be done by SectionRenderer
            return []
    
    def _render_date_picker(self, 
                           full_key: str, 
                           label: str, 
                           help_text: str, 
                           required: bool,
                           current_value: Any,
                           schema: dict = None) -> date:
        """Render date picker with support for empty/null dates and date range validation."""
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        # Handle null/None values - keep field empty
        if current_value is None or current_value == "null":
            current_value = None
        # Convert current value to date if needed
        elif isinstance(current_value, str):
            try:
                current_value = datetime.strptime(current_value, "%Y-%m-%d").date()
            except:
                # If invalid date string, set to None (empty)
                current_value = None
        elif not isinstance(current_value, date):
            # For any other type, set to None (empty)
            current_value = None
        
        # Determine min/max dates based on field relationships
        min_date = None
        max_date = None
        
        # Check if this is an 'end date' field that should be after a 'start date'
        if 'endDate' in full_key or 'DateTo' in full_key or full_key.endswith('.do'):
            # Find corresponding start date
            start_key = full_key.replace('endDate', 'startDate').replace('DateTo', 'DateFrom').replace('.do', '.od')
            start_value = self.context.get_field_value(start_key)
            if start_value and isinstance(start_value, date):
                min_date = start_value
                if help_text:
                    help_text += f" (mora biti po {start_value.strftime('%d.%m.%Y')})"
                else:
                    help_text = f"Mora biti po {start_value.strftime('%d.%m.%Y')}"
        
        # Check if this is a 'start date' field that should be before an 'end date'
        elif 'startDate' in full_key or 'DateFrom' in full_key or full_key.endswith('.od'):
            # Find corresponding end date
            end_key = full_key.replace('startDate', 'endDate').replace('DateFrom', 'DateTo').replace('.od', '.do')
            end_value = self.context.get_field_value(end_key)
            if end_value and isinstance(end_value, date):
                max_date = end_value
                if help_text:
                    help_text += f" (mora biti pred {end_value.strftime('%d.%m.%Y')})"
                else:
                    help_text = f"Mora biti pred {end_value.strftime('%d.%m.%Y')}"
        
        # Streamlit date_input with None shows empty field
        value = st.date_input(
            label=self._format_label(label, required, full_key),
            value=current_value,
            key=widget_key,
            help=help_text,
            format="DD.MM.YYYY",  # Use dd.mm.yyyy format
            min_value=min_date,
            max_value=max_date
        )
        
        self.context.set_field_value(full_key, value)
        
        # Add validation error if required and empty
        if required and value is None:
            self.context.add_validation_error(full_key, f"{label} je obvezno polje")
        
        return value
    
    def _render_datetime_picker(self, 
                               full_key: str, 
                               label: str, 
                               help_text: str, 
                               required: bool,
                               current_value: Any) -> datetime:
        """Render datetime picker (using date and time inputs)."""
        session_key = self.context.get_field_key(full_key)
        
        col1, col2 = st.columns(2)
        
        with col1:
            date_value = self._render_date_picker(
                f"{full_key}_date", 
                f"{label} (Date)", 
                None, 
                required,
                current_value
            )
        
        with col2:
            time_key = f"widget_{session_key}_time"
            # Handle None/null time values
            if current_value is None:
                time_default = None
            else:
                time_default = current_value.time() if hasattr(current_value, 'time') else None
            
            time_value = st.time_input(
                label="Čas",
                value=time_default,
                key=time_key
            )
        
        # Combine date and time
        datetime_value = datetime.combine(date_value, time_value)
        self.context.set_field_value(full_key, datetime_value)
        return datetime_value
    
    def _render_select_box(self, 
                          full_key: str, 
                          label: str, 
                          options: List[str], 
                          help_text: str, 
                          required: bool,
                          current_value: Any) -> str:
        """Render select box."""
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        # Ensure current value is in options
        if current_value not in options and options:
            current_value = options[0]
        
        index = options.index(current_value) if current_value in options else 0
        
        value = st.selectbox(
            label=self._format_label(label, required, full_key),
            options=options,
            index=index,
            key=widget_key,
            help=help_text
        )
        
        self.context.set_field_value(full_key, value)
        return value
    
    def _render_text_area(self, 
                         full_key: str, 
                         label: str, 
                         help_text: str, 
                         required: bool,
                         current_value: str) -> str:
        """Render text area."""
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        value = st.text_area(
            label=self._format_label(label, required, full_key),
            value=current_value,
            key=widget_key,
            help=help_text
        )
        
        self.context.set_field_value(full_key, value)
        
        if required and not value:
            self.context.add_validation_error(full_key, f"{label} is required")
        
        return value
    
    def _render_multiselect(self, 
                           full_key: str, 
                           label: str, 
                           options: List[str], 
                           help_text: str,
                           required: bool) -> List[str]:
        """Render multiselect for array of enums."""
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}"
        
        current_value = self.context.get_field_value(full_key, [])
        if not isinstance(current_value, list):
            current_value = []
        
        value = st.multiselect(
            label=self._format_label(label, required, full_key),
            options=options,
            default=current_value,
            key=widget_key,
            help=help_text
        )
        
        self.context.set_field_value(full_key, value)
        return value
    
    def _is_financial_field(self, field_name: str, parent_key: str) -> bool:
        """Check if field should use financial formatting."""
        # Check if it's in the financial fields list
        if any(field in field_name for field in self.FINANCIAL_FIELDS):
            return True
        
        # Check if it's a guarantee amount field
        if field_name == "amount" and parent_key:
            guarantee_types = ["fzSeriousness", "fzPerformance", "fzWarranty"]
            if any(g_type in parent_key for g_type in guarantee_types):
                return True
        
        return False
    
    def _render_financial_field(self, 
                               full_key: str, 
                               label: str, 
                               help_text: str, 
                               required: bool,
                               current_value: float) -> float:
        """Render financial field with EUR symbol and dot formatting."""
        session_key = self.context.get_field_key(full_key)
        widget_key = f"widget_{session_key}_formatted"
        
        # Format current value with dots
        formatted_str = self._format_number_with_dots(current_value)
        
        # Create columns for input and EUR symbol
        col_input, col_symbol = st.columns([5, 1])
        
        with col_input:
            value_str = st.text_input(
                label=self._format_label(label, required, full_key),
                value=formatted_str,
                key=widget_key,
                help=help_text or "Format: 1.000.000",
                placeholder="0"
            )
        
        with col_symbol:
            st.markdown(
                "<div style='padding-top: 28px; font-size: 16px; font-weight: 500;'>€</div>",
                unsafe_allow_html=True
            )
        
        # Parse and store unformatted value
        try:
            if value_str and value_str.strip():
                number_value = self._parse_formatted_number(value_str)
            else:
                number_value = 0.0
            self.context.set_field_value(full_key, number_value)
            
            # Debug logging for estimatedValue
            if 'estimatedValue' in full_key:
                logging.info(f"[ESTIMATED_VALUE] {full_key}={number_value}")
            
            return number_value
        except ValueError:
            st.warning(f"'{value_str}' ni veljavna številka")
            self.context.set_field_value(full_key, 0.0)
            return 0.0
    
    def _format_number_with_dots(self, value: float) -> str:
        """Format number with dots as thousand separators."""
        if value is None or value == "":
            return ""
        try:
            num_value = float(value)
            if num_value == int(num_value):
                # No decimals
                return f"{int(num_value):,}".replace(",", ".")
            else:
                # Format with 2 decimals
                formatted = f"{num_value:,.2f}"
                # Replace commas with dots for thousands
                formatted = formatted.replace(",", ".")
                return formatted
        except (ValueError, TypeError):
            return str(value)
    
    def _parse_formatted_number(self, formatted_str: str) -> float:
        """Parse number from formatted string."""
        if not formatted_str or not formatted_str.strip():
            return 0.0
        
        try:
            # Remove spaces
            cleaned = formatted_str.strip().replace(' ', '')
            
            # Detect format (Slovenian vs English)
            if ',' in cleaned and '.' in cleaned:
                # Has both separators
                comma_pos = cleaned.rfind(',')
                dot_pos = cleaned.rfind('.')
                
                if comma_pos > dot_pos:
                    # Slovenian format: 1.000.000,00
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # English format: 1,000,000.00
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Only comma - could be decimal separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Likely decimal: 1000,50
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Likely thousands: 1,000,000
                    cleaned = cleaned.replace(',', '')
            else:
                # No special formatting or only dots
                pass
            
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def render_address_fields(self, prefix: str, schema: dict, parent_key: str = "") -> dict:
        """
        Render address fields with side-by-side layout.
        Story 2.2: Address UI Components and Rendering
        
        Args:
            prefix: Field prefix (e.g., 'singleClient', 'cofinancer')
            schema: Schema containing address field definitions
            parent_key: Parent key for nested fields
            
        Returns:
            Dictionary with address field values
        """
        address_data = {}
        
        # Check if we're using new separated fields or old combined field
        has_new_fields = (f"{prefix}Street" in schema or 
                         f"{prefix}HouseNumber" in schema)
        
        if has_new_fields:
            # Render new separated address fields with side-by-side layout
            
            # Row 1: Street and House Number
            col1, col2 = st.columns([3, 1])
            
            with col1:
                street_key = f"{prefix}Street"
                if street_key in schema:
                    street_schema = schema[street_key]
                    street_value = self._render_string_field(
                        street_key,
                        street_schema,
                        parent_key,
                        street_schema.get('required', False)
                    )
                    address_data[street_key] = street_value
            
            with col2:
                house_key = f"{prefix}HouseNumber"
                if house_key in schema:
                    house_schema = schema[house_key]
                    house_value = self._render_string_field(
                        house_key,
                        house_schema,
                        parent_key,
                        house_schema.get('required', False)
                    )
                    address_data[house_key] = house_value
            
            # Row 2: Postal Code and City
            col3, col4 = st.columns([1, 3])
            
            with col3:
                postal_key = f"{prefix}PostalCode"
                if postal_key in schema:
                    postal_schema = schema[postal_key]
                    postal_value = self._render_string_field(
                        postal_key,
                        postal_schema,
                        parent_key,
                        postal_schema.get('required', False)
                    )
                    address_data[postal_key] = postal_value
            
            with col4:
                city_key = f"{prefix}City"
                if city_key in schema:
                    city_schema = schema[city_key]
                    city_value = self._render_string_field(
                        city_key,
                        city_schema,
                        parent_key,
                        city_schema.get('required', False)
                    )
                    address_data[city_key] = city_value
        
        else:
            # Fall back to old combined field rendering
            street_address_key = f"{prefix}StreetAddress"
            if street_address_key in schema:
                street_address_schema = schema[street_address_key]
                street_address_value = self._render_string_field(
                    street_address_key,
                    street_address_schema,
                    parent_key,
                    street_address_schema.get('required', False)
                )
                address_data[street_address_key] = street_address_value
            
            # Old postal code field (combined with city)
            postal_key = f"{prefix}PostalCode"
            if postal_key in schema:
                postal_schema = schema[postal_key]
                postal_value = self._render_string_field(
                    postal_key,
                    postal_schema,
                    parent_key,
                    postal_schema.get('required', False)
                )
                address_data[postal_key] = postal_value
        
        return address_data
    
    def is_mobile(self) -> bool:
        """
        Check if the user is on a mobile device.
        Returns True if the viewport width suggests mobile.
        """
        # This is a simplified check - in production you might use JavaScript
        # to get actual viewport width
        # For now, we'll assume desktop
        return False