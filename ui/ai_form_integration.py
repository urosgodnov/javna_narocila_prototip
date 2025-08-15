"""
AI Form Integration Module
Provides AI-powered suggestions for specific form fields
Part of Story 2: Vector Processing and Form AI Integration
"""

import streamlit as st
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AI processing capabilities
try:
    from ui.ai_processor import FormAIAssistant
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Define form field mappings
AI_ENABLED_FIELDS = {
    'vrsta_narocila': {
        'posebne_zahteve_sofinancerja': {
            'label': 'Posebne zahteve sofinancerja',
            'help': 'AI lahko predlaga zahteve na podlagi podobnih dokumentov'
        }
    },
    'pogajanja': {
        'posebne_zelje_pogajanja': {
            'label': 'Posebne želje v zvezi s pogajanji',
            'help': 'AI lahko predlaga pogoje za pogajanja'
        }
    },
    'pogoji_sodelovanje': {
        'ustreznost_poklicna_drugo': {
            'label': 'Poklicna ustreznost - drugo',
            'help': 'AI lahko predlaga dodatne pogoje poklicne ustreznosti'
        },
        'ekonomski_polozaj_drugo': {
            'label': 'Ekonomski položaj - drugo',
            'help': 'AI lahko predlaga ekonomske pogoje'
        },
        'tehnicna_sposobnost_drugo': {
            'label': 'Tehnična sposobnost - drugo',
            'help': 'AI lahko predlaga tehnične pogoje'
        }
    },
    'variante_merila': {
        'merila_drugo': {
            'label': 'Merila - drugo',
            'help': 'AI lahko predlaga dodatna merila ocenjevanja'
        }
    }
}

def render_ai_field(
    form_section: str,
    field_name: str,
    field_label: str = None,
    field_value: str = "",
    field_key: str = None,
    height: int = 150,
    placeholder: str = "",
    help_text: str = None,
    context: Dict[str, Any] = None
) -> str:
    """
    Render a text field with AI assistance button
    
    Args:
        form_section: Section of the form (e.g., 'vrsta_narocila')
        field_name: Name of the field (e.g., 'posebne_zahteve_sofinancerja')
        field_label: Label to display for the field
        field_value: Current value of the field
        field_key: Streamlit key for the field
        height: Height of the text area
        placeholder: Placeholder text
        help_text: Help text to display
        context: Form context for AI generation
    
    Returns:
        The value entered in the field
    """
    
    # Check if this field has AI support
    has_ai_support = (
        AI_AVAILABLE and 
        form_section in AI_ENABLED_FIELDS and 
        field_name in AI_ENABLED_FIELDS[form_section]
    )
    
    # Use provided label or get from mapping
    if not field_label and has_ai_support:
        field_label = AI_ENABLED_FIELDS[form_section][field_name]['label']
    elif not field_label:
        field_label = field_name.replace('_', ' ').title()
    
    # Generate unique key if not provided
    if not field_key:
        field_key = f"{form_section}_{field_name}"
    
    # Add AI help text if available
    if has_ai_support and not help_text:
        help_text = AI_ENABLED_FIELDS[form_section][field_name]['help']
    
    # Create columns for field and AI button
    if has_ai_support:
        col1, col2 = st.columns([5, 1])
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        # Render the text area
        value = st.text_area(
            field_label,
            value=field_value,
            key=field_key,
            height=height,
            placeholder=placeholder,
            help=help_text
        )
    
    # Add AI button if available
    if has_ai_support and col2:
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            
            button_key = f"ai_btn_{field_key}"
            if st.button("🤖 AI", key=button_key, help="Generiraj predlog z AI"):
                with st.spinner("Generiram predlog..."):
                    try:
                        # Initialize AI assistant
                        assistant = FormAIAssistant()
                        
                        # Get AI suggestion
                        suggestion = assistant.get_ai_suggestion(
                            form_section=form_section,
                            field_name=field_name,
                            context=context or {}
                        )
                        
                        # Update session state with suggestion
                        st.session_state[field_key] = suggestion
                        st.success("✅ AI predlog generiran!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Napaka pri generiranju: {str(e)}")
    
    return value

