"""
Modern card component that uses Streamlit native components
instead of HTML for better compatibility
"""
import streamlit as st
from typing import Optional, List, Dict, Any

def modern_card_v2(
    title: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    key: Optional[str] = None
) -> None:
    """
    Render a modern card using Streamlit native components
    
    Args:
        title: Card title
        content: Text content for the card body
        metadata: Dictionary of metadata to display (e.g., {'Velikost': '12KB', 'Tip': 'Word'})
        actions: List of action buttons with 'label' and 'key'
        key: Unique key for the card
    """
    with st.container():
        # Card container with custom styling
        with st.container():
            st.markdown(f"""
            <div style="background: var(--bg-primary, #FFFFFF); 
                        border: 1px solid var(--border, #E5E5E5); 
                        border-radius: var(--radius-lg, 8px); 
                        padding: 20px; 
                        margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; 
                          color: var(--text-primary, #000000);">{title}</h4>
            """, unsafe_allow_html=True)
            
            # Content section
            if content:
                st.markdown(f"""
                <div style="color: var(--text-secondary, #666666); font-size: 14px; 
                           line-height: 1.5; margin-bottom: 12px;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
            
            # Metadata section
            if metadata:
                for label, value in metadata.items():
                    st.markdown(f"""
                    <div style="font-size: 14px; margin-bottom: 6px;">
                        <span style="color: var(--text-primary, #000000); font-weight: 500;">{label}:</span>
                        <span style="color: var(--text-secondary, #666666);"> {value}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Actions section
            if actions:
                st.markdown("""
                <div style="margin-top: 16px; padding-top: 16px; 
                           border-top: 1px solid var(--border, #E5E5E5);">
                """, unsafe_allow_html=True)
                
                cols = st.columns(len(actions))
                for idx, action in enumerate(actions):
                    with cols[idx]:
                        if st.button(
                            action.get("label", ""),
                            key=action.get("key", f"{key}_action_{idx}"),
                            use_container_width=True,
                            type="secondary" if idx > 0 else "primary"
                        ):
                            # Handle action if callback provided
                            if "callback" in action:
                                action["callback"]()
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)