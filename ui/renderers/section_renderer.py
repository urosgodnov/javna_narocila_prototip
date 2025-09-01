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
    
    def _render_warning_box(self, title: str, content: str):
        """Render a custom warning box with consistent styling."""
        # Remove any existing warning prefixes from content
        content = content.replace("⚠️ **OPOZORILO:**", "").replace("**POZOR:**", "").strip()
        
        # Create custom HTML for warning box
        warning_html = f"""
        <div style="
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 0.25rem;
            padding: 1rem;
            margin: 1rem 0;
        ">
            <div style="
                display: flex;
                align-items: flex-start;
                gap: 0.5rem;
            ">
                <span style="font-size: 1.2rem;">⚠️</span>
                <div style="flex: 1;">
                    <strong style="color: #856404; font-size: 1rem;">{title}</strong>
                    <div style="color: #856404; margin-top: 0.5rem; line-height: 1.5;">
                        {content}
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(warning_html, unsafe_allow_html=True)
        
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
        
        # IMPORTANT: Skip rendering if both $ref and properties exist
        # This happens when app.py resolves $ref but leaves both in the schema
        # We should only use the properties, not process the $ref again
        if '$ref' in section_schema and 'properties' in section_schema:
            # The $ref has already been resolved by app.py, just use properties
            properties = section_schema.get('properties', {})
        else:
            properties = section_schema.get('properties', {})
        
        required_fields = section_schema.get('required', [])
        conditionally_required = section_schema.get('conditionally_required', [])
        
        # Get section title
        title = section_schema.get('title', section_name)
        description = section_schema.get('description')
        
        # Check if this section should be rendered (conditional rendering)
        if not self._should_render(section_schema, parent_key):
            return {}
        
        # Special handling for legalBasis field - use info icons with expanders
        if section_name == 'legalBasis':
            return self._render_legal_basis_section(section_schema, full_key, properties, required_fields)
        
        # Create container with border for visual grouping
        use_container = section_schema.get('use_container', level > 0)
        use_expander = section_schema.get('use_expander', False)
        
        if use_expander:
            # Use expander for collapsible sections
            with st.expander(title, expanded=True):
                if description:
                    # Special handling for very long descriptions (technical specifications)
                    if len(description) > 1000:
                        # Display as info box for better visibility
                        st.info(description)
                    elif description.startswith("⚠️ **OPOZORILO:**"):
                        # Display as custom warning box
                        self._render_warning_box("Opozorilo", description)
                    else:
                        st.caption(description)
                section_data = self._render_properties(
                    properties, full_key, required_fields, level + 1, conditionally_required
                )
        elif use_container:
            # Use container with border
            with st.container(border=True):
                if level == 0:
                    st.subheader(title)
                else:
                    st.markdown(f"**{title}**")
                    
                if description:
                    # Special handling for very long descriptions (technical specifications)
                    if len(description) > 1000:
                        # Display as info box for better visibility
                        st.info(description)
                    elif description.startswith("⚠️ **OPOZORILO:**"):
                        # Display as custom warning box
                        self._render_warning_box("Opozorilo", description)
                    else:
                        st.caption(description)
                    
                section_data = self._render_properties(
                    properties, full_key, required_fields, level + 1, conditionally_required
                )
        else:
            # No container (for top-level sections)
            if title and level == 0:
                st.subheader(title)
            elif title:
                st.markdown(f"**{title}**")
                
            if description:
                # Special handling for very long descriptions (technical specifications)
                if len(description) > 1000:
                    # Display as info box for better visibility
                    st.info(description)
                elif description.startswith("⚠️ **OPOZORILO:**"):
                    # Display as custom warning box
                    self._render_warning_box("Opozorilo", description)
                else:
                    st.caption(description)
                
            section_data = self._render_properties(
                properties, full_key, required_fields, level + 1, conditionally_required
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
            # Special handling for mixedOrderComponents - initialize with one default item
            if section_name == 'mixedOrderComponents':
                default_item = {
                    'type': 'blago',
                    'description': '',
                    'estimatedValue': 0,
                    'guaranteedFunds': 0,
                    'isCofinanced': False
                }
                self.context.set_field_value(full_key, [default_item])
            else:
                self.context.set_field_value(full_key, [])
        
        array_data = self.context.get_field_value(full_key, [])
        if not isinstance(array_data, list):
            array_data = []
            self.context.set_field_value(full_key, array_data)
        
        # For mixedOrderComponents, ensure at least one item exists
        if section_name == 'mixedOrderComponents' and len(array_data) == 0:
            default_item = {
                'type': 'blago',
                'description': '',
                'estimatedValue': 0,
                'guaranteedFunds': 0,
                'isCofinanced': False
            }
            array_data.append(default_item)
            self.context.set_field_value(full_key, array_data)
        
        # Render array header
        st.markdown(f"**{title}**")
        if description:
            # Special handling for very long descriptions (technical specifications)
            if len(description) > 1000:
                # Display as info box for better visibility  
                st.info(description)
            elif description.startswith("⚠️ **OPOZORILO:**"):
                # Display as custom warning box
                self._render_warning_box("Opozorilo", description)
            else:
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
                          level: int,
                          conditionally_required: list = None) -> dict:
        """Render all properties of an object."""
        section_data = {}
        
        # Story 2.2: Check if this is clientInfo section with address fields
        is_client_info = parent_key == 'clientInfo' or parent_key.endswith('.clientInfo')
        is_cofinancer = 'cofinancer' in parent_key.lower()
        
        # Define proper field ordering for client info
        if is_client_info:
            # Define the correct order for single client fields
            single_client_order = [
                'multipleClientsInfo',  # Info box
                'isSingleClient',        # Checkbox
                'singleClientName',      # Name FIRST
                'singleClientStreet',    # Then address fields
                'singleClientHouseNumber',
                'singleClientPostalCode',
                'singleClientCity',
                'singleClientLegalRepresentative',  # Legal rep
                'includeLogos',          # Logo checkbox
                'clients'                # Multiple clients array
            ]
            
            # Create ordered properties dict
            ordered_properties = {}
            for field in single_client_order:
                if field in properties:
                    ordered_properties[field] = properties[field]
            
            # Add any remaining fields not in the order list
            for field, schema in properties.items():
                if field not in ordered_properties and not schema.get('deprecated', False):
                    ordered_properties[field] = schema
            
            properties = ordered_properties
        
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
        address_field_names = set()
        
        # Identify all address field names
        for prefix in address_prefixes:
            if prefix:
                for field in ['Street', 'HouseNumber', 'PostalCode', 'City']:
                    address_field_names.add(f"{prefix}{field}")
            else:
                address_field_names.update(['street', 'houseNumber', 'postalCode', 'city'])
        
        # Render fields in order
        for prop_name, prop_schema in properties.items():
            # Skip if already rendered
            if prop_name in rendered_fields:
                continue
            
            # Check conditional rendering
            if not self._should_render(prop_schema, parent_key):
                continue
            
            prop_type = prop_schema.get('type')
            is_required = prop_name in required_fields
            
            # Check if field is conditionally required and currently visible
            if conditionally_required and prop_name in conditionally_required:
                # Check if the field should be rendered (visible)
                if self._should_render(prop_schema, parent_key):
                    is_required = True
            
            # Check if this is an address field that should be grouped
            if prop_name in address_field_names and any(prefix for prefix in address_prefixes):
                # Find the right prefix for this field
                field_prefix = None
                for prefix in address_prefixes:
                    if (prefix and prop_name.startswith(prefix)) or (not prefix and prop_name in ['street', 'houseNumber', 'postalCode', 'city']):
                        field_prefix = prefix
                        break
                
                if field_prefix is not None and field_prefix not in rendered_fields:
                    # Render entire address group at once
                    address_fields = ['Street', 'HouseNumber', 'PostalCode', 'City']
                    if not field_prefix:
                        address_fields = ['street', 'houseNumber', 'postalCode', 'city']
                    else:
                        address_fields = [f"{field_prefix}{field}" for field in address_fields]
                    
                    # Render address fields as a group
                    address_data = self.field_renderer.render_address_fields(
                        field_prefix, properties, parent_key
                    )
                    section_data.update(address_data)
                    
                    # Mark all address fields as rendered
                    for field in address_fields:
                        rendered_fields.add(field)
                    
                    # Mark this prefix as handled
                    rendered_fields.add(field_prefix)
                continue
            
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
            
            rendered_fields.add(prop_name)
        
        return section_data
    
    def _should_render(self, schema: dict, parent_key: str = "") -> bool:
        """
        Check if a field/section should be rendered based on conditions.
        Supports render_if, render_if_any, render_if_all conditions.
        """
        # Check render_if condition
        if 'render_if' in schema:
            condition = schema['render_if']
            if not self._check_condition(condition, parent_key):
                return False
        
        # Check render_if_any conditions (OR logic)
        if 'render_if_any' in schema:
            conditions = schema['render_if_any']
            if not any(self._check_condition(c, parent_key) for c in conditions):
                return False
        
        # Check render_if_all conditions (AND logic)
        if 'render_if_all' in schema:
            conditions = schema['render_if_all']
            if not all(self._check_condition(c, parent_key) for c in conditions):
                return False
        
        return True
    
    def _check_condition(self, condition: dict, parent_key: str = "") -> bool:
        """Check a single render condition."""
        field = condition.get('field')
        field_parent = condition.get('field_parent')
        
        # Debug logging for justification field
        if field and 'justification' in str(parent_key):
            import logging
            logging.info(f"[RENDER_CONDITION] Checking condition for justification: field={field}, condition={condition}")
        
        # Handle field_parent conditions (used in nested objects like orderType)
        if field_parent:
            # field_parent refers to a sibling field in the same parent object
            # Construct the full field path based on parent_key
            if parent_key:
                field = f"{parent_key}.{field_parent}"
            else:
                field = field_parent
            
        
        if not field:
            return True
        
        # ALWAYS use context to get field value (it handles lot scoping)
        actual_value = self.context.get_field_value(field)
        
        # Debug logging for justification/procedure fields
        if field and ('justification' in str(parent_key) or 'procedure' in field):
            import logging
            lot_key = self.context.get_field_key(field)
            logging.info(f"[RENDER_CONDITION] Field {field}: actual_value='{actual_value}', lot_scoped_key={lot_key}")
        
        # If value is None and we're checking orderType.type, use the default
        if actual_value is None and field.endswith('.type') and 'orderType' in field:
            actual_value = 'blago'  # Default value from schema
        
        # Handle different condition formats
        # Format 1: {"field": "x", "value": "y", "operator": "equals"}
        # Format 2: {"field": "x", "value": "y"} (implicit equals)
        # Format 3: {"field": "x", "not_in": ["a", "b"]} (operator as key)
        # Format 4: {"field_parent": "x", "not_in": ["a", "b"]} (with field_parent)
        
        # Check for operator as a key (Format 3/4)
        if 'not_in' in condition:
            result = actual_value not in condition['not_in']
            # Debug logging for justification field
            if field and 'justification' in str(parent_key):
                import logging
                logging.info(f"[RENDER_CONDITION] not_in check: actual_value='{actual_value}', not_in={condition['not_in']}, result={result}")
            return result
        elif 'in' in condition:
            return actual_value in condition['in']
        elif 'not_equals' in condition:
            return actual_value != condition['not_equals']
        elif 'exists' in condition:
            return actual_value is not None and actual_value != ""
        elif 'not_exists' in condition:
            return actual_value is None or actual_value == ""
        
        # Fall back to traditional format (Format 1/2)
        expected_value = condition.get('value')
        operator = condition.get('operator', 'equals')
        
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
    
    def _render_legal_basis_section(self, section_schema: dict, full_key: str, properties: dict, required_fields: list) -> dict:
        """
        Special rendering for legal basis section with info icons.
        Shows legal basis information in expandable sections with info icons.
        """
        st.subheader("📋 Pravna podlaga")
        
        # Display all legal bases in a clear, organized format
        st.info("Pri oddaji javnega naročila se bodo uporabljala določila naslednjih predpisov in drugih dokumentov:")
        
        # Create two columns for better organization
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📚 Obvezni predpisi za javna naročila")
            st.markdown("""
            1. **Zakon o javnem naročanju**  
               ZJN-3, Uradni list RS, št. 91/15 s spremembami
               
            2. **Zakon o pravnem varstvu v postopkih javnega naročanju**  
               ZPVPJN, Uradni list RS, št. 43/2011 s spremembami
               
            3. **Uredba o finančnih zavarovanjih pri javnem naročanju**  
               Uradni list RS, št. 27/16
               
            4. **Uredba o zelenem javnem naročanju**  
               Uradni list RS, št. 51/17 s spremembami  
               *V kolikor je njena uporaba glede na predmet javnega naročila obvezna*
               
            5. **Zakon o integriteti in preprečevanju korupcije**  
               ZIntPK-UPB2, Uradni list RS št. 69/2011 s spremembami
               
            6. **Zakon o varstvu osebnih podatkov**  
               ZVOP-2, Uradni list RS št. 163/22
               
            7. **Zakon o poslovni skrivnosti**  
               ZPosS, Uradni list RS, št. 22/19
            """)
        
        with col2:
            st.markdown("### 📖 Splošni predpisi")
            st.markdown("""
            8. **Obligacijski zakonik**  
               OZ, Uradni list RS, št. 83/2001 s spremembami
               
            9. **Zakon o javnih financah**  
               ZJF, Uradni list RS, št. 11/11 s spremembami
               
            10. **Zakon o davku na dodano vrednost**  
                ZDDV-1, Uradni list RS, št. 13/11 s spremembami
                
            11. **Zakon o splošnem upravnem postopku**  
                ZUP, Uradni list RS št. 80/99 s spremembami
                
            12. **Zakon o pravdnem postopku**  
                ZPP-UPB3, Uradni list RS št. 73/2007 s spremembami
                
            13. **Predpisi, ki urejajo področje, ki je predmet javnega naročila**  
                *Specifični za vsako naročilo*
            """)
        
        st.success("✅ Naročnik bo pri izvajanju postopka javnega naročanja ravnal v skladu z vsemi veljavnimi predpisi in zagotovil transparentnost ter enakopravno obravnavo vseh ponudnikov.")
        
        # Initialize session state for legal basis fields
        use_additional_key = f"{full_key}.useAdditional"
        additional_bases_key = f"{full_key}.additionalLegalBases"
        
        # ALWAYS use lot-scoped keys through context
        lot_scoped_use_key = self.context.get_field_key(use_additional_key)
        lot_scoped_bases_key = self.context.get_field_key(additional_bases_key)
        
        # Get values using lot-scoped keys
        use_additional_value = self.context.session_state.get(lot_scoped_use_key, False)
        additional_bases_value = self.context.session_state.get(lot_scoped_bases_key, [])
        
        # Checkbox for additional legal bases
        widget_key = f"widget_{lot_scoped_use_key}"
        use_additional = st.checkbox(
            "Želim, da se upošteva še kakšna pravna podlaga",
            value=use_additional_value,
            key=widget_key,
            help="Označite, če želite dodati dodatne pravne podlage poleg osnovne"
        )
        
        # Save using context (which handles lot scoping)
        self.context.set_field_value(use_additional_key, use_additional)
        
        # Show additional legal bases if checkbox is checked
        if use_additional:
            # Get current additional bases with fallback
            additional_bases = additional_bases_value if additional_bases_value else []
            
            st.markdown("**Dodatne pravne podlage:**")
            
            # Display existing legal bases with proper state management
            for idx in range(len(additional_bases)):
                col1, col2 = st.columns([5, 1])
                with col1:
                    # Use unique widget key for each input
                    widget_key = f"widget_legal_basis_{self.context.lot_index}_{idx}"
                    
                    # Update the value in the list directly
                    additional_bases[idx] = st.text_input(
                        f"Pravna podlaga {idx + 1}",
                        value=additional_bases[idx] if idx < len(additional_bases) else "",
                        key=widget_key,
                        placeholder="Vnesite pravno podlago (npr. člen zakona, uredba...)"
                    )
                with col2:
                    if st.button("🗑️", key=f"remove_legal_{self.context.lot_index}_{idx}", help="Odstrani"):
                        additional_bases.pop(idx)
                        self.context.set_field_value(additional_bases_key, additional_bases)
                        st.rerun()
            
            # Save changes using context (which handles lot scoping)
            self.context.set_field_value(additional_bases_key, additional_bases)
            
            # Add new legal basis button
            if st.button("➕ Dodaj pravno podlago", key=f"add_legal_basis_{self.context.lot_index}"):
                additional_bases.append("")
                self.context.set_field_value(additional_bases_key, additional_bases)
                st.rerun()
        
        # Return the data using context (which handles lot scoping)
        return {
            'useAdditional': self.context.get_field_value(use_additional_key, False),
            'additionalLegalBases': self.context.get_field_value(additional_bases_key, [])
        }