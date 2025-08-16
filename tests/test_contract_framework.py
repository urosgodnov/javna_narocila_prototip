#!/usr/bin/env python3
"""Test script to verify Contract Framework Enhancement implementation (Stories 24.1, 24.2, 24.3)."""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_json_schema():
    """Test that the JSON schema has been updated correctly."""
    print("Testing JSON Schema updates...")
    
    # Use relative path from tests folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Test Story 24.1: Framework Agreement Types
    contract_info = schema['properties']['contractInfo']['properties']
    
    # Check frameworkAgreementType field
    assert 'frameworkAgreementType' in contract_info, "Missing frameworkAgreementType field"
    framework_type = contract_info['frameworkAgreementType']
    
    # Check enum values
    expected_enums = ["en_brez_konkurence", "en_z_konkurenco", "vec_brez_konkurence", "vec_z_konkurenco", "vec_deloma"]
    assert framework_type['enum'] == expected_enums, f"Wrong enum values: {framework_type['enum']}"
    
    # Check enumLabels
    assert 'enumLabels' in framework_type, "Missing enumLabels"
    assert len(framework_type['enumLabels']) == 5, "Should have 5 enum labels"
    
    # Check format
    assert framework_type.get('format') == 'radio', "Should have format: radio"
    
    # Check render_if
    assert framework_type['render_if']['field'] == 'contractInfo.type', "Wrong render_if field"
    assert framework_type['render_if']['value'] == 'okvirni sporazum', "Wrong render_if value"
    
    print("✓ Story 24.1: Framework Agreement Types - PASSED")
    
    # Test competitionFrequency field
    competition_freq = contract_info['competitionFrequency']
    assert competition_freq.get('format') == 'textarea', "competitionFrequency should be textarea"
    assert 'render_if_any' in competition_freq, "competitionFrequency should have render_if_any"
    assert len(competition_freq['render_if_any']) == 3, "Should have 3 render conditions"
    
    # Check that render_if_any uses new enum values
    for condition in competition_freq['render_if_any']:
        assert condition['field'] == 'contractInfo.frameworkAgreementType', "Wrong field in render_if_any"
        assert condition['value'] in ["en_z_konkurenco", "vec_z_konkurenco", "vec_deloma"], "Wrong value in render_if_any"
    
    print("✓ Story 24.2: Competition Frequency Field - PASSED")
    
    # Test Story 24.3: Extension Fields
    assert 'canBeExtended' in contract_info, "Missing canBeExtended field"
    can_extend = contract_info['canBeExtended']
    assert can_extend['enum'] == ['ne', 'da'], "Wrong enum for canBeExtended"
    assert can_extend.get('format') == 'radio', "canBeExtended should be radio"
    assert can_extend.get('default') == 'ne', "Default should be 'ne'"
    
    # Check extension reasons
    assert 'extensionReasons' in contract_info, "Missing extensionReasons field"
    ext_reasons = contract_info['extensionReasons']
    assert ext_reasons.get('format') == 'textarea', "extensionReasons should be textarea"
    assert ext_reasons['render_if']['field'] == 'contractInfo.canBeExtended', "Wrong render_if field"
    assert ext_reasons['render_if']['value'] == 'da', "Wrong render_if value"
    assert 'required_if' in ext_reasons, "Missing required_if for extensionReasons"
    
    # Check extension duration
    assert 'extensionDuration' in contract_info, "Missing extensionDuration field"
    ext_duration = contract_info['extensionDuration']
    assert ext_duration['render_if']['field'] == 'contractInfo.canBeExtended', "Wrong render_if field"
    assert ext_duration['render_if']['value'] == 'da', "Wrong render_if value"
    assert 'required_if' in ext_duration, "Missing required_if for extensionDuration"
    
    print("✓ Story 24.3: Extension Fields - PASSED")
    
    return True

def test_form_renderer():
    """Test that form_renderer.py has been updated correctly."""
    print("\nTesting form_renderer.py updates...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    renderer_path = os.path.join(base_dir, 'ui', 'form_renderer.py')
    with open(renderer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for enumLabels handling
    assert "elif \"enumLabels\" in prop_details:" in content, "Missing enumLabels handling"
    assert "display_options = prop_details[\"enumLabels\"]" in content, "Missing enumLabels assignment"
    
    # Check for render_competition_criteria_info function
    assert "def render_competition_criteria_info" in content, "Missing render_competition_criteria_info function"
    assert "competition_types = [\"en_z_konkurenco\", \"vec_z_konkurenco\", \"vec_deloma\"]" in content, "Wrong competition types"
    
    print("✓ Form renderer updates - PASSED")
    
    return True

def test_validation():
    """Test that validation has been added to app.py."""
    print("\nTesting validation in app.py...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_dir, 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for framework duration validation
    assert "Obdobje okvirnega sporazuma ne sme presegati 4 let" in content, "Missing 4-year validation message"
    assert "48 mesecev" in content, "Missing 48 months validation"
    
    # Check for extension fields validation
    assert "Prosimo, navedite razloge za možnost podaljšanja pogodbe" in content, "Missing extension reasons validation"
    assert "Prosimo, navedite trajanje podaljšanja pogodbe" in content, "Missing extension duration validation"
    
    print("✓ Validation logic - PASSED")
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Contract Framework Enhancement Test Suite")
    print("Testing implementation of Stories 24.1, 24.2, and 24.3")
    print("=" * 60)
    
    try:
        test_json_schema()
        test_form_renderer()
        test_validation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nImplementation Summary:")
        print("- Story 24.1: Framework Agreement Types with 5 options ✓")
        print("- Story 24.2: Dynamic criteria display for competition ✓")
        print("- Story 24.3: Contract extension fields with validation ✓")
        print("\nThe contract framework enhancement is ready for use!")
        
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())