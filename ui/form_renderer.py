
"""Enhanced form rendering components with localization and improved UX."""
import streamlit as st
from datetime import date
from typing import List, Dict
from localization import get_text, get_validation_message
from utils.lot_utils import get_lot_scoped_key, render_lot_context_step
from ui.components.cpv_selector import render_cpv_selector
# Story 27.3: Removed direct criteria_validation imports - now using centralized ValidationManager
from utils.criteria_validation import get_validation_summary  # Still needed for render_validation_summary
from utils.criteria_suggestions import (
    get_suggested_criteria_for_cpv,
    get_criteria_help_text,
    get_criteria_display_names
)
# Story 003: Field Type Enhancements
from utils.field_types import FieldTypeManager, RealTimeValidator
from utils.ui_components import render_field_with_validation


def format_number_with_dots(value):
    """Format number with dots as thousand separators (Story 3.0.3)."""
    if value is None or value == "":
        return ""
    try:
        # Handle both int and float values
        num_value = float(value)
        if num_value == int(num_value):
            # No decimals
            return f"{int(num_value):,}".replace(",", ".")
        else:
            # Format with 2 decimals, then replace separators
            formatted = f"{num_value:,.2f}"
            # First replace commas (thousands) with dots
            formatted = formatted.replace(",", ".")
            # The decimal point stays as is
            return formatted
    except (ValueError, TypeError):
        return str(value)


def parse_formatted_number(formatted_str):
    """Parse formatted number back to float (Story 3.0.3)."""
    if not formatted_str:
        return 0
    try:
        # Count dots to determine if last one is decimal separator
        dot_count = formatted_str.count(".")
        if dot_count > 0:
            # Split by dots
            parts = formatted_str.split(".")
            if len(parts) > 1 and len(parts[-1]) <= 2:
                # Last part likely decimals if 2 digits or less
                integer_part = "".join(parts[:-1])
                decimal_part = parts[-1]
                cleaned = f"{integer_part}.{decimal_part}"
            else:
                # All dots are thousand separators
                cleaned = formatted_str.replace(".", "")
        else:
            cleaned = formatted_str
        
        return float(cleaned)
    except (ValueError, TypeError):
        return 0


def get_social_criteria_specific_labels(criteria_prefix="selectionCriteria"):
    """Get specific labels for selected social criteria sub-options."""
    social_options = {
        'youngEmployeesShare': 'Delež zaposlenih mladih',
        'elderlyEmployeesShare': 'Delež zaposlenih starejših',
        'registeredStaffEmployed': 'Priglašeni kader je zaposlen pri ponudniku',
        'averageSalary': 'Povprečna plača priglašenega kadra',
        'otherSocial': 'Drugo',
        'otherSocialCustom': 'Drugo, imam predlog',
        'otherSocialAI': 'Drugo, prosim predlog AI'
    }
    
    selected = []
    for key, label in social_options.items():
        if st.session_state.get(f"{criteria_prefix}.socialCriteriaOptions.{key}", False):
            selected.append(f"Socialna merila - {label}")
    
    return selected


def get_selected_criteria_labels(parent_key="", lot_context=None):
    """Get labels of currently selected criteria for the tiebreaker dropdown."""
    criteria_mapping = {
        'price': 'Cena',
        'additionalReferences': 'Dodatne reference imenovanega kadra',
        'additionalTechnicalRequirements': 'Dodatne tehnične zahteve',
        'shorterDeadline': 'Krajši rok izvedbe',
        'longerWarranty': 'Garancija daljša od zahtevane',
        'costEfficiency': 'Stroškovna učinkovitost',
        'otherCriteriaCustom': 'Drugo merilo (ne-socialno)'
    }
    
    selected_labels = []
    
    # Determine the correct prefix for the criteria
    if lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
        criteria_prefix = get_lot_scoped_key("selectionCriteria", lot_context['lot_index'])
    elif lot_context and lot_context['mode'] == 'general':
        criteria_prefix = get_lot_scoped_key("selectionCriteria", None)
    else:
        criteria_prefix = "selectionCriteria"
    
    # Check each criterion
    for criterion_key, label in criteria_mapping.items():
        session_key = f"{criteria_prefix}.{criterion_key}"
        if st.session_state.get(session_key, False):
            selected_labels.append(label)
    
    # Add specific social criteria labels instead of generic one
    if st.session_state.get(f"{criteria_prefix}.socialCriteria", False):
        social_labels = get_social_criteria_specific_labels(criteria_prefix)
        if social_labels:
            selected_labels.extend(social_labels)
        else:
            # If no specific social criteria selected, still show generic
            selected_labels.append('Socialna merila')
    
    return selected_labels


def render_competition_criteria_info(parent_key="contractInfo", lot_context=None):
    """Display selected criteria for framework agreements with competition reopening."""
    framework_type = st.session_state.get(f"{parent_key}.frameworkAgreementType", "")
    
    # Check if competition reopening is selected
    competition_types = ["en_z_konkurenco", "vec_z_konkurenco", "vec_deloma"]
    
    if framework_type in competition_types:
        # Get selected criteria using existing function
        selected_criteria = get_selected_criteria_labels(lot_context=lot_context)
        
        if selected_criteria:
            criteria_text = ", ".join(selected_criteria)
            st.info(f"ℹ **Pri odpiranju konkurence bodo uporabljena naslednja merila:**\n{criteria_text}")
        else:
            st.warning(" Niste izbrali nobenih meril. Pri odpiranju konkurence morate imeti definirana merila.")


