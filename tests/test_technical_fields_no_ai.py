#!/usr/bin/env python3
"""
Test that technical capability detail fields don't get AI buttons
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.renderers.ai_integration_helper import AIIntegrationHelper

def test_technical_fields_no_ai():
    """Test that technical section detail fields are excluded from AI"""
    helper = AIIntegrationHelper()
    
    # Fields from the screenshot that should NOT have AI
    technical_fields = [
        'participationConditions.technicalSection.companyReferencesDetails',
        'participationConditions.technicalSection.staffReferencesDetails',
        'participationConditions.technicalSection.staffRequirementsDetails',
        'participationConditions.technicalSection.qualityCertificatesDetails',
        # With lot prefixes
        'lots.0.participationConditions.technicalSection.companyReferencesDetails',
        'lots.0.participationConditions.technicalSection.staffReferencesDetails',
        'lots.0.participationConditions.technicalSection.staffRequirementsDetails',
        'lots.0.participationConditions.technicalSection.qualityCertificatesDetails'
    ]
    
    print("=" * 60)
    print("TESTING TECHNICAL FIELDS - NO AI BUTTONS")
    print("=" * 60)
    print("\nThese are simple text fields for describing requirements")
    print("They should NOT have AI assistance\n")
    
    all_passed = True
    for field_key in technical_fields:
        # Test with a simple string schema
        schema = {
            'type': 'string',
            'title': '→ Opišite zahtevo'
        }
        
        should_have_ai = helper.should_use_ai_renderer(field_key, schema)
        
        if should_have_ai:
            print(f"❌ FAIL: {field_key}")
            print(f"         Has AI button (should NOT have!)")
            all_passed = False
        else:
            print(f"✅ PASS: {field_key}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! 🎉")
        print("Technical capability detail fields will NOT have AI buttons")
    else:
        print("SOME TESTS FAILED! ❌")
        print("Please check the configuration")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_technical_fields_no_ai()
    sys.exit(0 if success else 1)