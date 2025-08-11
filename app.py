
"""Main Streamlit application for public procurement document generation."""
import streamlit as st
import database
from config import get_dynamic_form_steps, SCHEMA_FILE
from utils.schema_utils import load_json_schema, get_form_data_from_session
from utils.lot_utils import (
    get_current_lot_context, initialize_lot_session_state, 
    migrate_existing_data_to_lot_structure, get_lot_progress_info
)
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

    # Initialize lot-aware session state
    initialize_lot_session_state()
    migrate_existing_data_to_lot_structure()

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
        original_key = key
        if key.startswith('lot_'):
            try:
                original_key = key.split('_', 2)[2]
            except IndexError:
                continue  # Skip malformed keys

        prop_details = schema["properties"].get(original_key, {})
        if "required" in prop_details:
            for required_field in prop_details["required"]:
                # The full key in session_state includes the lot-specific prefix
                full_key = f"{key}.{required_field}"
                if not st.session_state.get(full_key):
                    try:
                        field_title = prop_details['properties'][required_field]['title']
                        st.warning(get_text("fill_required_field", field_name=field_title))
                        is_valid = False
                    except KeyError:
                        # Failsafe if schema is structured unexpectedly
                        pass
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
        # Get dynamic form steps based on lots
        dynamic_form_steps = get_dynamic_form_steps(st.session_state)
        
        # Enhanced header with step information
        current_step_num = st.session_state.current_step + 1
        total_steps = len(dynamic_form_steps)
        
        # Get lot progress info for enhanced header
        lot_progress = get_lot_progress_info()
        
        # Enhanced header with lot context
        header_content = f"<h1>{st.session_state.schema.get('title', 'Obrazec')}</h1>"
        if lot_progress['mode'] == 'lots':
            header_content += f"<h3>📦 {lot_progress['lot_name']} ({lot_progress['current_lot']}/{lot_progress['total_lots']})</h3>"
        elif lot_progress['mode'] == 'general':
            header_content += f"<h3>📄 {lot_progress['lot_name']}</h3>"
        
        st.markdown(f"""
        <div class="form-header">
            {header_content}
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
        current_step_keys = dynamic_form_steps[st.session_state.current_step]
        
        # Get lot context for current step
        lot_context = get_current_lot_context(current_step_keys)
        
        # Store current step keys for use in lot utilities
        st.session_state.current_step_keys = current_step_keys
        
        # Get properties - handle lot context steps and regular properties  
        current_step_properties = {}
        for key in current_step_keys:
            if key.startswith('lot_context_'):
                # Lot context steps don't need schema properties
                current_step_properties[key] = {"type": "lot_context"}
            elif key.startswith('lot_'):
                # Map lot-specific keys back to original schema properties
                original_key = key.split('_', 2)[2]  # lot_0_orderType -> orderType
                if original_key in st.session_state.schema["properties"]:
                    # Copy the schema property but remove render_if conditions for lot-specific fields
                    prop_copy = st.session_state.schema["properties"][original_key].copy()
                    if "render_if" in prop_copy:
                        del prop_copy["render_if"]  # Lot logic handles visibility
                    current_step_properties[key] = prop_copy
            else:
                # Regular properties
                if key in st.session_state.schema["properties"]:
                    prop_copy = st.session_state.schema["properties"][key].copy()
                    
                    # For orderType in general mode, remove render_if condition
                    if key == "orderType" and lot_context and lot_context['mode'] == 'general':
                        if "render_if" in prop_copy:
                            del prop_copy["render_if"]
                    
                    current_step_properties[key] = prop_copy
        
        # Render form with enhanced styling and lot context
        st.markdown('<div class="form-content">', unsafe_allow_html=True)
        render_form(current_step_properties, lot_context=lot_context)
        st.markdown('</div>', unsafe_allow_html=True)

        # Enhanced Navigation buttons
        render_navigation_buttons(current_step_keys)

    with col2:
        render_drafts_sidebar(draft_options)

def add_custom_css():
    """Add premium custom CSS for professional government application styling."""
    st.markdown("""
    <style>
    /* Import Inter font for modern, professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* === CSS VARIABLES - DESIGN SYSTEM === */
    :root {
        /* Primary Colors - Government Professional */
        --primary-900: #1e3a8a;
        --primary-700: #1d4ed8;
        --primary-500: #3b82f6;
        --primary-100: #dbeafe;
        --primary-50: #eff6ff;
        
        /* Neutral Colors */
        --gray-900: #111827;
        --gray-700: #374151;
        --gray-500: #6b7280;
        --gray-300: #d1d5db;
        --gray-100: #f3f4f6;
        --gray-50: #f9fafb;
        --white: #ffffff;
        
        /* Semantic Colors */
        --success: #059669;
        --success-light: #d1fae5;
        --warning: #d97706;
        --warning-light: #fef3c7;
        --error: #dc2626;
        --error-light: #fee2e2;
        --info: #0ea5e9;
        --info-light: #e0f2fe;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        
        /* Border radius */
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
    }
    
    /* === GLOBAL TYPOGRAPHY === */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--gray-900);
        line-height: 1.6;
    }
    
    /* Typography Hierarchy */
    h1 { 
        font-size: 2.5rem; 
        font-weight: 700; 
        line-height: 1.2; 
        color: var(--gray-900);
        margin-bottom: 1rem;
    }
    h2 { 
        font-size: 2rem; 
        font-weight: 600; 
        line-height: 1.3; 
        color: var(--primary-900);
        margin-bottom: 0.75rem;
    }
    h3 { 
        font-size: 1.5rem; 
        font-weight: 600; 
        line-height: 1.4; 
        color: var(--primary-700);
        margin-bottom: 0.5rem;
    }
    
    /* === MAIN LAYOUT === */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* === FORM HEADER === */
    .form-header {
        background: linear-gradient(135deg, var(--primary-900) 0%, var(--primary-700) 100%);
        color: white;
        padding: 2rem;
        border-radius: var(--radius-lg);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }
    
    .form-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                    linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                    linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        opacity: 0.3;
        pointer-events: none;
    }
    
    .form-header h1 {
        margin: 0;
        font-size: 2.25rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    .form-header h3 {
        margin: 0.5rem 0 0 0;
        font-size: 1.125rem;
        font-weight: 500;
        opacity: 0.9;
        position: relative;
        z-index: 1;
        color: var(--primary-50);
    }
    
    .step-indicator {
        font-size: 0.875rem;
        font-weight: 500;
        opacity: 0.9;
        margin-top: 0.75rem;
        position: relative;
        z-index: 1;
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: var(--radius-md);
        display: inline-block;
    }
    
    /* === PROGRESS BAR === */
    .stProgress .st-bo {
        background-color: var(--primary-100) !important;
        height: 1rem !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }
    
    .stProgress .st-bp {
        background: linear-gradient(90deg, var(--primary-500), var(--primary-700)) !important;
        border-radius: var(--radius-md) !important;
        position: relative;
    }
    
    .stProgress .st-bp::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* === BREADCRUMBS === */
    .step-breadcrumbs {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0 2rem 0;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .breadcrumb-item {
        padding: 0.625rem 1.25rem;
        border-radius: var(--radius-lg);
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .breadcrumb-item.completed {
        background: var(--success-light);
        color: var(--success);
        border-color: var(--success);
        box-shadow: var(--shadow-sm);
    }
    
    .breadcrumb-item.current {
        background: var(--primary-700);
        color: white;
        border-color: var(--primary-700);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .breadcrumb-item.current::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.2), transparent);
    }
    
    .breadcrumb-item.pending {
        background: var(--gray-100);
        color: var(--gray-500);
        border-color: var(--gray-300);
    }
    
    .breadcrumb-item:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* === FORM CONTENT === */
    .form-content {
        background: white;
        padding: 2.5rem;
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--gray-200);
        margin-bottom: 2rem;
        position: relative;
    }
    
    .form-content::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-500), var(--primary-700));
        border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    }
    
    /* === NAVIGATION BUTTONS === */
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid var(--gray-200);
    }
    
    /* === STREAMLIT COMPONENT OVERRIDES === */
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, var(--primary-700), var(--primary-500)) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        color: white !important;
        text-transform: none !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(135deg, var(--primary-900), var(--primary-700)) !important;
    }
    
    .stButton button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* Secondary buttons */
    .stButton button[kind="secondary"] {
        background: white !important;
        color: var(--primary-700) !important;
        border: 2px solid var(--primary-700) !important;
    }
    
    .stButton button[kind="secondary"]:hover {
        background: var(--primary-50) !important;
        border-color: var(--primary-900) !important;
        color: var(--primary-900) !important;
    }
    
    /* Form Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        background: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px var(--primary-100) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea {
        min-height: 120px !important;
        resize: vertical !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px var(--primary-100) !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label > div {
        background: white !important;
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-sm) !important;
    }
    
    .stCheckbox > label > div[data-checked="true"] {
        background: var(--primary-500) !important;
        border-color: var(--primary-500) !important;
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        border: 2px dashed var(--gray-300) !important;
        border-radius: var(--radius-lg) !important;
        padding: 2rem !important;
        background: var(--gray-50) !important;
        transition: all 0.2s ease !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: var(--primary-500) !important;
        background: var(--primary-50) !important;
    }
    
    /* === SECTION HEADERS === */
    [data-testid="stMarkdownContainer"] h2 {
        color: var(--primary-900) !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin: 2rem 0 1rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid var(--primary-100) !important;
        position: relative;
    }
    
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--primary-700) !important;
        font-weight: 500 !important;
        font-size: 1.25rem !important;
        margin: 1.5rem 0 0.75rem 0 !important;
    }
    
    /* === LOT/SLOT CARDS === */
    .lot-card {
        background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%) !important;
        border: 2px solid var(--primary-500) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        position: relative;
        overflow: hidden;
    }
    
    .lot-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-500);
    }
    
    .lot-card h4 {
        color: var(--primary-900) !important;
        margin: 0 0 0.5rem 0 !important;
        font-weight: 600 !important;
    }
    
    /* === SUCCESS/ERROR MESSAGES === */
    .stSuccess {
        background: var(--success-light) !important;
        border: 1px solid var(--success) !important;
        border-radius: var(--radius-md) !important;
        color: var(--success) !important;
    }
    
    .stError {
        background: var(--error-light) !important;
        border: 1px solid var(--error) !important;
        border-radius: var(--radius-md) !important;
        color: var(--error) !important;
    }
    
    .stWarning {
        background: var(--warning-light) !important;
        border: 1px solid var(--warning) !important;
        border-radius: var(--radius-md) !important;
        color: var(--warning) !important;
    }
    
    .stInfo {
        background: var(--info-light) !important;
        border: 1px solid var(--info) !important;
        border-radius: var(--radius-md) !important;
        color: var(--info) !important;
    }
    
    /* === SIDEBAR === */
    .sidebar .sidebar-content {
        padding: 1rem !important;
    }
    
    .sidebar-header {
        background: var(--gray-50) !important;
        padding: 1rem !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 1rem !important;
        border-left: 4px solid var(--primary-700) !important;
    }
    
    /* === RESPONSIVE DESIGN === */
    @media (max-width: 768px) {
        .form-header {
            padding: 1.5rem !important;
        }
        
        .form-header h1 {
            font-size: 1.75rem !important;
        }
        
        .form-content {
            padding: 1.5rem !important;
        }
        
        .step-breadcrumbs {
            gap: 0.25rem !important;
        }
        
        .breadcrumb-item {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.75rem !important;
        }
    }
    
    /* === ANIMATIONS === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .form-content {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* === ACCESSIBILITY === */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* === PRINT STYLES === */
    @media print {
        .form-header {
            background: var(--primary-900) !important;
            -webkit-print-color-adjust: exact !important;
            color-adjust: exact !important;
        }
        
        .navigation-buttons {
            display: none !important;
        }
        
        .step-breadcrumbs {
            display: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_step_breadcrumbs():
    """Render step navigation breadcrumbs."""
    from localization import get_step_label
    
    # Get dynamic form steps for breadcrumbs
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
    breadcrumbs_html = '<div class="step-breadcrumbs">'
    
    for i, step_keys in enumerate(dynamic_form_steps):
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
    # Get dynamic form steps for navigation
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
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
        if st.session_state.current_step < len(dynamic_form_steps) - 1:
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