def display_criteria_ratios_total(parent_key="", lot_context=None):
    """Display running total of criteria ratio points."""
    total = 0
    
    # Determine the correct prefix
    if lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
        criteria_prefix = get_lot_scoped_key("selectionCriteria", lot_context['lot_index'])
    elif lot_context and lot_context['mode'] == 'general':
        criteria_prefix = get_lot_scoped_key("selectionCriteria", None)
    else:
        criteria_prefix = "selectionCriteria"
    
    # Mapping of criteria to their ratio fields
    criteria_mapping = {
        'price': 'priceRatio',
        'additionalReferences': 'additionalReferencesRatio',
        'additionalTechnicalRequirements': 'additionalTechnicalRequirementsRatio',
        'shorterDeadline': 'shorterDeadlineRatio',
        'longerWarranty': 'longerWarrantyRatio',
        'costEfficiency': 'costEfficiencyRatio',
        'otherCriteriaCustom': 'otherCriteriaCustomRatio',
        'otherCriteriaAI': 'otherCriteriaAIRatio'
    }
    
    # Social criteria specific mapping
    social_mapping = {
        'socialCriteriaOptions.youngEmployeesShare': 'socialCriteriaYoungRatio',
        'socialCriteriaOptions.elderlyEmployeesShare': 'socialCriteriaElderlyRatio',
        'socialCriteriaOptions.registeredStaffEmployed': 'socialCriteriaStaffRatio',
        'socialCriteriaOptions.averageSalary': 'socialCriteriaSalaryRatio',
        'socialCriteriaOptions.otherSocial': 'socialCriteriaOtherRatio'
    }
    
    # Sum up the ratio points for selected criteria
    for criterion, ratio_field in criteria_mapping.items():
        criterion_key = f"{criteria_prefix}.{criterion}"
        ratio_key = f"{criteria_prefix}.{ratio_field}"
        
        if st.session_state.get(criterion_key, False):
            points = st.session_state.get(ratio_key, 0)
            if points:
                total += points
    
    # Sum up the social criteria ratio points
    for social_criterion, ratio_field in social_mapping.items():
        criterion_key = f"{criteria_prefix}.{social_criterion}"
        ratio_key = f"{criteria_prefix}.{ratio_field}"
        
        if st.session_state.get(criterion_key, False):
            points = st.session_state.get(ratio_key, 0)
            if points:
                total += points
    
    # Display total if greater than 0
    if total > 0:
        st.info(f" **Skupaj točk razmerij:** {total}")
    
    return total


def _get_default_value(full_key, prop_details, lot_context=None):
    """Get appropriate default value for form field."""
    # Apply lot scoping if context is provided, but respect global fields
    # Global fields are those that are shared across all lots
    global_fields = ['clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 
                    'lotsInfo', 'lots', 'lotConfiguration']
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
        # Global fields are those that are shared across all lots
        global_fields = ['clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 
                        'lotsInfo', 'lots', 'lotConfiguration']
        is_global_field = any(condition_field.startswith(gf) for gf in global_fields)
        
        # Special handling: If parent_key already contains lot prefix (e.g., lot_0.executionDeadline)
        # and condition_field is relative to parent (e.g., executionDeadline.type),
        # we need to build the correct path
        if parent_key and parent_key.startswith('lot_') and '.' in parent_key:
            # Extract lot prefix from parent_key (e.g., lot_0 from lot_0.executionDeadline)
            lot_prefix = parent_key.split('.')[0]
            # Build the full condition field path
            if '.' not in condition_field or not condition_field.startswith(lot_prefix):
                # Only add lot prefix if not already present
                actual_session_key = f"{lot_prefix}.{condition_field}"
            else:
                actual_session_key = condition_field
            current_field_value = st.session_state.get(actual_session_key)
        elif is_global_field:
            actual_session_key = condition_field
            current_field_value = st.session_state.get(actual_session_key)
        elif session_key_prefix:
            # If we have a session key prefix (from lot scoping), use it
            actual_session_key = f"{session_key_prefix}.{condition_field}"
            current_field_value = st.session_state.get(actual_session_key)
        elif lot_context and lot_context['mode'] == 'lots' and lot_context['lot_index'] is not None:
            # Try multiple possible key formats due to double-prefixing issues
            lot_index = lot_context['lot_index']
            possible_keys = [
                # Double-prefixed format (what form renderer creates)
                # e.g., technicalSpecifications.hasSpecifications -> lot_0.lot_0_technicalSpecifications.hasSpecifications
                f"lot_{lot_index}.lot_{lot_index}_{condition_field.replace('.', '.')}",
                # Normal lot-scoped format
                get_lot_scoped_key(condition_field, lot_index),
                # Fallback to original field
                condition_field
            ]
            # Try each key format until we find one that exists
            current_field_value = None
            for key in possible_keys:
                if key in st.session_state:
                    current_field_value = st.session_state.get(key)
                    actual_session_key = key
                    break
            else:
                # If no key found, use the normal scoped key
                actual_session_key = get_lot_scoped_key(condition_field, lot_index)
                current_field_value = st.session_state.get(actual_session_key)
        elif lot_context and lot_context['mode'] == 'general':
            actual_session_key = get_lot_scoped_key(condition_field, None)
            current_field_value = st.session_state.get(actual_session_key)
        else:
            actual_session_key = condition_field
            current_field_value = st.session_state.get(actual_session_key)
    else:
        current_field_value = None
    
    # Handle 'value' condition (exact match)
    if condition_value is not None and condition_field:
        # Debug logging for contractInfo fields
        if "contractInfo" in condition_field:
            import logging
            logging.info(f"[render_if debug] Checking condition: {condition_field} == {condition_value}")
            logging.info(f"[render_if debug] Actual session key used: {actual_session_key}")
            logging.info(f"[render_if debug] Actual value in session: {current_field_value}")
            logging.info(f"[render_if debug] Parent key: {parent_key}")
            logging.info(f"[render_if debug] Result: {current_field_value == condition_value}")
        
        # CRITICAL FIX: For contractInfo fields in lot context, 
        # the condition_field in schema is "contractInfo.type" but 
        # actual session key might be "lot_0.contractInfo.type"
        # We need to check if we're comparing the right values
        if "contractInfo" in str(condition_field) and parent_key and parent_key.startswith("lot_"):
            # Extract just the field part without lot prefix for comparison
            field_parts = condition_field.split('.')
            if len(field_parts) >= 2:
                # Get the actual value from the lot-prefixed key
                lot_prefix = parent_key.split('.')[0]  # e.g., "lot_0"
                corrected_key = f"{lot_prefix}.{condition_field}"
                actual_value = st.session_state.get(corrected_key, current_field_value)
                if actual_value != current_field_value:
                    import logging
                    logging.info(f"[render_if debug] Using corrected value from {corrected_key}: {actual_value}")
                    current_field_value = actual_value
        
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

