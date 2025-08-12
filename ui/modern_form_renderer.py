"""Modern form renderer with beautiful UI components."""
import streamlit as st
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from localization import get_text, get_validation_message
from utils.lot_utils import get_lot_scoped_key, render_lot_context_step

def render_modern_form():
    """Render the modern multi-step form with beautiful UI."""
    
    # Import existing form renderer to use as fallback
    from ui.form_renderer import render_form
    from config import get_dynamic_form_steps
    from utils.lot_utils import get_current_lot_context
    
    # Get form configuration
    form_steps = get_dynamic_form_steps(st.session_state)
    current_step = st.session_state.get('current_step', 0)
    
    # Get current step keys for lot context
    if current_step < len(form_steps):
        current_step_keys = form_steps[current_step]
    else:
        current_step_keys = []
    
    lot_context = get_current_lot_context(current_step_keys)
    
    if current_step < len(form_steps):
        current_step_properties = form_steps[current_step]
    else:
        current_step_properties = {}
    
    # Inject modern CSS styling
    inject_modern_styles()
    
    # Render the form using existing renderer with enhanced styling
    render_form(current_step_properties, lot_context=lot_context)

def inject_modern_styles():
    """Inject modern CSS styling for the form."""
    st.markdown("""
    <style>
    /* Form container styling */
    .form-container {
        background: white;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
        margin-bottom: 24px;
    }
    
    /* Progress bar styling */
    .progress-container {
        background: white;
        padding: 28px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 8px;
        background: #E5E7EB;
        border-radius: 4px;
        overflow: hidden;
        margin: 20px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3B82F6 0%, #1E40AF 100%);
        border-radius: 4px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Step indicators */
    .steps-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        position: relative;
    }
    
    .step-item {
        flex: 1;
        text-align: center;
        position: relative;
        z-index: 2;
    }
    
    .step-circle {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 16px;
        margin-bottom: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        background: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .step-circle.active {
        background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
        color: white;
        transform: scale(1.1);
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.5);
    }
    
    .step-circle.completed {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
    }
    
    .step-circle.pending {
        background: #F3F4F6;
        color: #9CA3AF;
        border: 2px solid #E5E7EB;
    }
    
    .step-label {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        transition: color 0.3s ease;
    }
    
    .step-item.active .step-label {
        color: #1E40AF;
        font-weight: 700;
    }
    
    .step-item.completed .step-label {
        color: #10B981;
    }
    
    /* Connecting lines between steps */
    .step-connector {
        position: absolute;
        top: 24px;
        left: 50%;
        right: -50%;
        height: 2px;
        background: #E5E7EB;
        z-index: 1;
    }
    
    .step-connector.completed {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
    }
    
    /* Form field styling */
    .field-container {
        margin-bottom: 28px;
        position: relative;
    }
    
    .field-label {
        display: block;
        color: #374151;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
        letter-spacing: 0.025em;
    }
    
    .field-label .required {
        color: #EF4444;
        margin-left: 4px;
    }
    
    .field-description {
        color: #6B7280;
        font-size: 13px;
        margin-top: 6px;
        display: flex;
        align-items: start;
        gap: 6px;
    }
    
    .field-description svg {
        flex-shrink: 0;
        margin-top: 1px;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        border: 2px solid #E5E7EB !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: white !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input:hover,
    .stSelectbox > div > div > div:hover,
    .stTextArea > div > div > textarea:hover,
    .stNumberInput > div > div > input:hover {
        border-color: #93C5FD !important;
    }
    
    /* Validation states */
    .field-valid input,
    .field-valid textarea,
    .field-valid select {
        border-color: #10B981 !important;
        background: #F0FDF4 !important;
    }
    
    .field-invalid input,
    .field-invalid textarea,
    .field-invalid select {
        border-color: #EF4444 !important;
        background: #FEF2F2 !important;
    }
    
    .validation-message {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
    }
    
    .validation-error {
        background: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    
    .validation-success {
        background: #D1FAE5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 28px;
        border-left: 4px solid #3B82F6;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .section-icon {
        width: 48px;
        height: 48px;
        background: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    
    .section-subtitle {
        font-size: 14px;
        color: #6B7280;
        margin-top: 4px;
    }
    
    /* Button styling */
    .form-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 28px;
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        border-radius: 16px;
        margin-top: 40px;
        border: 1px solid #E5E7EB;
        gap: 16px;
    }
    
    .stButton > button {
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%) !important;
        color: white !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: white !important;
        color: #374151 !important;
        border: 2px solid #E5E7EB !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #F9FAFB !important;
        border-color: #D1D5DB !important;
    }
    
    /* Success animation */
    @keyframes successPulse {
        0% { transform: scale(0); opacity: 0; }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .success-checkmark {
        animation: successPulse 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 240px;
        background: #1F2937;
        color: white;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        margin-left: -120px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 13px;
        line-height: 1.4;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Chip/Tag styling */
    .chip {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        background: #EBF5FF;
        color: #1E40AF;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin: 4px;
        border: 1px solid #BFDBFE;
    }
    
    .chip-remove {
        margin-left: 8px;
        cursor: pointer;
        color: #6B7280;
        transition: color 0.2s;
    }
    
    .chip-remove:hover {
        color: #EF4444;
    }
    
    /* Loading state */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    
    .loading-spinner {
        width: 48px;
        height: 48px;
        border: 4px solid #E5E7EB;
        border-top-color: #3B82F6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Accordion for expandable sections */
    .accordion {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        margin-bottom: 16px;
        overflow: hidden;
    }
    
    .accordion-header {
        padding: 16px 20px;
        background: #F9FAFB;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: background 0.2s;
    }
    
    .accordion-header:hover {
        background: #F3F4F6;
    }
    
    .accordion-content {
        padding: 20px;
        background: white;
        border-top: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

def render_form_step(step_data: Dict[str, Any], step_index: int, total_steps: int):
    """Render a single form step with modern UI."""
    
    # Step header with icon and description
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon">{step_data.get('icon', '📝')}</div>
        <div>
            <h3 class="section-title">{step_data.get('title', f'Korak {step_index + 1}')}</h3>
            <p class="section-subtitle">{step_data.get('description', '')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render form fields
    for field_key, field_data in step_data.get('fields', {}).items():
        render_modern_field(field_key, field_data)

def render_modern_field(field_key: str, field_data: Dict[str, Any]):
    """Render a modern form field with validation and styling."""
    
    field_type = field_data.get('type', 'text')
    label = field_data.get('label', field_key)
    required = field_data.get('required', False)
    help_text = field_data.get('help', '')
    placeholder = field_data.get('placeholder', '')
    
    # Create field container with validation state
    container_class = "field-container"
    if field_key in st.session_state.get('validation_errors', {}):
        container_class += " field-invalid"
    elif field_key in st.session_state.get('validated_fields', []):
        container_class += " field-valid"
    
    # Render label with required indicator
    label_html = f"""
    <div class="{container_class}">
        <label class="field-label">
            {label}
            {"<span class='required'>*</span>" if required else ""}
        </label>
    """
    st.markdown(label_html, unsafe_allow_html=True)
    
    # Render the appropriate input type
    if field_type == 'text':
        value = st.text_input(
            "",
            key=field_key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == 'textarea':
        value = st.text_area(
            "",
            key=field_key,
            placeholder=placeholder,
            height=120,
            label_visibility="collapsed"
        )
    elif field_type == 'number':
        value = st.number_input(
            "",
            key=field_key,
            min_value=field_data.get('min', 0),
            max_value=field_data.get('max', None),
            label_visibility="collapsed"
        )
    elif field_type == 'select':
        value = st.selectbox(
            "",
            options=field_data.get('options', []),
            key=field_key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == 'multiselect':
        value = st.multiselect(
            "",
            options=field_data.get('options', []),
            key=field_key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == 'date':
        value = st.date_input(
            "",
            key=field_key,
            label_visibility="collapsed"
        )
    elif field_type == 'checkbox':
        value = st.checkbox(
            label,
            key=field_key
        )
    else:
        value = None
    
    # Show help text with icon
    if help_text:
        st.markdown(f"""
        <div class="field-description">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="#6B7280">
                <path d="M8 0a8 8 0 100 16A8 8 0 008 0zm0 12a1 1 0 110-2 1 1 0 010 2zm1-3.5v.5a1 1 0 11-2 0V7a1 1 0 011-1 1.5 1.5 0 10-1.5-1.5 1 1 0 11-2 0 3.5 3.5 0 114 3.5z"/>
            </svg>
            {help_text}
        </div>
        """, unsafe_allow_html=True)
    
    # Show validation message if exists
    if field_key in st.session_state.get('validation_errors', {}):
        error_msg = st.session_state['validation_errors'][field_key]
        st.markdown(f"""
        <div class="validation-message validation-error">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8z"/>
                <path d="M7.25 5v3.25h1.5V5h-1.5zm0 4.75v1.5h1.5v-1.5h-1.5z"/>
            </svg>
            {error_msg}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return value

def render_progress_indicator(current_step: int, total_steps: int, step_names: List[str]):
    """Render a beautiful progress indicator with step names."""
    
    progress_percentage = ((current_step + 1) / total_steps) * 100
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="steps-container">
    """, unsafe_allow_html=True)
    
    # Render step circles
    for i, name in enumerate(step_names):
        status = "completed" if i < current_step else "active" if i == current_step else "pending"
        icon = "✓" if status == "completed" else str(i + 1)
        
        st.markdown(f"""
        <div class="step-item {status}">
            <div class="step-circle {status}">{icon}</div>
            <div class="step-label">{name}</div>
            {f'<div class="step-connector {status}"></div>' if i < len(step_names) - 1 else ''}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_percentage}%"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
            <span style="color: #6B7280; font-size: 14px; font-weight: 500;">
                Korak {current_step + 1} od {total_steps}
            </span>
            <span style="color: #3B82F6; font-size: 14px; font-weight: 600;">
                {int(progress_percentage)}% dokončano
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_form_actions(can_go_back: bool = True, can_save_draft: bool = True):
    """Render form action buttons with modern styling."""
    
    st.markdown('<div class="form-actions">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if can_go_back:
            if st.button("← Nazaj", key="back_btn", use_container_width=True):
                return "back"
    
    with col2:
        if can_save_draft:
            if st.button("💾 Shrani", key="save_btn", use_container_width=True):
                return "save"
    
    with col3:
        if st.button("❌ Prekliči", key="cancel_btn", use_container_width=True):
            return "cancel"
    
    with col4:
        if st.button("Naprej →", key="next_btn", type="primary", use_container_width=True):
            return "next"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return None

def show_success_animation():
    """Show a success animation when form is completed."""
    st.markdown("""
    <div style="text-align: center; padding: 60px;">
        <div class="success-checkmark" style="
            width: 100px;
            height: 100px;
            margin: 0 auto 24px;
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
            box-shadow: 0 20px 25px -5px rgba(16, 185, 129, 0.3);
        ">
            ✓
        </div>
        <h2 style="color: #111827; margin-bottom: 12px;">Uspešno shranjeno!</h2>
        <p style="color: #6B7280; font-size: 16px;">
            Vaš obrazec je bil uspešno shranjen in poslan v pregled.
        </p>
    </div>
    """, unsafe_allow_html=True)