"""
Accessibility and performance enhancements for admin UI
Implements WCAG 2.1 AA compliance and performance optimizations
"""

import streamlit as st
from functools import lru_cache
import time
from typing import Any, List, Dict, Optional


def add_keyboard_navigation():
    """Add comprehensive keyboard navigation support"""
    
    keyboard_script = """
    <script>
    // Global keyboard navigation handler
    document.addEventListener('DOMContentLoaded', function() {
        // Tab order management
        const tabbableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Alt + 1-7 for tab navigation
            if (e.altKey && e.key >= '1' && e.key <= '7') {
                const tabIndex = parseInt(e.key) - 1;
                const tabs = document.querySelectorAll('[role="tab"]');
                if (tabs[tabIndex]) {
                    tabs[tabIndex].click();
                    tabs[tabIndex].focus();
                }
            }
            
            // Ctrl+K for search focus
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('.search-input');
                if (searchInput) searchInput.focus();
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal.active');
                if (modal) modal.classList.remove('active');
            }
        });
        
        // Skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-to-main';
        skipLink.textContent = 'Preskoči na glavno vsebino';
        skipLink.setAttribute('aria-label', 'Preskoči na glavno vsebino');
        document.body.insertBefore(skipLink, document.body.firstChild);
    });
    </script>
    
    <style>
    /* Skip link for keyboard navigation */
    .skip-to-main {
        position: absolute;
        left: -9999px;
        z-index: 999;
        padding: 1em;
        background: var(--accent-blue);
        color: white;
        text-decoration: none;
        border-radius: var(--radius-md);
    }
    
    .skip-to-main:focus {
        left: 50%;
        transform: translateX(-50%);
        top: 10px;
    }
    
    /* Enhanced focus indicators */
    *:focus {
        outline: none;
    }
    
    *:focus-visible {
        outline: 2px solid var(--accent-blue);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
    }
    
    button:focus-visible,
    a:focus-visible {
        outline: 3px solid var(--accent-blue);
        outline-offset: 3px;
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        * {
            border-width: 2px !important;
        }
        
        button, .button, .modern-button {
            border: 2px solid currentColor !important;
        }
        
        .modern-card {
            border: 2px solid var(--text-primary) !important;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """
    
    st.markdown(keyboard_script, unsafe_allow_html=True)


def enhance_with_aria(component_html: str, component_type: str, **aria_attrs) -> str:
    """
    Add ARIA attributes to components for screen reader support
    
    Args:
        component_html: HTML string to enhance
        component_type: Type of component
        **aria_attrs: Additional ARIA attributes
        
    Returns:
        Enhanced HTML with ARIA attributes
    """
    
    aria_mappings = {
        'card': {
            'role': 'article',
            'aria-label': aria_attrs.get('label', 'Content card')
        },
        'table': {
            'role': 'table',
            'aria-label': aria_attrs.get('label', 'Data table'),
            'aria-rowcount': aria_attrs.get('rowcount', ''),
            'aria-colcount': aria_attrs.get('colcount', '')
        },
        'button': {
            'role': 'button',
            'aria-label': aria_attrs.get('label', ''),
            'aria-pressed': aria_attrs.get('pressed', 'false'),
            'aria-disabled': aria_attrs.get('disabled', 'false')
        },
        'notification': {
            'role': 'alert',
            'aria-live': 'polite',
            'aria-atomic': 'true'
        },
        'search': {
            'role': 'search',
            'aria-label': 'Iskanje',
            'aria-describedby': aria_attrs.get('describedby', '')
        },
        'navigation': {
            'role': 'navigation',
            'aria-label': aria_attrs.get('label', 'Glavna navigacija')
        },
        'tab': {
            'role': 'tab',
            'aria-selected': aria_attrs.get('selected', 'false'),
            'aria-controls': aria_attrs.get('controls', '')
        }
    }
    
    # Build ARIA attribute string
    aria_string = ''
    if component_type in aria_mappings:
        for attr, value in aria_mappings[component_type].items():
            if value:
                aria_string += f' {attr}="{value}"'
    
    # Inject ARIA attributes into HTML
    if '<div' in component_html:
        component_html = component_html.replace('<div', f'<div{aria_string}', 1)
    elif '<button' in component_html:
        component_html = component_html.replace('<button', f'<button{aria_string}', 1)
    elif '<table' in component_html:
        component_html = component_html.replace('<table', f'<table{aria_string}', 1)
    
    return component_html


def announce_to_screen_reader(message: str, priority: str = "polite"):
    """
    Create live region for screen reader announcements
    
    Args:
        message: Message to announce
        priority: Priority level (polite, assertive)
    """
    
    announcement_html = f"""
    <div role="status" aria-live="{priority}" aria-atomic="true" class="sr-only">
        {message}
    </div>
    <style>
    .sr-only {{
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }}
    </style>
    """
    
    st.markdown(announcement_html, unsafe_allow_html=True)


