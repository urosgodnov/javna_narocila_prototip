
"""Main Streamlit application for public procurement document generation."""
import streamlit as st
import database
from config import FORM_STEPS, SCHEMA_FILE
from utils.schema_utils import load_json_schema, get_form_data_from_session
from ui.form_renderer import render_form
from ui.admin_panel import render_admin_panel
from localization import get_text, format_step_indicator

def main():
    """Main application entry point."""
    st.set_page_config(layout="wide", page_title=get_text("app_title"))
    st.title(get_text("app_title"))

    if 'schema' not in st.session_state:
        try:
            st.session_state['schema'] = load_json_schema(SCHEMA_FILE)
        except FileNotFoundError:
            st.error(get_text("schema_file_not_found", filename=SCHEMA_FILE))
            st.stop()

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    st.sidebar.header(get_text("navigation_header"))
    page_selection = st.sidebar.radio(
        get_text("go_to"), 
        [get_text("form_header"), get_text("admin_header")], 
        key="page_selection"
    )

    if page_selection == get_text("form_header"):
        render_main_form()
    else:
        render_admin_panel()

def validate_step(step_keys, schema):
    """Validate the fields for the current step based on 'required' keys in the schema."""
    is_valid = True
    for key in step_keys:
        # This validation is simplistic and only checks top-level properties.
        # A robust solution would recursively check nested objects and arrays.
        prop_details = schema["properties"].get(key, {})
        if "required" in prop_details:
            for required_field in prop_details["required"]:
                full_key = f"{key}.{required_field}"
                if not st.session_state.get(full_key):
                    field_title = prop_details['properties'][required_field]['title']
                    st.warning(get_text("fill_required_field", field_name=field_title))
                    is_valid = False
    return is_valid

def render_main_form():
    """Render the main multi-step form interface with enhanced UX."""
    database.init_db()
    draft_metadata = database.get_all_draft_metadata()
    draft_options = {f"{ts} (ID: {id})": id for id, ts in draft_metadata}

    # Add custom CSS for better styling
    add_custom_css()

    col1, col2 = st.columns([3, 1])

    with col1:
        # Enhanced header with step information
        current_step_num = st.session_state.current_step + 1
        total_steps = len(FORM_STEPS)
        
        st.markdown(f"""
        <div class="form-header">
            <h1>{st.session_state.schema.get("title", "Obrazec")}</h1>
            <div class="step-indicator">
                {format_step_indicator(st.session_state.current_step, total_steps)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Enhanced Progress Bar with step labels
        progress_percentage = current_step_num / total_steps
        st.progress(progress_percentage, text=f"{get_text('progress')}: {current_step_num}/{total_steps}")
        
        # Step navigation breadcrumbs
        render_step_breadcrumbs()

        # Get properties for the current step and render the form
        current_step_keys = FORM_STEPS[st.session_state.current_step]
        current_step_properties = {k: st.session_state.schema["properties"][k] for k in current_step_keys}
        
        # Render form with enhanced styling
        st.markdown('<div class="form-content">', unsafe_allow_html=True)
        render_form(current_step_properties)
        st.markdown('</div>', unsafe_allow_html=True)

        # Enhanced Navigation buttons
        render_navigation_buttons(current_step_keys)

    with col2:
        render_drafts_sidebar(draft_options)

def add_custom_css():
    """Add custom CSS for enhanced styling."""
    st.markdown("""
    <style>
    .form-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .form-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    .step-indicator {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    .form-content {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e1e5e9;
        margin-bottom: 2rem;
    }
    
    .step-breadcrumbs {
        display: flex;
        justify-content: center;
        margin: 1rem 0 2rem 0;
        flex-wrap: wrap;
    }
    
    .breadcrumb-item {
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .breadcrumb-item.completed {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .breadcrumb-item.current {
        background: #1f4e79;
        color: white;
        border: 1px solid #1f4e79;
    }
    
    .breadcrumb-item.pending {
        background: #f8f9fa;
        color: #6c757d;
        border: 1px solid #dee2e6;
    }
    
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        padding: 1rem 0;
        margin-top: 2rem;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
    }
    
    .sidebar-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f4e79;
    }
    
    /* Enhanced form fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px !important;
        border: 2px solid #e1e5e9 !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: #1f4e79 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 78, 121, 0.25) !important;
    }
    
    /* Section headers */
    .form-section-header {
        color: #1f4e79;
        font-weight: 600;
        font-size: 1.2rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e1e5e9;
    }
    </style>
    """, unsafe_allow_html=True)

def render_step_breadcrumbs():
    """Render step navigation breadcrumbs."""
    from localization import get_step_label
    
    breadcrumbs_html = '<div class="step-breadcrumbs">'
    
    for i, step_keys in enumerate(FORM_STEPS):
        step_num = i + 1
        step_label = get_step_label(step_num)
        
        if i < st.session_state.current_step:
            css_class = "completed"
        elif i == st.session_state.current_step:
            css_class = "current"
        else:
            css_class = "pending"
            
        breadcrumbs_html += f'<span class="breadcrumb-item {css_class}">{step_num}. {step_label}</span>'
    
    breadcrumbs_html += '</div>'
    st.markdown(breadcrumbs_html, unsafe_allow_html=True)

def render_navigation_buttons(current_step_keys):
    """Render enhanced navigation buttons."""
    st.markdown('<div class="navigation-buttons">', unsafe_allow_html=True)
    
    col_nav_left, col_nav_center, col_nav_right = st.columns([1, 2, 1])
    
    with col_nav_left:
        if st.session_state.current_step > 0:
            if st.button(
                f"← {get_text('back_button')}", 
                type="secondary",
                use_container_width=True
            ):
                st.session_state.current_step -= 1
                st.rerun()

    with col_nav_right:
        if st.session_state.current_step < len(FORM_STEPS) - 1:
            if st.button(
                f"{get_text('next_button')} →", 
                type="primary",
                use_container_width=True
            ):
                # Enhanced validation can be added here
                if validate_step(current_step_keys, st.session_state.schema):
                    st.session_state.current_step += 1
                    st.rerun()
        else:
            if st.button(
                f"📄 {get_text('submit_button')}", 
                type="primary",
                use_container_width=True
            ):
                if validate_step(current_step_keys, st.session_state.schema):
                    final_form_data = get_form_data_from_session()
                    st.markdown("---")
                    st.subheader(get_text("form_submitted_with_data"))
                    st.json(final_form_data)
                    st.success(get_text("documents_prepared"))
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_drafts_sidebar(draft_options):
    """Render the enhanced drafts management sidebar."""
    st.markdown(f'<div class="sidebar-header"><h3>{get_text("drafts_header")}</h3></div>', unsafe_allow_html=True)
    
    if not draft_options:
        st.info(get_text("no_drafts"))
        return

    selected_draft_label = st.selectbox(
        get_text("load_draft"), 
        options=list(draft_options.keys()),
        help="Izberite osnutek, ki ga želite naložiti"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            get_text("load_selected_draft"),
            type="secondary",
            use_container_width=True
        ):
            selected_draft_id = draft_options[selected_draft_label]
            loaded_data = database.load_draft(selected_draft_id)
            if loaded_data:
                st.session_state.update(loaded_data)
                st.success(get_text("draft_loaded"))
                st.rerun()
            else:
                st.error(get_text("draft_load_error"))

    with col2:
        if st.button(
            get_text("save_draft"),
            type="primary",
            use_container_width=True
        ):
            form_values = get_form_data_from_session()
            draft_id = database.save_draft(form_values)
            st.success(get_text("draft_saved", draft_id=draft_id))
            st.rerun()

if __name__ == "__main__":
    main()
