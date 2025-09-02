"""
Logging Reduction Patch
Converts verbose info/debug logging to conditional logging only in debug mode.

This patch wraps logging calls to only execute when explicitly in debug mode,
significantly reducing I/O overhead in production.
"""

import logging
import streamlit as st
from functools import wraps

# Original loggers - store references
_original_loggers = {}

class ConditionalLogger:
    """
    A logger wrapper that only logs when debug mode is enabled.
    """
    
    def __init__(self, name, original_logger):
        self.name = name
        self.original_logger = original_logger
        self._debug_mode = None
    
    @property
    def debug_mode(self):
        """Check if debug mode is enabled."""
        if self._debug_mode is not None:
            return self._debug_mode
        # Check session state for debug flag
        return st.session_state.get('debug_logging', False)
    
    def debug(self, msg, *args, **kwargs):
        """Only log debug messages in debug mode."""
        if self.debug_mode:
            self.original_logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Only log info messages in debug mode."""
        if self.debug_mode:
            self.original_logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Always log warnings."""
        self.original_logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Always log errors."""
        self.original_logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Always log critical messages."""
        self.original_logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """Always log exceptions."""
        self.original_logger.exception(msg, *args, **kwargs)
    
    # Pass through other logger methods
    def setLevel(self, level):
        self.original_logger.setLevel(level)
    
    def addHandler(self, handler):
        self.original_logger.addHandler(handler)
    
    def removeHandler(self, handler):
        self.original_logger.removeHandler(handler)


def wrap_logger(logger_name):
    """
    Wrap a logger to make it conditional.
    
    Args:
        logger_name: Name of the logger to wrap
    
    Returns:
        Wrapped logger
    """
    original = logging.getLogger(logger_name)
    
    # Store original if not already stored
    if logger_name not in _original_loggers:
        _original_loggers[logger_name] = original
    
    # Return wrapped logger
    return ConditionalLogger(logger_name, original)


def apply_logging_reduction():
    """
    Apply logging reduction to all verbose modules.
    This significantly reduces logging overhead in production.
    """
    
    # List of modules with excessive logging
    verbose_modules = [
        'ui.renderers.section_renderer',
        'ui.renderers.field_renderer',
        'ui.renderers.ai_field_renderer',
        'ui.renderers.ai_integration_helper',
        'ui.renderers.validation_renderer',
        'ui.controllers.form_controller',
        'utils.validations',
        'utils.validation_adapter',
        'utils.schema_utils',
        'utils.form_helpers',
        'utils.lot_utils',
        'utils.lot_navigation',
        'services.ai_response_service',
        'services.ai_suggestion_service',
        'services.qdrant_crud_service',
        'config',
        'database',
        '__main__'  # For app.py logging
    ]
    
    # Wrap each logger
    for module_name in verbose_modules:
        try:
            # Get the module's logger
            logger = logging.getLogger(module_name)
            
            # Set level to WARNING for production
            if not st.session_state.get('debug_logging', False):
                logger.setLevel(logging.WARNING)
            
        except Exception as e:
            # Silently continue if module doesn't exist
            pass
    
    # Also reduce root logger verbosity
    root_logger = logging.getLogger()
    if not st.session_state.get('debug_logging', False):
        root_logger.setLevel(logging.WARNING)
    
    return True


def enable_debug_logging():
    """Enable debug logging for troubleshooting."""
    st.session_state['debug_logging'] = True
    
    # Restore original logging levels
    for module_name in _original_loggers:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)
    
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Debug logging enabled")


def disable_debug_logging():
    """Disable debug logging for production."""
    st.session_state['debug_logging'] = False
    apply_logging_reduction()
    logging.info("Debug logging disabled")


# Configuration
LOGGING_CONFIG = {
    'production_level': logging.WARNING,
    'debug_level': logging.DEBUG,
    'verbose_modules_level': logging.ERROR,  # Even less logging for verbose modules
    'enable_performance_logging': False,  # Set to True to log performance metrics
}


def get_logging_status():
    """Get current logging configuration status."""
    return {
        'debug_mode': st.session_state.get('debug_logging', False),
        'root_level': logging.getLevelName(logging.getLogger().level),
        'wrapped_loggers': len(_original_loggers),
        'config': LOGGING_CONFIG
    }


# Auto-apply on import
if __name__ != "__main__":
    # Apply logging reduction immediately
    try:
        apply_logging_reduction()
    except:
        # Don't fail if streamlit isn't initialized yet
        pass