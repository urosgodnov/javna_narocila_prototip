"""
Validation control utilities for form validation toggles.
Story 22: Granular Validation Control
"""
import streamlit as st

def render_warning_box(title: str, content: str):
    """Render a consistent warning box with yellow/orange styling."""
    # Remove any existing warning prefixes from content
    content = content.replace("⚠️", "").replace("ℹ️", "").replace("**Opozorilo:**", "").replace("**OPOZORILO:**", "").strip()
    
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


def should_validate(step_num: int) -> bool:
    """
    Story 22.3: Determine if validation should run for a given step.
    
    Returns True if validation should run, False otherwise.
    Logic: Validate if master is disabled (unchecked) OR step is enabled (checked)
    """
    # Get master toggle state (checked = validation disabled)
    master_disabled = st.session_state.get('validation_disabled', True)
    
    # Get per-step toggle state (checked = validation enabled for this step)
    step_enabled = st.session_state.get(f'step_{step_num}_validation_enabled', False)
    
    # Validate if: master OFF (not disabled) OR step ON (enabled)
    return (not master_disabled) or step_enabled


def render_master_validation_toggle():
    """
    Story 22.1: Render master validation toggle on first step.
    Checkbox is checked by default = validation disabled.
    """
    st.markdown("### ⚙️ Nastavitve validacije")
    
    # Initialize session state if not exists
    if 'validation_disabled' not in st.session_state:
        st.session_state['validation_disabled'] = True  # Default checked (disabled)
    
    # Render checkbox
    validation_disabled = st.checkbox(
        "Izklopljena validacija",
        value=st.session_state['validation_disabled'],
        help="Ko je označeno, validacija obrazca je izklopljena na vseh korakih",
        key="master_validation_toggle"
    )
    
    # Update session state if changed
    if validation_disabled != st.session_state['validation_disabled']:
        st.session_state['validation_disabled'] = validation_disabled
    
    # Show status indicator
    if validation_disabled:
        render_warning_box("Opozorilo", "Validacija je trenutno IZKLOPLJENA - obrazec ne bo preverjal pravilnosti podatkov")
    else:
        st.success("✅ Validacija je vklopljena - obrazec bo preverjal pravilnost podatkov")
    
    st.markdown("---")


def render_step_validation_toggle(step_num: int):
    """
    Story 22.2: Render per-step validation toggle.
    Checkbox is unchecked by default = use master setting.
    """
    # Initialize session state for this step if not exists
    step_key = f'step_{step_num}_validation_enabled'
    if step_key not in st.session_state:
        st.session_state[step_key] = False  # Default unchecked
    
    # Add separator before validation section
    st.markdown("---")
    
    # Create columns for better layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Render checkbox
        step_validation = st.checkbox(
            "Uveljavi validacijo",
            value=st.session_state[step_key],
            help="Vklopi validacijo samo za ta korak",
            key=f"step_{step_num}_validation_checkbox"
        )
        
        # Update session state if changed
        if step_validation != st.session_state[step_key]:
            st.session_state[step_key] = step_validation
    
    with col2:
        # Show status indicator
        if st.session_state[step_key]:
            st.success("✓ Validacija vklopljena")
        else:
            # Check if master is disabled
            if st.session_state.get('validation_disabled', True):
                st.info("○ Validacija izklopljena")
            else:
                st.info("○ Globalna validacija")
    
    # Show info message if this overrides master setting
    master_disabled = st.session_state.get('validation_disabled', True)
    if master_disabled and step_validation:
        st.info("ℹ️ Validacija bo izvedena za ta korak kljub globalni izključitvi")
    
    st.markdown("---")


def get_validation_status_message(step_num: int) -> str:
    """Get a status message for the current validation state."""
    if should_validate(step_num):
        return "🔍 Validacija aktivna"
    else:
        return "⏭️ Validacija preskočena"