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
    
    # Class-level cache for AI service to avoid recreation
    _cached_ai_service = None
    
    def __init__(self, context=None):
        """Initialize with form context."""
        self.context = context
        
        # Use cached AI service to avoid expensive recreation
        if AIFieldRenderer._cached_ai_service is None:
            AIFieldRenderer._cached_ai_service = AIFieldSuggestionService()
        self.ai_service = AIFieldRenderer._cached_ai_service
        
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
        
        # FORCE specialNegotiationWishes
        if 'specialNegotiationWishes' in full_key:
            logger.warning(f"[AI_FIELD_RENDERER_FORCE] DETECTED specialNegotiationWishes: {full_key}")
            logger.warning(f"[AI_FIELD_RENDERER_FORCE] Original has_ai: {has_ai_option}, forcing to True")
            has_ai_option = True
            schema['ai_enabled'] = True
        
        logger.info(f"[AI_FIELD_RENDERER] Processing field: {full_key}, type: {field_type}, has_ai: {has_ai_option}")
        
        # Check if this field should have AI based on its path
        if not has_ai_option:
            has_ai_option = self._should_have_ai(full_key, schema)
            logger.info(f"[AI_FIELD_RENDERER] After _should_have_ai check: {full_key} -> has_ai={has_ai_option}")
        
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
            'specialRequirementsOption',  # Cofinancer field with AI option
            'cofinancer_requirements',
            'priceFixation',
            'special_requests',
            'negotiation',
            'pogajanja',
            'specialNegotiationWishes',  # Special negotiation wishes field
            'professionalOption',  # New professional field
            'economicOption',  # New economic field
            'technicalOption',  # New technical field
            'otherCriteriaOption',  # New criteria field
            'drugo',  # "Other" fields often need AI
            'custom',  # Custom fields benefit from AI
            'description'  # Description fields can use AI
        ]
        
        # Check if field matches any AI-enabled pattern
        field_lower = full_key.lower()
        logger.debug(f"[AI_FIELD_RENDERER] Checking field: {full_key}, lowercase: {field_lower}")
        
        # IMPORTANT: Exclude specialRequirements without Option suffix
        if 'specialrequirements' in field_lower and 'option' not in field_lower:
            return False
        
        for pattern in ai_enabled_patterns:
            if pattern.lower() in field_lower:
                logger.info(f"[AI_FIELD_RENDERER] Field {full_key} matches AI pattern: {pattern}")
                return True
        
        # Check schema for AI hints
        if schema.get('ai_suggestion', False):
            return True
        
        # Check if it's an "other" option in an enum
        if 'enum' in schema and any('drugo' in str(opt).lower() or 'prosim' in str(opt).lower() for opt in schema['enum']):
            return True
        
        return False
    
    def _generate_ai_suggestion_direct(self, full_key: str, schema: dict) -> str:
        """
        Generate AI suggestion directly without showing transfer UI.
        Returns the suggestion text immediately.
        """
        try:
            # Collect form context
            context = self._collect_form_context()
            
            # Determine field type
            field_type = self._determine_field_type(full_key, schema)
            
            # Get suggestion from AI service
            suggestions_data = self.ai_service.get_field_suggestion(
                field_context=full_key,
                field_type=field_type,
                query=schema.get('description', ''),
                form_data=context
            )
            
            # Return first suggestion if available
            if suggestions_data and suggestions_data.get('suggestions'):
                text = suggestions_data['suggestions'][0]['text']
                # Clean up the text - remove field key prefix and quotes
                if ':' in text:
                    # Check if text starts with any field-like key pattern (contains dots or underscores)
                    prefix = text.split(':', 1)[0]
                    if '.' in prefix or '_' in prefix or prefix.startswith(full_key):
                        # Remove the field key prefix if it looks like a field key
                        text = text.split(':', 1)[1].strip()
                # Remove surrounding quotes if present
                text = text.strip('"').strip("'")
                # Check if it's a "no suggestion" response
                if text == "Ne vem oz. nimam predloga" or text.startswith("Ne vem"):
                    return "Ne vem oz. nimam predloga"
                return text
            
            return "Ne vem oz. nimam predloga"
            
        except Exception as e:
            logger.error(f"Error generating AI suggestion: {e}")
            return "Ne vem oz. nimam predloga"
    
    def _render_radio_with_text_fields(
        self, 
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """
        Render radio buttons with a single text field that's conditionally visible.
        For specialRequirements: text field always visible.
        For priceFixation: text field only for "drugo" or AI options.
        """
        import logging
        logger = logging.getLogger(__name__)
        # logger.info(f"[RADIO_RENDER] Processing field: {full_key}")  # Reduced logging
        options = list(schema['enum'])
        
        # Don't add AI option if it's already in the enum
        # Check for any option that contains 'AI'
        ai_option = None
        for opt in options:
            if 'AI' in opt or 'ai' in opt.lower():
                ai_option = opt
                break
        
        # If no AI option found and AI is enabled, add default one
        if not ai_option and has_ai_option:
            ai_option = "prosim za predlog AI"
            options.append(ai_option)
        
        # Display the field title
        st.markdown(f"**{field_title}**")
        if schema.get('description'):
            st.caption(schema.get('description'))
        
        # Track selected value and text field content
        selected_value = current_value or options[0] if options else ""
        
        # Get the text value from the actual requirements field
        text_key = f"{full_key}_text"
        if 'specialRequirementsOption' in full_key:
            # For special requirements, use the actual requirements field
            requirements_key = full_key.replace('Option', '')
            text_field_value = st.session_state.get(requirements_key, "")
        else:
            text_field_value = st.session_state.get(text_key, "")
        
        # Create radio button selection
        selected = st.radio(
            "Izbira možnosti",  # Provide non-empty label for accessibility
            options=options,
            index=options.index(selected_value) if selected_value in options else 0,
            key=f"{full_key}_radio",
            label_visibility="collapsed"
        )
        
        # Store the selection in session state
        st.session_state[full_key] = selected
        
        # Log for debugging price fixation visibility
        if 'priceFixation' in full_key:
            import logging
            logger = logging.getLogger(__name__)
            # logger.info(f"[PRICE_FIXATION] Field: {full_key}, Selected: '{selected}'")  # Reduced logging
        
        # Determine if text area should be shown
        # For specialRequirements - ALWAYS show text area
        # For priceFixation - show ONLY for "drugo" or AI options
        if 'specialRequirementsOption' in full_key:
            needs_text_input = True  # ALWAYS show for special requirements
        elif 'priceFixation' in full_key:
            # For price fixation - ONLY show for specific options
            needs_text_input = (
                selected == "drugo" or 
                selected == "prosim za predlog AI" or
                'ai' in selected.lower()
            )
            # logger.info(f"[PRICE_FIXATION] needs_text_input: {needs_text_input}")  # Reduced logging
        else:
            # For other fields - conditional based on content
            needs_text_input = ('drugo' in selected.lower() or 'ai' in selected.lower())
        
        if needs_text_input:
            text_container = st.container()
            
            with text_container:
                # Add some spacing
                st.write("")
                
                # If AI option is selected, generate suggestion and populate the field
                if ai_option and selected == ai_option:
                    # Check if we need to generate new suggestion
                    cache_key = f"{full_key}_ai_generated"
                    textarea_key = f"{full_key}_textarea"
                    if cache_key not in st.session_state:
                        with st.spinner("Generiram AI predlog..."):
                            logger.info(f"[AI_FIELD_RENDERER] User selected AI option for field: {full_key}")
                            suggestion = self._generate_ai_suggestion_direct(full_key, schema)
                            st.session_state[cache_key] = suggestion
                            text_field_value = suggestion
                            # Also update the textarea key
                            st.session_state[textarea_key] = suggestion
                            
                            # For price fixation, immediately update the validation field
                            if 'priceFixation' in full_key:
                                ai_custom_key = full_key.replace('priceFixation', 'aiPriceFixationCustom')
                                st.session_state[ai_custom_key] = suggestion
                    else:
                        text_field_value = st.session_state.get(cache_key, text_field_value)
                        # Make sure textarea has the AI value
                        if textarea_key not in st.session_state or not st.session_state[textarea_key]:
                            st.session_state[textarea_key] = text_field_value
                            
                            # For price fixation, update validation field
                            if 'priceFixation' in full_key:
                                ai_custom_key = full_key.replace('priceFixation', 'aiPriceFixationCustom')
                                st.session_state[ai_custom_key] = text_field_value
                
                # Use columns for better layout
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Determine the appropriate label based on the field
                    if 'priceFixation' in full_key:
                        label = "Opišite način oblikovanja cen"
                        placeholder = "Vnesite opis načina oblikovanja cen..."
                        help_text = "Opišite kako želite oblikovati cene"
                    else:
                        # Default for specialRequirements
                        label = "Vnesite posebne zahteve"
                        placeholder = "Vnesite posebne zahteve sofinancerja..."
                        help_text = "Vnesite zahteve ročno ali uporabite AI predlog"
                    
                    # Initialize the text area key in session state if needed
                    textarea_key = f"{full_key}_textarea"
                    if textarea_key not in st.session_state:
                        # For price fixation, load from the appropriate field
                        if 'priceFixation' in full_key:
                            if selected == "drugo":
                                other_key = full_key.replace('priceFixation', 'otherPriceFixation')
                                st.session_state[textarea_key] = st.session_state.get(other_key, text_field_value)
                            elif selected == "prosim za predlog AI" or (ai_option and selected == ai_option):
                                ai_custom_key = full_key.replace('priceFixation', 'aiPriceFixationCustom')
                                st.session_state[textarea_key] = st.session_state.get(ai_custom_key, text_field_value)
                            else:
                                st.session_state[textarea_key] = text_field_value
                        else:
                            st.session_state[textarea_key] = text_field_value
                    
                    # Always show text area with appropriate label
                    # Don't use 'value' parameter when using session state key
                    text_value = st.text_area(
                        label,
                        height=100,
                        key=textarea_key,
                        placeholder=placeholder,
                        help=help_text
                    )
                    
                    # Store the text value in the text key for other uses
                    st.session_state[text_key] = text_value
                    
                    # For special requirements, also update the actual requirements field
                    if 'specialRequirementsOption' in full_key:
                        requirements_key = full_key.replace('Option', '')
                        st.session_state[requirements_key] = text_value
                    
                    # For price fixation, update both fields that validation checks
                    if 'priceFixation' in full_key:
                        # Always update based on selected option
                        if selected == "drugo":
                            # For "drugo" option, save to otherPriceFixation
                            other_key = full_key.replace('priceFixation', 'otherPriceFixation')
                            st.session_state[other_key] = text_value
                            # Clear the AI field
                            ai_custom_key = full_key.replace('priceFixation', 'aiPriceFixationCustom')
                            if ai_custom_key in st.session_state:
                                st.session_state[ai_custom_key] = ""
                        elif selected == "prosim za predlog AI" or (ai_option and selected == ai_option):
                            # For AI option, save to aiPriceFixationCustom
                            ai_custom_key = full_key.replace('priceFixation', 'aiPriceFixationCustom')
                            st.session_state[ai_custom_key] = text_value
                            # Also save to otherPriceFixation for compatibility
                            other_key = full_key.replace('priceFixation', 'otherPriceFixation')
                            st.session_state[other_key] = text_value
                
                with col2:
                    # Add regenerate button only when AI option is selected
                    if ai_option and selected == ai_option:
                        st.write("")  # Spacing to align with text area
                        st.write("")  # More spacing
                        # Use a unique key that doesn't conflict with session state
                        regen_key = f"{full_key}_regenerate_btn"
                        # Remove any existing session state for this button to avoid conflicts
                        if regen_key in st.session_state:
                            del st.session_state[regen_key]
                        if st.button("🔄", key=regen_key, help="Generiraj nov predlog"):
                            # Clear the cache to force regeneration
                            cache_key = f"{full_key}_ai_generated"
                            textarea_key = f"{full_key}_textarea"
                            if cache_key in st.session_state:
                                del st.session_state[cache_key]
                            # Also clear the text key and textarea key to force refresh
                            if text_key in st.session_state:
                                del st.session_state[text_key]
                            if textarea_key in st.session_state:
                                del st.session_state[textarea_key]
                            st.rerun()
        
        # Return the selected option (not the text value)
        # The text is stored in the related field
        return selected
    
    def _render_dropdown_with_ai(
        self, 
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """DEPRECATED: Use _render_radio_with_text_fields instead."""
        # Redirect to new radio button implementation
        return self._render_radio_with_text_fields(
            full_key, schema, field_title, current_value, has_ai_option
        )
    
    def _render_dropdown_with_ai_OLD(
        self, 
        full_key: str,
        schema: dict,
        field_title: str,
        current_value: Any,
        has_ai_option: bool
    ) -> str:
        """OLD: Render dropdown field with AI option."""
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
            # Special handling for price fixation field
            if 'priceFixation' in full_key:
                st.markdown("### AI predlogi za oblikovanje cen")
                self._show_ai_suggestions(full_key, schema, 'dropdown')
                
                # Show text area for the result
                other_key = full_key.replace('priceFixation', 'otherPriceFixation')
                transferred_value = st.session_state.ai_suggestions.get(full_key, '')
                
                other_value = st.text_area(
                    "Opišite željeni način oblikovanja cen",
                    value=transferred_value,
                    key=f"{other_key}_textarea",
                    height=150,
                    help="Vnesite svoj opis ali uporabite AI predlog zgoraj"
                )
                
                # Store the value
                st.session_state[other_key] = other_value
                
                # Return 'drugo' to indicate custom option was selected
                if other_value:
                    return 'drugo'
            else:
                # For other fields, standard handling
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
        """Render text area with radio button AI trigger."""
        
        # LOGGING FOR specialNegotiationWishes
        if 'specialNegotiationWishes' in full_key:
            logger.warning(f"[TEXTAREA_AI] Rendering specialNegotiationWishes with AI: {has_ai_option}")
        
        # Display the field title
        st.markdown(f"**{field_title}**")
        if schema.get('description'):
            st.caption(schema.get('description'))
        
        value = current_value or ""
        
        # If AI option is enabled, use radio buttons
        if has_ai_option:
            options = ["Vnesem sam", "Prosim za pomoč AI"]
            
            # Determine current selection
            ai_selected_key = f"{full_key}_ai_selected"
            if ai_selected_key not in st.session_state:
                st.session_state[ai_selected_key] = options[0]
            
            # Create radio button selection
            selected = st.radio(
                "Način vnosa",  # Provide non-empty label for accessibility
                options=options,
                index=options.index(st.session_state[ai_selected_key]),
                key=f"{full_key}_radio",
                label_visibility="collapsed"
            )
            st.session_state[ai_selected_key] = selected
            
            # If AI option selected, generate suggestion
            if selected == "Prosim za pomoč AI":
                cache_key = f"{full_key}_ai_generated"
                textarea_key = f"{full_key}_textarea"
                
                if cache_key not in st.session_state:
                    with st.spinner("Generiram AI predlog..."):
                        suggestion = self._generate_ai_suggestion_direct(full_key, schema)
                        st.session_state[cache_key] = suggestion
                        value = suggestion
                        # CRITICAL: Update textarea session state IMMEDIATELY
                        st.session_state[textarea_key] = suggestion
                        # Force rerun to update the textarea
                        st.rerun()
                else:
                    value = st.session_state.get(cache_key, value)
                    # CRITICAL: Make sure textarea has the AI value
                    st.session_state[textarea_key] = value
            
            # Layout with text area and regenerate button
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Render text area
                # Use a unique key for the text area widget
                textarea_key = f"{full_key}_textarea"
                
                # Initialize ONLY if not exists (to avoid warning)
                if textarea_key not in st.session_state:
                    st.session_state[textarea_key] = value
                
                value = st.text_area(
                    "Vsebina",  # Provide non-empty label for accessibility
                    key=textarea_key,  # Use ONLY key, not value parameter
                    height=schema.get('height', 150),
                    placeholder=schema.get('placeholder', 'Vnesite besedilo...'),
                    label_visibility="collapsed"
                )
            
            with col2:
                # Add regenerate button for AI
                if selected == "Prosim za pomoč AI":
                    st.write("")  # Spacing
                    st.write("")  # More spacing
                    # Use a unique key that doesn't conflict with session state
                    regen_key = f"{full_key}_regenerate_textarea_btn"
                    # Remove any existing session state for this button to avoid conflicts
                    if regen_key in st.session_state:
                        del st.session_state[regen_key]
                    if st.button("🔄", key=regen_key, help="Generiraj nov predlog"):
                        # Clear the cache to force regeneration
                        cache_key = f"{full_key}_ai_generated"
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.rerun()
        else:
            # Regular text area without AI
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
                # Use a unique key that doesn't conflict with session state
                btn_key = f"{full_key}_ai_button"
                # Remove any existing session state for this button to avoid conflicts
                if btn_key in st.session_state:
                    del st.session_state[btn_key]
                if st.button("AI predlog", key=btn_key):
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
                try:
                    suggestions_data = self.ai_service.get_field_suggestion(
                        field_context=full_key,
                        field_type=field_type,
                        query=schema.get('description', ''),
                        form_data=context
                    )
                except Exception as e:
                    st.error(f"Napaka pri pridobivanju AI predlogov: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    suggestions_data = {'suggestions': [], 'error': str(e)}
            
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
            st.warning("Ne vem oz. nimam predloga")
            return
        
        # Check if the only suggestion is "no suggestion"
        if len(suggestions) == 1 and suggestions[0].get('text') == "Ne vem oz. nimam predloga":
            st.warning("Ne vem oz. nimam predloga")
            return
        
        for idx, suggestion in enumerate(suggestions):
            # Create container for each suggestion
            with st.container():
                # Show source and confidence
                source_label = "Iz baze znanja" if suggestion['source'] == 'knowledge_base' else "AI generirano"
                
                # Header with source
                st.markdown(f"**Predlog {idx+1} ({source_label}):**")
                
                # Show suggestion text
                # Special handling for "no suggestion" message
                if suggestion['text'] == "Ne vem oz. nimam predloga":
                    st.warning(suggestion['text'])
                else:
                    st.info(suggestion['text'])
                
                # Show confidence if available
                if 'confidence' in suggestion and suggestion['confidence'] > 0:
                    st.progress(suggestion['confidence'], text=f"Zaupanje: {suggestion['confidence']*100:.0f}%")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    # Don't show "Use" button for "no suggestion" message
                    if suggestion['text'] != "Ne vem oz. nimam predloga" and st.button(f"Uporabi", key=f"use_{full_key}_{idx}"):
                        # Transfer to field
                        st.session_state.ai_suggestions[full_key] = suggestion['text']
                        
                        # For price fixation, also set the other field directly
                        if 'priceFixation' in full_key:
                            other_key = full_key.replace('priceFixation', 'otherPriceFixation')
                            st.session_state[other_key] = suggestion['text']
                        
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
            for key in st.session_state:
                # Skip internal keys, widget keys, and cache keys
                if (not key.startswith('_') and 
                    not key.startswith('widget_') and 
                    not key.endswith('_cache') and
                    not key.endswith('_ai_generated') and
                    not key.endswith('_ai_selected')):
                    try:
                        # Safely get the value
                        context[key] = st.session_state[key]
                    except Exception as e:
                        # Skip any keys that can't be accessed
                        logger.debug(f"Skipping session state key {key}: {e}")
                        continue
        
        return context
    
    def _determine_field_type(self, full_key: str, schema: dict) -> str:
        """
        Determine the field type for AI context.
        """
        # Check key patterns
        key_lower = full_key.lower()
        
        if 'cofinancer' in key_lower or 'sofinancer' in key_lower:
            logger.debug(f"[AI_FIELD_RENDERER] Field {full_key} identified as cofinancer_requirements")
            return 'cofinancer_requirements'
        elif 'negotiation' in key_lower or 'pogajanja' in key_lower or 'specialnegotiationwishes' in key_lower:
            logger.debug(f"[AI_FIELD_RENDERER] Field {full_key} identified as negotiation_terms")
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