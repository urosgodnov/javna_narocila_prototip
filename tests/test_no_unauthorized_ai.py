#!/usr/bin/env python3
"""
Test that detail fields in participationConditions don't get AI buttons
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.renderers.ai_integration_helper import AIIntegrationHelper

def test_participation_conditions_no_ai():
    """Test that participation conditions detail fields are excluded from AI"""
    helper = AIIntegrationHelper()
    
    # Fields that should NOT have AI - these are simple clarification inputs
    excluded_fields = [
        # Professional activity details
        'participationConditions.professionalActivitySection.professionalRegisterDetails',
        'participationConditions.professionalActivitySection.businessRegisterDetails',
        'participationConditions.professionalActivitySection.licenseDetails',
        'participationConditions.professionalActivitySection.membershipDetails',
        'participationConditions.professionalActivitySection.professionalOtherDetails',
        # Economic/financial details
        'participationConditions.economicFinancialSection.generalTurnoverDetails',
        'participationConditions.economicFinancialSection.specificTurnoverDetails',
        'participationConditions.economicFinancialSection.averageTurnoverDetails',
        'participationConditions.economicFinancialSection.averageSpecificTurnoverDetails',
        'participationConditions.economicFinancialSection.financialRatioDetails',
        'participationConditions.economicFinancialSection.professionalInsuranceDetails',
        'participationConditions.economicFinancialSection.accountNotBlockedDetails',
        'participationConditions.economicFinancialSection.economicOtherDetails',
        # Technical details
        'participationConditions.technicalSection.technicalStaffDetails',
        'participationConditions.technicalSection.equipmentDetails',
        'participationConditions.technicalSection.experienceDetails',
        'participationConditions.technicalSection.qualificationDetails',
        'participationConditions.technicalSection.qualityControlDetails',
        'participationConditions.technicalSection.environmentalManagementDetails',
        'participationConditions.technicalSection.subcontractingDetails',
        'participationConditions.technicalSection.technicalOtherDetails',
        # With lot prefixes
        'lots.0.participationConditions.professionalActivitySection.professionalRegisterDetails',
        'lots.0.participationConditions.economicFinancialSection.generalTurnoverDetails',
        'lots.0.participationConditions.technicalSection.technicalStaffDetails'
    ]
    
    print("=" * 60)
    print("TESTING PARTICIPATION CONDITIONS - NO AI BUTTONS")
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
            print(f"❌ FAIL: {field_key}")
            print(f"         Has AI (should NOT have AI!)")
            all_passed = False
        else:
            print(f"✅ PASS: {field_key}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! 🎉")
        print("ParticipationConditions detail fields will NOT have AI buttons")
        print("These are simple text inputs for clarification only")
    else:
        print("SOME TESTS FAILED! ❌")
        print("Please check the configuration")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_participation_conditions_no_ai()
    sys.exit(0 if success else 1)