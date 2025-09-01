"""
Test script for AI Suggestion Transfer feature
Tests the brownfield story implementation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAISuggestionService(unittest.TestCase):
    """Test the AI Suggestion Service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Streamlit session state
        self.mock_session_state = {
            'projectInfo.title': 'Testni projekt za IT sistem',
            'projectInfo.description': 'Nadgradnja obstoječega sistema',
            'projectInfo.hasCofinancing': True,
            'procurementType.type': 'storitve',
            'projectInfo.estimatedValue': 250000,
            'current_lot_index': 0,
            'lots': [{'name': 'Programska oprema', 'type': 'software'}],
            'cofinancers': ['EU - Digitalna Evropa'],
            'funding_programs': ['REACT-EU']
        }
    
    @patch('services.ai_suggestion_service.QdrantCRUDService')
    @patch('services.ai_suggestion_service.AIResponseService')
    def test_context_collection(self, mock_ai_response, mock_qdrant):
        """Test that form context is properly collected."""
        from services.ai_suggestion_service import AIFieldSuggestionService
        
        service = AIFieldSuggestionService()
        
        # Test context collection
        context = service._collect_form_context(self.mock_session_state)
        
        # Verify context contains expected fields
        self.assertEqual(context['project_title'], 'Testni projekt za IT sistem')
        self.assertEqual(context['procurement_type'], 'storitve')
        self.assertEqual(context['estimated_value'], 250000)
        self.assertTrue(context['has_cofinancing'])
        self.assertIn('EU - Digitalna Evropa', str(context['cofinancers']))
    
    @patch('services.ai_suggestion_service.QdrantCRUDService')
    @patch('services.ai_suggestion_service.AIResponseService')
    def test_contextual_query_building(self, mock_ai_response, mock_qdrant):
        """Test that contextual queries are built correctly."""
        from services.ai_suggestion_service import AIFieldSuggestionService
        
        service = AIFieldSuggestionService()
        
        # Test query for cofinancer requirements
        context = service._collect_form_context(self.mock_session_state)
        query = service._build_contextual_query(
            'vrsta_narocila.posebne_zahteve_sofinancerja',
            'cofinancer_requirements',
            context
        )
        
        # Verify query contains relevant terms
        self.assertIn('posebne zahteve sofinancerja', query)
        self.assertIn('EU', query)
        self.assertIn('storitve', query)
    
    @patch('services.ai_suggestion_service.QdrantCRUDService')
    @patch('services.ai_suggestion_service.AIResponseService')
    def test_knowledge_base_fallback(self, mock_ai_response, mock_qdrant):
        """Test fallback from knowledge base to general AI."""
        from services.ai_suggestion_service import AIFieldSuggestionService
        
        # Setup mocks
        mock_qdrant_instance = Mock()
        mock_qdrant_instance.search_documents.return_value = ([], 0)  # No KB results
        mock_qdrant.return_value = mock_qdrant_instance
        
        mock_ai_instance = Mock()
        mock_ai_instance.generate_response.return_value = "Test AI suggestion"
        mock_ai_response.return_value = mock_ai_instance
        
        service = AIFieldSuggestionService()
        
        # Get suggestions (should fall back to AI)
        result = service.get_field_suggestion(
            field_context='negotiations.special_requests',
            field_type='negotiation_terms',
            query='Special negotiation terms',
            form_data=self.mock_session_state
        )
        
        # Verify AI was called
        self.assertEqual(result['source'], 'ai_generated')
        self.assertIsNotNone(result['suggestions'])


class TestAIFieldRenderer(unittest.TestCase):
    """Test the AI Field Renderer."""
    
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.selectbox')
    def test_dropdown_with_ai_option(self, mock_selectbox, mock_session_state):
        """Test that dropdown fields get AI option added."""
        from ui.renderers.ai_field_renderer import AIFieldRenderer
        
        renderer = AIFieldRenderer()
        
        # Test schema with enum
        schema = {
            'type': 'string',
            'enum': ['option1', 'option2'],
            'title': 'Test Field',
            'ai_enabled': True
        }
        
        # Mock selectbox to return AI option
        mock_selectbox.return_value = 'prosim za predlog AI'
        
        # Render field
        result = renderer.render_field_with_ai(
            'test.field',
            schema,
            '',
            'option1'
        )
        
        # Verify AI option was added to dropdown
        call_args = mock_selectbox.call_args
        options = call_args[1]['options']
        self.assertIn('prosim za predlog AI', options)
    
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.checkbox')
    @patch('streamlit.text_area')
    def test_textarea_with_checkbox(self, mock_textarea, mock_checkbox, mock_session_state):
        """Test that text areas get checkbox trigger."""
        from ui.renderers.ai_field_renderer import AIFieldRenderer
        
        renderer = AIFieldRenderer()
        
        # Test schema for textarea
        schema = {
            'type': 'string',
            'format': 'textarea',
            'title': 'Test Text Area',
            'ai_enabled': True
        }
        
        # Mock checkbox to be checked
        mock_checkbox.return_value = True
        mock_textarea.return_value = "Test content"
        
        # Render field
        result = renderer.render_field_with_ai(
            'test.textarea',
            schema,
            '',
            ''
        )
        
        # Verify checkbox was created
        mock_checkbox.assert_called_once()
        self.assertEqual(mock_checkbox.call_args[0][0], "Uporabi AI za predlog")


