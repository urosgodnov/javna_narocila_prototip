"""
Test suite for AI field extension functionality.
Story 4.1-4.3: Extended AI prompts and field management
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.ai_manager import (
    PROMPT_SECTIONS,
    get_field_type,
    get_default_prompt,
    prepare_prompt_context
)


class TestPromptSectionsCoverage:
    """Test that all required fields are covered in PROMPT_SECTIONS"""
    
    def test_all_required_fields_present(self):
        """Verify all required fields are in PROMPT_SECTIONS"""
        required_fields = [
            'specialRequirements',
            'useAIForRequirements',
            'mixedOrder_specialRequirements',
            'eu_funding_requirements',
            'reporting_requirements',
            'national_funding_requirements',
            'cofinancer_special_requirements',
            'cofinancer_program_requirements',
            'mixedOrder_cofinancer_requirements',
            'mixedOrderComponents_requirements'
        ]
        
        all_fields = []
        for section in PROMPT_SECTIONS.values():
            all_fields.extend(section.get('fields', []))
        
        for field in required_fields:
            assert field in all_fields, f"Missing field: {field}"
    
    def test_new_sections_exist(self):
        """Test that new sections were added"""
        assert 'mesano_narocilo' in PROMPT_SECTIONS
        assert 'sofinanciranje' in PROMPT_SECTIONS
        
        # Check section titles
        assert PROMPT_SECTIONS['mesano_narocilo']['title'] == 'Mešano javno naročilo'
        assert PROMPT_SECTIONS['sofinanciranje']['title'] == 'Sofinanciranje'
    
    def test_context_fields_included(self):
        """Test that context fields are included"""
        sofinanciranje_fields = PROMPT_SECTIONS['sofinanciranje']['fields']
        
        context_fields = [
            'programName_context',
            'programArea_context',
            'programCode_context'
        ]
        
        for field in context_fields:
            assert field in sofinanciranje_fields, f"Missing context field: {field}"


class TestFieldTypeDetection:
    """Test field type detection accuracy"""
    
    def test_boolean_field_detection(self):
        """Test detection of boolean/checkbox fields"""
        boolean_fields = [
            'useAIForRequirements',
            'enableCheckbox',
            'allowAccess',
            'is_active'
        ]
        
        for field in boolean_fields:
            assert get_field_type(field) == 'boolean', f"Field {field} should be boolean"
    
    def test_textarea_field_detection(self):
        """Test detection of textarea fields"""
        textarea_fields = [
            'specialRequirements',
            'project_description',
            'technical_specification',
            'evaluation_criteria',
            'special_conditions',
            'additional_notes'
        ]
        
        for field in textarea_fields:
            assert get_field_type(field) == 'textarea', f"Field {field} should be textarea"
    
    def test_context_field_detection(self):
        """Test detection of context fields"""
        context_fields = [
            'programCode_context',
            'user_reference',
            'document_id',
            'project_code'
        ]
        
        for field in context_fields:
            assert get_field_type(field) == 'context', f"Field {field} should be context"
    
    def test_select_field_detection(self):
        """Test detection of select/dropdown fields"""
        select_fields = [
            'order_type',
            'document_category',
            'project_status',
            'program_name'
        ]
        
        for field in select_fields:
            assert get_field_type(field) == 'select', f"Field {field} should be select"
    
    def test_default_text_field(self):
        """Test that unknown fields default to text"""
        text_fields = [
            'contact_name',
            'email_address',
            'phone_number',
            'random_field'
        ]
        
        for field in text_fields:
            assert get_field_type(field) == 'text', f"Field {field} should default to text"


class TestDefaultPromptGeneration:
    """Test default prompts for new fields"""
    
    def test_specific_field_prompts(self):
        """Test that specific fields have custom prompts"""
        fields_with_prompts = [
            'specialRequirements',
            'mixedOrder_specialRequirements',
            'eu_funding_requirements',
            'national_funding_requirements',
            'reporting_requirements'
        ]
        
        for field in fields_with_prompts:
            prompt = get_default_prompt('', field)
            assert prompt, f"No default prompt for {field}"
            assert 'slovenščini' in prompt.lower() or 'slovenš' in prompt.lower(), \
                f"Prompt for {field} should mention Slovenian language"
            assert len(prompt) > 50, f"Prompt for {field} seems too short"
    
    def test_eu_funding_prompt_content(self):
        """Test EU funding requirements prompt has correct content"""
        prompt = get_default_prompt('', 'eu_funding_requirements')
        
        # Check for key EU requirements
        assert 'EU' in prompt
        assert 'vidnost' in prompt.lower() or 'financiranja' in prompt.lower()
        assert 'državnih pomoči' in prompt.lower()
        assert 'horizontalni cilji' in prompt.lower()
    
    def test_mixed_order_prompt_content(self):
        """Test mixed order prompt references components"""
        prompt = get_default_prompt('', 'mixedOrder_specialRequirements')
        
        assert 'mešano' in prompt.lower()
        assert 'komponente' in prompt.lower() or 'deleži' in prompt.lower()
        assert '{componentBreakdown}' in prompt  # Should have placeholder
    
    def test_fallback_prompt(self):
        """Test fallback for unknown fields"""
        # Test original field format
        prompt = get_default_prompt('vrsta_narocila', 'posebne_zahteve_sofinancerja')
        assert 'javna naročila' in prompt.lower()
        assert 'slovenščini' in prompt.lower()
        
        # Test completely unknown field
        prompt = get_default_prompt('unknown_section', 'unknown_field')
        assert prompt  # Should return something
        assert 'generiraj' in prompt.lower() or 'pripravi' in prompt.lower()


class TestPromptContextExtraction:
    """Test context variable extraction"""
    
    def test_basic_context_extraction(self):
        """Test extraction of basic context variables"""
        form_data = {
            'vrsta_narocila': 'blago',
            'programName': 'Kohezijski sklad',
            'programArea': 'Digitalizacija',
            'programCode': 'EU-2021-2027',
            'estimatedValue': 100000
        }
        
        context = prepare_prompt_context(form_data, 'specialRequirements')
        
        assert context['order_type'] == 'blago'
        assert context['programName'] == 'Kohezijski sklad'
        assert context['programArea'] == 'Digitalizacija'
        assert context['programCode'] == 'EU-2021-2027'
        assert context['estimatedValue'] == 100000
    
    def test_mixed_order_context(self):
        """Test context extraction for mixed orders"""
        form_data = {
            'vrsta_narocila': 'mešano javno naročilo',
            'mixedOrderComponents': [
                {'type': 'blago', 'percentage': 60},
                {'type': 'storitve', 'percentage': 30},
                {'type': 'gradnje', 'percentage': 10}
            ]
        }
        
        context = prepare_prompt_context(form_data, 'mixedOrder_specialRequirements')
        
        assert context['order_type'] == 'mešano javno naročilo'
        assert 'componentBreakdown' in context
        assert 'blago: 60%' in context['componentBreakdown']
        assert 'storitve: 30%' in context['componentBreakdown']
        assert 'gradnje: 10%' in context['componentBreakdown']
    
    def test_missing_data_handling(self):
        """Test handling of missing form data"""
        form_data = {}  # Empty form data
        
        context = prepare_prompt_context(form_data, 'specialRequirements')
        
        # Should have defaults
        assert context['order_type'] == 'blago'  # Default value
        assert context['programName'] == ''
        assert context['programArea'] == ''
        assert context['programCode'] == ''
        assert context['estimatedValue'] == 0


class TestIntegration:
    """Integration tests for the complete flow"""
    
    def test_field_in_section_with_correct_type(self):
        """Test that a field is correctly configured end-to-end"""
        # Check field is in sections
        all_fields = []
        for section in PROMPT_SECTIONS.values():
            all_fields.extend(section.get('fields', []))
        
        assert 'specialRequirements' in all_fields
        
        # Check field type is detected correctly
        field_type = get_field_type('specialRequirements')
        assert field_type == 'textarea'
        
        # Check default prompt exists
        prompt = get_default_prompt('', 'specialRequirements')
        assert 'sofinanciranja' in prompt.lower()
    
    def test_checkbox_field_configuration(self):
        """Test checkbox field is properly configured"""
        # Check field exists
        all_fields = []
        for section in PROMPT_SECTIONS.values():
            all_fields.extend(section.get('fields', []))
        
        assert 'useAIForRequirements' in all_fields
        
        # Check type detection
        field_type = get_field_type('useAIForRequirements')
        assert field_type == 'boolean'


class TestDocumentationExamples:
    """Test that documentation examples work correctly"""
    
    def test_example_scenarios(self):
        """Test the example scenarios from documentation"""
        scenarios = [
            {
                'name': 'EU Kohezijski sklad - Digitalizacija',
                'data': {
                    'programName': 'Kohezijski sklad',
                    'programArea': 'Digitalna transformacija',
                    'programCode': 'SI-EU-KS-2021',
                    'vrsta_narocila': 'blago'
                },
                'field': 'eu_funding_requirements'
            },
            {
                'name': 'Nacionalno sofinanciranje - Infrastruktura',
                'data': {
                    'programName': 'Slovenski regionalni razvoj',
                    'programArea': 'Cestna infrastruktura',
                    'programCode': 'SI-RR-2024',
                    'vrsta_narocila': 'gradnje'
                },
                'field': 'national_funding_requirements'
            }
        ]
        
        for scenario in scenarios:
            # Get context for scenario
            context = prepare_prompt_context(scenario['data'], scenario['field'])
            
            # Verify context was extracted
            assert context['programName'] == scenario['data']['programName']
            assert context['programArea'] == scenario['data']['programArea']
            
            # Get prompt for field
            prompt = get_default_prompt('', scenario['field'])
            assert prompt, f"No prompt for {scenario['field']}"
            
            # Verify prompt is relevant
            if 'EU' in scenario['name']:
                assert 'EU' in prompt
            if 'Nacionalno' in scenario['name']:
                assert 'nacionalno' in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])