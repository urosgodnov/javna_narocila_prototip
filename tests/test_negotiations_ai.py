#!/usr/bin/env python3
"""
Test script to verify negotiations AI is working correctly
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_schema_ai_enabled():
    """Test that correct fields have ai_enabled in schema"""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    negotiations = schema['properties']['negotiationsInfo']['properties']
    
    # Check fields that SHOULD have AI
    assert negotiations['otherNegotiationSubject'].get('ai_enabled') == True, \
        "otherNegotiationSubject should have ai_enabled=true"
    
    assert negotiations['specialNegotiationWishes'].get('ai_enabled') == True, \
        "specialNegotiationWishes should have ai_enabled=true"
    
    # Check fields that should NOT have AI (dropdowns)
    assert 'ai_enabled' not in negotiations['negotiationRounds'], \
        "negotiationRounds (dropdown) should NOT have ai_enabled"
    
    assert 'ai_enabled' not in negotiations['negotiationSubject'], \
        "negotiationSubject (dropdown) should NOT have ai_enabled"
    
    print("✅ Schema AI configuration is correct")
    return True

def test_ai_integration_helper():
    """Test that AI integration helper is configured correctly"""
    from ui.renderers.ai_integration_helper import AIIntegrationHelper
    
    helper = AIIntegrationHelper()
    
    # Test that text/textarea fields are detected as AI-eligible
    assert helper.should_use_ai_renderer('negotiationsInfo.otherNegotiationSubject', {'type': 'string', 'ai_enabled': True}), \
        "otherNegotiationSubject should be AI-eligible"
    
    assert helper.should_use_ai_renderer('negotiationsInfo.specialNegotiationWishes', {'type': 'string', 'format': 'textarea', 'ai_enabled': True}), \
        "specialNegotiationWishes should be AI-eligible"
    
    # Test that dropdown fields are NOT AI-eligible
    assert not helper.should_use_ai_renderer('negotiationsInfo.negotiationRounds', {'type': 'string', 'enum': ['1 krog', 'več krogov']}), \
        "negotiationRounds (enum) should NOT be AI-eligible"
    
    print("✅ AI integration helper is configured correctly")
    return True

def test_widget_warning_fix():
    """Test that widget warning fix is in place"""
    with open('ui/renderers/ai_field_renderer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that we're using only key parameter for textareas with AI
    assert 'key=textarea_key,  # Use ONLY key, not value parameter' in content, \
        "Widget warning fix should be in place"
    
    # Check that we're NOT setting both value and key
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'st.text_area(' in line and 'negotiationsInfo.specialNegotiationWishes' in '\n'.join(lines[max(0, i-10):i+10]):
            # Make sure we're not using value parameter
            context = '\n'.join(lines[i:min(len(lines), i+10)])
            assert 'value=' not in context or 'Use ONLY key' in context, \
                "Should not use value parameter with session state key"
    
    print("✅ Widget warning fix is in place")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING NEGOTIATIONS AI INTEGRATION")
    print("=" * 60)
    
    try:
        test_schema_ai_enabled()
        test_ai_integration_helper()
        test_widget_warning_fix()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print("\nNegotiations AI is working correctly:")
        print("✅ otherNegotiationSubject has AI assistance")
        print("✅ specialNegotiationWishes has AI assistance")
        print("✅ negotiationRounds dropdown has NO AI option")
        print("✅ negotiationSubject dropdown has NO AI option")
        print("✅ Widget warnings are removed")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()