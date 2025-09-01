"""
Section renderer for complex form sections.
Handles nested objects, arrays of objects, and conditional rendering.
Preserves EXACT visual design from current form_renderer.py.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from utils.form_helpers import FormContext
from .field_renderer import FieldRenderer


class SectionRenderer:
    """
    Renders complex sections and nested objects.
    Works with unified lot architecture - ALL sections are lot-scoped.
    Preserves visual elements: containers, borders, icons.
    """
    
    # Icons used in UI (preserve exact icons)
    ICONS = {
        'delete': '🗑️',
        'add': '➕',
        'lot': '📦',
        'left': '⬅️',
        'right': '➡️',
        'expand': '▼',
        'collapse': '▲'
    }
    
    def __init__(self, context: FormContext, field_renderer: FieldRenderer):
        """
        Initialize section renderer.
        
        Args:
            context: FormContext instance
            field_renderer: FieldRenderer instance for rendering individual fields
        """
        self.context = context
        self.field_renderer = field_renderer
        
    def render_section(self, 
                      section_name: str, 
                      section_schema: dict, 
                      parent_key: str = "",
                      level: int = 0) -> Dict[str, Any]:
        """
        Render a section with nested fields.
        
        Args:
            section_name: Name of the section
            section_schema: JSON schema for the section
            parent_key: Parent key for nested sections
            level: Nesting level for proper indentation
            
        Returns:
            Dictionary with section data
        """
        section_type = section_schema.get('type')
        
        if section_type == 'object':
            return self._render_object_section(section_name, section_schema, parent_key, level)
        elif section_type == 'array':
            return self._render_array_section(section_name, section_schema, parent_key, level)
        else:
            # Fallback to field renderer for simple types
            return self.field_renderer.render_field(section_name, section_schema, parent_key)
    
    def _render_object_section(self, 
                              section_name: str, 
                              section_schema: dict, 
                              parent_key: str,
                              level: int) -> Dict[str, Any]:
        """Render an object section with nested properties."""
        full_key = f"{parent_key}.{section_name}" if parent_key else section_name
        properties = section_schema.get('properties', {})
        required_fields = section_schema.get('required', [])
        
        # Get section title
        title = section_schema.get('title', section_name)
        description = section_schema.get('description')
        
        # Check if this section should be rendered (conditional rendering)
        if not self._should_render(section_schema):
            return {}
        
        # Create container with border for visual grouping
        use_container = section_schema.get('use_container', level > 0)
        use_expander = section_schema.get('use_expander', False)
        
        if use_expander:
            # Use expander for collapsible sections
            with st.expander(title, expanded=True):
                if description:
                    st.caption(description)
                section_data = self._render_properties(
                    properties, full_key, required_fields, level + 1
                )
        elif use_container:
            # Use container with border
            with st.container(border=True):
                if level == 0:
                    st.subheader(title)
                else:
                    st.markdown(f"**{title}**")
                    
                if description:
                    st.caption(description)
                    
                section_data = self._render_properties(
                    properties, full_key, required_fields, level + 1
                )
        else:
            # No container (for top-level sections)
            if title and level == 0:
                st.subheader(title)
            elif title:
                st.markdown(f"**{title}**")
                
            if description:
                st.caption(description)
                
            section_data = self._render_properties(
                properties, full_key, required_fields, level + 1
            )
        
        return section_data
    
    def _render_array_section(self, 
                             section_name: str, 
                             section_schema: dict, 
                             parent_key: str,
                             level: int) -> List[Any]:
        """Render an array section (array of objects)."""
        full_key = f"{parent_key}.{section_name}" if parent_key else section_name
        items_schema = section_schema.get('items', {})
        title = section_schema.get('title', section_name)
        description = section_schema.get('description')
        
        # Check if this is a simple array (handled by FieldRenderer)
        if items_schema.get('type') != 'object':
            return self.field_renderer.render_field(section_name, section_schema, parent_key)
        
        # Get or initialize array data
        session_key = self.context.get_field_key(full_key)
        if not self.context.field_exists(full_key):
            self.context.set_field_value(full_key, [])
        
        array_data = self.context.get_field_value(full_key, [])
        if not isinstance(array_data, list):
            array_data = []
            self.context.set_field_value(full_key, array_data)
        
        # Render array header
        st.markdown(f"**{title}**")
        if description:
            st.caption(description)
        
        # Render each array item
        updated_array = []
        for idx, item_data in enumerate(array_data):
            if self._render_array_item(
                full_key, idx, item_data, items_schema, level
            ):
                updated_array.append(item_data)
        
        # Update array if items were removed
        if len(updated_array) != len(array_data):
            self.context.set_field_value(full_key, updated_array)
            st.rerun()
        
        # Add button
        self._render_add_button(full_key, items_schema, title)
        
        return self.context.get_field_value(full_key, [])
    
    def _render_array_item(self, 
                          array_key: str, 
                          index: int, 
                          item_data: dict,
                          items_schema: dict,
                          level: int) -> bool:
        """
        Render a single array item with remove button.
        
        Returns:
            True if item should be kept, False if removed
        """
        item_key = f"{array_key}.{index}"
        session_key = self.context.get_field_key(item_key)
        
        # Create container with border for array item
        with st.container(border=True):
            # Header with item number and remove button
            col_title, col_remove = st.columns([5, 1])
            
            with col_title:
                item_title = items_schema.get('title', 'Item')
                st.markdown(f"**{item_title} {index + 1}**")
            
            with col_remove:
                remove_key = f"remove_{session_key}"
                if st.button(self.ICONS['delete'], key=remove_key, help="Remove item"):
                    return False  # Signal to remove this item
            
            # Render item properties
            properties = items_schema.get('properties', {})
            required_fields = items_schema.get('required', [])
            
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get('type')
                
                if prop_type == 'object':
                    self._render_object_section(
                        prop_name, prop_schema, item_key, level + 1
                    )
                elif prop_type == 'array':
                    self._render_array_section(
                        prop_name, prop_schema, item_key, level + 1
                    )
                else:
                    self.field_renderer.render_field(
                        prop_name, prop_schema, item_key, 
                        required=prop_name in required_fields
                    )
        
        return True  # Keep this item
    
    def _render_add_button(self, array_key: str, items_schema: dict, title: str):
        """Render add button for array."""
        session_key = self.context.get_field_key(array_key)
        add_key = f"add_{session_key}"
        
        if st.button(f"{self.ICONS['add']} Add {title}", key=add_key):
            # Create new empty item
            new_item = self._create_empty_item(items_schema)
            
            # Add to array
            current_array = self.context.get_field_value(array_key, [])
            current_array.append(new_item)
            self.context.set_field_value(array_key, current_array)
            st.rerun()
    
    def _create_empty_item(self, items_schema: dict) -> dict:
        """Create empty item based on schema."""
        if items_schema.get('type') != 'object':
            return None
        
        properties = items_schema.get('properties', {})
        new_item = {}
        
        for prop_name, prop_schema in properties.items():
            default = prop_schema.get('default')
            prop_type = prop_schema.get('type')
            
            if default is not None:
                new_item[prop_name] = default
            elif prop_type == 'string':
                new_item[prop_name] = ''
            elif prop_type in ['number', 'integer']:
                new_item[prop_name] = 0
            elif prop_type == 'boolean':
                new_item[prop_name] = False
            elif prop_type == 'array':
                new_item[prop_name] = []
            elif prop_type == 'object':
                new_item[prop_name] = {}
        
        return new_item
    
    def _render_properties(self, 
                          properties: dict, 
                          parent_key: str, 
                          required_fields: list,
                          level: int) -> dict:
        """Render all properties of an object."""
        section_data = {}
        
        # Story 2.2: Check if this is clientInfo section with address fields
        is_client_info = parent_key == 'clientInfo' or parent_key.endswith('.clientInfo')
        is_cofinancer = 'cofinancer' in parent_key.lower()
        
        # Detect address field groups for special rendering
        address_prefixes = []
        if is_client_info:
            # Check for single client address fields
            if 'singleClientStreet' in properties or 'singleClientHouseNumber' in properties:
                address_prefixes.append('singleClient')
        elif is_cofinancer:
            # Check for cofinancer address fields
            if 'cofinancerStreet' in properties or 'cofinancerHouseNumber' in properties:
                address_prefixes.append('cofinancer')
        
        # For client array items
        if 'street' in properties or 'houseNumber' in properties:
            address_prefixes.append('')  # No prefix for client array items
        
        # Track which fields have been rendered as part of address groups
        rendered_fields = set()
        
        # Render address fields as groups if detected
        for prefix in address_prefixes:
            address_fields = ['Street', 'HouseNumber', 'PostalCode', 'City']
            if not prefix:
                # For client array items, field names don't have prefix
                address_fields = ['street', 'houseNumber', 'postalCode', 'city']
            else:
                address_fields = [f"{prefix}{field}" for field in address_fields]
            
            # Check if we have these fields in properties
            has_address_fields = any(field in properties for field in address_fields)
            
            if has_address_fields:
                # Render address fields as a group
                address_data = self.field_renderer.render_address_fields(
                    prefix, properties, parent_key
                )
                section_data.update(address_data)
                
                # Mark these fields as rendered
                for field in address_fields:
                    if field in properties:
                        rendered_fields.add(field)
        
        # Render remaining fields normally
        for prop_name, prop_schema in properties.items():
            # Skip if already rendered as part of address group
            if prop_name in rendered_fields:
                continue
            
            # Check conditional rendering
            if not self._should_render(prop_schema):
                continue
            
            prop_type = prop_schema.get('type')
            is_required = prop_name in required_fields
            
            if prop_type == 'object':
                section_data[prop_name] = self._render_object_section(
                    prop_name, prop_schema, parent_key, level
                )
            elif prop_type == 'array' and prop_schema.get('items', {}).get('type') == 'object':
                section_data[prop_name] = self._render_array_section(
                    prop_name, prop_schema, parent_key, level
                )
            else:
                # Use field renderer for simple fields
                section_data[prop_name] = self.field_renderer.render_field(
                    prop_name, prop_schema, parent_key, required=is_required
                )
        
        return section_data
    
    def _should_render(self, schema: dict) -> bool:
        """
        Check if a field/section should be rendered based on conditions.
        Supports render_if, render_if_any, render_if_all conditions.
        """
        # Check render_if condition
        if 'render_if' in schema:
            condition = schema['render_if']
            if not self._check_condition(condition):
                return False
        
        # Check render_if_any conditions (OR logic)
        if 'render_if_any' in schema:
            conditions = schema['render_if_any']
            if not any(self._check_condition(c) for c in conditions):
                return False
        
        # Check render_if_all conditions (AND logic)
        if 'render_if_all' in schema:
            conditions = schema['render_if_all']
            if not all(self._check_condition(c) for c in conditions):
                return False
        
        return True
    
    def _check_condition(self, condition: dict) -> bool:
        """Check a single render condition."""
        field = condition.get('field')
        expected_value = condition.get('value')
        operator = condition.get('operator', 'equals')
        
        if not field:
            return True
        
        # Get field value (might be lot-scoped or global)
        actual_value = self.context.get_field_value(field)
        
        # Check condition based on operator
        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'in':
            return actual_value in expected_value
        elif operator == 'not_in':
            return actual_value not in expected_value
        elif operator == 'exists':
            return actual_value is not None and actual_value != ""
        elif operator == 'not_exists':
            return actual_value is None or actual_value == ""
        else:
            # Default to equals
            return actual_value == expected_value