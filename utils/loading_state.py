"""Loading state management for smooth UI transitions."""
import streamlit as st
import time

def set_loading_state(message="Nalagam..."):
    """Set loading state with message that persists across reruns.
    
    Args:
        message: Loading message to display
    """
    st.session_state['_is_loading'] = True
    st.session_state['_loading_message'] = message
    st.session_state['_loading_timestamp'] = time.time()

def clear_loading_state():
    """Clear the loading state."""
    if '_is_loading' in st.session_state:
        del st.session_state['_is_loading']
    if '_loading_message' in st.session_state:
        del st.session_state['_loading_message']
    if '_loading_timestamp' in st.session_state:
        del st.session_state['_loading_timestamp']

def is_loading():
    """Check if currently in loading state."""
    return st.session_state.get('_is_loading', False)

def get_loading_message():
    """Get current loading message."""
    return st.session_state.get('_loading_message', 'Nalagam...')

def render_loading_indicator():
    """Render loading indicator if in loading state.
    Returns True if loading, False otherwise.
    """
    if is_loading():
        # Clear loading state immediately
        message = get_loading_message()
        clear_loading_state()
        
        # Don't show spinner, just let the page transition happen
        # The loading state was just used to track the transition
        return False
    return False

# Loading messages for different operations
LOADING_MESSAGES = {
    'new_form': 'Pripravljam nov obrazec...',
    'load_form': 'Nalagam obrazec...',
    'next_step': 'Nalagam naslednji korak...',
    'prev_step': 'Vračam na prejšnji korak...',
    'save_progress': 'Shranjujem napredek...',
    'load_draft': 'Nalagam osnutek...',
    'submit_form': 'Oddajam naročilo...',
    'refresh': 'Osvežujem podatke...',
    'delete': 'Brišem vnos...',
    'edit': 'Pripravljam urejanje...',
    'back_to_dashboard': 'Vračam na pregled...',
    'cancel': 'Prekinjam vnos...',
    'validate': 'Preverjam podatke...'
}