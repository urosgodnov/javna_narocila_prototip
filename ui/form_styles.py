"""
Form styling CSS that matches the dashboard design.
Consistent color scheme and button styles across the application.
"""

import streamlit as st

def get_form_styles():
    """Return CSS styles for the form that match dashboard styling."""
    return """
    <style>
    /* ========================================
       COLOR PALETTE - Matching Dashboard
    ======================================== */
    :root {
        --primary-green: #86efac;
        --primary-green-hover: #65d989;
        --primary-green-dark: #14532d;
        
        --secondary-gray: #6c757d;
        --secondary-gray-dark: #5a6268;
        --secondary-gray-darker: #495057;
        
        --danger-red: #ef4444;
        --danger-red-dark: #dc2626;
        
        --border-light: #e2e8f0;
        --border-focus: #667eea;
        --bg-light: #f8fafc;
        --text-dark: #1e293b;
        --text-muted: #64748b;
    }
    
    /* ========================================
       BUTTON STYLES - Exact Dashboard Match
    ======================================== */
    
    /* Ensure all buttons in navigation are aligned */
    .navigation-buttons .stButton {
        display: flex !important;
        align-items: center !important;
        height: 100% !important;
    }
    
    /* Default navigation buttons (Nazaj) - Gray gradient like dashboard */
    .stButton > button {
        background: linear-gradient(135deg, #6c757d, #5a6268) !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        min-width: 100px;
        margin: 0 !important;  /* Remove all margins for consistent alignment */
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6268, #495057) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(108,117,125,0.3) !important;
    }
    
    /* Primary button (Naprej) - Blue gradient */
    .primary-button > button,
    button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2) !important;
        margin: 0 !important;  /* Remove all margins for consistent alignment */
        padding: 0.5rem 1.5rem !important;  /* Same padding as other buttons */
    }
    
    .primary-button > button:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Note: Save buttons now use default gray style - removed green styling */
    
    /* Cancel/Abort buttons - Neutral style with border and X icon */
    button:has-text("Prekliči"),
    button:has-text("✕"),
    button:has-text("Opusti"),
    .cancel-button > button {
        background-color: white !important;
        background-image: none !important;
        color: #374151 !important;
        border: 2px solid #9ca3af !important;
        font-weight: 500 !important;
    }
    
    button:has-text("Prekliči"):hover,
    button:has-text("✕"):hover,
    button:has-text("Opusti"):hover,
    .cancel-button > button:hover {
        background-color: #f3f4f6 !important;
        border-color: #6b7280 !important;
        color: #111827 !important;
    }
    
    /* Delete/Remove buttons - Consistent neutral style with border for all removal actions */
    button:has-text("❌"),
    button:has-text("Odstrani"),
    button:has-text("Izbriši"),
    button[key*="remove"],
    button[key*="delete"],
    .delete-button > button {
        background-color: white !important;
        background-image: none !important;
        color: #dc2626 !important;
        border: 2px solid #dc2626 !important;
        font-weight: 500 !important;
        min-width: auto !important;
        padding: 0.25rem 0.75rem !important;
    }
    
    button:has-text("❌"):hover,
    button:has-text("Odstrani"):hover,
    button:has-text("Izbriši"):hover,
    button[key*="remove"]:hover,
    button[key*="delete"]:hover,
    .delete-button > button:hover {
        background-color: #fef2f2 !important;
        border-color: #b91c1c !important;
        color: #991b1b !important;
    }
    
    /* ========================================
       INPUT FIELD STYLES
    ======================================== */
    
    /* Text inputs and textareas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.2s ease !important;
        background-color: white !important;
        font-size: 14px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > div {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background-color: white !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div > div:hover {
        border-color: #cbd5e1 !important;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div > div {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background-color: white !important;
    }
    
    /* ========================================
       FORM STEP INDICATOR - Disabled to prevent conflicts
    ======================================== */
    
    /* Progress bar container - COMMENTED OUT to prevent blue rectangle issue
    .step-indicator {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .step-indicator h3 {
        color: white !important;
        margin: 0 !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
    }
    
    .step-indicator .progress-text {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem !important;
        margin-top: 0.5rem !important;
    }
    */
    
    /* Progress bar itself */
    .stProgress > div > div {
        background-color: rgba(255, 255, 255, 0.2) !important;
        height: 8px !important;
        border-radius: 4px !important;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #86efac, #65d989) !important;
        border-radius: 4px !important;
    }
    
    /* ========================================
       VALIDATION & ERROR STATES
    ======================================== */
    
    /* Error state for inputs */
    .input-error {
        border-color: #ef4444 !important;
        background-color: #fef2f2 !important;
    }
    
    .input-error:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    /* Success state */
    .input-success {
        border-color: #16a34a !important;
        background-color: #f0fdf4 !important;
    }
    
    /* Validation messages */
    .validation-error {
        color: #dc2626;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .validation-success {
        color: #16a34a;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    /* ========================================
       FORM SECTIONS & CARDS
    ======================================== */
    
    /* Form section cards */
    .form-section {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    .form-section:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        border-color: #cbd5e1;
    }
    
    .form-section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f1f5f9;
    }
    
    /* ========================================
       CHECKBOX & RADIO STYLES
    ======================================== */
    
    /* Checkboxes */
    .stCheckbox > label > div[data-testid="stCheckbox"] > label {
        display: flex !important;
        align-items: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > label:hover {
        color: #667eea !important;
    }
    
    /* Radio buttons */
    .stRadio > div > label {
        display: flex !important;
        align-items: center !important;
        padding: 0.5rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stRadio > div > label:hover {
        background-color: #f8fafc !important;
        color: #667eea !important;
    }
    
    /* ========================================
       HELPER TEXT & LABELS
    ======================================== */
    
    /* Field labels */
    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stTextArea > label,
    .stDateInput > label {
        color: #1e293b !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Required field indicator */
    .required-field::after {
        content: " *";
        color: #ef4444;
        font-weight: bold;
    }
    
    /* Help text */
    .field-help-text {
        color: #64748b;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        font-style: italic;
    }
    
    /* ========================================
       EXPANDER STYLES
    ======================================== */
    
    .streamlit-expanderHeader {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        color: #1e293b !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
    }
    
    /* ========================================
       ANIMATION CLASSES
    ======================================== */
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-slide-in {
        animation: slideIn 0.3s ease-out;
    }
    
    /* Smooth transitions for all interactive elements */
    button, input, textarea, select {
        transition: all 0.2s ease !important;
    }
    </style>
    """

def apply_form_styles():
    """Apply form styles to the current page."""
    st.markdown(get_form_styles(), unsafe_allow_html=True)