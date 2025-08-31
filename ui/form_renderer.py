"""
Form Renderer - Now using new unified lot architecture.
This module redirects to the new FormController system.
"""

# Import everything from the new system
from ui.controllers.form_controller import FormController
from ui.form_renderer_compat import (
    render_form,
    render_step,
    get_form_data,
    validate_form,
    clear_form
)

# For backward compatibility, export the main function
__all__ = [
    'render_form',
    'render_step', 
    'get_form_data',
    'validate_form',
    'clear_form',
    'FormController'
]