def render_form(schema_properties, parent_key="", lot_context=None, field_manager=None, real_time_validator=None):
    """Recursively render form fields based on JSON schema properties.
    
    Args:
        schema_properties: Schema properties to render
        parent_key: Parent key for nested fields
        lot_context: Lot context information (from get_current_lot_context)
        field_manager: FieldTypeManager instance for enhanced field rendering
        real_time_validator: RealTimeValidator instance for field validation
    """
    # Initialize field manager if not provided
    if field_manager is None:
        field_manager = FieldTypeManager()
    
    # Initialize real-time validator if not provided
    if real_time_validator is None:
        from utils.validations import ValidationManager
        validation_manager = ValidationManager(
            st.session_state.get('schema', {}),
            st.session_state
        )
        real_time_validator = RealTimeValidator(validation_manager)
    # Debug: Show what we're rendering when contractInfo is involved
    if parent_key == '' and 'contractInfo' in schema_properties:
        with st.expander(" Debug: render_form input", expanded=False):
            st.write(f"**Parent key:** '{parent_key}'")
            st.write(f"**Schema properties keys:** {list(schema_properties.keys())}")
            if 'contractInfo' in schema_properties:
                contract_info = schema_properties['contractInfo']
                st.write(f"**contractInfo type:** {contract_info.get('type', 'N/A')}")
                if 'properties' in contract_info:
                    st.write(f"**contractInfo has properties:** {len(contract_info['properties'])}")
                else:
                    st.write("**contractInfo has NO properties key!**")
    
    for prop_name, prop_details in schema_properties.items():
        if not _should_render(prop_details, parent_key, lot_context):
            continue

        full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
        
        # Handle lot context steps
        if full_key.startswith('lot_context_'):
            lot_index = int(full_key.split('_')[2])
            render_lot_context_step(lot_index)
            continue
        
        # Handle lot configuration step (new - only collects lot names)
        if full_key == 'lotConfiguration':
            from utils.lot_configuration_renderer import render_lot_configuration
            render_lot_configuration()
            continue
            
        label = prop_details.get("title", prop_name)
        help_text = prop_details.get("description")
        # Get raw default from schema (don't use complex _get_default_value logic)
        raw_default = prop_details.get("default", "")
        
        # Create the session state key (scoped for lots)
        # Some fields should never be lot-scoped as they control global form behavior
        # Global fields are those that are shared across all lots
        global_fields = ['clientInfo', 'projectInfo', 'legalBasis', 'submissionProcedure', 
                        'lotsInfo', 'lots', 'lotConfiguration']
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
                render_form(ref_props.get("properties", {}), parent_key=full_key, lot_context=lot_context, field_manager=field_manager, real_time_validator=real_time_validator)
            else:
                # Only show section header if there's an explicit title
                if "title" in prop_details:
                    st.subheader(label)
                
                # Keep helpful expandable info for complex sections
                if help_text:
                    if "Pravna podlaga" in label:
                        with st.expander("ℹ Prikaži pravne podlage in predpise", expanded=False):
                            st.text(help_text)
                    elif "Tehnične zahteve" in label or "specifikacije" in label:
                        with st.expander("ℹ Kaj so tehnične specifikacije?", expanded=False):
                            st.text(help_text)
                    elif "Opozorilo" in label:
                        st.warning(help_text)
                        return  # Don't render form fields for warning objects
                    elif "Informacija" in label and label.startswith("ℹ"):
                        # Handle information tooltip objects
                        st.info(help_text)
                        # Continue processing other fields in this section
                
                # Add special indentation for socialCriteriaOptions to show hierarchy
                if prop_name == "socialCriteriaOptions":
                    # Use columns to create indentation effect
                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        # Empty column for spacing
                        st.write("")
                    with col2:
                        # Render social sub-options in the indented column
                        render_form(prop_details.get("properties", {}), parent_key=full_key, lot_context=lot_context, field_manager=field_manager, real_time_validator=real_time_validator)
                else:
                    render_form(prop_details.get("properties", {}), parent_key=full_key, lot_context=lot_context, field_manager=field_manager, real_time_validator=real_time_validator)
                
                # Add validation and ratio totals ONLY for the main selectionCriteria section
                # Not for nested objects like socialCriteriaOptions or ratiosHeader
                if full_key == "selectionCriteria" or full_key.endswith(".selectionCriteria"):
                    render_criteria_validation(full_key, lot_context)
                    # Display ratio totals after all ratio fields
                    display_criteria_ratios_total(full_key, lot_context)
        
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
                # Debug: Check what's in session state for clients
                if 'clients' in session_key:
                    import logging
                    logging.info(f"[form_renderer] Rendering {session_key}, current value: {st.session_state.get(session_key, 'NOT FOUND')}")
                
                # Initialize array only if it doesn't exist
                # This preserves existing data when navigating back
                if session_key not in st.session_state:
                    st.session_state[session_key] = []
                    if 'clients' in session_key:
                        import logging
                        logging.info(f"[form_renderer] Initialized empty array for {session_key}")

                for i in range(len(st.session_state[session_key])):
                    # Create container with header row for remove button
                    container = st.container(border=True)
                    with container:
                        # Add header with remove button
                        col_header, col_remove = st.columns([5, 1])
                        with col_header:
                            item_title = items_schema.get('title', 'element')
                            
                            # Try to get a meaningful name from the item data
                            display_name = None
                            
                            # For clients - use name field
                            if 'clients' in session_key:
                                name_key = f"{session_key}.{i}.name"
                                display_name = st.session_state.get(name_key, '')
                                if display_name:
                                    display_name = f"{display_name}"
                                else:
                                    display_name = f"{item_title} {i + 1} (brez imena)"
                            
                            # For cofinancers - use name field
                            elif 'cofinancers' in session_key:
                                name_key = f"{session_key}.{i}.name"
                                display_name = st.session_state.get(name_key, '')
                                if display_name:
                                    # Also show percentage if available
                                    percentage_key = f"{session_key}.{i}.percentage"
                                    percentage = st.session_state.get(percentage_key, '')
                                    if percentage:
                                        display_name = f"{display_name} ({percentage}%)"
                                    else:
                                        display_name = f"{display_name}"
                                else:
                                    display_name = f"{item_title} {i + 1} (brez imena)"
                            
                            # For lots - use name field
                            elif session_key == 'lots':
                                name_key = f"{session_key}.{i}.name"
                                display_name = st.session_state.get(name_key, '')
                                if display_name:
                                    display_name = f"{display_name}"
                                else:
                                    display_name = f"Sklop {i + 1}"
                            
                            # For inspection dates - use date and time
                            elif 'inspectionDates' in session_key:
                                date_key = f"{session_key}.{i}.date"
                                time_key = f"{session_key}.{i}.time"
                                date = st.session_state.get(date_key, '')
                                time = st.session_state.get(time_key, '')
                                if date:
                                    if time:
                                        display_name = f"Ogled: {date} ob {time}"
                                    else:
                                        display_name = f"Ogled: {date}"
                                else:
                                    display_name = f"Termin ogleda {i + 1}"
                            
                            # For specification documents - use filename
                            elif 'specificationDocuments' in session_key:
                                filename_key = f"{session_key}.{i}.filename"
                                filename = st.session_state.get(filename_key, '')
                                if filename:
                                    display_name = f"Dokument: {filename}"
                                else:
                                    display_name = f"Dokument {i + 1}"
                            
                            # For mixed order components - use description
                            elif 'mixedOrderComponents' in session_key:
                                desc_key = f"{session_key}.{i}.description"
                                description = st.session_state.get(desc_key, '')
                                if description:
                                    # Truncate if too long
                                    if len(description) > 50:
                                        display_name = f"{description[:47]}..."
                                    else:
                                        display_name = description
                                else:
                                    display_name = f"Postavka {i + 1}"
                            
                            # Default fallback
                            if not display_name:
                                display_name = f"{item_title} {i + 1}"
                            
                            st.markdown(f"**{display_name}**")
                        with col_remove:
                            if st.button("", key=f"widget_remove_{session_key}_{i}", help=f"Odstrani"):
                                # Remove the item and ensure state is preserved
                                st.session_state[session_key].pop(i)
                                # Mark that we've made changes
                                st.session_state['unsaved_changes'] = True
                                st.rerun()
                        
                        # Render the form fields for this object
                        render_form(items_schema.get("properties", {}), parent_key=f"{full_key}.{i}", lot_context=lot_context, field_manager=field_manager, real_time_validator=real_time_validator)
                
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
                elif "specificationDocuments" in full_key:
                    button_text = "➕ Dodaj dokument s tehničnimi zahtevami"
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
                        if st.button("", key=f"widget_remove_{session_key}_{i}", help="Odstrani to pravno podlago"):
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
                continue
            
            # Handle info fields that display selected criteria
            if prop_details.get("format") == "info":
                # Check if we should show the criteria info
                if "selectedCriteriaInfo" in full_key:
                    # Call the dynamic criteria display function
                    render_competition_criteria_info(parent_key, lot_context)
                continue
            
            # Add required indicator to label
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Check if this field should be rendered as radio buttons
            use_radio = False
            if ("contractInfo.type" in full_key or 
                "contractInfo.contractPeriodType" in full_key or
                "contractInfo.canBeExtended" in full_key or
                "selectionCriteria.tiebreakerRule" in full_key or
                prop_details.get("format") == "radio"):
                use_radio = True
            
            if "enum" in prop_details and use_radio:
                # Radio button rendering for mutually exclusive choices
                available_options = prop_details["enum"].copy()
                
                # Special labels for tiebreaker rule
                if "tiebreakerRule" in full_key:
                    display_options = {
                        "žreb": "V primeru, da imata dve popolni in samostojni ponudbi enako končno skupno ponudbeno vrednost, bo naročnik med njima izbral ponudbo izbranega ponudnika z žrebom.",
                        "prednost po merilu": "V primeru, da imata dve popolni in samostojni ponudbi enako končno skupno ponudbeno vrednost, bo naročnik med njima izbral ponudbo izbranega ponudnika, ki je pri merilu prejela višje število točk."
                    }
                elif "enumLabels" in prop_details:
                    # Use enumLabels from schema if provided
                    display_options = prop_details["enumLabels"]
                else:
                    display_options = {opt: opt for opt in available_options}
                
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    if raw_default and raw_default in available_options:
                        st.session_state[session_key] = raw_default
                    elif available_options:
                        st.session_state[session_key] = available_options[0]
                    else:
                        st.session_state[session_key] = ""
                
                # Use a separate widget key
                widget_key = f"widget_{session_key}"
                
                # Create radio buttons
                if "tiebreakerRule" in full_key or "enumLabels" in prop_details:
                    # Use special display for fields with custom labels
                    selected_value = st.radio(
                        display_label,
                        options=available_options,
                        format_func=lambda x: display_options.get(x, x),
                        index=available_options.index(st.session_state[session_key]) if st.session_state[session_key] in available_options else 0,
                        key=widget_key,
                        help=help_text,
                        horizontal=False  # Always vertical for long text
                    )
                else:
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
                    old_value = st.session_state.get(session_key)
                    st.session_state[session_key] = selected_value
                    
                    # Clear dependent fields when contractInfo.type changes
                    if "contractInfo.type" in session_key or session_key.endswith(".contractInfo.type"):
                        # Clear fields that depend on contractInfo.type
                        prefix = session_key.replace(".type", "")
                        
                        # If switching away from "pogodba", clear contract-specific fields
                        if old_value == "pogodba" and selected_value != "pogodba":
                            fields_to_clear = [
                                f"{prefix}.contractPeriodType",
                                f"{prefix}.contractValidity",
                                f"{prefix}.contractDateFrom",
                                f"{prefix}.contractDateTo"
                            ]
                            for field in fields_to_clear:
                                if field in st.session_state:
                                    del st.session_state[field]
                                    import logging
                                    logging.info(f"[contractInfo] Cleared {field} after type change from pogodba")
                        
                        # If switching away from "okvirni sporazum", clear framework-specific fields  
                        if old_value == "okvirni sporazum" and selected_value != "okvirni sporazum":
                            fields_to_clear = [
                                f"{prefix}.frameworkAgreementType",
                                f"{prefix}.frameworkDuration"
                            ]
                            for field in fields_to_clear:
                                if field in st.session_state:
                                    del st.session_state[field]
                                    import logging
                                    logging.info(f"[contractInfo] Cleared {field} after type change from okvirni sporazum")
                    
                    # Clear dependent fields when contractPeriodType changes
                    if "contractPeriodType" in session_key:
                        prefix = session_key.replace(".contractPeriodType", "")
                        
                        # If switching away from "z veljavnostjo", clear validity field
                        if old_value == "z veljavnostjo" and selected_value != "z veljavnostjo":
                            field_to_clear = f"{prefix}.contractValidity"
                            if field_to_clear in st.session_state:
                                del st.session_state[field_to_clear]
                                import logging
                                logging.info(f"[contractInfo] Cleared {field_to_clear} after contractPeriodType change")
                        
                        # If switching away from "za obdobje od-do", clear date fields
                        if old_value == "za obdobje od-do" and selected_value != "za obdobje od-do":
                            fields_to_clear = [
                                f"{prefix}.contractDateFrom",
                                f"{prefix}.contractDateTo"
                            ]
                            for field in fields_to_clear:
                                if field in st.session_state:
                                    del st.session_state[field]
                                    import logging
                                    logging.info(f"[contractInfo] Cleared {field} after contractPeriodType change")
                    
            elif "enum" in prop_details:
                # Story 3.0.2: Add legal article references to procurement procedures
                procedure_display_map = {
                    "odprti postopek": "odprti postopek (40. člen ZJN-3)",
                    "omejeni postopek": "omejeni postopek (41. člen ZJN-3)",
                    "konkurenčni dialog": "konkurenčni dialog (42. člen ZJN-3)",
                    "partnerstvo za inovacije": "partnerstvo za inovacije (43. člen ZJN-3)",
                    "konkurenčni postopek s pogajanji (zgolj za javno naročanje na splošnem področju)": "konkurenčni postopek s pogajanji (zgolj za javno naročanje na splošnem področju) (44. člen ZJN-3)",
                    "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)": "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju) (45. člen ZJN-3)",
                    "postopek s pogajanji brez predhodne objave": "postopek s pogajanji brez predhodne objave (46. člen ZJN-3)",
                    "postopek naročila male vrednosti": "postopek naročila male vrednosti (47. člen ZJN-3)",
                    "vseeno": "vseeno"
                }
                
                # Handle dynamic population for tiebreaker criterion
                if "tiebreakerCriterion" in full_key:
                    # Get selected criteria labels dynamically
                    available_options = get_selected_criteria_labels(parent_key, lot_context)
                    
                    if not available_options:
                        st.info("ℹ Najprej izberite merila v točki A, da boste lahko določili merilo za prednost.")
                        return
                else:
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
                        st.info("ℹ Vse vrste naročil (blago, storitve, gradnje) so že izbrane v drugih postavkah.")
                        return  # Skip rendering the selectbox
                
                # Enhanced selectbox with proper placeholder and filtered options
                # This section is actually not needed anymore since we handle options differently
                # Remove this entire legacy logic block
                
                # Special handling for "vseeno" auto-selection in procedure field
                                                # Enhanced selectbox with proper placeholder and filtered options
                enum_options = available_options
                
                # Initialize the session state if it doesn't exist - BUT PRESERVE EXISTING VALUES
                if session_key not in st.session_state:
                    # Use raw_default if available and valid, otherwise use first option as default
                    if raw_default and raw_default in enum_options:
                        st.session_state[session_key] = raw_default
                    elif enum_options:  # If we have options, use the first one as default
                        st.session_state[session_key] = enum_options[0]
                    else:
                        st.session_state[session_key] = ""
                
                # Calculate index based on current session state value, not current_value
                session_value = st.session_state[session_key]
                if session_value and session_value in enum_options:
                    index = enum_options.index(session_value)
                elif enum_options:  # If we have options but no valid selection, use first option
                    index = 0
                else:
                    index = None

                # Use a separate widget key to avoid Streamlit cleaning up our session state
                widget_key = f"widget_{session_key}"
                
                # Apply display mapping for procedures (Story 3.0.2)
                if "submissionProcedure.procedure" in full_key:
                    display_options = [procedure_display_map.get(opt, opt) for opt in enum_options]
                    # Create reverse mapping to get value from display
                    reverse_map = {procedure_display_map.get(opt, opt): opt for opt in enum_options}
                else:
                    display_options = enum_options
                    reverse_map = {opt: opt for opt in enum_options}
                
                # Adjust index for display options
                if session_value and session_value in enum_options:
                    display_value = procedure_display_map.get(session_value, session_value) if "submissionProcedure.procedure" in full_key else session_value
                    if display_value in display_options:
                        index = display_options.index(display_value)
                
                # Special handling for "vseeno" auto-selection in procedure field
                selected_display = st.selectbox(
                    display_label, 
                    options=display_options, 
                    index=index,
                    key=widget_key,  # Use separate widget key
                    help=help_text,
                    placeholder=get_text("select_option")
                )
                
                # Convert display back to value
                selected_value = reverse_map.get(selected_display, selected_display)
                
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
                        st.info("ℹ Ker ste izbrali 'vseeno', smo avtomatsko nastavili 'odprti postopek', ki je najčešji in priporočeni postopek za večino javnih naročil.")
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
                # Enhanced file uploader with document persistence
                from io import BytesIO
                import os
                
                # Check if we have existing documents for this field
                existing_doc = None
                remove_key = f"{session_key}_remove"
                file_info_key = f"{session_key}_file_info"
                
                # Check if file was marked for removal
                if remove_key not in st.session_state or not st.session_state[remove_key]:
                    # First check if we have a file in session state (recently uploaded)
                    if file_info_key in st.session_state:
                        # We have a recently uploaded file in session
                        file_info = st.session_state[file_info_key]
                        existing_doc = {
                            'original_name': file_info['name'],
                            'file_size': file_info['size'],
                            'from_session': True  # Mark as from session, not database
                        }
                    # If no file in session, check database
                    elif 'form_id' in st.session_state and st.session_state.form_id:
                        try:
                            from services.form_document_service import FormDocumentService
                            doc_service = FormDocumentService()
                            existing_docs = doc_service.get_documents_for_form(
                                st.session_state.form_id, 
                                'draft', 
                                prop_name
                            )
                            if existing_docs:
                                existing_doc = existing_docs[0]  # Take the most recent
                        except Exception as e:
                            # Service not available or error - continue without persistence
                            pass
                
                # Show existing file info if available
                if existing_doc:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info(f" Current file: {existing_doc['original_name']} ({existing_doc['file_size'] / 1024:.1f} KB)")
                    with col2:
                        if st.button("Remove", key=f"remove_{session_key}"):
                            # Mark for removal in session state
                            st.session_state[remove_key] = True
                            # If it's from session, remove the file info
                            if existing_doc.get('from_session'):
                                if file_info_key in st.session_state:
                                    del st.session_state[file_info_key]
                            else:
                                # Store document ID for removal on save (for database files)
                                st.session_state[f"{session_key}_remove_doc_id"] = existing_doc['id']
                            st.rerun()
                
                # Show file uploader (for new upload or replacement)
                uploaded_file = st.file_uploader(
                    display_label if not existing_doc else "Replace file:", 
                    key=session_key, 
                    help=help_text,
                    type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
                )
                
                # Handle new upload - store in session for later persistence
                if uploaded_file is not None:
                    # Read file data and store in session
                    file_data = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset for potential re-reading
                    
                    # Store file metadata in session for persistence on save
                    file_info_key = f"{session_key}_file_info"
                    st.session_state[file_info_key] = {
                        'data': file_data,
                        'name': uploaded_file.name,
                        'type': uploaded_file.type,
                        'size': uploaded_file.size,
                        'field': prop_name
                    }
                    
                    # Show upload feedback
                    st.success(f" {uploaded_file.name} ready to save ({uploaded_file.size / 1024:.1f} KB)")
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
            elif prop_details.get("format") == "time":
                # Time input field
                from datetime import time as datetime_time
                
                # Initialize session state if it doesn't exist
                if session_key not in st.session_state:
                    default_time = datetime_time(10, 0)  # Default to 10:00
                    st.session_state[session_key] = default_time
                
                # Handle string time values
                current_value = st.session_state[session_key]
                if isinstance(current_value, str):
                    try:
                        # Parse string time "HH:MM"
                        hour, minute = current_value.split(':')
                        current_value = datetime_time(int(hour), int(minute))
                    except:
                        current_value = datetime_time(10, 0)
                
                # Enhanced time input with separate widget key
                widget_key = f"widget_{session_key}"
                time_value = st.time_input(
                    display_label,
                    value=current_value,
                    key=widget_key,
                    help=help_text
                )
                
                # Sync widget value back to session state
                if time_value != st.session_state.get(session_key):
                    st.session_state[session_key] = time_value
            else:
                # Check if this field has enhanced configuration
                if field_manager.is_enhanced_field(full_key):
                    # Use enhanced field rendering
                    enhanced_value = field_manager.render_field(
                        full_key,
                        value=st.session_state.get(session_key, raw_default),
                        disabled=False,
                        label=display_label,
                        help=help_text
                    )
                    # Sync value back to session state
                    if enhanced_value != st.session_state.get(session_key):
                        st.session_state[session_key] = enhanced_value
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
                                    st.error(" Okvirni sporazum ne sme presegati 4 let!")
                        elif "mesec" in text_value.lower():
                            # Extract number before "mesec"
                            import re
                            numbers = re.findall(r'(\d+)', text_value)
                            if numbers:
                                months = int(numbers[0])
                                if months > 48:
                                    st.error(" Okvirni sporazum ne sme presegati 4 let (48 mesecev)!")
                    except:
                        pass  # If parsing fails, don't show error

        elif prop_type == "number":
            display_label = _format_field_label(label, prop_details, parent_key, prop_name)
            
            # Check if this field has enhanced configuration
            if field_manager.is_enhanced_field(full_key):
                # Use enhanced field rendering
                enhanced_value = field_manager.render_field(
                    full_key,
                    value=st.session_state.get(session_key, raw_default),
                    disabled=False,
                    label=display_label,
                    help=help_text
                )
                # Sync value back to session state
                if enhanced_value != st.session_state.get(session_key):
                    st.session_state[session_key] = enhanced_value
            else:
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
            
            # Story 3.0.3: Apply formatting for financial fields
            financial_fields = ["estimatedValue", "guaranteedFunds", "availableFunds", "averageSalary"]
            
            # Check if this is a guarantee amount field from financialGuarantees section
            guarantee_amount_field = (prop_name == "amount" and 
                                    parent_key and 
                                    any(guarantee_type in parent_key for guarantee_type in 
                                        ["fzSeriousness", "fzPerformance", "fzWarranty"]))
            
            is_financial = any(field in prop_name for field in financial_fields) or guarantee_amount_field
            
            if is_financial:
                # Use formatted display for financial fields
                current_value = st.session_state.get(session_key, 0)
                formatted_str = format_number_with_dots(current_value)
                widget_key = f"widget_{session_key}_formatted"
                
                # Create columns for input and EUR symbol
                col_input, col_symbol = st.columns([5, 1])
                
                with col_input:
                    number_text = st.text_input(
                        display_label,
                        value=formatted_str,
                        key=widget_key,
                        help=help_text or "Format: 1.000.000",
                        placeholder="0"
                    )
                
                with col_symbol:
                    st.markdown("<div style='padding-top: 28px; font-size: 16px; font-weight: 500;'>€</div>", unsafe_allow_html=True)
                
                # Parse and store unformatted value
                try:
                    if number_text.strip():
                        number_value = parse_formatted_number(number_text)
                    else:
                        number_value = 0.0
                    st.session_state[session_key] = number_value
                except ValueError:
                    st.warning(f"'{number_text}' ni veljavna številka")
                    st.session_state[session_key] = 0.0
            else:
                # Use standard number input for non-financial fields
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
            
            # For checkboxes with detailed descriptions containing ✓/✗, show info box instead of help tooltip
            if help_text and ('✓' in help_text or '✗' in help_text):
                # Render checkbox without help parameter
                checkbox_value = st.checkbox(display_label, value=st.session_state[session_key], key=widget_key)
                # Display help text as info box below checkbox for consistency
                with st.expander("ℹ Kaj pomeni označitev?", expanded=False):
                    st.info(help_text)
            else:
                # Regular checkbox with tooltip help for simple descriptions
                checkbox_value = st.checkbox(display_label, value=st.session_state[session_key], key=widget_key, help=help_text)
            
            # Sync widget value back to session state
            if checkbox_value != st.session_state.get(session_key):
                st.session_state[session_key] = checkbox_value
            
            # Special handling for wantsLogo to provide user feedback
            if prop_name == "wantsLogo" and checkbox_value != raw_default:
                if checkbox_value:
                    st.success(" Polje za nalaganje logotipov je sedaj na voljo spodaj.")
                else:
                    st.info("ℹ Polje za nalaganje logotipov je skrito, ker niste izbrali te možnosti.")
            
            # Removed help text expanders for criteria per Story 23.2 requirements


