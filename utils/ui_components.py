import streamlit as st
from typing import Optional, List


def render_field_with_validation(field_renderer, field_key: str, 
                                validator, **kwargs):
    """Render field with real-time validation feedback"""
    
    # Create container for field and feedback
    container = st.container()
    
    with container:
        # Render the field
        value = field_renderer(field_key, **kwargs)
        
        # Validate if value exists
        if value is not None and value != '':
            is_valid, error_msg = validator.validate_field(field_key, value)
            
            if not is_valid and error_msg:
                st.error(f"❌ {error_msg}")
            elif is_valid and value:  # Don't show success for empty optional fields
                st.success("✅")
    
    return value


def render_required_indicator(label: str, is_required: bool = True) -> str:
    """Add required indicator to field label"""
    if is_required:
        return f"{label} *"
    return label


def render_field_help(help_text: Optional[str], is_required: bool = False):
    """Render help text with required indicator"""
    texts = []
    
    if is_required:
        texts.append("Obvezno polje")
    
    if help_text:
        texts.append(help_text)
    
    if texts:
        return " | ".join(texts)
    
    return None


def render_section_validation_summary(errors: list, warnings: list = None):
    """Show validation summary for a section"""
    if errors:
        with st.expander(f"❌ Napake ({len(errors)})", expanded=True):
            for error in errors:
                st.error(error)
    
    if warnings:
        with st.expander(f"⚠️ Opozorila ({len(warnings)})"):
            for warning in warnings:
                st.warning(warning)
    
    if not errors and not warnings:
        st.success("✅ Vsa polja so pravilno izpolnjena")


def set_tab_order(field_keys: List[str]):
    """Set logical tab order for fields"""
    # This would require custom JavaScript injection
    tab_order_script = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const fieldOrder = {field_keys};
        let tabIndex = 1;
        
        fieldOrder.forEach(fieldKey => {{
            const element = document.querySelector(`[data-testid="${{fieldKey}}"] input, [data-testid="${{fieldKey}}"] textarea`);
            if (element) {{
                element.tabIndex = tabIndex++;
            }}
        }});
    }});
    </script>
    """
    
    st.markdown(tab_order_script, unsafe_allow_html=True)