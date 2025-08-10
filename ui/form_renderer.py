
"""Enhanced form rendering components with localization and improved UX."""
import streamlit as st
from datetime import date
from localization import get_text, get_validation_message

def _get_default_value(full_key, prop_details):
    """Get appropriate default value for form field."""
    default_value = prop_details.get("default")
    if prop_details.get("type") == "number":
        return st.session_state.get(full_key, default_value if default_value is not None else 0.0)
    elif prop_details.get("format") == "date":
        return st.session_state.get(full_key, default_value if default_value is not None else date.today())
    elif prop_details.get("type") == "array":
        return st.session_state.get(full_key, default_value if default_value is not None else [])
    elif prop_details.get("type") == "boolean":
        return st.session_state.get(full_key, default_value if default_value is not None else False)
    else:
        return st.session_state.get(full_key, default_value if default_value is not None else "")

def _should_render(prop_details):
    """Check if a field should be rendered based on a conditional flag in the schema."""
    render_if = prop_details.get("render_if")
    if not render_if:
        return True
    
    condition_field = render_if.get("field")
    condition_value = render_if.get("value")
    condition_not_in = render_if.get("not_in")
    
    current_field_value = st.session_state.get(condition_field)
    
    # Handle 'value' condition (exact match)
    if condition_value is not None:
        return current_field_value == condition_value
    
    # Handle 'not_in' condition (value should not be in list)
    if condition_not_in is not None:
        return current_field_value not in condition_not_in
    
    return True

def _format_field_label(label, prop_details, parent_key, prop_name):
    """Format field label with required indicator and optional marker."""
    formatted_label = label
    
    # Check if field is required by looking at parent schema
    if parent_key and st.session_state.get('schema'):
        parent_schema = st.session_state['schema']['properties']
        for key in parent_key.split('.'):
            if key in parent_schema:
                parent_schema = parent_schema[key]
        
        if 'required' in parent_schema and prop_name in parent_schema['required']:
            formatted_label = f"{label} {get_text('required_field')}"
    
    # Add optional indicator if explicitly marked as optional
    if prop_details.get('description') and 'ni obvezen' in prop_details.get('description', '').lower():
        formatted_label = f"{label} {get_text('optional_field')}"
        
    return formatted_label

def _is_field_required(parent_key, prop_name):
    """Check if a field is required based on schema."""
    if not parent_key or not st.session_state.get('schema'):
        return False
    
    try:
        parent_schema = st.session_state['schema']['properties']
        for key in parent_key.split('.'):
            if key in parent_schema:
                parent_schema = parent_schema[key]
                if 'properties' in parent_schema:
                    parent_schema = parent_schema['properties']
        
        return 'required' in parent_schema and prop_name in parent_schema['required']
    except (KeyError, TypeError):
        return False

