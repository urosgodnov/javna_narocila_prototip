"""
AI-Enhanced Field Renderer
Implements multiple trigger types for AI suggestions as per brownfield story
"""

import streamlit as st
from typing import Any, Dict, Optional, List
import logging
from services.ai_suggestion_service import AIFieldSuggestionService

logger = logging.getLogger(__name__)


class AIFieldRenderer:
    """
    Enhanced field renderer with AI suggestion capabilities.
    Supports dropdowns, checkboxes, and buttons as triggers.
    """
    
    def __init__(self, context=None):
        """Initialize with form context."""
        self.context = context
        self.ai_service = AIFieldSuggestionService()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for AI suggestions."""
        if 'ai_suggestions' not in st.session_state:
            st.session_state.ai_suggestions = {}
        if 'ai_triggers' not in st.session_state:
            st.session_state.ai_triggers = {}
    
    def render_field_with_ai(
        self, 
        full_key: str, 
        schema: dict, 
        parent_key: str = "",
        current_value: Any = None
    ) -> Any:
        """
        Render field with appropriate AI trigger based on field type.
        
        Args:
            full_key: Full key path to the field
            schema: Field schema from JSON
            parent_key: Parent key for nested fields
            current_value: Current field value
            
        Returns:
            The field value (updated if AI suggestion was selected)
        """
        field_type = schema.get('type', 'string')
        has_ai_option = schema.get('ai_enabled', False)
        field_title = schema.get('title', full_key.split('.')[-1])
        
        # Check if this field should have AI based on its path
        if not has_ai_option:
            has_ai_option = self._should_have_ai(full_key, schema)
        
        # Determine AI trigger type and render accordingly
        if field_type == 'string' and 'enum' in schema:
            # Dropdown with AI option
            return self._render_dropdown_with_ai(
                full_key, schema, field_title, current_value, has_ai_option
            )
            
        elif field_type == 'string' and schema.get('format') == 'textarea':
            # Text area with checkbox
            return self._render_textarea_with_ai(
                full_key, schema, field_title, current_value, has_ai_option
            )
            
        else:
            # Regular input with button
            return self._render_input_with_ai(
                full_key, schema, field_title, current_value, has_ai_option
            )
    
    def _should_have_ai(self, full_key: str, schema: dict) -> bool:
        """
        Determine if a field should have AI assistance based on its path and type.
        """
        # Priority fields that should have AI
        ai_enabled_patterns = [
            'posebne_zahteve_sofinancerja',
            'specialRequirements',
            'cofinancer_requirements',
            'priceFixation',
            'special_requests',
            'negotiation',
            'pogajanja',
            'drugo',  # "Other" fields often need AI
            'custom',  # Custom fields benefit from AI
            'description',  # Description fields can use AI
            'requirements'  # Any requirements field
        ]
        
        # Check if field matches any AI-enabled pattern
        field_lower = full_key.lower()
        for pattern in ai_enabled_patterns:
            if pattern.lower() in field_lower:
                return True
        
        # Check schema for AI hints
        if schema.get('ai_suggestion', False):
            return True
        
        # Check if it's an "other" option in an enum
        if 'enum' in schema and any('drugo' in str(opt).lower() or 'prosim' in str(opt).lower() for opt in schema['enum']):
            return True
        
        return False
    
    def _render_dropdown_with_ai(
        self, 
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """Render dropdown field with AI option."""
        options = list(schema['enum'])
        
        # Add AI option if enabled and not already present
        ai_option = "prosim za predlog AI"
        if has_ai_option and ai_option not in options:
            options.append(ai_option)
        
        # Determine current selection
        if current_value in options:
            index = options.index(current_value)
        else:
            index = 0
        
        # Render selectbox
        selected = st.selectbox(
            field_title,
            options=options,
            index=index,
            key=f"{full_key}_select",
            help=schema.get('description', '')
        )
        
        # Show AI suggestions if AI option selected
        if selected == ai_option:
            self._show_ai_suggestions(full_key, schema, 'dropdown')
            # Return the last selected AI suggestion if any
            if full_key in st.session_state.ai_suggestions:
                last_suggestion = st.session_state.ai_suggestions[full_key]
                if last_suggestion:
                    return last_suggestion
        
        return selected
    
    def _render_textarea_with_ai(
        self,
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """Render text area with AI checkbox trigger."""
        value = current_value or ""
        
        # Show checkbox for AI if enabled
        if has_ai_option:
            col1, col2 = st.columns([1, 4])
            with col1:
                use_ai = st.checkbox(
                    "Uporabi AI za predlog",
                    key=f"{full_key}_ai_checkbox",
                    value=st.session_state.ai_triggers.get(full_key, False)
                )
                st.session_state.ai_triggers[full_key] = use_ai
            
            # Show suggestions if checkbox is checked
            if use_ai:
                self._show_ai_suggestions(full_key, schema, 'checkbox')
                # Check if user selected a suggestion
                if full_key in st.session_state.ai_suggestions:
                    suggestion = st.session_state.ai_suggestions[full_key]
                    if suggestion and suggestion != value:
                        value = suggestion
        
        # Render text area
        value = st.text_area(
            field_title,
            value=value,
            key=f"{full_key}_textarea",
            height=schema.get('height', 150),
            help=schema.get('description', ''),
            placeholder=schema.get('placeholder', '')
        )
        
        return value
    
    def _render_input_with_ai(
        self,
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """Render input field with AI button trigger."""
        value = current_value or ""
        
        if has_ai_option:
            # Create columns for input and AI button
            col1, col2 = st.columns([5, 1])
            
            with col1:
                value = st.text_input(
                    field_title,
                    value=value,
                    key=f"{full_key}_input",
                    help=schema.get('description', ''),
                    placeholder=schema.get('placeholder', '')
                )
            
            with col2:
                st.write("")  # Spacing to align with input
                if st.button("AI predlog", key=f"{full_key}_ai_btn"):
                    st.session_state.ai_triggers[full_key] = True
            
            # Show suggestions if button was clicked
            if st.session_state.ai_triggers.get(full_key, False):
                self._show_ai_suggestions(full_key, schema, 'button')
                # Check if user selected a suggestion
                if full_key in st.session_state.ai_suggestions:
                    suggestion = st.session_state.ai_suggestions[full_key]
                    if suggestion and suggestion != value:
                        value = suggestion
                        # Clear trigger after use
                        st.session_state.ai_triggers[full_key] = False
                        st.rerun()
        else:
            # Regular input without AI
            value = st.text_input(
                field_title,
                value=value,
                key=f"{full_key}_input",
                help=schema.get('description', ''),
                placeholder=schema.get('placeholder', '')
            )
        
        return value
    
    def _show_ai_suggestions(self, full_key: str, schema: dict, trigger_type: str):
        """
        Display AI suggestions with transfer buttons.
        Shows context being used and allows selection or rejection.
        """
        # Check if we already have suggestions for this field
        cache_key = f"{full_key}_suggestions_cache"
        if cache_key not in st.session_state:
            # Collect form context
            context = self._collect_form_context()
            
            # Determine field type from schema and key
            field_type = self._determine_field_type(full_key, schema)
            
            # Get suggestions from AI service
            with st.spinner("Analiziram kontekst projekta..."):
                suggestions_data = self.ai_service.get_field_suggestion(
                    field_context=full_key,
                    field_type=field_type,
                    query=schema.get('description', ''),
                    form_data=context
                )
            
            # Cache suggestions
            st.session_state[cache_key] = suggestions_data
        else:
            suggestions_data = st.session_state[cache_key]
        
        # Display context being used
        if suggestions_data.get('context_used'):
            with st.expander("Kontekst za AI predloge", expanded=False):
                context = suggestions_data['context_used']
                if context.get('project'):
                    st.write(f"**Projekt:** {context['project']}")
                if context.get('cofinancers'):
                    st.write(f"**Sofinancerji:** {', '.join(context['cofinancers'])}")
                if context.get('lot'):
                    st.write(f"**Sklop:** {context['lot']}")
                if context.get('procurement_type'):
                    st.write(f"**Tip naročila:** {context['procurement_type']}")
        
        # Display each suggestion with transfer buttons
        suggestions = suggestions_data.get('suggestions', [])
        
        if not suggestions:
            st.warning("Ni najdenih predlogov. Prosimo, vnesite ročno.")
            return
        
        for idx, suggestion in enumerate(suggestions):
            # Create container for each suggestion
            with st.container():
                # Show source and confidence
                source_label = "Iz baze znanja" if suggestion['source'] == 'knowledge_base' else "AI generirano"
                
                # Header with source
                st.markdown(f"**Predlog {idx+1} ({source_label}):**")
                
                # Show suggestion text
                st.info(suggestion['text'])
                
                # Show confidence if available
                if 'confidence' in suggestion and suggestion['confidence'] > 0:
                    st.progress(suggestion['confidence'], text=f"Zaupanje: {suggestion['confidence']*100:.0f}%")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if st.button(f"Uporabi", key=f"use_{full_key}_{idx}"):
                        # Transfer to field
                        st.session_state.ai_suggestions[full_key] = suggestion['text']
                        st.success("Predlog prenešen")
                        # Clear suggestions cache to allow regeneration
                        if f"{full_key}_suggestions_cache" in st.session_state:
                            del st.session_state[f"{full_key}_suggestions_cache"]
                        st.rerun()
                
                with col2:
                    if st.button(f"Zavrži", key=f"reject_{full_key}_{idx}"):
                        # Mark as rejected and potentially get new suggestions
                        if f"{full_key}_suggestions_cache" in st.session_state:
                            del st.session_state[f"{full_key}_suggestions_cache"]
                        st.info("Generiram nove predloge...")
                        st.rerun()
        
        # Option to generate more suggestions
        if st.button("Generiraj več predlogov", key=f"more_{full_key}"):
            # Clear cache and regenerate
            if f"{full_key}_suggestions_cache" in st.session_state:
                del st.session_state[f"{full_key}_suggestions_cache"]
            st.rerun()
    
    def _collect_form_context(self) -> Dict[str, Any]:
        """
        Collect complete form context from session state.
        """
        context = {}
        
        # Use the context object if available
        if self.context:
            context = self.context.session_state
        
        # Also check Streamlit session state
        if hasattr(st, 'session_state'):
            for key, value in st.session_state.items():
                if not key.startswith('_') and not key.endswith('_cache'):
                    context[key] = value
        
        return context
    
    def _determine_field_type(self, full_key: str, schema: dict) -> str:
        """
        Determine the field type for AI context.
        """
        # Check key patterns
        key_lower = full_key.lower()
        
        if 'cofinancer' in key_lower or 'sofinancer' in key_lower:
            return 'cofinancer_requirements'
        elif 'negotiation' in key_lower or 'pogajanja' in key_lower:
            return 'negotiation_terms'
        elif 'price' in key_lower or 'cen' in key_lower:
            return 'price_formation'
        elif 'criteria' in key_lower or 'merila' in key_lower:
            return 'evaluation_criteria'
        elif 'technical' in key_lower or 'tehni' in key_lower:
            return 'technical_requirements'
        elif 'requirement' in key_lower or 'zahtev' in key_lower:
            return 'requirements'
        else:
            # Use schema type as fallback
            return schema.get('ai_field_type', 'general')