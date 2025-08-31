"""
Compatibility wrapper for transitioning from old form_renderer to new FormController.
This module provides a drop-in replacement for the old render_form function.
"""

import streamlit as st
from typing import Dict, Any, Optional
from ui.controllers.form_controller import FormController


def render_form(schema: Dict[str, Any], 
                step: Optional[str] = None,
                lot_context: Optional[Dict] = None,
                **kwargs) -> None:
    """
    Compatibility wrapper for old render_form function.
    Maps old API to new FormController architecture.
    
    Args:
        schema: Form schema or step properties
        step: Current step name (optional)
        lot_context: Lot context (handled automatically in new system)
        **kwargs: Additional arguments (for compatibility)
    """
    # Initialize FormController with current session state
    controller = FormController()
    
    # Handle different schema formats
    if schema:
        # Check if this is a step schema or full form schema
        if 'type' in schema or 'properties' in schema:
            # This is a valid schema
            controller.set_schema(schema)
        elif isinstance(schema, dict):
            # Might be step properties, wrap in object schema
            wrapped_schema = {
                'type': 'object',
                'properties': schema
            }
            controller.set_schema(wrapped_schema)
    
    # Handle lot context if provided (for backward compatibility)
    if lot_context:
        # In new system, lot context is managed automatically
        # Check if we need to switch to a specific lot
        if 'lot_index' in lot_context:
            controller.context.switch_to_lot(lot_context['lot_index'])
        elif 'current_lot' in lot_context:
            # Find lot by name
            lots = controller.context.get_all_lots()
            for lot in lots:
                if lot['name'] == lot_context['current_lot']:
                    controller.context.switch_to_lot(lot['index'])
                    break
    
    # Render the form using new controller
    # Check for specific rendering options in kwargs
    show_lot_navigation = kwargs.get('show_lot_navigation', True)
    lot_navigation_style = kwargs.get('lot_navigation_style', 'tabs')
    show_progress = kwargs.get('show_progress', False)
    show_validation_summary = kwargs.get('show_validation_summary', True)
    
    # If we have multiple lots, show navigation
    if controller.context.get_lot_count() > 1:
        show_lot_navigation = True
    
    # Render form with new controller
    controller.render_form(
        schema=None,  # Already set above
        show_lot_navigation=show_lot_navigation,
        lot_navigation_style=lot_navigation_style,
        show_progress=show_progress,
        show_validation_summary=show_validation_summary
    )


def render_step(step_name: str, step_schema: Dict[str, Any], **kwargs) -> None:
    """
    Render a specific step of a form.
    Compatibility function for step-based rendering.
    
    Args:
        step_name: Name of the step
        step_schema: Schema for the step
        **kwargs: Additional rendering options
    """
    # Use render_form with step context
    render_form(step_schema, step=step_name, **kwargs)


def get_form_data() -> Dict[str, Any]:
    """
    Get all form data in the new lot-structured format.
    
    Returns:
        Dictionary with lot-structured form data
    """
    controller = FormController()
    return controller.get_form_data()


def validate_form() -> bool:
    """
    Validate the entire form.
    
    Returns:
        True if valid, False otherwise
    """
    controller = FormController()
    return controller.validate_form()


def clear_form() -> None:
    """
    Clear all form data while preserving lot structure.
    """
    controller = FormController()
    controller.clear_form()


# Additional compatibility exports
__all__ = [
    'render_form',
    'render_step',
    'get_form_data',
    'validate_form',
    'clear_form'
]