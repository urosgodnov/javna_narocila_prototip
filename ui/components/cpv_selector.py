"""CPV code selector component for forms."""
import streamlit as st
from typing import List, Optional, Union
from utils.cpv_manager import get_cpv_codes_for_dropdown, get_cpv_count, search_cpv_codes


def render_cpv_selector(
    field_key: str, 
    field_schema: dict, 
    current_value: Optional[Union[str, List[str]]] = None,
    disabled: bool = False
) -> str:
    """
    Render CPV multi-select component with bi-directional lookup.
    
    Args:
        field_key: Unique key for the field
        field_schema: Schema definition for the field
        current_value: Current value (comma-separated string or list)
        disabled: Whether the field is disabled
    
    Returns:
        Comma-separated string of selected CPV codes
    """
    # Check if CPV database has any codes
    cpv_count = get_cpv_count()
    
    # If no CPV codes in database, fall back to text input
    if cpv_count == 0:
        st.warning("⚠️ Ni CPV kod v bazi. Uporabite besedilno polje ali uvozite CPV kode v admin panelu.")
        value = st.text_area(
            field_schema.get('title', 'CPV kode'),
            value=current_value if isinstance(current_value, str) else '',
            help=field_schema.get('description', 'Vnesite CPV kode ločene z vejico'),
            disabled=disabled,
            key=f"{field_key}_text"
        )
        return value
    
    # Load CPV codes for dropdown
    cpv_options = get_cpv_codes_for_dropdown()
    
    # Parse current value
    selected_codes = []
    if current_value:
        if isinstance(current_value, str):
            # Parse comma-separated string
            codes = [code.strip() for code in current_value.split(',') if code.strip()]
            selected_codes = codes
        elif isinstance(current_value, list):
            selected_codes = current_value
    
    # Find matching display values for selected codes
    selected_displays = []
    for code in selected_codes:
        for opt in cpv_options:
            if opt['value'] == code:
                selected_displays.append(opt['display'])
                break
            # Also check if the full display string was stored
            elif opt['display'] == code:
                selected_displays.append(opt['display'])
                break
    
    # Create multiselect with all options
    all_displays = [opt['display'] for opt in cpv_options]
    
    # Render the multiselect component
    selected = st.multiselect(
        label=field_schema.get('title', 'CPV kode'),
        options=all_displays,
        default=selected_displays,
        help=field_schema.get('description', 'Začnite tipkati kodo ali opis za iskanje'),
        disabled=disabled,
        key=field_key,
        placeholder="Izberite ali poiščite CPV kode..."
    )
    
    # Extract codes from selected display values
    selected_codes = []
    for display in selected:
        # Extract code from "CODE - Description" format
        if ' - ' in display:
            code = display.split(' - ')[0]
            selected_codes.append(code)
    
    # Return comma-separated codes
    return ', '.join(selected_codes)


def render_cpv_selector_with_chips(
    field_key: str, 
    field_schema: dict, 
    current_value: Optional[Union[str, List[str]]] = None,
    disabled: bool = False
) -> str:
    """
    Enhanced CPV selector with chip/tag display for selected items.
    
    Args:
        field_key: Unique key for the field
        field_schema: Schema definition for the field
        current_value: Current value (comma-separated string or list)
        disabled: Whether the field is disabled
    
    Returns:
        Comma-separated string of selected CPV codes
    """
    # Check if CPV database has any codes
    cpv_count = get_cpv_count()
    
    if cpv_count == 0:
        st.warning("⚠️ Ni CPV kod v bazi. Uporabite besedilno polje ali uvozite CPV kode v admin panelu.")
        value = st.text_area(
            field_schema.get('title', 'CPV kode'),
            value=current_value if isinstance(current_value, str) else '',
            help=field_schema.get('description', 'Vnesite CPV kode ločene z vejico'),
            disabled=disabled,
            key=f"{field_key}_text"
        )
        return value
    
    # Initialize session state for this field if not exists
    if f"{field_key}_selected" not in st.session_state:
        # Parse initial value
        if current_value:
            if isinstance(current_value, str):
                codes = [code.strip() for code in current_value.split(',') if code.strip()]
                st.session_state[f"{field_key}_selected"] = codes
            elif isinstance(current_value, list):
                st.session_state[f"{field_key}_selected"] = current_value
        else:
            st.session_state[f"{field_key}_selected"] = []
    
    # Search input
    search_key = f"{field_key}_search"
    search_term = st.text_input(
        "🔍 Išči CPV kodo ali opis",
        key=search_key,
        disabled=disabled,
        placeholder="Začnite tipkati za iskanje..."
    )
    
    # Search for CPV codes if search term provided
    if search_term and not disabled:
        search_results = search_cpv_codes(search_term, limit=10)
        
        if search_results:
            st.markdown("**Rezultati iskanja:**")
            for result in search_results:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"`{result['code']}` - {result['description'][:60]}...")
                with col2:
                    if result['code'] not in st.session_state[f"{field_key}_selected"]:
                        if st.button("➕", key=f"add_{field_key}_{result['code']}"):
                            st.session_state[f"{field_key}_selected"].append(result['code'])
                            st.rerun()
                    else:
                        st.markdown("✅")
        else:
            st.info("Ni rezultatov za to iskanje")
    
    # Display selected CPV codes as chips
    if st.session_state[f"{field_key}_selected"]:
        st.markdown("**Izbrane CPV kode:**")
        
        # Create chips display
        for i, code in enumerate(st.session_state[f"{field_key}_selected"]):
            col1, col2 = st.columns([5, 1])
            with col1:
                # Get description for code
                cpv_options = get_cpv_codes_for_dropdown()
                description = code
                for opt in cpv_options:
                    if opt['value'] == code:
                        description = opt['display']
                        break
                
                st.markdown(
                    f'<div style="display: inline-block; background-color: #e3f2fd; '
                    f'padding: 5px 10px; border-radius: 15px; margin: 2px;">'
                    f'{description}</div>',
                    unsafe_allow_html=True
                )
            
            with col2:
                if not disabled:
                    if st.button("❌", key=f"remove_{field_key}_{i}"):
                        st.session_state[f"{field_key}_selected"].pop(i)
                        st.rerun()
    else:
        st.info("Ni izbranih CPV kod. Uporabite iskanje zgoraj.")
    
    # Return comma-separated codes
    return ', '.join(st.session_state[f"{field_key}_selected"])


def parse_cpv_from_text(text: str) -> List[str]:
    """
    Parse CPV codes from text field (backward compatibility).
    
    Args:
        text: Text containing CPV codes
    
    Returns:
        List of parsed CPV codes
    """
    if not text:
        return []
    
    # Try to parse comma-separated codes
    codes = []
    parts = text.split(',')
    
    for part in parts:
        part = part.strip()
        # Check if it looks like a CPV code (digits and dashes)
        if part and any(c.isdigit() for c in part):
            # Extract just the code part if description is included
            if ' - ' in part:
                code = part.split(' - ')[0].strip()
            else:
                code = part
            codes.append(code)
    
    return codes


def validate_cpv_codes(codes: List[str]) -> List[str]:
    """
    Validate CPV codes against database.
    
    Args:
        codes: List of CPV codes to validate
    
    Returns:
        List of valid CPV codes
    """
    valid_codes = []
    cpv_options = get_cpv_codes_for_dropdown()
    valid_code_set = {opt['value'] for opt in cpv_options}
    
    for code in codes:
        if code in valid_code_set:
            valid_codes.append(code)
    
    return valid_codes