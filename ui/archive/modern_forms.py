"""Modern form components with beautiful styling and validation."""
import streamlit as st
from typing import Dict, Any, Optional, List

def render_modern_form_field(
    field_type: str,
    label: str,
    key: str,
    required: bool = False,
    placeholder: str = "",
    help_text: str = "",
    options: List[str] = None,
    min_value: Any = None,
    max_value: Any = None,
    validation_error: str = ""
):
    """Render a modern styled form field with validation."""
    
    # Add custom CSS for form styling
    st.markdown("""
    <style>
    .form-field-container {
        margin-bottom: 24px;
        position: relative;
    }
    
    .form-label {
        display: block;
        color: #374151;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
        letter-spacing: 0.025em;
    }
    
    .form-label-required {
        color: #EF4444;
        margin-left: 4px;
    }
    
    .form-help-text {
        color: #6B7280;
        font-size: 12px;
        margin-top: 4px;
        display: block;
    }
    
    .form-error {
        color: #EF4444;
        font-size: 12px;
        margin-top: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border: 2px solid #E5E7EB !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        background: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9CA3AF !important;
        font-style: normal !important;
    }
    
    /* Validation styling */
    .field-valid {
        border-color: #10B981 !important;
    }
    
    .field-invalid {
        border-color: #EF4444 !important;
        background: #FEF2F2 !important;
    }
    
    /* Success checkmark animation */
    @keyframes checkmark {
        0% {
            transform: scale(0) rotate(45deg);
            opacity: 0;
        }
        100% {
            transform: scale(1) rotate(45deg);
            opacity: 1;
        }
    }
    
    .validation-checkmark {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: #10B981;
        animation: checkmark 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render label with required indicator
    label_html = f"""
    <label class="form-label">
        {label}
        {"<span class='form-label-required'>*</span>" if required else ""}
    </label>
    """
    st.markdown(label_html, unsafe_allow_html=True)
    
    # Render appropriate field type
    if field_type == "text":
        value = st.text_input(
            "",
            key=key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == "textarea":
        value = st.text_area(
            "",
            key=key,
            placeholder=placeholder,
            height=100,
            label_visibility="collapsed"
        )
    elif field_type == "number":
        value = st.number_input(
            "",
            key=key,
            min_value=min_value,
            max_value=max_value,
            label_visibility="collapsed"
        )
    elif field_type == "select":
        value = st.selectbox(
            "",
            options=options or [],
            key=key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == "multiselect":
        value = st.multiselect(
            "",
            options=options or [],
            key=key,
            placeholder=placeholder,
            label_visibility="collapsed"
        )
    elif field_type == "date":
        value = st.date_input(
            "",
            key=key,
            label_visibility="collapsed"
        )
    elif field_type == "time":
        value = st.time_input(
            "",
            key=key,
            label_visibility="collapsed"
        )
    elif field_type == "checkbox":
        value = st.checkbox(
            label,
            key=key
        )
    else:
        value = None
    
    # Show help text if provided
    if help_text:
        st.markdown(f"<span class='form-help-text'>{help_text}</span>", unsafe_allow_html=True)
    
    # Show validation error if provided
    if validation_error:
        st.markdown(f"""
        <div class='form-error'>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8z"/>
                <path d="M7.25 5v3.25h1.5V5h-1.5zm0 4.75v1.5h1.5v-1.5h-1.5z"/>
            </svg>
            {validation_error}
        </div>
        """, unsafe_allow_html=True)
    
    return value

def render_form_section(title: str, description: str = "", icon: str = "📋"):
    """Render a form section header with modern styling."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 24px;
                border-left: 4px solid #3B82F6;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 24px;">{icon}</span>
            <div>
                <h3 style="margin: 0; color: #111827; font-size: 18px; font-weight: 600;">
                    {title}
                </h3>
                {"<p style='margin: 4px 0 0 0; color: #6B7280; font-size: 14px;'>" + description + "</p>" if description else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_form_progress(current_step: int, total_steps: int, step_names: List[str] = None):
    """Render a beautiful form progress indicator."""
    progress_percentage = (current_step / total_steps) * 100
    
    st.markdown(f"""
    <div style="background: white; padding: 24px; border-radius: 12px; 
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); margin-bottom: 32px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
            <span style="color: #374151; font-weight: 600;">Napredek izpolnjevanja</span>
            <span style="color: #3B82F6; font-weight: 600;">{current_step}/{total_steps}</span>
        </div>
        <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #3B82F6 0%, #1E40AF 100%); 
                        height: 100%; width: {progress_percentage}%; 
                        transition: width 0.3s ease; border-radius: 4px;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render step indicators if step names provided
    if step_names:
        cols = st.columns(len(step_names))
        for i, (col, name) in enumerate(zip(cols, step_names)):
            with col:
                step_num = i + 1
                is_active = step_num == current_step
                is_completed = step_num < current_step
                
                if is_completed:
                    status_color = "#10B981"
                    status_bg = "#D1FAE5"
                    icon = "✓"
                elif is_active:
                    status_color = "#3B82F6"
                    status_bg = "#DBEAFE"
                    icon = str(step_num)
                else:
                    status_color = "#9CA3AF"
                    status_bg = "#F3F4F6"
                    icon = str(step_num)
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="display: inline-flex; align-items: center; justify-content: center;
                                width: 40px; height: 40px; border-radius: 50%;
                                background: {status_bg}; color: {status_color};
                                font-weight: 600; margin-bottom: 8px;">
                        {icon}
                    </div>
                    <div style="color: {'#111827' if is_active else '#6B7280'}; 
                                font-size: 12px; font-weight: {'600' if is_active else '400'};">
                        {name}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_form_actions(
    primary_label: str = "Naprej",
    secondary_label: str = "Nazaj",
    show_secondary: bool = True,
    show_save_draft: bool = True
):
    """Render form action buttons with modern styling."""
    st.markdown("""
    <style>
    .form-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        background: #F9FAFB;
        border-radius: 12px;
        margin-top: 32px;
        border: 1px solid #E5E7EB;
    }
    
    .form-actions-left {
        display: flex;
        gap: 12px;
    }
    
    .form-actions-right {
        display: flex;
        gap: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if show_secondary:
            if st.button(f"← {secondary_label}", key="form_back", use_container_width=True):
                return "back"
    
    with col2:
        if show_save_draft:
            if st.button("💾 Shrani osnutek", key="form_save", use_container_width=True):
                return "save"
    
    with col3:
        if st.button(f"{primary_label} →", key="form_next", type="primary", use_container_width=True):
            return "next"
    
    return None

def render_validation_summary(errors: List[str], warnings: List[str] = None):
    """Render a validation summary with errors and warnings."""
    if errors:
        st.markdown("""
        <div style="background: #FEF2F2; border: 1px solid #FCA5A5; 
                    border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <div style="display: flex; align-items: start; gap: 12px;">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="#DC2626">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 8px 0; color: #991B1B; font-weight: 600;">
                        Popravite naslednje napake:
                    </h4>
                    <ul style="margin: 0; padding-left: 20px; color: #DC2626;">
        """, unsafe_allow_html=True)
        
        for error in errors:
            st.markdown(f"<li>{error}</li>", unsafe_allow_html=True)
        
        st.markdown("""
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if warnings:
        st.markdown("""
        <div style="background: #FEF3C7; border: 1px solid #FCD34D; 
                    border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <div style="display: flex; align-items: start; gap: 12px;">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="#D97706">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 8px 0; color: #92400E; font-weight: 600;">
                        Opozorila:
                    </h4>
                    <ul style="margin: 0; padding-left: 20px; color: #D97706;">
        """, unsafe_allow_html=True)
        
        for warning in warnings:
            st.markdown(f"<li>{warning}</li>", unsafe_allow_html=True)
        
        st.markdown("""
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)