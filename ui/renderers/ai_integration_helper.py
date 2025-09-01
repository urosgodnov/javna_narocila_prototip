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
        'vrsta_narocila.posebne_zahteve_sofinancerja': {
            'type': 'cofinancer_requirements',
            'trigger': 'checkbox',
            'priority': 'high'
        },
        'procurementType.specialRequirements': {
            'type': 'cofinancer_requirements', 
            'trigger': 'checkbox',
            'priority': 'high'
        },
        
        # Price information fields
        'priceInfo.priceFixation': {
            'type': 'price_formation',
            'trigger': 'dropdown',
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
    
    def __init__(self, context=None):
        """Initialize with form context."""
        self.context = context
        self.ai_renderer = AIFieldRenderer(context)
    
    def should_use_ai_renderer(self, field_key: str, schema: dict) -> bool:
        """
        Determine if a field should use the AI renderer.
        
        Args:
            field_key: Full key path to the field
            schema: Field schema
            
        Returns:
            True if field should use AI renderer
        """
        # Check if field is in our AI-enabled list
        if field_key in self.AI_ENABLED_FIELDS:
            return True
        
        # Check for patterns that indicate AI should be enabled
        key_lower = field_key.lower()
        ai_patterns = [
            'drugo',  # "Other" fields
            'custom',  # Custom fields
            'ai',  # Explicitly AI fields
            'predlog',  # Suggestion fields
            'requirements',  # Requirements often need AI
            'zahteve',  # Requirements in Slovenian
            'special',  # Special fields
            'posebn'  # Special in Slovenian
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
                    return True
        
        return False
    
    def get_ai_config(self, field_key: str) -> Dict[str, Any]:
        """
        Get AI configuration for a specific field.
        
        Args:
            field_key: Full key path to the field
            
        Returns:
            Configuration dictionary with type, trigger, and priority
        """
        # Return specific config if field is in our list
        if field_key in self.AI_ENABLED_FIELDS:
            return self.AI_ENABLED_FIELDS[field_key]
        
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
        if self.should_use_ai_renderer(field_key, schema):
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
        
        logger.info("AI integration injected into section renderer")
        
        return section_renderer_instance