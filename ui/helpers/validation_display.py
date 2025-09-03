"""
Unified validation display helper for consistent error styling across all form fields.
This module provides a centralized approach to displaying validation errors with red borders.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
import hashlib
import json


class ValidationDisplay:
    """
    Centralized validation display helper that provides:
    - Consistent red border styling for invalid fields
    - Error message display below fields
    - Session-based error tracking
    - Simple, reliable CSS injection without complex selectors
    """
    
    # Track which fields have been styled in this session to avoid duplicates
    _styled_fields = set()
    
    @staticmethod
    def inject_global_error_styles():
        """
        Inject global CSS for error styling once per app load.
        This provides base styles that will be applied via classes.
        """
        st.markdown("""
            <style>
            /* Global validation error styles */
            .field-error-container {
                position: relative;
                margin-bottom: 0.5rem;
            }
            
            .field-error-border {
                border: 2px solid #ff4444 !important;
                background-color: #fff5f5 !important;
                box-shadow: 0 0 0 1px #ff4444 !important;
            }
            
            .field-error-message {
                color: #ff4444;
                font-size: 0.875rem;
                margin-top: 0.25rem;
                display: flex;
                align-items: center;
                gap: 0.25rem;
            }
            
            .field-required-asterisk {
                color: #ff4444;
                font-weight: bold;
                margin-left: 0.25rem;
            }
            
            /* Apply red borders to all input types within error container */
            .has-validation-error input,
            .has-validation-error textarea,
            .has-validation-error select,
            .has-validation-error [data-baseweb="select"] > div:first-child,
            .has-validation-error [data-baseweb="input"],
            .has-validation-error [data-baseweb="textarea"] {
                border: 2px solid #ff4444 !important;
                background-color: #fff5f5 !important;
                outline: none !important;
            }
            
            /* Ensure the styles apply to Streamlit's specific elements */
            .stTextInput.has-validation-error > div > div > input,
            .stNumberInput.has-validation-error > div > div > input,
            .stSelectbox.has-validation-error > div > div > div,
            .stTextArea.has-validation-error > div > div > textarea,
            .stDateInput.has-validation-error > div > div > input,
            .stTimeInput.has-validation-error > div > div > input {
                border: 2px solid #ff4444 !important;
                background-color: #fff5f5 !important;
            }
            
            /* Style for validation summary box */
            .validation-summary {
                background-color: #fee;
                border: 2px solid #ff4444;
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
            }
            
            .validation-summary-title {
                color: #cc0000;
                font-weight: bold;
                margin-bottom: 0.5rem;
                font-size: 1rem;
            }
            
            .validation-summary-item {
                color: #660000;
                margin-left: 1.5rem;
                margin-top: 0.25rem;
                list-style-type: none;
                position: relative;
            }
            
            .validation-summary-item:before {
                content: "•";
                position: absolute;
                left: -1rem;
                color: #ff4444;
            }
            </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def mark_field_with_error(widget_key: str, field_name: str = "") -> None:
        """
        Mark a specific field as having a validation error.
        Uses JavaScript to directly add classes to the field's container.
        
        Args:
            widget_key: The Streamlit widget key
            field_name: Optional field name for more specific targeting
        """
        # Generate a unique identifier for this error marking
        error_id = hashlib.md5(f"{widget_key}_{field_name}".encode()).hexdigest()[:8]
        
        # Only inject if not already styled
        if error_id not in ValidationDisplay._styled_fields:
            ValidationDisplay._styled_fields.add(error_id)
            
            # Use JavaScript to find and mark the field
            st.markdown(f"""
                <script>
                (function() {{
                    // Wait for Streamlit to render
                    setTimeout(() => {{
                        // Try multiple strategies to find the field
                        let field = null;
                        
                        // Strategy 1: Find by key attribute
                        field = document.querySelector('[key="{widget_key}"]');
                        
                        // Strategy 2: Find input/textarea/select with matching id or name
                        if (!field) {{
                            field = document.querySelector('#{widget_key}, [name="{widget_key}"]');
                        }}
                        
                        // Strategy 3: Find by aria-label containing the field name
                        if (!field && "{field_name}") {{
                            field = document.querySelector('[aria-label*="{field_name}"]');
                        }}
                        
                        // Strategy 4: Find any input in a container with the widget key
                        if (!field) {{
                            const container = document.querySelector('[data-testid*="{widget_key}"]');
                            if (container) {{
                                field = container.querySelector('input, textarea, select');
                            }}
                        }}
                        
                        // If we found the field, style it and its containers
                        if (field) {{
                            // Add error class to the field itself
                            field.classList.add('field-error-border');
                            
                            // Find and mark parent containers
                            let parent = field.parentElement;
                            let depth = 0;
                            while (parent && depth < 5) {{
                                // Look for Streamlit component containers
                                if (parent.className && (
                                    parent.className.includes('stTextInput') ||
                                    parent.className.includes('stNumberInput') ||
                                    parent.className.includes('stSelectbox') ||
                                    parent.className.includes('stTextArea') ||
                                    parent.className.includes('stDateInput') ||
                                    parent.className.includes('stTimeInput')
                                )) {{
                                    parent.classList.add('has-validation-error');
                                    break;
                                }}
                                parent = parent.parentElement;
                                depth++;
                            }}
                            
                            // Alternative: Mark by data-testid
                            const testidContainers = document.querySelectorAll('[data-testid]');
                            testidContainers.forEach(container => {{
                                if (container.contains(field)) {{
                                    container.classList.add('has-validation-error');
                                }}
                            }});
                        }}
                    }}, 100);
                }})();
                </script>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def display_field_error(error_message: str) -> None:
        """
        Display an error message below a field.
        
        Args:
            error_message: The error message to display
        """
        st.markdown(
            f'<div class="field-error-message">⚠️ {error_message}</div>',
            unsafe_allow_html=True
        )
    
    @staticmethod
    def display_validation_summary(errors: List[str], title: str = "Prosimo, popravite naslednje napake:") -> None:
        """
        Display a validation summary box with all errors.
        
        Args:
            errors: List of error messages
            title: Title for the validation summary
        """
        if not errors:
            return
        
        error_html = f'<div class="validation-summary"><div class="validation-summary-title">❌ {title}</div>'
        for error in errors:
            error_html += f'<div class="validation-summary-item">{error}</div>'
        error_html += '</div>'
        
        st.markdown(error_html, unsafe_allow_html=True)
    
    @staticmethod
    def format_label_with_asterisk(label: str, required: bool) -> str:
        """
        Format a field label with a red asterisk if required.
        
        Args:
            label: The field label
            required: Whether the field is required
            
        Returns:
            HTML formatted label with asterisk if required
        """
        if required:
            return f'{label}<span class="field-required-asterisk">*</span>'
        return label
    
    @staticmethod
    def clear_field_errors():
        """Clear all field error markings for a fresh validation pass."""
        ValidationDisplay._styled_fields.clear()
        
        # Inject JavaScript to remove error classes
        st.markdown("""
            <script>
            // Remove all validation error classes
            document.querySelectorAll('.has-validation-error').forEach(el => {
                el.classList.remove('has-validation-error');
            });
            document.querySelectorAll('.field-error-border').forEach(el => {
                el.classList.remove('field-error-border');
            });
            </script>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_field_with_validation(
        field_renderer_func,
        field_name: str,
        widget_key: str,
        validation_errors: List[str] = None,
        required: bool = False,
        **field_args
    ) -> Any:
        """
        Wrapper to render a field with validation styling.
        
        Args:
            field_renderer_func: The function to render the field
            field_name: Name of the field
            widget_key: Widget key for the field
            validation_errors: List of validation errors for this field
            required: Whether field is required
            **field_args: Additional arguments for the field renderer
            
        Returns:
            The value from the field renderer
        """
        # Mark field with error if there are validation errors
        if validation_errors:
            ValidationDisplay.mark_field_with_error(widget_key, field_name)
        
        # Render the field
        value = field_renderer_func(**field_args)
        
        # Display error messages below the field
        if validation_errors:
            for error in validation_errors:
                ValidationDisplay.display_field_error(error)
        
        return value