class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def cached_data_load(query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Cache frequently accessed data
        
        Args:
            query: Database query or data identifier
            params: Query parameters
            
        Returns:
            Cached data
        """
        # This would be replaced with actual data loading logic
        return []
    
    @staticmethod
    def debounce_input(key: str, delay_ms: int = 300) -> bool:
        """
        Debounce user input to reduce processing
        
        Args:
            key: Session state key for the input
            delay_ms: Delay in milliseconds
            
        Returns:
            True if input should be processed
        """
        
        current_time = time.time()
        
        if f"{key}_timer" not in st.session_state:
            st.session_state[f"{key}_timer"] = current_time
            return True
        
        time_diff = (current_time - st.session_state[f"{key}_timer"]) * 1000
        
        if time_diff >= delay_ms:
            st.session_state[f"{key}_timer"] = current_time
            return True
        
        return False
    
    @staticmethod
    def lazy_load_component(component_func, placeholder_text="Nalagam..."):
        """
        Lazy load heavy components
        
        Args:
            component_func: Function that renders the component
            placeholder_text: Text to show while loading
            
        Returns:
            Component result
        """
        placeholder = st.empty()
        placeholder.text(placeholder_text)
        
        # Use session state to track if component is loaded
        component_key = f"{component_func.__name__}_loaded"
        
        if component_key not in st.session_state:
            # Load component
            result = component_func()
            st.session_state[component_key] = True
            placeholder.empty()
            return result
        else:
            placeholder.empty()
            return component_func()


def add_micro_interactions():
    """Add subtle animations and micro-interactions"""
    
    interactions_css = """
    <style>
    /* Button press effect */
    button, .button, .modern-button {
        position: relative;
        transition: all 0.15s ease;
        transform: translateY(0);
    }
    
    button:active, .button:active, .modern-button:active {
        transform: translateY(1px);
    }
    
    /* Card hover lift */
    .modern-card {
        transition: all 0.2s ease;
        transform: translateY(0);
    }
    
    .modern-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Smooth focus transitions */
    input, select, textarea {
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    
    /* Success animation */
    @keyframes success-pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
        }
    }
    
    .success-animation {
        animation: success-pulse 1s;
    }
    
    /* Smooth scroll behavior */
    html {
        scroll-behavior: smooth;
    }
    
    /* Link underline animation */
    a {
        position: relative;
        text-decoration: none;
    }
    
    a::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 0;
        height: 1px;
        background: var(--accent-blue);
        transition: width 0.3s ease;
    }
    
    a:hover::after {
        width: 100%;
    }
    
    /* Loading dots animation */
    @keyframes loading-dots {
        0%, 20% {
            content: '.';
        }
        40% {
            content: '..';
        }
        60%, 100% {
            content: '...';
        }
    }
    
    .loading-dots::after {
        content: '';
        animation: loading-dots 1.5s infinite;
    }
    </style>
    """
    
    st.markdown(interactions_css, unsafe_allow_html=True)


def prepare_dark_mode():
    """Prepare CSS variables for dark mode support"""
    
    dark_mode_css = """
    <style>
    /* Dark mode color scheme */
    [data-theme="dark"] {
        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-tertiary: #94A3B8;
        --bg-primary: #0F172A;
        --bg-secondary: #1E293B;
        --bg-tertiary: #334155;
        --border: #334155;
        --border-hover: #475569;
        --accent: #3B82F6;
        --accent-hover: #60A5FA;
        --accent-blue: #3B82F6;
        --success-green: #10B981;
        --warning-amber: #F59E0B;
        --error-red: #EF4444;
    }
    
    /* Automatic dark mode based on system preference */
    @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) {
            --text-primary: #F8FAFC;
            --text-secondary: #CBD5E1;
            --text-tertiary: #94A3B8;
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-tertiary: #334155;
            --border: #334155;
            --border-hover: #475569;
        }
        
        /* Adjust component styles for dark mode */
        .modern-card {
            background: var(--bg-secondary);
            border-color: var(--border);
        }
        
        .modern-table {
            background: var(--bg-secondary);
        }
        
        .modern-table th {
            background: var(--bg-tertiary);
        }
        
        .modern-table tbody tr:hover {
            background: var(--bg-tertiary);
        }
        
        .status-badge {
            filter: brightness(1.2);
        }
    }
    
    /* Theme toggle preparation (for future use) */
    .theme-toggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--bg-tertiary);
        border: 2px solid var(--border);
        cursor: pointer;
        z-index: 1000;
        display: none; /* Hidden by default */
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }
    
    .theme-toggle:hover {
        transform: scale(1.1);
    }
    </style>
    """
    
    st.markdown(dark_mode_css, unsafe_allow_html=True)


def initialize_accessibility():
    """Initialize all accessibility features"""
    add_keyboard_navigation()
    add_micro_interactions()
    prepare_dark_mode()


# Export all functions
__all__ = [
    'add_keyboard_navigation',
    'enhance_with_aria',
    'announce_to_screen_reader',
    'PerformanceOptimizer',
    'add_micro_interactions',
    'prepare_dark_mode',
    'initialize_accessibility'
]