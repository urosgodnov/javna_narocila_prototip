"""
AI Integration Patch for app.py
This module provides a minimal patch to add AI suggestions to the existing app.py
without modifying the core file.

Usage:
    Import this at the beginning of app.py:
    from patches.ai_integration_patch import apply_ai_integration
    
    Then call it after initializing the form:
    apply_ai_integration()
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def apply_ai_integration():
    """
    Apply AI integration to the current Streamlit app.
    This function should be called in app.py after form initialization.
    """
    try:
        # Import the AI integration helper
        from ui.renderers.ai_integration_helper import AIIntegrationHelper
        
        # Check if we're in a form rendering context
        if 'current_step' in st.session_state:
            current_step = st.session_state.get('current_step', 0)
            
            # Log integration
            logger.info(f"Applying AI integration to step {current_step}")
            
            # Initialize AI helper in session state if not present
            if 'ai_integration_helper' not in st.session_state:
                st.session_state.ai_integration_helper = AIIntegrationHelper()
            
            # Add AI status indicator
            if st.sidebar:
                with st.sidebar:
                    st.markdown("---")
                    st.markdown("**AI Asistent**")
                    st.success("AI predlogi so na voljo")
                    st.caption("Poiščite polja z AI opcijami")
        
        return True
        
    except ImportError as e:
        logger.warning(f"AI integration not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Error applying AI integration: {e}")
        return False


def inject_ai_into_renderer(renderer_instance):
    """
    Inject AI capabilities into an existing renderer instance.
    
    Args:
        renderer_instance: The renderer to enhance with AI
        
    Returns:
        Enhanced renderer instance
    """
    try:
        from ui.renderers.ai_integration_helper import AIIntegrationHelper
        
        # Apply injection
        AIIntegrationHelper.inject_ai_into_section_renderer(renderer_instance)
        
        logger.info("AI successfully injected into renderer")
        return renderer_instance
        
    except Exception as e:
        logger.error(f"Failed to inject AI into renderer: {e}")
        return renderer_instance


def add_ai_to_field(field_key: str, field_value: Any, schema: Dict[str, Any]) -> Any:
    """
    Add AI assistance to a specific field.
    
    Args:
        field_key: The field identifier
        field_value: Current field value
        schema: Field schema/configuration
        
    Returns:
        Updated field value after AI interaction
    """
    try:
        from ui.renderers.ai_field_renderer import AIFieldRenderer
        
        # Initialize AI renderer
        ai_renderer = AIFieldRenderer()
        
        # Render field with AI
        return ai_renderer.render_field_with_ai(
            field_key,
            schema,
            "",
            field_value
        )
        
    except Exception as e:
        logger.error(f"Failed to add AI to field {field_key}: {e}")
        return field_value


# Configuration for easy import
AI_CONFIG = {
    'enabled': True,
    'knowledge_base_first': True,  # Query Qdrant before general AI
    'show_context': True,  # Show context used for suggestions
    'max_suggestions': 3,  # Maximum number of suggestions to show
    'cache_suggestions': True,  # Cache suggestions to avoid repeated API calls
    'trigger_types': {
        'dropdown': 'prosim za predlog AI',
        'checkbox': 'Uporabi AI za predlog',
        'button': 'AI predlog'
    }
}


def get_ai_status() -> Dict[str, Any]:
    """
    Get current AI integration status.
    
    Returns:
        Dictionary with status information
    """
    try:
        from services.qdrant_crud_service import QdrantCRUDService
        from services.ai_response_service import AIResponseService
        
        status = {
            'ai_available': False,
            'knowledge_base_available': False,
            'openai_configured': False,
            'qdrant_connected': False
        }
        
        # Check OpenAI
        try:
            ai_service = AIResponseService()
            if ai_service.client:
                status['openai_configured'] = True
                status['ai_available'] = True
        except:
            pass
        
        # Check Qdrant
        try:
            qdrant_service = QdrantCRUDService()
            if qdrant_service.qdrant_client:
                status['qdrant_connected'] = True
                status['knowledge_base_available'] = True
        except:
            pass
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return {
            'ai_available': False,
            'knowledge_base_available': False,
            'error': str(e)
        }


# Auto-apply integration if imported
if __name__ != "__main__":
    # Log that the patch is loaded
    logger.info("AI Integration Patch loaded - ready to apply")
    
    # Check status
    status = get_ai_status()
    if status['ai_available']:
        logger.info("AI services are available")
    else:
        logger.warning("AI services are not fully configured")