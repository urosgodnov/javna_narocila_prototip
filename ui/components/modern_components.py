"""
Modern component library for admin UI
Implements reusable components following the design system
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Literal
import time
from contextlib import contextmanager


def modern_card(
    title: str,
    content: str,
    actions: Optional[List[Dict[str, Any]]] = None,
    key: Optional[str] = None
) -> None:
    """
    Render a modern card component
    
    Args:
        title: Card title
        content: HTML content for the card body
        actions: List of action buttons with 'label' and 'key'
        key: Unique key for the card
    """
    actions_html = ""
    if actions:
        action_buttons = []
        for action in actions:
            button_html = f'''
            <button class="modern-button modern-button-secondary" 
                    onclick="handleAction('{action.get("key", "")}')">
                {action.get("label", "")}
            </button>
            '''
            action_buttons.append(button_html)
        actions_html = f'<div class="card-actions">{"".join(action_buttons)}</div>'
    
    card_html = f"""
    <div class="modern-card" id="{key or 'card'}">
        <div class="card-header">
            <h3>{title}</h3>
        </div>
        <div class="card-content">
            {content}
        </div>
        {actions_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def modern_table(
    data: List[Dict],
    columns: List[str],
    sortable: bool = True,
    key: Optional[str] = None
) -> None:
    """
    Render a modern data table
    
    Args:
        data: List of dictionaries with table data
        columns: List of column names to display
        sortable: Whether columns should be sortable
        key: Unique key for the table
    """
    if not data:
        st.info("No data to display")
        return
    
    # Build table HTML
    thead_html = "<thead><tr>"
    for col in columns:
        sort_class = "sortable" if sortable else ""
        thead_html += f'<th class="{sort_class}">{col}</th>'
    thead_html += "</tr></thead>"
    
    tbody_html = "<tbody>"
    for row in data:
        tbody_html += "<tr>"
        for col in columns:
            value = row.get(col, "")
            tbody_html += f"<td>{value}</td>"
        tbody_html += "</tr>"
    tbody_html += "</tbody>"
    
    table_html = f"""
    <table class="modern-table" id="{key or 'table'}">
        {thead_html}
        {tbody_html}
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def status_badge(
    status: Literal["success", "warning", "error", "info", "default"],
    text: str,
    key: Optional[str] = None
) -> str:
    """
    Return HTML for a status badge
    
    Args:
        status: Badge status type
        text: Badge text
        key: Optional unique key
        
    Returns:
        HTML string for the badge
    """
    return f"""
    <span class="status-badge status-{status}" id="{key or 'badge'}">
        {text}
    </span>
    """


def skeleton_loader(
    lines: int = 3,
    width_percentages: Optional[List[int]] = None
) -> None:
    """
    Display skeleton loading animation
    
    Args:
        lines: Number of skeleton lines
        width_percentages: Width for each line as percentage
    """
    widths = width_percentages or [60, 80, 45]
    skeleton_html = '<div class="skeleton-loader">'
    for i in range(lines):
        width = widths[i % len(widths)]
        skeleton_html += f'<div class="skeleton-line" style="width: {width}%"></div>'
    skeleton_html += '</div>'
    st.markdown(skeleton_html, unsafe_allow_html=True)


def progress_bar(
    percentage: float,
    label: Optional[str] = None,
    key: Optional[str] = None
) -> str:
    """
    Return HTML for a progress bar
    
    Args:
        percentage: Progress percentage (0-100)
        label: Optional label text
        key: Unique key
        
    Returns:
        HTML string for progress bar
    """
    percentage = max(0, min(100, percentage))  # Clamp between 0-100
    
    label_html = f'<div class="progress-label">{label}</div>' if label else ''
    
    return f"""
    <div id="{key or 'progress'}">
        <div class="progress-container">
            <div class="progress-bar" style="width: {percentage}%"></div>
        </div>
        {label_html}
    </div>
    """


def toast_notification(
    message: str,
    type: Literal["success", "error", "warning", "info"] = "info",
    duration: int = 5000,
    key: Optional[str] = None
) -> None:
    """
    Display a toast notification
    
    Args:
        message: Notification message
        type: Notification type
        duration: Duration in milliseconds
        key: Unique key
    """
    toast_html = f"""
    <div class="toast-notification toast-{type}" id="{key or 'toast'}">
        <div class="toast-content">{message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    </div>
    <script>
        setTimeout(() => {{
            const toast = document.getElementById('{key or "toast"}');
            if (toast) toast.remove();
        }}, {duration});
    </script>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


def search_input(
    placeholder: str = "Search...",
    value: str = "",
    key: Optional[str] = None,
    on_change: Optional[Any] = None
) -> str:
    """
    Render a modern search input
    
    Args:
        placeholder: Placeholder text
        value: Current value
        key: Streamlit key for the input
        on_change: Callback function
        
    Returns:
        The search input value
    """
    # Use Streamlit's native text_input with custom styling
    search_value = st.text_input(
        label="Search",
        placeholder=placeholder,
        value=value,
        key=key,
        on_change=on_change,
        label_visibility="collapsed"
    )
    
    # Add custom styling
    st.markdown("""
    <style>
        div[data-testid="stTextInput"] > div > div > input {
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            transition: all var(--transition-fast);
        }
        
        div[data-testid="stTextInput"] > div > div > input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    return search_value


def modern_button(
    text: str,
    variant: Literal["primary", "secondary"] = "primary",
    size: Literal["small", "medium", "large"] = "medium",
    key: Optional[str] = None,
    disabled: bool = False,
    use_container_width: bool = False
) -> bool:
    """
    Render a modern button
    
    Args:
        text: Button text
        variant: Button variant (primary/secondary)
        size: Button size
        key: Streamlit key
        disabled: Whether button is disabled
        use_container_width: Use full width
        
    Returns:
        True if button was clicked
    """
    # Size mappings
    size_classes = {
        "small": "padding: 6px 12px; font-size: 12px;",
        "medium": "padding: 8px 16px; font-size: 14px;",
        "large": "padding: 12px 24px; font-size: 16px;"
    }
    
    # Use Streamlit button with custom styling
    clicked = st.button(
        text,
        key=key,
        disabled=disabled,
        use_container_width=use_container_width,
        type="primary" if variant == "primary" else "secondary"
    )
    
    return clicked


# Loading state manager
@contextmanager
def loading_state(message: str = "Loading...", show_after_ms: int = 500):
    """
    Context manager for showing loading states
    
    Args:
        message: Loading message
        show_after_ms: Show loader after this many milliseconds
    """
    placeholder = st.empty()
    start_time = time.time()
    
    try:
        yield placeholder
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > show_after_ms:
            placeholder.empty()


def with_loading(func):
    """
    Decorator for functions that need loading states
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with loading state
    """
    def wrapper(*args, **kwargs):
        with st.spinner("Processing..."):
            return func(*args, **kwargs)
    return wrapper


# Helper function to render multiple cards in a grid
def card_grid(cards: List[Dict[str, Any]], columns: int = 3) -> None:
    """
    Render cards in a grid layout
    
    Args:
        cards: List of card definitions
        columns: Number of columns
    """
    cols = st.columns(columns)
    for idx, card in enumerate(cards):
        with cols[idx % columns]:
            modern_card(
                title=card.get("title", ""),
                content=card.get("content", ""),
                actions=card.get("actions", None),
                key=card.get("key", f"card_{idx}")
            )


# Additional UI components
def empty_state(
    title: str = "Ni podatkov",
    description: str = "Trenutno ni podatkov za prikaz",
    action_label: Optional[str] = None,
    action_key: Optional[str] = None
) -> None:
    """
    Display empty state message
    
    Args:
        title: Empty state title
        description: Description text
        action_label: Optional action button label
        action_key: Optional action button key
    """
    empty_html = f"""
    <div class="empty-state" style="
        text-align: center;
        padding: 48px 24px;
        color: var(--text-secondary);
    ">
        <h3 style="color: var(--text-primary); margin-bottom: 8px;">{title}</h3>
        <p style="margin-bottom: 24px;">{description}</p>
        {f'<button class="modern-button modern-button-primary" id="{action_key}">{action_label}</button>' if action_label else ''}
    </div>
    """
    st.markdown(empty_html, unsafe_allow_html=True)


def error_message(
    title: str = "Napaka",
    message: str = "Prišlo je do napake",
    details: Optional[str] = None,
    retry_key: Optional[str] = None
) -> None:
    """
    Display error message
    
    Args:
        title: Error title
        message: Error message
        details: Optional error details
        retry_key: Optional retry button key
    """
    error_html = f"""
    <div class="error-message" style="
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--error-red);
        border-radius: var(--radius-md);
        padding: 16px;
        margin: 16px 0;
    ">
        <h4 style="color: var(--error-red); margin: 0 0 8px 0;">{title}</h4>
        <p style="color: var(--text-primary); margin: 0;">{message}</p>
        {f'<details style="margin-top: 12px;"><summary>Podrobnosti</summary><pre style="margin-top: 8px; font-size: 12px;">{details}</pre></details>' if details else ''}
        {f'<button class="modern-button modern-button-secondary" id="{retry_key}" style="margin-top: 12px;">Poskusi znova</button>' if retry_key else ''}
    </div>
    """
    st.markdown(error_html, unsafe_allow_html=True)


def success_message(
    title: str = "Uspeh",
    message: str = "Operacija uspešno zaključena",
    auto_dismiss: bool = False,
    duration: int = 5000
) -> None:
    """
    Display success message
    
    Args:
        title: Success title
        message: Success message
        auto_dismiss: Whether to auto-dismiss
        duration: Duration before auto-dismiss in ms
    """
    success_id = f"success_{int(time.time() * 1000)}"
    dismiss_script = f"""
    <script>
        setTimeout(() => {{
            const el = document.getElementById('{success_id}');
            if (el) el.style.display = 'none';
        }}, {duration});
    </script>
    """ if auto_dismiss else ""
    
    success_html = f"""
    <div class="success-message" id="{success_id}" style="
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid var(--success-green);
        border-radius: var(--radius-md);
        padding: 16px;
        margin: 16px 0;
    ">
        <h4 style="color: var(--success-green); margin: 0 0 8px 0;">{title}</h4>
        <p style="color: var(--text-primary); margin: 0;">{message}</p>
    </div>
    {dismiss_script}
    """
    st.markdown(success_html, unsafe_allow_html=True)


def info_banner(
    message: str,
    icon: Optional[str] = None,
    dismissible: bool = True,
    key: Optional[str] = None
) -> None:
    """
    Display info banner
    
    Args:
        message: Banner message
        icon: Optional icon character
        dismissible: Whether banner can be dismissed
        key: Unique key
    """
    banner_id = key or f"banner_{int(time.time() * 1000)}"
    dismiss_button = f"""
    <button onclick="document.getElementById('{banner_id}').style.display='none'" 
            style="background: none; border: none; color: var(--text-secondary); cursor: pointer; float: right;">
        ×
    </button>
    """ if dismissible else ""
    
    banner_html = f"""
    <div class="info-banner" id="{banner_id}" style="
        background: var(--primary-50);
        border-left: 4px solid var(--accent-blue);
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: var(--radius-sm);
    ">
        {dismiss_button}
        <div style="color: var(--text-primary);">
            {f'<span style="margin-right: 8px;">{icon}</span>' if icon else ''}
            {message}
        </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


# Export all components
__all__ = [
    'modern_card',
    'modern_table',
    'status_badge',
    'skeleton_loader',
    'progress_bar',
    'toast_notification',
    'search_input',
    'modern_button',
    'loading_state',
    'with_loading',
    'card_grid',
    'empty_state',
    'error_message',
    'success_message',
    'info_banner'
]