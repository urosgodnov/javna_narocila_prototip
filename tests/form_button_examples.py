"""
Examples of how to use styled buttons in the form.
These match the dashboard color scheme.
"""

import streamlit as st

def render_navigation_buttons():
    """Render form navigation buttons with proper styling."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Back button - gray gradient (default)
        if st.button("← Nazaj", key="back_button", use_container_width=True):
            st.session_state.current_step -= 1
            st.rerun()
    
    with col3:
        # Next button - gray gradient (default) 
        if st.button("Naprej →", key="next_button", use_container_width=True):
            st.session_state.current_step += 1
            st.rerun()


def render_save_buttons():
    """Render save/submit buttons with green styling."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Save draft - green button (add 'save-button' class via markdown)
        st.markdown('<div class="save-button">', unsafe_allow_html=True)
        if st.button("💾 Shrani osnutek", key="save_draft", use_container_width=True):
            # Save logic here
            st.success("Osnutek shranjen!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Submit form - green button
        st.markdown('<div class="save-button">', unsafe_allow_html=True)
        if st.button("✅ Oddaj naročilo", key="submit_form", use_container_width=True):
            # Submit logic here
            st.success("Naročilo oddano!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        # Cancel - red danger button
        st.markdown('<div class="danger-button">', unsafe_allow_html=True)
        if st.button("❌ Prekliči", key="cancel_form", use_container_width=True):
            # Cancel logic here
            st.session_state.current_page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_action_buttons():
    """Render various action buttons with appropriate styling."""
    
    # Add new item - primary green
    st.markdown('<div class="save-button">', unsafe_allow_html=True)
    if st.button("➕ Dodaj nov sklop", key="add_lot"):
        # Add logic here
        pass
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Delete item - danger red
    st.markdown('<div class="danger-button">', unsafe_allow_html=True)
    if st.button("🗑️ Izbriši sklop", key="delete_lot"):
        # Delete logic here
        pass
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Edit item - secondary gray (default)
    if st.button("✏️ Uredi podatke", key="edit_data"):
        # Edit logic here
        pass


def render_form_header_with_progress():
    """Render a styled form header with progress indicator."""
    # Gradient header with progress
    st.markdown("""
    <div class="step-indicator">
        <h3>📝 Vnos javnega naročila</h3>
        <div class="progress-text">Korak {current} od {total} - {step_name}</div>
    </div>
    """.format(
        current=st.session_state.get('current_step', 1),
        total=st.session_state.get('total_steps', 13),
        step_name=st.session_state.get('current_step_name', 'Osnovni podatki')
    ), unsafe_allow_html=True)
    
    # Progress bar
    progress = st.session_state.get('current_step', 1) / st.session_state.get('total_steps', 13)
    st.progress(progress)


def render_form_section(title, content_func):
    """Render a form section with consistent styling."""
    st.markdown(f"""
    <div class="form-section">
        <div class="form-section-title">{title}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call the content function to render fields
    content_func()


def render_validation_feedback(field_name, is_valid, message):
    """Render validation feedback for a field."""
    if is_valid:
        st.markdown(f"""
        <div class="validation-success">
            ✅ {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="validation-error">
            ❌ {message}
        </div>
        """, unsafe_allow_html=True)


# Usage example in form_renderer.py:
"""
from ui.form_button_examples import (
    render_navigation_buttons,
    render_save_buttons,
    render_form_header_with_progress
)

# At the top of your form step:
render_form_header_with_progress()

# Your form fields here...

# At the bottom of your form step:
st.markdown("---")
render_navigation_buttons()

# Or for the final step:
render_save_buttons()
"""