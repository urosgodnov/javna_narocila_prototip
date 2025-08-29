"""
Loading state management for admin UI
Provides loading indicators and state management
"""

import streamlit as st
import time
from contextlib import contextmanager
from typing import Any, Optional
from ui.components.modern_components import skeleton_loader


class LoadingStateManager:
    """Manages loading states across the application"""
    
    @staticmethod
    @contextmanager
    def loading_section(
        message: str = "Nalagam...", 
        show_after_ms: int = 500,
        show_skeleton: bool = True
    ):
        """
        Context manager for showing loading states for sections
        
        Args:
            message: Loading message to display
            show_after_ms: Show loader after this many milliseconds
            show_skeleton: Whether to show skeleton loader
        """
        placeholder = st.empty()
        start_time = time.time()
        
        try:
            # Show initial state immediately if needed
            if show_after_ms == 0:
                with placeholder.container():
                    st.info(message)
                    if show_skeleton:
                        skeleton_loader(lines=3)
            
            yield placeholder
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Only show loader if operation took longer than threshold
            if elapsed_ms > show_after_ms and show_after_ms > 0:
                with placeholder.container():
                    st.info(message)
                    if show_skeleton:
                        skeleton_loader(lines=3)
                time.sleep(0.5)  # Show loader briefly
            
            placeholder.empty()
    
    @staticmethod
    def with_spinner(message: str = "Procesiranje..."):
        """
        Decorator for functions that need loading spinner
        
        Args:
            message: Loading message
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                with st.spinner(message):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def show_progress(
        current: int, 
        total: int, 
        message: str = "Napredek",
        key: Optional[str] = None
    ):
        """
        Show progress bar for long operations
        
        Args:
            current: Current progress value
            total: Total value
            message: Progress message
            key: Unique key for the progress bar
        """
        progress = min(current / total if total > 0 else 0, 1.0)
        
        # Create progress container
        container = st.container()
        with container:
            st.markdown(f"**{message}**")
            progress_bar = st.progress(progress, key=key)
            st.caption(f"{current} od {total} ({progress*100:.0f}%)")
        
        return progress_bar
    
    @staticmethod
    def lazy_load_section(
        section_func,
        cache_key: str,
        placeholder_text: str = "Nalagam vsebino...",
        cache_ttl: int = 300
    ):
        """
        Lazy load a section with caching
        
        Args:
            section_func: Function that renders the section
            cache_key: Key for caching
            placeholder_text: Text to show while loading
            cache_ttl: Cache time-to-live in seconds
        """
        # Check if already loaded in session
        loaded_key = f"{cache_key}_loaded"
        data_key = f"{cache_key}_data"
        
        if loaded_key not in st.session_state:
            with LoadingStateManager.loading_section(placeholder_text):
                # Load the section
                result = section_func()
                
                # Cache the result
                st.session_state[loaded_key] = True
                st.session_state[data_key] = result
                
                return result
        else:
            # Return cached result
            return st.session_state.get(data_key)
    
    @staticmethod
    def batch_operation_progress(
        items: list,
        operation_func,
        message: str = "Procesiranje",
        show_items: bool = True
    ):
        """
        Process items in batch with progress indicator
        
        Args:
            items: List of items to process
            operation_func: Function to apply to each item
            message: Progress message
            show_items: Whether to show current item being processed
        """
        total = len(items)
        results = []
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        for idx, item in enumerate(items):
            # Update progress
            with progress_placeholder.container():
                progress = (idx + 1) / total
                st.progress(progress)
                
            # Update status
            with status_placeholder.container():
                if show_items:
                    st.caption(f"{message}: {item} ({idx + 1}/{total})")
                else:
                    st.caption(f"{message}: {idx + 1}/{total}")
            
            # Process item
            result = operation_func(item)
            results.append(result)
        
        # Clear placeholders
        progress_placeholder.empty()
        status_placeholder.empty()
        
        return results


# Standalone functions for easy import
def show_loading_skeleton(lines: int = 3, width_percentages: Optional[list] = None):
    """Show skeleton loader with default styling"""
    skeleton_loader(lines, width_percentages)


def async_load_with_cache(func):
    """
    Decorator for async loading with automatic caching
    
    Usage:
        @async_load_with_cache
        def load_heavy_data():
            # Heavy computation
            return data
    """
    @st.cache_data(ttl=300)
    def cached_func(*args, **kwargs):
        return func(*args, **kwargs)
    
    def wrapper(*args, **kwargs):
        with LoadingStateManager.loading_section("Nalagam podatke..."):
            return cached_func(*args, **kwargs)
    
    return wrapper


# Export all utilities
__all__ = [
    'LoadingStateManager',
    'show_loading_skeleton',
    'async_load_with_cache'
]