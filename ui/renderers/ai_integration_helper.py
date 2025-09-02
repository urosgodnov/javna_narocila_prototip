"""
AI Integration Helper
Bridges AI field renderer with existing section renderer
"""

import streamlit as st
from typing import Any, Dict, Optional
import logging
from ui.renderers.ai_field_renderer import AIFieldRenderer

logger = logging.getLogger(__name__)


class AIIntegrationHelper:
    """
    Helper class to integrate AI suggestions into existing form rendering.
    """
    
    # Fields that should have AI assistance enabled
    AI_ENABLED_FIELDS = {
        # Cofinancer requirements - ALL procurement types
        # Note: These patterns will match array indices too (e.g., cofinancers.0.specialRequirementsOption)
        'specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'projectInfo.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.blago.lot_sklopi.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.blago.en_sklop.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.storitve.lot_sklopi.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.storitve.en_sklop.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.gradnje.lot_sklopi.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'orderType.gradnje.en_sklop.cofinancers.specialRequirementsOption': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        'vrsta_narocila.posebne_zahteve_sofinancerja': {
            'type': 'cofinancer_requirements',
            'trigger': 'radio',
            'priority': 'high'
        },
        
        # Price information fields
        'priceInfo.priceClause': {
            'type': 'price_formation',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'priceInfo.otherPriceClause': {
            'type': 'price_formation',
            'trigger': 'text',
            'priority': 'high'
        },
        'priceInfo.priceFixation': {
            'type': 'price_formation',
            'trigger': 'radio',  # Has "prosim za predlog AI" option
            'priority': 'high'
        },
        'priceInfo.otherPriceFixation': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'priceInfo.aiPriceFixationCustom': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        # Add lot-aware versions of priceInfo fields
        'lots.priceInfo.priceClause': {
            'type': 'price_formation',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'lots.priceInfo.otherPriceClause': {
            'type': 'price_formation',
            'trigger': 'text',
            'priority': 'high'
        },
        'lots.priceInfo.priceFixation': {
            'type': 'price_formation',
            'trigger': 'radio',
            'priority': 'high'
        },
        'lots.priceInfo.otherPriceFixation': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'lots.priceInfo.aiPriceFixationCustom': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'lot_0.priceInfo.priceClause': {
            'type': 'price_formation',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'lot_0.priceInfo.otherPriceClause': {
            'type': 'price_formation',
            'trigger': 'text',
            'priority': 'high'
        },
        'lot_0.priceInfo.priceFixation': {
            'type': 'price_formation',
            'trigger': 'radio',
            'priority': 'high'
        },
        'lot_0.priceInfo.otherPriceFixation': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'lot_0.priceInfo.aiPriceFixationCustom': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'lots.0.priceInfo.priceClause': {
            'type': 'price_formation',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'lots.0.priceInfo.otherPriceClause': {
            'type': 'price_formation',
            'trigger': 'text',
            'priority': 'high'
        },
        'lots.0.priceInfo.priceFixation': {
            'type': 'price_formation',
            'trigger': 'radio',
            'priority': 'high'
        },
        'lots.0.priceInfo.otherPriceFixation': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        'lots.0.priceInfo.aiPriceFixationCustom': {
            'type': 'price_formation',
            'trigger': 'button',
            'priority': 'high'
        },
        
        # Negotiation fields
        'negotiations.specialRequests': {
            'type': 'negotiation_terms',
            'trigger': 'checkbox',
            'priority': 'high'
        },
        'pogajanja.posebne_zelje': {
            'type': 'negotiation_terms',
            'trigger': 'checkbox',
            'priority': 'high'
        },
        'negotiationsInfo.specialNegotiationWishes': {
            'type': 'negotiation_terms',
            'trigger': 'radio',
            'priority': 'high',
            'prompt_key': 'pogajanja_posebne_zelje_pogajanja'
        },
        # Add ACTUAL negotiations fields from schema
        'negotiationsInfo.otherNegotiationSubject': {
            'type': 'negotiation_terms',
            'trigger': 'text',
            'priority': 'high'
        },
        # Add lot-prefixed versions of REAL negotiations fields
        'lots.negotiationsInfo.specialNegotiationWishes': {
            'type': 'negotiation_terms',
            'trigger': 'radio',
            'priority': 'high',
            'prompt_key': 'pogajanja_posebne_zelje_pogajanja'
        },
        'lots.negotiationsInfo.otherNegotiationSubject': {
            'type': 'negotiation_terms',
            'trigger': 'text',
            'priority': 'high'
        },
        # Add lot-indexed versions (lot_0, lot_1, etc) for unified architecture
        'lot_0.negotiationsInfo.specialNegotiationWishes': {
            'type': 'negotiation_terms',
            'trigger': 'radio',
            'priority': 'high',
            'prompt_key': 'pogajanja_posebne_zelje_pogajanja'
        },
        'lot_0.negotiationsInfo.otherNegotiationSubject': {
            'type': 'negotiation_terms',
            'trigger': 'text',
            'priority': 'high'
        },
        # Also add pattern for lots.0 format
        'lots.0.negotiationsInfo.specialNegotiationWishes': {
            'type': 'negotiation_terms',
            'trigger': 'radio',
            'priority': 'high',
            'prompt_key': 'pogajanja_posebne_zelje_pogajanja'
        },
        'lots.0.negotiationsInfo.otherNegotiationSubject': {
            'type': 'negotiation_terms',
            'trigger': 'text',
            'priority': 'high'
        },
        
        # Criteria fields
        'evaluationCriteria.socialCriteria.other': {
            'type': 'social_criteria',
            'trigger': 'button',
            'priority': 'medium'
        },
        'evaluationCriteria.environmentalCriteria.other': {
            'type': 'environmental_criteria',
            'trigger': 'button',
            'priority': 'medium'
        },
        
        # Participation conditions
        'participationConditions.professionalSuitabilitySection.professionalOption': {
            'type': 'professional_requirements',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'participationConditions.economicFinancialSection.economicOption': {
            'type': 'economic_requirements',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'participationConditions.technicalProfessionalSection.technicalOption': {
            'type': 'technical_requirements',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'selectionCriteria.otherCriteriaOption': {
            'type': 'selection_criteria',
            'trigger': 'dropdown',
            'priority': 'medium'
        },
        'participationConditions.professionalSuitability.other': {
            'type': 'professional_requirements',
            'trigger': 'button',
            'priority': 'medium'
        },
        'participationConditions.economicStatus.other': {
            'type': 'economic_requirements',
            'trigger': 'button',
            'priority': 'medium'
        },
        'participationConditions.technicalCapability.other': {
            'type': 'technical_requirements',
            'trigger': 'button',
            'priority': 'medium'
        }
    }
    
    # Class-level cache for AI renderer
    _cached_ai_renderer = None
    
    def __init__(self, context=None):
        """Initialize with form context."""
        self.context = context
        
        # Use cached AI renderer to avoid recreation
        if AIIntegrationHelper._cached_ai_renderer is None or AIIntegrationHelper._cached_ai_renderer.context != context:
            AIIntegrationHelper._cached_ai_renderer = AIFieldRenderer(context)
        self.ai_renderer = AIIntegrationHelper._cached_ai_renderer
    
    def should_use_ai_renderer(self, field_key: str, schema: dict) -> bool:
        """
        Determine if a field should use the AI renderer.
        
        Args:
            field_key: Full key path to the field
            schema: Field schema
            
        Returns:
            True if field should use AI renderer
        """
        # Add logging for all fields being checked
        logger.debug(f"[AI_FIELD_CHECK] Checking field: {field_key}")
        
        # EXPLICIT EXCLUSION for participationAndExclusion and participationConditions detail fields
        # These fields should NEVER have AI buttons - they are simple text inputs for clarification
        excluded_fields = [
            # participationAndExclusion detail fields
            'professionalMisconductDetails',
            'contractDeficienciesDetails', 
            'comparableSanctionsDetails',
            # participationConditions detail fields  
            'professionalRegisterDetails',
            'businessRegisterDetails',
            'licenseDetails',
            'membershipDetails',
            'professionalOtherDetails',
            'generalTurnoverDetails',
            'specificTurnoverDetails',
            'averageTurnoverDetails',
            'averageSpecificTurnoverDetails',
            'financialRatioDetails',
            'professionalInsuranceDetails',
            'accountNotBlockedDetails',
            'economicOtherDetails',
            'technicalStaffDetails',
            'equipmentDetails',
            'experienceDetails',
            'qualificationDetails',
            'qualityControlDetails',
            'environmentalManagementDetails',
            'subcontractingDetails',
            'technicalOtherDetails'
        ]
        for excluded in excluded_fields:
            if excluded in field_key:
                logger.info(f"[AI_FIELD_EXCLUDE] Explicitly excluding field from AI: {field_key}")
                return False
        
        # EXPLICIT CHECK FOR specialNegotiationWishes - FORCE AI
        if 'specialNegotiationWishes' in field_key:
            logger.warning(f"[NEGOTIATIONS_DEBUG] Found specialNegotiationWishes: {field_key}")
            logger.warning(f"[NEGOTIATIONS_DEBUG] Schema ai_enabled: {schema.get('ai_enabled', False)}")
            logger.warning(f"[NEGOTIATIONS_DEBUG] FORCING AI FOR THIS FIELD")
            return True  # FORCE AI for this field
        
        # First check if schema explicitly enables AI
        if schema.get('ai_enabled', False):
            logger.info(f"[AI_FIELD_MATCH] Field has ai_enabled=true in schema: {field_key}")
            return True
        
        # Debug logging for specific fields (only for text fields that should have AI)
        if ('negotiation' in field_key.lower() or 'pogajanja' in field_key.lower()) and schema.get('type') == 'string':
            logger.debug(f"[AI_FIELD_CHECK] NEGOTIATIONS field detected: {field_key}")
            logger.debug(f"[AI_FIELD_CHECK] Schema type: {schema.get('type')}, format: {schema.get('format')}, ai_enabled: {schema.get('ai_enabled', False)}")
        
        # Debug logging for cofinancer fields
        if 'cofinancer' in field_key.lower() or 'specialrequirements' in field_key.lower():
            # logger.info(f"[AI_FIELD_CHECK] Checking field: {field_key}")  # Reduced logging
            # logger.info(f"[AI_FIELD_CHECK] Schema type: {schema.get('type')}, Has enum: {'enum' in schema}")  # Reduced logging
            if 'enum' in schema:
                # logger.info(f"[AI_FIELD_CHECK] Enum options: {schema['enum']}")  # Reduced logging
                pass  # Keep the if block valid
        
        # Check if field is in our AI-enabled list (exact match)
        if field_key in self.AI_ENABLED_FIELDS:
            logger.info(f"[AI_FIELD_MATCH] Direct match for field: {field_key}")
            return True
        
        # Check for array patterns (e.g., cofinancers.0.specialRequirementsOption)
        # Remove array indices to check against our patterns
        normalized_key = field_key
        import re
        # Replace array indices with just the array name
        normalized_key = re.sub(r'\.\d+\.', '.', normalized_key)
        
        if normalized_key in self.AI_ENABLED_FIELDS:
            # logger.info(f"[AI_FIELD_MATCH] Normalized match for field: {field_key} -> {normalized_key}")  # Reduced logging
            return True
        
        # Also check for patterns where array index might be at different position
        # e.g., orderType.cofinancers.0.specialRequirementsOption
        parts = field_key.split('.')
        for i, part in enumerate(parts):
            if part.isdigit():
                # Remove the numeric index and rejoin
                test_key = '.'.join(parts[:i] + parts[i+1:])
                if test_key in self.AI_ENABLED_FIELDS:
                    return True
                # Also try with the array name before the index
                if i > 0:
                    test_key2 = '.'.join(parts[:i-1] + [parts[i-1]] + parts[i+1:])
                    if test_key2 in self.AI_ENABLED_FIELDS:
                        return True
        
        # Check for patterns that indicate AI should be enabled
        key_lower = field_key.lower()
        
        # IMPORTANT: Exclude specialRequirements without Option suffix
        if 'specialrequirements' in key_lower and 'option' not in key_lower:
            # logger.info(f"[AI_FIELD_EXCLUDE] Excluding specialRequirements field (no Option suffix): {field_key}")  # Reduced logging
            return False
        
        ai_patterns = [
            'specialrequirementsoption',  # The new enum field name
            'drugo',  # "Other" fields
            'custom',  # Custom fields
            'ai',  # Explicitly AI fields
            'predlog'  # Suggestion fields
        ]
        
        for pattern in ai_patterns:
            if pattern in key_lower:
                # Check schema to confirm it's a text field
                field_type = schema.get('type', '')
                if field_type == 'string':
                    return True
        
        # Check schema for AI hints
        if schema.get('ai_enabled', False):
            return True
        
        if schema.get('ai_suggestion', False):
            return True
        
        # Check for "prosim za predlog AI" in enum options
        if 'enum' in schema:
            for option in schema['enum']:
                if 'prosim' in str(option).lower() and 'ai' in str(option).lower():
                    # logger.info(f"[AI_FIELD_MATCH] Enum option match for field: {field_key} - found AI option")  # Reduced logging
                    return True
        
        # Final logging if no match
        if 'specialrequirements' in field_key.lower():
            # logger.info(f"[AI_FIELD_NO_MATCH] No AI match for field: {field_key}")  # Reduced logging
            pass  # Keep the if block valid
        
        # Log when field doesn't get AI (only for actual text fields, not checkboxes)
        if ('negotiation' in field_key.lower() or 'pogajanja' in field_key.lower()) and 'specialnegotiationwishes' in field_key.lower():
            logger.warning(f"[AI_FIELD_NO_MATCH] Negotiations text field NOT getting AI: {field_key}")
        
        return False
    
    def get_ai_config(self, field_key: str) -> Dict[str, Any]:
        """
        Get AI configuration for a specific field.
        
        Args:
            field_key: Full key path to the field
            
        Returns:
            Configuration dictionary with type, trigger, and priority
        """
        # Return specific config if field is in our list (exact match)
        if field_key in self.AI_ENABLED_FIELDS:
            return self.AI_ENABLED_FIELDS[field_key]
        
        # Check for array patterns (same logic as should_use_ai_renderer)
        import re
        normalized_key = re.sub(r'\.\d+\.', '.', field_key)
        
        if normalized_key in self.AI_ENABLED_FIELDS:
            return self.AI_ENABLED_FIELDS[normalized_key]
        
        # Check with removed indices
        parts = field_key.split('.')
        for i, part in enumerate(parts):
            if part.isdigit():
                test_key = '.'.join(parts[:i] + parts[i+1:])
                if test_key in self.AI_ENABLED_FIELDS:
                    return self.AI_ENABLED_FIELDS[test_key]
                if i > 0:
                    test_key2 = '.'.join(parts[:i-1] + [parts[i-1]] + parts[i+1:])
                    if test_key2 in self.AI_ENABLED_FIELDS:
                        return self.AI_ENABLED_FIELDS[test_key2]
        
        # Check if it's a special requirements option field
        if 'specialrequirementsoption' in field_key.lower():
            return {
                'type': 'cofinancer_requirements',
                'trigger': 'radio',
                'priority': 'high'
            }
        
        # Return default config for other AI fields
        return {
            'type': 'general',
            'trigger': 'button',  # Default to button for unknown fields
            'priority': 'low'
        }
    
    def render_field_with_ai(
        self, 
        field_key: str,
        schema: dict,
        parent_key: str = "",
        current_value: Any = None
    ) -> Any:
        """
        Render a field with AI assistance if appropriate.
        
        Args:
            field_key: Full key path to the field
            schema: Field schema
            parent_key: Parent key for nested fields
            current_value: Current field value
            
        Returns:
            The field value
        """
        # Check if this field should have AI
        logger.info(f"[AI_INTEGRATION] Checking field for AI: {field_key}")
        if self.should_use_ai_renderer(field_key, schema):
            logger.info(f"[AI_INTEGRATION] Field {field_key} will use AI renderer")
            # Get AI configuration
            ai_config = self.get_ai_config(field_key)
            
            # Add AI config to schema
            enhanced_schema = dict(schema)
            enhanced_schema['ai_enabled'] = True
            enhanced_schema['ai_field_type'] = ai_config['type']
            enhanced_schema['ai_trigger'] = ai_config['trigger']
            
            # Use AI renderer
            return self.ai_renderer.render_field_with_ai(
                field_key,
                enhanced_schema,
                parent_key,
                current_value
            )
        else:
            # Fall back to regular rendering (caller should handle this)
            return None
    
    def enhance_schema_with_ai(self, schema: dict, field_key: str) -> dict:
        """
        Enhance a field schema with AI configuration.
        
        Args:
            schema: Original field schema
            field_key: Full key path to the field
            
        Returns:
            Enhanced schema with AI configuration
        """
        if self.should_use_ai_renderer(field_key, schema):
            ai_config = self.get_ai_config(field_key)
            
            enhanced_schema = dict(schema)
            enhanced_schema['ai_enabled'] = True
            enhanced_schema['ai_field_type'] = ai_config['type']
            enhanced_schema['ai_trigger'] = ai_config['trigger']
            enhanced_schema['ai_priority'] = ai_config['priority']
            
            # Add AI option to enum if it's a dropdown
            if 'enum' in enhanced_schema and ai_config['trigger'] == 'dropdown':
                ai_option = "prosim za predlog AI"
                if ai_option not in enhanced_schema['enum']:
                    enhanced_schema['enum'] = list(enhanced_schema['enum'])
                    enhanced_schema['enum'].append(ai_option)
            
            return enhanced_schema
        
        return schema
    
    @staticmethod
    def inject_ai_into_section_renderer(section_renderer_instance):
        """
        Monkey-patch the section renderer to use AI for appropriate fields.
        This is a non-invasive way to add AI without modifying the original renderer.
        
        Args:
            section_renderer_instance: Instance of SectionRenderer to enhance
        """
        # Store original render method
        original_render = section_renderer_instance.field_renderer.render_field
        
        # Create AI helper
        ai_helper = AIIntegrationHelper(section_renderer_instance.context)
        
        # Create enhanced render method
        def enhanced_render_field(prop_name, prop_schema, parent_key, required=False):
            """Enhanced field renderer with AI support."""
            full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
            
            # Log ALL fields being rendered, especially negotiations
            if 'negotiation' in full_key.lower() or 'pogajanja' in full_key.lower() or 'specialnegotiationwishes' in full_key.lower():
                logger.info(f"[ENHANCED_RENDER_SECTION] Processing negotiations field: {full_key}")
                logger.info(f"[ENHANCED_RENDER_SECTION] Schema type: {prop_schema.get('type')}, ai_enabled: {prop_schema.get('ai_enabled', False)}")
            
            # Check if this field should use AI
            if ai_helper.should_use_ai_renderer(full_key, prop_schema):
                # Get current value
                current_value = section_renderer_instance.context.get_field_value(
                    full_key, 
                    prop_schema.get('default', '')
                )
                
                # Render with AI
                value = ai_helper.render_field_with_ai(
                    full_key,
                    prop_schema,
                    parent_key,
                    current_value
                )
                
                if value is not None:
                    # Store the value
                    section_renderer_instance.context.set_field_value(full_key, value)
                    return value
            
            # Fall back to original renderer
            return original_render(prop_name, prop_schema, parent_key, required)
        
        # Replace the render method
        section_renderer_instance.field_renderer.render_field = enhanced_render_field
        
        logger.info("[AI_INJECTION] AI integration successfully injected into section renderer")
        logger.info(f"[AI_INJECTION] Enhanced render method installed: {enhanced_render_field}")
        
        return section_renderer_instance
    
    @staticmethod
    def inject_ai_into_field_renderer(field_renderer_instance):
        """
        Monkey-patch the field renderer directly to use AI for appropriate fields.
        
        Args:
            field_renderer_instance: Instance of FieldRenderer to enhance
        """
        # Store original render method
        original_render = field_renderer_instance.render_field
        
        # Create AI helper - note: context might not be available here
        ai_helper = AIIntegrationHelper(getattr(field_renderer_instance, 'context', None))
        
        # Create enhanced render method
        def enhanced_render_field(prop_name, prop_schema, parent_key, required=False):
            """Enhanced field renderer with AI support."""
            full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
            
            # Log ALL fields being rendered, especially negotiations
            if 'negotiation' in full_key.lower() or 'pogajanja' in full_key.lower() or 'specialnegotiationwishes' in full_key.lower():
                logger.warning(f"[ENHANCED_RENDER_FIELD] Processing negotiations field: {full_key}")
                logger.warning(f"[ENHANCED_RENDER_FIELD] Schema type: {prop_schema.get('type')}, ai_enabled: {prop_schema.get('ai_enabled', False)}")
                
                # FORCE AI FOR specialNegotiationWishes
                if 'specialNegotiationWishes' in full_key:
                    logger.warning(f"[ENHANCED_RENDER_FIELD] FORCING AI FOR specialNegotiationWishes")
                    prop_schema['ai_enabled'] = True  # Force it!
            
            # Check if this field should use AI
            if ai_helper.should_use_ai_renderer(full_key, prop_schema):
                # Try to get current value from session state
                import streamlit as st
                current_value = st.session_state.get(full_key, prop_schema.get('default', ''))
                
                # Render with AI
                value = ai_helper.render_field_with_ai(
                    full_key,
                    prop_schema,
                    parent_key,
                    current_value
                )
                
                if value is not None:
                    # Store the value in session state
                    st.session_state[full_key] = value
                    return value
            
            # Fall back to original renderer
            return original_render(prop_name, prop_schema, parent_key, required)
        
        # Replace the render method
        field_renderer_instance.render_field = enhanced_render_field
        
        # logger.info("AI integration injected into field renderer")  # Reduced logging
        
        return field_renderer_instance