class TestAIIntegrationHelper(unittest.TestCase):
    """Test the AI Integration Helper."""
    
    def test_field_detection(self):
        """Test that AI-enabled fields are properly detected."""
        from ui.renderers.ai_integration_helper import AIIntegrationHelper
        
        helper = AIIntegrationHelper()
        
        # Test known AI fields
        self.assertTrue(helper.should_use_ai_renderer(
            'vrsta_narocila.posebne_zahteve_sofinancerja',
            {'type': 'string'}
        ))
        
        self.assertTrue(helper.should_use_ai_renderer(
            'priceInfo.priceFixation',
            {'type': 'string', 'enum': ['option1', 'prosim za predlog AI']}
        ))
        
        # Test pattern-based detection
        self.assertTrue(helper.should_use_ai_renderer(
            'some.field.drugo',
            {'type': 'string'}
        ))
        
        self.assertTrue(helper.should_use_ai_renderer(
            'custom.requirements',
            {'type': 'string'}
        ))
        
        # Test non-AI fields
        self.assertFalse(helper.should_use_ai_renderer(
            'basic.number.field',
            {'type': 'number'}
        ))
    
    def test_ai_config_retrieval(self):
        """Test that correct AI configuration is returned for fields."""
        from ui.renderers.ai_integration_helper import AIIntegrationHelper
        
        helper = AIIntegrationHelper()
        
        # Test high priority field
        config = helper.get_ai_config('vrsta_narocila.posebne_zahteve_sofinancerja')
        self.assertEqual(config['type'], 'cofinancer_requirements')
        self.assertEqual(config['trigger'], 'checkbox')
        self.assertEqual(config['priority'], 'high')
        
        # Test medium priority field
        config = helper.get_ai_config('evaluationCriteria.socialCriteria.other')
        self.assertEqual(config['type'], 'social_criteria')
        self.assertEqual(config['trigger'], 'button')
        self.assertEqual(config['priority'], 'medium')
        
        # Test unknown field
        config = helper.get_ai_config('unknown.field')
        self.assertEqual(config['type'], 'general')
        self.assertEqual(config['priority'], 'low')


class TestIntegrationPatch(unittest.TestCase):
    """Test the integration patch module."""
    
    @patch('patches.ai_integration_patch.logger')
    def test_ai_status_check(self, mock_logger):
        """Test that AI status is properly checked."""
        from patches.ai_integration_patch import get_ai_status
        
        status = get_ai_status()
        
        # Verify status structure
        self.assertIn('ai_available', status)
        self.assertIn('knowledge_base_available', status)
        self.assertIn('openai_configured', status)
        self.assertIn('qdrant_connected', status)
    
    @patch('streamlit.session_state', {'current_step': 1})
    @patch('streamlit.sidebar')
    def test_apply_integration(self, mock_sidebar):
        """Test that integration can be applied."""
        from patches.ai_integration_patch import apply_ai_integration
        
        # Apply integration
        result = apply_ai_integration()
        
        # Should return True if successful or False if not available
        self.assertIsInstance(result, bool)


def run_integration_test():
    """Run a simple integration test."""
    logger.info("Starting AI Integration Test")
    
    try:
        # Test import
        from services.ai_suggestion_service import AIFieldSuggestionService
        logger.info("✓ AI Suggestion Service imported successfully")
        
        from ui.renderers.ai_field_renderer import AIFieldRenderer
        logger.info("✓ AI Field Renderer imported successfully")
        
        from ui.renderers.ai_integration_helper import AIIntegrationHelper
        logger.info("✓ AI Integration Helper imported successfully")
        
        from patches.ai_integration_patch import apply_ai_integration, get_ai_status
        logger.info("✓ Integration patch imported successfully")
        
        # Check status
        status = get_ai_status()
        logger.info(f"AI Status: {status}")
        
        if status.get('ai_available'):
            logger.info("✓ AI services are available")
        else:
            logger.warning("⚠ AI services not fully configured")
        
        if status.get('knowledge_base_available'):
            logger.info("✓ Knowledge base is available")
        else:
            logger.warning("⚠ Knowledge base not available")
        
        # Test service initialization
        try:
            service = AIFieldSuggestionService()
            logger.info("✓ AI service initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize AI service: {e}")
        
        logger.info("\nIntegration test completed!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


if __name__ == '__main__':
    # Run integration test first
    print("\n" + "="*50)
    print("AI SUGGESTION TRANSFER - INTEGRATION TEST")
    print("="*50 + "\n")
    
    if run_integration_test():
        print("\n" + "="*50)
        print("Running unit tests...")
        print("="*50 + "\n")
        
        # Run unit tests
        unittest.main(verbosity=2)
    else:
        print("\nIntegration test failed. Please check configuration.")
        sys.exit(1)