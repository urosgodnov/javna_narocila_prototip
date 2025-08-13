
"""Enhanced form rendering components with localization and improved UX."""
import streamlit as st
from datetime import date
from localization import get_text, get_validation_message
from utils.lot_utils import get_lot_scoped_key, render_lot_context_step
from ui.components.cpv_selector import render_cpv_selector


def _get_default_value(full_key, prop_details, lot_context=None):
    """Get appropriate default value for form field."""
    # Apply lot scoping if context is provided, but respect global fields
    global_fields = ['lotsInfo', 'lots', 'clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 'contractInfo', 'otherInfo', 'executionDeadline', 'priceInfo', 'negotiationsInfo', 'inspectionInfo', 'participationAndExclusion', 'participationConditions', 'financialGuarantees']
    is_global_field = any(full_key.startswith(gf) for gf in global_fields)
    
    if is_global_field:
        scoped_key = full_key  # Global fields always use original key
    elif lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
        scoped_key = get_lot_scoped_key(full_key, lot_context['lot_index'])
    elif lot_context and lot_context['mode'] == 'general':
        scoped_key = get_lot_scoped_key(full_key, None)
    else:
        scoped_key = full_key
    
    # Check if this key exists in session state
    if scoped_key in st.session_state:
        return st.session_state[scoped_key]
    
    # Only use schema defaults for truly new fields (never been set)
    # For critical fields like procedure, don't override user selections with schema defaults
    default_value = prop_details.get("default")
    
    # Special handling for submission procedure to preserve user choices
    if full_key == "submissionProcedure.procedure":
        # Check if any procedure has been set previously (even if the exact key doesn't exist)
        procedure_keys = [k for k in st.session_state.keys() if k.endswith('submissionProcedure.procedure')]
        if procedure_keys:
            # Use the first found procedure value instead of schema default
            return st.session_state.get(procedure_keys[0], default_value)
        # Only use default if no procedure has ever been set
        return default_value if default_value is not None else ""
    
    if prop_details.get("type") == "number":
        return default_value if default_value is not None else 0.0
    elif prop_details.get("type") == "integer":
        return default_value if default_value is not None else 0
    elif prop_details.get("format") == "date":
        return default_value if default_value is not None else date.today()
    elif prop_details.get("type") == "array":
        return default_value if default_value is not None else []
    elif prop_details.get("type") == "boolean":
        return default_value if default_value is not None else False
    else:
        return default_value if default_value is not None else ""

def _should_render(prop_details, parent_key="", lot_context=None, session_key_prefix=""):
    """Check if a field should be rendered based on a conditional flag in the schema."""
    # Check for render_if_any (OR logic)
    render_if_any = prop_details.get("render_if_any")
    if render_if_any:
        # If any condition is true, render the field
        for condition in render_if_any:
            if _check_single_condition(condition, parent_key, lot_context, session_key_prefix):
                return True
        return False
    
    # Check for regular render_if
    render_if = prop_details.get("render_if")
    if not render_if:
        return True
    
    return _check_single_condition(render_if, parent_key, lot_context, session_key_prefix)

def _check_single_condition(render_if, parent_key="", lot_context=None, session_key_prefix=""):
    """Check a single render condition."""
    condition_field = render_if.get("field")
    condition_field_parent = render_if.get("field_parent")
    condition_value = render_if.get("value")
    condition_not_in = render_if.get("not_in")
    condition_contains = render_if.get("contains")
    
    # Handle parent-relative field reference
    if condition_field_parent and parent_key:
        # Build the full field path from parent context
        condition_field = f"{parent_key}.{condition_field_parent}"
    elif condition_field_parent:
        # No parent context, use as-is
        condition_field = condition_field_parent
    
    # Resolve the actual session key considering lot context
    if condition_field:
        # Check if this is a global field that shouldn't be scoped
        global_fields = ['lotsInfo', 'lots', 'clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 'contractInfo', 'otherInfo', 'executionDeadline', 'priceInfo', 'negotiationsInfo', 'inspectionInfo', 'participationAndExclusion', 'participationConditions', 'financialGuarantees']
        is_global_field = any(condition_field.startswith(gf) for gf in global_fields)
        
        if is_global_field:
            actual_session_key = condition_field
        elif session_key_prefix:
            # If we have a session key prefix (from lot scoping), use it
            actual_session_key = f"{session_key_prefix}.{condition_field}"
        elif lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
            actual_session_key = get_lot_scoped_key(condition_field, lot_context['lot_index'])
        elif lot_context and lot_context['mode'] == 'general':
            actual_session_key = get_lot_scoped_key(condition_field, None)
        else:
            actual_session_key = condition_field
        
        current_field_value = st.session_state.get(actual_session_key)
    else:
        current_field_value = None
    
    # Handle 'value' condition (exact match)
    if condition_value is not None and condition_field:
        return current_field_value == condition_value
    
    # Handle 'not_in' condition (value should not be in list)
    if condition_not_in is not None and condition_field:
        return current_field_value not in condition_not_in
    
    # Handle 'contains' condition (array contains value)
    if condition_contains is not None and condition_field:
        if isinstance(current_field_value, list):
            return condition_contains in current_field_value
        return False
    
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

def render_form(schema_properties, parent_key="", lot_context=None):
    """Recursively render form fields based on JSON schema properties.
    
    Args:
        schema_properties: Schema properties to render
        parent_key: Parent key for nested fields
        lot_context: Lot context information (from get_current_lot_context)
    """
    for prop_name, prop_details in schema_properties.items():
        if not _should_render(prop_details, parent_key, lot_context):
            continue

        full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
        
        # Handle lot context steps
        if full_key.startswith('lot_context_'):
            lot_index = int(full_key.split('_')[2])
            render_lot_context_step(lot_index)
            continue
            
        label = prop_details.get("title", prop_name)
        help_text = prop_details.get("description")
        # Get raw default from schema (don't use complex _get_default_value logic)
        raw_default = prop_details.get("default", "")
        
        # Create the session state key (scoped for lots)
        # Some fields should never be lot-scoped as they control global form behavior
        global_fields = ['lotsInfo', 'lots', 'clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 'contractInfo', 'otherInfo', 'executionDeadline', 'priceInfo', 'negotiationsInfo', 'inspectionInfo', 'participationAndExclusion', 'participationConditions', 'financialGuarantees']
        is_global_field = any(full_key.startswith(gf) for gf in global_fields)
        
        if is_global_field:
            session_key = full_key  # Global fields always use original key
        elif lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
            session_key = get_lot_scoped_key(full_key, lot_context['lot_index'])
        elif lot_context and lot_context['mode'] == 'general':
            session_key = get_lot_scoped_key(full_key, None)
        else:
            session_key = full_key

        prop_type = prop_details.get("type")

        if prop_type == "object":
            if "$ref" in prop_details:
                # Only show section header if there's an explicit title
                if "title" in prop_details:
                    st.subheader(label)
                
                ref_path = prop_details["$ref"].split('/')[1:]
                ref_props = st.session_state['schema']
                for part in ref_path:
                    ref_props = ref_props[part]
                render_form(ref_props.get("properties", {}), parent_key=full_key, lot_context=lot_context)
            else:
                # Only show section header if there's an explicit title
                if "title" in prop_details:
                    st.subheader(label)
                
                # Keep helpful expandable info for complex sections
                if help_text:
                    if "Pravna podlaga" in label:
                        with st.expander("ℹ️ Prikaži pravne podlage in predpise", expanded=False):
                            st.text(help_text)
                    elif "Tehnične zahteve" in label or "specifikacije" in label:
                        with st.expander("ℹ️ Kaj so tehnične specifikacije?", expanded=False):
                            st.text(help_text)
                    elif "Opozorilo" in label:
                        st.warning(help_text)
                        return  # Don't render form fields for warning objects
                    elif "Informacija" in label and label.startswith("ℹ️"):
                        # Handle information tooltip objects
                        st.info(help_text)
                        # Continue processing other fields in this section
                        
                render_form(prop_details.get("properties", {}), parent_key=full_key, lot_context=lot_context)
        
        elif prop_type == "array":
            # Use smaller header for conditional arrays to reduce visual clutter
            if prop_details.get("render_if"):
                st.markdown(f"**{label}**", help=help_text)
            else:
                st.subheader(label, help=help_text)
            items_schema = prop_details.get("items", {})
            
            # Array of simple enums (multiselect)
            if "enum" in items_schema:
                if session_key not in st.session_state:
                    st.session_state[session_key] = []
                widget_key = f"widget_{session_key}"
                selected_values = st.multiselect(
                    label, 
                    options=items_schema["enum"], 
                    default=st.session_state.get(session_key, []), 
                    key=widget_key, 
                    help=help_text
                )
                
                # Sync widget value back to session state
                if selected_values != st.session_state.get(session_key):
                    st.session_state[session_key] = selected_values
            
            # Array of objects
            elif items_schema.get("type") == "object":
                if session_key not in st.session_state:
                    st.session_state[session_key] = []

                for i in range(len(st.session_state[session_key])):
                    # Create container with header row for remove button
                    container = st.container(border=True)
                    with container:
                        # Add header with remove button
                        col_header, col_remove = st.columns([5, 1])
                        with col_header:
                            item_title = items_schema.get('title', 'element')
                            st.markdown(f"**{item_title} {i + 1}**")
                        with col_remove:
                            if st.button("❌", key=f"widget_remove_{session_key}_{i}", help=f"Odstrani {item_title.lower()} {i + 1}"):
                                st.session_state[session_key].pop(i)
                                st.rerun()
                        
                        # Render the form fields for this object
                        render_form(items_schema.get("properties", {}), parent_key=f"{full_key}.{i}", lot_context=lot_context)
                
                # Add new item with improved UX and correct Slovenian grammar
                item_title = items_schema.get('title', 'element')
                if full_key == "clientInfo.clients" and item_title == "Naročnik":
                    button_text = "➕ Dodaj naročnika"
                elif "cofinancers" in full_key and item_title == "Sofinancer":
                    button_text = "➕ Dodaj novega sofinancerja"
                elif "mixedOrderComponents" in full_key and item_title == "Postavka":
                    button_text = "➕ Dodaj postavko"
                elif full_key == "lots" and item_title == "Sklop":
                    button_text = "➕ Dodaj sklop"
                elif "inspectionDates" in full_key:
                    button_text = "➕ Dodaj nov termin ogleda"
                else:
                    button_text = f"➕ Dodaj {item_title.lower()}"
                
                if st.button(button_text, key=f"widget_add_{session_key}"):
                    st.session_state[session_key].append({})
                    st.rerun()
            
            # Array of strings (like additional legal bases)
            elif items_schema.get("type") == "string":
                if session_key not in st.session_state:
                    st.session_state[session_key] = []

                # Display existing string entries with X buttons
                for i in range(len(st.session_state[session_key])):
                    col_input, col_remove = st.columns([5, 1])
                    
                    with col_input:
                        current_text = st.session_state[session_key][i]
                        widget_key = f"widget_{session_key}_item_{i}"
                        new_text = st.text_input(
                            f"{items_schema.get('title', 'Vnos')} {i + 1}",
                            value=current_text,
                            key=widget_key,
                            placeholder="Vnesite naziv zakona/predpisa"
                        )
                        # Update the value if changed
                        if new_text != current_text:
                            st.session_state[session_key][i] = new_text
                    
                    with col_remove:
                        # Add some vertical spacing to align with input field
                        st.write("")
                        if st.button("❌", key=f"widget_remove_{session_key}_{i}", help="Odstrani to pravno podlago"):
                            st.session_state[session_key].pop(i)
                            st.rerun()

                # Special handling for additional legal bases
                if "additionalLegalBases" in full_key:
                    button_text = "➕ Dodaj pravno podlago"
                else:
                    item_title = items_schema.get('title', 'element').lower()
                    button_text = f"➕ Dodaj {item_title}"
                
                if st.button(button_text, key=f"widget_add_{session_key}"):
                    st.session_state[session_key].append("")
                    st.rerun()

        elif prop_type == "string":
            # Handle readonly section headers
            if prop_details.get("readonly") and prop_name.endswith("_title"):
                st.markdown(f"### {prop_details.get('title', label)}")
                return
            
            # Handle info fields that display selected criteria
            if prop_details.get("format") == "info":
                # Check if we should show the criteria info
                if "selectedCriteriaInfo" in full_key:
                    # Get selected criteria from session state
                    selected_criteria = []
                    criteria_keys = [
                        'selectionCriteria.price',
                        'selectionCriteria.additionalReferences', 
                        'selectionCriteria.additionalTechnicalRequirements',
                        'selectionCriteria.shorterDeadline',
                        'selectionCriteria.longerWarranty',
                        'selectionCriteria.costEfficiency',
                        'selectionCriteria.socialCriteria',
                        'selectionCriteria.otherCriteriaCustom',
                        'selectionCriteria.otherCriteriaAI'
                    ]
                    criteria_labels = {
                        'selectionCriteria.price': 'Cena',
                        'selectionCriteria.additionalReferences': 'Dodatne reference imenovanega kadra',
                        'selectionCriteria.additionalTechnicalRequirements': 'Dodatne tehnične zahteve',
                        'selectionCriteria.shorterDeadline': 'Krajši rok izvedbe',
                        'selectionCriteria.longerWarranty': 'Garancija daljša od zahtevane',
                        'selectionCriteria.costEfficiency': 'Stroškovna učinkovitost',
                        'selectionCriteria.socialCriteria': 'Socialna merila',
                        'selectionCriteria.otherCriteriaCustom': 'Drugo (lasten predlog)',
                        'selectionCriteria.otherCriteriaAI': 'Drugo (AI predlog)'
                    }
                    
                    for key in criteria_keys:
                        if st.session_state.get(key):
                            selected_criteria.append(criteria_labels.get(key, key))
                    
                    if selected_criteria:
                        st.info(f"ℹ️ Pri odpiranju konkurence bodo uporabljena naslednja merila: **{', '.join(selected_criteria)}**")
                    else:
                        st.warning("⚠️ Niste izbrali nobenih meril v prejšnji točki. Pri odpiranju konkurence morate imeti definirana merila.")
                return
            
            # Add required indicator to label
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Check if this field should be rendered as radio buttons (for contractInfo type selection)
            use_radio = False
            if ("contractInfo.type" in full_key or 
                "contractInfo.contractPeriodType" in full_key or
                "contractInfo.canBeExtended" in full_key):
                use_radio = True
            
            if "enum" in prop_details and use_radio:
                # Radio button rendering for mutually exclusive choices
                available_options = prop_details["enum"].copy()
                
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    st.session_state[session_key] = raw_default if raw_default in available_options else available_options[0] if prop_details.get("default") else ""
                
                # Use a separate widget key
                widget_key = f"widget_{session_key}"
                
                # Create radio buttons
                selected_value = st.radio(
                    display_label,
                    options=available_options,
                    index=available_options.index(st.session_state[session_key]) if st.session_state[session_key] in available_options else 0,
                    key=widget_key,
                    help=help_text,
                    horizontal=True if len(available_options) <= 2 else False
                )
                
                # Sync widget value back to session state
                if selected_value != st.session_state.get(session_key):
                    st.session_state[session_key] = selected_value
                    
            elif "enum" in prop_details:
                # Handle dynamic filtering for mixed order component types
                available_options = prop_details["enum"].copy()
                
                # Filter out already selected types in mixed order components
                if (prop_name == "type" and 
                    "mixedOrderComponents" in full_key and 
                    prop_details["enum"] == ["blago", "storitve", "gradnje"]):
                    
                    # Get the parent array key - FIXED: extract correctly
                    # full_key format: "orderType.mixedOrderComponents.0.type" 
                    # we want: "orderType.mixedOrderComponents"
                    key_parts = full_key.split('.')
                    if len(key_parts) >= 3 and key_parts[-1] == "type" and key_parts[-2].isdigit():
                        parent_array_key = '.'.join(key_parts[:-2])  # Remove index and "type"
                        current_index = int(key_parts[-2])  # Extract the index
                    else:
                        return  # Invalid key format, skip filtering
                    
                    current_components = st.session_state.get(parent_array_key, [])
                    
                    # Get already selected types (exclude current component being edited)
                    selected_types = []
                    for i, component in enumerate(current_components):
                        if i != current_index and isinstance(component, dict) and 'type' in component:
                            selected_types.append(component['type'])
                    
                    # Filter out already selected types
                    available_options = [opt for opt in available_options if opt not in selected_types]
                    
                    # Show info if no options are available (all types selected)
                    if not available_options:
                        st.info("ℹ️ Vse vrste naročil (blago, storitve, gradnje) so že izbrane v drugih postavkah.")
                        return  # Skip rendering the selectbox
                
                # Enhanced selectbox with proper placeholder and filtered options
                # This section is actually not needed anymore since we handle options differently
                # Remove this entire legacy logic block
                
                # Special handling for "vseeno" auto-selection in procedure field
                                                # Enhanced selectbox with proper placeholder and filtered options
                enum_options = available_options
                
                # Initialize the session state if it doesn't exist - BUT PRESERVE EXISTING VALUES
                if session_key not in st.session_state:
                    st.session_state[session_key] = raw_default if raw_default in enum_options else ""
                
                # Calculate index based on current session state value, not current_value
                index = None
                session_value = st.session_state[session_key]
                if session_value and session_value in enum_options:
                    index = enum_options.index(session_value)

                # Use a separate widget key to avoid Streamlit cleaning up our session state
                widget_key = f"widget_{session_key}"
                
                # Special handling for "vseeno" auto-selection in procedure field
                selected_value = st.selectbox(
                    display_label, 
                    options=enum_options, 
                    index=index,
                    key=widget_key,  # Use separate widget key
                    help=help_text,
                    placeholder=get_text("select_option")
                )
                
                # Manually sync the widget value back to our persistent session state
                if selected_value != st.session_state.get(session_key):
                    st.session_state[session_key] = selected_value
                
                # Auto-selection logic for "vseeno" in procedure field - fixed to handle all cases
                # Use the persistent session state value, not the widget value
                persistent_value = st.session_state.get(session_key, "")
                
                if (prop_name == "procedure" and 
                    "submissionProcedure" in full_key):
                    
                    # Use session state to track user interaction
                    user_clicked_key = f"{session_key}_user_clicked_vseeno"
                    previous_value_key = f"{session_key}_previous_value"
                    navigation_key = f"{session_key}_navigation_flag"
                    
                    # Get previous values
                    previous_value = st.session_state.get(previous_value_key, "")
                    is_navigation = st.session_state.get(navigation_key, False)
                    
                    # Check if user actively selected "vseeno" (not during navigation)
                    user_actively_selected = (
                        persistent_value == "vseeno" and 
                        previous_value != "" and 
                        previous_value != "vseeno" and 
                        not is_navigation  # Don't trigger during navigation
                    )
                    
                    # If user actively clicked "vseeno", trigger auto-selection
                    if user_actively_selected and not st.session_state.get(user_clicked_key, False):
                        st.session_state[session_key] = "odprti postopek"
                        st.session_state[user_clicked_key] = True  # Mark that user interaction occurred
                        st.info("ℹ️ Ker ste izbrali 'vseeno', smo avtomatsko nastavili 'odprti postopek', ki je najčešji in priporočeni postopek za večino javnih naročil.")
                        st.rerun()
                    
                    # Store current value for next comparison and clear navigation flag
                    st.session_state[previous_value_key] = persistent_value
                    st.session_state[navigation_key] = False  # Clear navigation flag after processing
                
                # Reset tracking flags if user manually selects something else
                if (prop_name == "procedure" and 
                    "submissionProcedure" in full_key and 
                    persistent_value not in ["vseeno", ""]):
                    user_clicked_key = f"{session_key}_user_clicked_vseeno"
                    previous_value_key = f"{session_key}_previous_value"
                    navigation_key = f"{session_key}_navigation_flag"
                    st.session_state[user_clicked_key] = False
                    st.session_state[previous_value_key] = persistent_value
                    st.session_state[navigation_key] = False
            elif prop_details.get("format") == "textarea":
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    st.session_state[session_key] = raw_default
                
                # Enhanced textarea with separate widget key
                widget_key = f"widget_{session_key}"
                textarea_value = st.text_area(
                    display_label, 
                    value=st.session_state[session_key], 
                    key=widget_key, 
                    help=help_text,
                    placeholder=get_text("enter_text"),
                    height=100
                )
                
                # Sync widget value back to session state
                if textarea_value != st.session_state.get(session_key):
                    st.session_state[session_key] = textarea_value
            elif prop_details.get("format") == "cpv" or "cpv" in prop_name.lower():
                # CPV code selector component
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    st.session_state[session_key] = raw_default
                
                # Render CPV selector
                cpv_value = render_cpv_selector(
                    field_key=f"widget_{session_key}",
                    field_schema=prop_details,
                    current_value=st.session_state[session_key],
                    disabled=False
                )
                
                # Sync value back to session state
                if cpv_value != st.session_state.get(session_key):
                    st.session_state[session_key] = cpv_value
            elif prop_details.get("format") == "file":
                # Enhanced file uploader
                st.file_uploader(
                    display_label, 
                    key=session_key, 
                    help=help_text,
                    type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
                )
            elif prop_details.get("format") == "date":
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    default_date = raw_default if raw_default else date.today()
                    st.session_state[session_key] = default_date
                
                # Enhanced date input with separate widget key
                widget_key = f"widget_{session_key}"
                date_value = st.date_input(
                    display_label, 
                    value=st.session_state[session_key], 
                    key=widget_key, 
                    help=help_text,
                    format="DD.MM.YYYY"
                )
                
                # Sync widget value back to session state
                if date_value != st.session_state.get(session_key):
                    st.session_state[session_key] = date_value
            else:
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    st.session_state[session_key] = raw_default
                
                # Enhanced text input with separate widget key
                widget_key = f"widget_{session_key}"
                text_value = st.text_input(
                    display_label, 
                    value=st.session_state[session_key], 
                    key=widget_key, 
                    help=help_text,
                    placeholder=get_text("enter_text")
                )
                
                # Sync widget value back to session state
                if text_value != st.session_state.get(session_key):
                    st.session_state[session_key] = text_value
                
                # Validation for framework agreement duration (4 year limit)
                if "frameworkDuration" in full_key and text_value:
                    # Try to parse the duration and check if it exceeds 4 years
                    try:
                        # Simple check for common patterns
                        if "let" in text_value.lower():
                            # Extract number before "let"
                            import re
                            numbers = re.findall(r'(\d+)', text_value)
                            if numbers:
                                years = int(numbers[0])
                                if years > 4:
                                    st.error("⚠️ Okvirni sporazum ne sme presegati 4 let!")
                        elif "mesec" in text_value.lower():
                            # Extract number before "mesec"
                            import re
                            numbers = re.findall(r'(\d+)', text_value)
                            if numbers:
                                months = int(numbers[0])
                                if months > 48:
                                    st.error("⚠️ Okvirni sporazum ne sme presegati 4 let (48 mesecev)!")
                    except:
                        pass  # If parsing fails, don't show error

        elif prop_type == "number":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Initialize session state if it doesn't exist
            if session_key not in st.session_state:
                if isinstance(raw_default, (int, float)):
                    st.session_state[session_key] = float(raw_default)
                elif isinstance(raw_default, str) and raw_default:
                    try:
                        st.session_state[session_key] = float(raw_default)
                    except ValueError:
                        st.session_state[session_key] = 0.0
                else:
                    st.session_state[session_key] = 0.0
            
            # Use text input styled as number to remove spinner
            current_str = str(st.session_state[session_key]) if st.session_state[session_key] != 0.0 else ""
            widget_key = f"widget_{session_key}_text"
            number_text = st.text_input(
                display_label, 
                value=current_str, 
                key=widget_key,
                help=help_text,
                placeholder="0.00"
            )
            
            # Convert back to number and store in session state
            try:
                if number_text.strip():
                    number_value = float(number_text.replace(',', '.'))  # Handle both comma and dot
                else:
                    number_value = 0.0
                st.session_state[session_key] = number_value
            except ValueError:
                st.warning(f"'{number_text}' ni veljavna številka")
                st.session_state[session_key] = 0.0

        elif prop_type == "integer":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Initialize session state if it doesn't exist
            if session_key not in st.session_state:
                if isinstance(raw_default, int):
                    st.session_state[session_key] = raw_default
                elif isinstance(raw_default, str) and raw_default:
                    try:
                        st.session_state[session_key] = int(raw_default)
                    except ValueError:
                        st.session_state[session_key] = 0
                else:
                    st.session_state[session_key] = 0
            
            # Get minimum value constraint if specified
            minimum = prop_details.get("minimum", 1)
            
            # Use text input for integers to avoid spinner
            current_str = str(st.session_state[session_key]) if st.session_state[session_key] != 0 else ""
            widget_key = f"widget_{session_key}_text"
            integer_text = st.text_input(
                display_label, 
                value=current_str, 
                key=widget_key,
                help=help_text,
                placeholder=f"Vnesite celo število (min. {minimum})"
            )
            
            # Convert back to integer and validate constraints
            try:
                if integer_text.strip():
                    integer_value = int(integer_text)
                    if integer_value < minimum:
                        st.warning(f"Vrednost mora biti najmanj {minimum}")
                        st.session_state[session_key] = minimum
                    else:
                        st.session_state[session_key] = integer_value
                else:
                    st.session_state[session_key] = 0
            except ValueError:
                st.warning(f"'{integer_text}' ni veljavno celo število")
                st.session_state[session_key] = 0

        elif prop_type == "boolean":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Initialize session state if it doesn't exist
            if session_key not in st.session_state:
                # Ensure boolean conversion for raw_default
                if isinstance(raw_default, bool):
                    st.session_state[session_key] = raw_default
                elif isinstance(raw_default, str):
                    st.session_state[session_key] = raw_default.lower() in ('true', '1', 'yes')
                else:
                    st.session_state[session_key] = False
            
            widget_key = f"widget_{session_key}"
            checkbox_value = st.checkbox(display_label, value=st.session_state[session_key], key=widget_key, help=help_text)
            
            # Sync widget value back to session state
            if checkbox_value != st.session_state.get(session_key):
                st.session_state[session_key] = checkbox_value
            
            # Special handling for wantsLogo to provide user feedback
            if prop_name == "wantsLogo" and checkbox_value != raw_default:
                if checkbox_value:
                    st.success("✅ Polje za nalaganje logotipov je sedaj na voljo spodaj.")
                else:
                    st.info("ℹ️ Polje za nalaganje logotipov je skrito, ker niste izbrali te možnosti.")