def render_ai_text_input(
    form_section: str,
    field_name: str,
    field_label: str = None,
    field_value: str = "",
    field_key: str = None,
    placeholder: str = "",
    help_text: str = None,
    context: Dict[str, Any] = None
) -> str:
    """
    Render a text input field with AI assistance button
    Similar to render_ai_field but for single-line inputs
    """
    
    # Check if this field has AI support
    has_ai_support = (
        AI_AVAILABLE and 
        form_section in AI_ENABLED_FIELDS and 
        field_name in AI_ENABLED_FIELDS[form_section]
    )
    
    # Use provided label or get from mapping
    if not field_label and has_ai_support:
        field_label = AI_ENABLED_FIELDS[form_section][field_name]['label']
    elif not field_label:
        field_label = field_name.replace('_', ' ').title()
    
    # Generate unique key if not provided
    if not field_key:
        field_key = f"{form_section}_{field_name}_input"
    
    # Add AI help text if available
    if has_ai_support and not help_text:
        help_text = AI_ENABLED_FIELDS[form_section][field_name]['help']
    
    # Create columns for field and AI button
    if has_ai_support:
        col1, col2 = st.columns([5, 1])
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        # Render the text input
        value = st.text_input(
            field_label,
            value=field_value,
            key=field_key,
            placeholder=placeholder,
            help=help_text
        )
    
    # Add AI button if available
    if has_ai_support and col2:
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            
            button_key = f"ai_btn_{field_key}"
            if st.button("🤖 AI", key=button_key, help="Generiraj predlog z AI"):
                with st.spinner("Generiram predlog..."):
                    try:
                        # Initialize AI assistant
                        assistant = FormAIAssistant()
                        
                        # Get AI suggestion
                        suggestion = assistant.get_ai_suggestion(
                            form_section=form_section,
                            field_name=field_name,
                            context=context or {}
                        )
                        
                        # Update session state with suggestion
                        st.session_state[field_key] = suggestion
                        st.success("✅ AI predlog generiran!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Napaka pri generiranju: {str(e)}")
    
    return value

def check_ai_availability() -> bool:
    """Check if AI features are available"""
    return AI_AVAILABLE and os.getenv('OPENAI_API_KEY') is not None

def get_ai_status_badge() -> str:
    """Get HTML badge showing AI status"""
    if check_ai_availability():
        return """
        <span style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-block;
        ">
            🤖 AI Aktiviran
        </span>
        """
    else:
        return """
        <span style="
            background: #e5e7eb;
            color: #6b7280;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-block;
        ">
            🤖 AI Neaktiven
        </span>
        """

# Example usage in a form
def example_form_with_ai():
    """Example of how to use AI fields in a form"""
    
    st.title("Primer obrazca z AI podporo")
    
    # Show AI status
    st.markdown(get_ai_status_badge(), unsafe_allow_html=True)
    
    # Form context (would come from actual form data)
    form_context = {
        'vrsta_postopka': 'odprti postopek',
        'predmet_narocila': 'gradnja cestne infrastrukture',
        'vrednost': 500000
    }
    
    # Section 1: Vrsta naročila
    st.header("1. Vrsta naročila")
    
    posebne_zahteve = render_ai_field(
        form_section='vrsta_narocila',
        field_name='posebne_zahteve_sofinancerja',
        field_label='Posebne zahteve sofinancerja',
        placeholder='Vnesite posebne zahteve...',
        context=form_context
    )
    
    # Section 2: Pogajanja
    st.header("2. Pogajanja")
    
    pogajanja = render_ai_field(
        form_section='pogajanja',
        field_name='posebne_zelje_pogajanja',
        field_label='Posebne želje v zvezi s pogajanji',
        placeholder='Opišite želje glede pogajanj...',
        context=form_context
    )
    
    # Section 3: Pogoji za sodelovanje
    st.header("3. Pogoji za sodelovanje")
    
    poklicna = render_ai_field(
        form_section='pogoji_sodelovanje',
        field_name='ustreznost_poklicna_drugo',
        field_label='Poklicna ustreznost - dodatni pogoji',
        context=form_context
    )
    
    ekonomski = render_ai_field(
        form_section='pogoji_sodelovanje',
        field_name='ekonomski_polozaj_drugo',
        field_label='Ekonomski položaj - dodatni pogoji',
        context=form_context
    )
    
    tehnicna = render_ai_field(
        form_section='pogoji_sodelovanje',
        field_name='tehnicna_sposobnost_drugo',
        field_label='Tehnična sposobnost - dodatni pogoji',
        context=form_context
    )
    
    # Section 4: Merila
    st.header("4. Merila")
    
    merila = render_ai_field(
        form_section='variante_merila',
        field_name='merila_drugo',
        field_label='Dodatna merila za ocenjevanje',
        context=form_context
    )
    
    # Submit button
    if st.button("Shrani obrazec", type="primary"):
        st.success("Obrazec shranjen!")
        st.json({
            'posebne_zahteve': posebne_zahteve,
            'pogajanja': pogajanja,
            'poklicna': poklicna,
            'ekonomski': ekonomski,
            'tehnicna': tehnicna,
            'merila': merila
        })