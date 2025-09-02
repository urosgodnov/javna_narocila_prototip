#!/usr/bin/env python3
"""
Test that participationAndExclusion detail fields don't get AI buttons
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.renderers.ai_integration_helper import AIIntegrationHelper

def test_exclusion_fields_no_ai():
    """Test that exclusion detail fields are excluded from AI"""
    helper = AIIntegrationHelper()
    
    # Fields that should NOT have AI
    excluded_fields = [
        'participationAndExclusion.professionalMisconductDetails',
        'participationAndExclusion.contractDeficienciesDetails',
        'participationAndExclusion.comparableSanctionsDetails',
        'lots.0.participationAndExclusion.professionalMisconductDetails',
        'lots.0.participationAndExclusion.contractDeficienciesDetails',
        'lots.0.participationAndExclusion.comparableSanctionsDetails'
    ]
    
    print("=" * 60)
    print("TESTING PARTICIPATION FIELDS - NO AI BUTTONS")
    print("=" * 60)
    
    all_passed = True
    for field_key in excluded_fields:
        # Test with a simple string schema (like these fields have)
        schema = {
            'type': 'string',
            'title': 'Test field'
        }
        
        should_have_ai = helper.should_use_ai_renderer(field_key, schema)
        
        if should_have_ai:
            print(f"❌ FAIL: {field_key} - Has AI (should NOT have AI!)")
            all_passed = False
        else:
            print(f"✅ PASS: {field_key} - No AI (correct)")
    
    # Also test that negotiation fields that SHOULD have AI still work
    print("\n" + "=" * 60)
    print("VERIFYING NEGOTIATIONS FIELDS STILL HAVE AI")
    print("=" * 60)
    
    ai_fields = [
        'negotiationsInfo.specialNegotiationWishes',
        'negotiationsInfo.otherNegotiationSubject'
    ]
    
    for field_key in ai_fields:
        schema = {
            'type': 'string',
            'ai_enabled': True
        }
        
        should_have_ai = helper.should_use_ai_renderer(field_key, schema)
        
        if should_have_ai:
            print(f"✅ PASS: {field_key} - Has AI (correct)")
        else:
            print(f"❌ FAIL: {field_key} - No AI (should HAVE AI!)")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! 🎉")
        print("ParticipationAndExclusion detail fields will NOT have AI buttons")
    else:
        print("SOME TESTS FAILED! ❌")
        print("Please check the configuration")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_exclusion_fields_no_ai()
    sys.exit(0 if success else 1)