def render_form(schema_properties, parent_key=""):
    """Recursively render form fields based on JSON schema properties."""
    for prop_name, prop_details in schema_properties.items():
        if not _should_render(prop_details):
            continue

        full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
        label = prop_details.get("title", prop_name)
        help_text = prop_details.get("description")
        current_value = _get_default_value(full_key, prop_details)

        prop_type = prop_details.get("type")

        if prop_type == "object":
            if "$ref" in prop_details:
                ref_path = prop_details["$ref"].split('/')[1:]
                ref_props = st.session_state['schema']
                for part in ref_path:
                    ref_props = ref_props[part]
                render_form(ref_props.get("properties", {}), parent_key=full_key)
            else:
                # Enhanced section header with better styling
                if help_text:
                    # Special handling for legal basis section - restore original superior design
                    if "Pravna podlaga" in label:
                        # Create header with info icon
                        col_header, col_info = st.columns([4, 1])
                        with col_header:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                                padding: 1rem;
                                border-radius: 8px;
                                border-left: 4px solid #1f4e79;
                                margin: 1rem 0;
                            ">
                                <h3 style="margin: 0; color: #1f4e79;">{label}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Add dropdown/expandable section with legal framework info
                        with st.expander("ℹ️ Prikaži pravne podlage in predpise", expanded=False):
                            st.markdown(f"""
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;">
                                <p style="margin: 0; color: #495057; font-size: 0.9rem; line-height: 1.6;">
                                    {help_text.replace(chr(10), '<br>')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        # Regular sections with truncated description
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                            padding: 1rem;
                            border-radius: 8px;
                            border-left: 4px solid #1f4e79;
                            margin: 1rem 0;
                        ">
                            <h3 style="margin: 0; color: #1f4e79;">{label}</h3>
                            <p style="margin: 0.5rem 0 0 0; color: #6c757d; font-size: 0.9rem;">{help_text[:200]}{'...' if len(help_text) > 200 else ''}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.subheader(label)
                render_form(prop_details.get("properties", {}), parent_key=full_key)
        
        elif prop_type == "array":
            st.subheader(label, help=help_text)
            items_schema = prop_details.get("items", {})
            
            # Array of simple enums (multiselect)
            if "enum" in items_schema:
                st.multiselect(label, options=items_schema["enum"], default=current_value, key=full_key, help=help_text)
            
            # Array of objects
            elif items_schema.get("type") == "object":
                if full_key not in st.session_state:
                    st.session_state[full_key] = []

                for i in range(len(st.session_state[full_key])):
                    # Create container with header row for remove button
                    container = st.container(border=True)
                    with container:
                        # Add header with remove button
                        col_header, col_remove = st.columns([5, 1])
                        with col_header:
                            item_title = items_schema.get('title', 'element')
                            st.markdown(f"**{item_title} {i + 1}**")
                        with col_remove:
                            if st.button("❌", key=f"remove_{full_key}_{i}", help=f"Odstrani {item_title.lower()} {i + 1}"):
                                st.session_state[full_key].pop(i)
                                st.rerun()
                        
                        # Render the form fields for this object
                        render_form(items_schema.get("properties", {}), parent_key=f"{full_key}.{i}")
                
                # Add new item with improved UX
                item_title = items_schema.get('title', 'element')
                if full_key == "clientInfo.clients" and item_title == "Naročnik":
                    button_text = "➕ Dodaj naročnika"
                else:
                    button_text = f"➕ Dodaj {item_title.lower()}"
                
                if st.button(button_text, key=f"add_{full_key}"):
                    st.session_state[full_key].append({})
                    st.rerun()
            
            # Array of strings (like additional legal bases)
            elif items_schema.get("type") == "string":
                if full_key not in st.session_state:
                    st.session_state[full_key] = []

                # Display existing string entries with X buttons
                for i in range(len(st.session_state[full_key])):
                    col_input, col_remove = st.columns([5, 1])
                    
                    with col_input:
                        current_text = st.session_state[full_key][i]
                        new_text = st.text_input(
                            f"{items_schema.get('title', 'Vnos')} {i + 1}",
                            value=current_text,
                            key=f"{full_key}_item_{i}",
                            placeholder="Vnesite naziv zakona/predpisa"
                        )
                        # Update the value if changed
                        if new_text != current_text:
                            st.session_state[full_key][i] = new_text
                    
                    with col_remove:
                        # Add some vertical spacing to align with input field
                        st.write("")
                        if st.button("❌", key=f"remove_{full_key}_{i}", help="Odstrani to pravno podlago"):
                            st.session_state[full_key].pop(i)
                            st.rerun()

                # Special handling for additional legal bases
                if "additionalLegalBases" in full_key:
                    button_text = "➕ Dodaj pravno podlago"
                else:
                    item_title = items_schema.get('title', 'element').lower()
                    button_text = f"➕ Dodaj {item_title}"
                
                if st.button(button_text, key=f"add_{full_key}"):
                    st.session_state[full_key].append("")
                    st.rerun()

        elif prop_type == "string":
            # Add required indicator to label
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            if "enum" in prop_details:
                # Enhanced selectbox with proper placeholder
                enum_options = [""] + prop_details["enum"] if not current_value else prop_details["enum"]
                index = 0
                if current_value and current_value in prop_details["enum"]:
                    # Calculate correct index based on whether empty option is present
                    if current_value in enum_options:
                        index = enum_options.index(current_value)
                    else:
                        index = 0
                
                # Special handling for "vseeno" auto-selection in procedure field
                selected_value = st.selectbox(
                    display_label, 
                    options=enum_options, 
                    index=index,
                    key=full_key, 
                    help=help_text,
                    placeholder=get_text("select_option")
                )
                
                # Auto-selection logic for "vseeno" in procedure field - fixed to handle all cases
                if (prop_name == "procedure" and 
                    "submissionProcedure" in full_key and 
                    selected_value == "vseeno"):
                    
                    # Use session state to track user interaction
                    user_clicked_key = f"{full_key}_user_clicked_vseeno"
                    previous_value_key = f"{full_key}_previous_value"
                    
                    # Check if user actively selected "vseeno" (not just default)
                    previous_value = st.session_state.get(previous_value_key, "")
                    user_actively_selected = (previous_value != "" and previous_value != "vseeno" and selected_value == "vseeno")
                    
                    # If user actively clicked "vseeno", trigger auto-selection
                    if user_actively_selected and not st.session_state.get(user_clicked_key, False):
                        st.session_state[full_key] = "odprti postopek"
                        st.session_state[user_clicked_key] = True  # Mark that user interaction occurred
                        st.info("ℹ️ Ker ste izbrali 'vseeno', smo avtomatsko nastavili 'odprti postopek', ki je najčešji in priporočeni postopek za večino javnih naročil.")
                        st.rerun()
                    
                    # Store current value for next comparison
                    st.session_state[previous_value_key] = selected_value
                
                # Reset tracking flags if user manually selects something else
                if (prop_name == "procedure" and 
                    "submissionProcedure" in full_key and 
                    selected_value != "vseeno"):
                    user_clicked_key = f"{full_key}_user_clicked_vseeno"
                    previous_value_key = f"{full_key}_previous_value"
                    st.session_state[user_clicked_key] = False
                    st.session_state[previous_value_key] = selected_value
            elif prop_details.get("format") == "textarea":
                # Enhanced textarea
                st.text_area(
                    display_label, 
                    value=current_value, 
                    key=full_key, 
                    help=help_text,
                    placeholder=get_text("enter_text"),
                    height=100
                )
            elif prop_details.get("format") == "file":
                # Enhanced file uploader
                st.file_uploader(
                    display_label, 
                    key=full_key, 
                    help=help_text,
                    type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
                )
            elif prop_details.get("format") == "date":
                # Enhanced date input
                st.date_input(
                    display_label, 
                    value=current_value, 
                    key=full_key, 
                    help=help_text,
                    format="DD.MM.YYYY"
                )
            else:
                # Enhanced text input
                st.text_input(
                    display_label, 
                    value=current_value, 
                    key=full_key, 
                    help=help_text,
                    placeholder=get_text("enter_text")
                )

        elif prop_type == "number":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            st.number_input(
                display_label, 
                value=current_value, 
                key=full_key, 
                help=help_text,
                step=0.01,
                format="%.2f"
            )

        elif prop_type == "boolean":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            checkbox_value = st.checkbox(display_label, value=current_value, key=full_key, help=help_text)
            
            # Special handling for wantsLogo to provide user feedback
            if prop_name == "wantsLogo" and checkbox_value != current_value:
                if checkbox_value:
                    st.success("✅ Polje za nalaganje logotipov je sedaj na voljo spodaj.")
                else:
                    st.info("ℹ️ Polje za nalaganje logotipov je skrito, ker niste izbrali te možnosti.")
