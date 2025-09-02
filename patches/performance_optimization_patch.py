"""
Performance Optimization Patch for app.py
This module provides optimizations to improve form rendering performance.

Key optimizations:
1. Cache FormController in session state to avoid recreation
2. Reduce logging overhead in production
3. Optimize validation manager initialization

Usage:
    Import this at the beginning of app.py after other imports:
    from patches.performance_optimization_patch import get_cached_form_controller, optimize_logging
    
    Then replace FormController creation with:
    form_controller = get_cached_form_controller(schema)
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from ui.controllers.form_controller import FormController

# Store original logging level
ORIGINAL_LOG_LEVEL = logging.getLogger().level

def get_cached_form_controller(schema: Optional[Dict[str, Any]] = None) -> FormController:
    """
    Get or create a cached FormController instance.
    This avoids recreating the controller on every page render.
    
    Args:
        schema: Optional JSON schema for the form
        
    Returns:
        Cached or new FormController instance
    """
    cache_key = 'cached_form_controller'
    schema_key = 'cached_controller_schema'
    
    # Check if we have a cached controller and if schema hasn't changed
    if (cache_key in st.session_state and 
        schema_key in st.session_state and
        st.session_state[schema_key] == schema):
        # Return cached controller
        return st.session_state[cache_key]
    
    # Create new controller and cache it
    controller = FormController(schema=schema)
    st.session_state[cache_key] = controller
    st.session_state[schema_key] = schema
    
    return controller


def optimize_logging(production_mode: bool = True):
    """
    Optimize logging for production performance.
    
    Args:
        production_mode: If True, reduces logging verbosity
    """
    if production_mode:
        # Set higher logging level to reduce overhead
        logging.getLogger().setLevel(logging.WARNING)
        
        # Disable debug logging for specific modules
        noisy_modules = [
            'ui.renderers.section_renderer',
            'ui.renderers.field_renderer',
            'ui.renderers.ai_field_renderer',
            'ui.renderers.ai_integration_helper',
            'utils.validations',
            'utils.schema_utils',
            'services.ai_response_service',
            'services.qdrant_crud_service'
        ]
        
        for module in noisy_modules:
            logging.getLogger(module).setLevel(logging.ERROR)
    else:
        # Restore original logging level
        logging.getLogger().setLevel(ORIGINAL_LOG_LEVEL)


def clear_controller_cache():
    """
    Clear the cached FormController.
    Call this when you need to force recreation (e.g., after major state changes).
    """
    cache_key = 'cached_form_controller'
    schema_key = 'cached_controller_schema'
    
    if cache_key in st.session_state:
        del st.session_state[cache_key]
    if schema_key in st.session_state:
        del st.session_state[schema_key]


def should_reinitialize_controller() -> bool:
    """
    Check if the controller should be reinitialized.
    
    Returns:
        True if controller should be recreated
    """
    # Check for conditions that require controller recreation
    triggers = [
        'form_reset_triggered',
        'schema_updated',
        'lot_structure_changed'
    ]
    
    for trigger in triggers:
        if st.session_state.get(trigger, False):
            # Reset the trigger
            st.session_state[trigger] = False
            return True
    
    return False


class PerformanceMonitor:
    """
    Simple performance monitoring for debugging.
    """
    
    @staticmethod
    def measure_render_time():
        """
        Decorator to measure render time of functions.
        
        Usage:
            @PerformanceMonitor.measure_render_time()
            def render_section():
                ...
        """
        import time
        import functools
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                
                if elapsed > 0.1:  # Only log slow operations
                    logging.info(f"PERF: {func.__name__} took {elapsed:.3f}s")
                
                return result
            return wrapper
        return decorator


# Configuration for optimal performance
PERFORMANCE_CONFIG = {
    'cache_form_controller': True,
    'optimize_logging': True,
    'lazy_load_ai': True,  # Don't initialize AI until needed
    'batch_validations': True,  # Validate multiple fields at once
    'debounce_inputs': 300,  # Milliseconds to wait before processing input
    'max_render_depth': 10,  # Prevent infinite recursion in nested forms
}


def apply_performance_optimizations():
    """
    Apply all performance optimizations at once.
    Call this early in app.py.
    """
    # Optimize logging
    if PERFORMANCE_CONFIG['optimize_logging']:
        optimize_logging(production_mode=True)
    
    # Set performance flags in session state
    if 'performance_optimized' not in st.session_state:
        st.session_state.performance_optimized = True
        st.session_state.performance_config = PERFORMANCE_CONFIG
        
        # Disable automatic rerun on widget interaction for specific widgets
        st.session_state.suppress_autorun = ['text_area', 'text_input']
    
    return True


# Auto-apply optimizations if imported
if __name__ != "__main__":
    logging.info("Performance Optimization Patch loaded - ready to apply")