def render_criteria_validation(parent_key: str, lot_context: dict = None):
    """
    Render validation messages for criteria selection based on CPV codes.
    Story 21.2: Real-time validation UI
    Story 22.3: Respect validation toggles
    Story 27.3: Refactored to use centralized ValidationManager
    """
    # Check if validation should run (Story 22.3)
    from utils.validation_control import should_validate
    from utils.validations import ValidationManager
    
    current_step = st.session_state.get('current_step', 0)
    
    if not should_validate(current_step):
        # Show subtle indicator that validation is off
        with st.expander("ℹ Validacija meril izklopljena", expanded=False):
            st.caption("Validacija meril je trenutno izklopljena za ta korak")
        return
    
    # Get current CPV codes from session state
    cpv_key = get_lot_scoped_key("orderDescription.cpvCodes", lot_context) if lot_context else "orderDescription.cpvCodes"
    cpv_codes_raw = st.session_state.get(cpv_key, [])
    
    # Convert string to list if needed
    if isinstance(cpv_codes_raw, str):
        # Parse comma-separated CPV codes
        cpv_codes = []
        for code in cpv_codes_raw.split(','):
            code = code.strip()
            # Remove any description if present (format: "50700000-2 - Description")
            if ' - ' in code:
                code = code.split(' - ')[0].strip()
            if code:
                cpv_codes.append(code)
    else:
        cpv_codes = cpv_codes_raw if cpv_codes_raw else []
    
    
    if not cpv_codes:
        return  # No validation needed without CPV codes
    
    # Get current criteria selection
    criteria_prefix = get_lot_scoped_key("selectionCriteria", lot_context) if lot_context else "selectionCriteria"
    selected_criteria = {
        'price': st.session_state.get(f"{criteria_prefix}.price", False),
        'additionalReferences': st.session_state.get(f"{criteria_prefix}.additionalReferences", False),
        'additionalTechnicalRequirements': st.session_state.get(f"{criteria_prefix}.additionalTechnicalRequirements", False),
        'shorterDeadline': st.session_state.get(f"{criteria_prefix}.shorterDeadline", False),
        'longerWarranty': st.session_state.get(f"{criteria_prefix}.longerWarranty", False),
        'environmentalCriteria': st.session_state.get(f"{criteria_prefix}.environmentalCriteria", False),
        'socialCriteria': st.session_state.get(f"{criteria_prefix}.socialCriteria", False),
    }
    
    # Use centralized ValidationManager for validation
    validator = ValidationManager(st.session_state.get('schema', {}), st.session_state)
    is_valid, errors, warnings, restricted_info = validator.validate_criteria_real_time(cpv_codes, selected_criteria)
    
    # Store validation state
    validation_key = f"{criteria_prefix}_validation" if lot_context else "selectionCriteria_validation"
    st.session_state[validation_key] = is_valid
    
    # Get restriction information from the centralized validator
    restricted_cpv = restricted_info.get('additional_required', {})
    social_cpv = restricted_info.get('social_required', {})
    
    # Story 21.3: Enhanced guidance
    if restricted_cpv or social_cpv:
        st.markdown("---")
        
        # Educational info box
        with st.expander("ℹ **Zakaj so potrebna dodatna merila?**", expanded=False):
            st.markdown("""
            **Pravna podlaga:** Zakon o javnem naročanju (ZJN-3) določa, da pri nekaterih 
            vrstah storitev cena ne sme biti edino merilo za izbor. To velja predvsem za:
            
            • **Intelektualne storitve** (arhitektura, inženiring, svetovanje) - kjer je kakovost ključna
            • **Socialne storitve** - kjer štejejo družbeni vidiki in izkušnje
            • **Inovativne rešitve** - kjer je pomembna dodana vrednost in kreativnost
            • **Kompleksne tehnične storitve** - kjer so reference in strokovnost bistvenega pomena
            
            Vaše izbrane CPV kode spadajo v kategorije, kjer je zahtevana 
            celovitejša ocena ponudb za zagotovitev najboljšega razmerja med ceno in kakovostjo.
            """)
        
        # Get and show suggestions
        suggestions = get_suggested_criteria_for_cpv(cpv_codes)
        
        if suggestions['recommended']:
            st.info(f" **Priporočilo:** {suggestions['explanation']}")
            
            # Auto-selection option
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**Priporočena dodatna merila za vaše CPV kode:**")
                criteria_names = get_criteria_display_names()
                
                for criteria in suggestions['recommended']:
                    if criteria in criteria_names:
                        st.markdown(f"- {criteria_names[criteria]}")
                
                if suggestions['commonly_used']:
                    st.markdown("**Pogosto uporabljena merila:**")
                    for criteria in suggestions['commonly_used']:
                        if criteria in criteria_names:
                            st.markdown(f"- {criteria_names[criteria]}")
            
            with col2:
                if st.button(" Samodejno izberi", key=f"{parent_key}_auto_select", type="primary"):
                    # Auto-select suggested criteria
                    for criteria in suggestions['recommended']:
                        key = f"{criteria_prefix}.{criteria}"
                        st.session_state[key] = True
                    st.success(" Priporočena merila so bila izbrana!")
                    st.rerun()
    
    # Display validation messages - now using centralized validation results
    if not is_valid:
        # TODO(human): Implement error display logic
        # Display errors and warnings from the centralized validation
        # Consider prioritizing errors over warnings and providing clear guidance
        pass
    
    # Display warnings even if validation is valid
    for warning in warnings:
        st.warning(f"ℹ {warning}")
    
    # Add override option for advanced users if there are errors
    if not is_valid and errors:
        col1, col2 = st.columns([3, 1])
        with col2:
            override_key = f"{validation_key}_override"
            if st.checkbox("Prezri opozorilo", key=override_key, help="Nadaljuj na lastno odgovornost"):
                st.session_state[validation_key] = True
                st.caption(" Nadaljevanje na lastno odgovornost")
    
    # Story 21.3: Validation summary
    render_validation_summary(cpv_codes, restricted_cpv, lot_context)


def render_validation_summary(cpv_codes: List, restricted_cpv: Dict, lot_context: dict = None):
    """
    Show summary of all active validation rules.
    Story 21.3: Enhanced guidance
    """
    if cpv_codes and restricted_cpv:
        with st.container():
            st.markdown("---")
            st.markdown(" **Povzetek pravil za izbrane CPV kode:**")
            
            summary = get_validation_summary(cpv_codes)
            
            if summary['has_restrictions']:
                st.markdown(f"- ✓ Dodatna merila poleg cene so obvezna ({summary['restricted_count']} kod)")
                
                # Get current validation state
                criteria_prefix = get_lot_scoped_key("selectionCriteria", lot_context) if lot_context else "selectionCriteria"
                validation_key = f"{criteria_prefix}_validation" if lot_context else "selectionCriteria_validation"
                is_valid = st.session_state.get(validation_key, True)
                
                if is_valid:
                    st.success(" Vaša izbira meril je ustrezna")
                else:
                    override_key = f"{validation_key}_override"
                    if st.session_state.get(override_key, False):
                        st.warning(" Opozorilo prezrto - nadaljevanje na lastno odgovornost")
                    else:
                        st.error(" Izberite dodatna merila za nadaljevanje")
