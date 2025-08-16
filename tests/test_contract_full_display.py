#!/usr/bin/env python3
"""Test that all contract fields are properly displayed on the last page."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_contract_full_display():
    """Test that contract fields display properly on last page."""
    print("=" * 60)
    print("Contract Fields Display Test")
    print("=" * 60)
    
    # Load schema
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    contract_info = schema['properties']['contractInfo']
    
    print("\n1. Contract Section Structure:")
    print(f"   Title: {contract_info.get('title', 'N/A')}")
    print(f"   Type: {contract_info.get('type', 'N/A')}")
    print(f"   Properties: {len(contract_info.get('properties', {}))}")
    
    print("\n2. Fields that should be visible immediately:")
    always_visible = []
    for prop_name, prop_details in contract_info['properties'].items():
        if 'render_if' not in prop_details and not prop_details.get('readonly'):
            always_visible.append(prop_name)
    
    for field in always_visible:
        prop = contract_info['properties'][field]
        print(f"   - {field}: {prop.get('title', 'N/A')}")
        if 'enum' in prop:
            print(f"     Options: {prop['enum']}")
    
    if not always_visible:
        print("   ⚠️ WARNING: No always-visible fields found!")
        print("   The 'type' field should be always visible!")
    
    print("\n3. Checking 'type' field specifically:")
    type_field = contract_info['properties'].get('type', {})
    print(f"   Title: {type_field.get('title', 'N/A')}")
    print(f"   Has enum: {'enum' in type_field}")
    print(f"   Has render_if: {'render_if' in type_field}")
    print(f"   Options: {type_field.get('enum', [])}")
    
    if 'render_if' in type_field:
        print("   ❌ ERROR: 'type' field should NOT have render_if!")
    else:
        print("   ✓ 'type' field has no render_if - should be visible")
    
    print("\n4. Section headers (readonly):")
    for prop_name, prop_details in contract_info['properties'].items():
        if prop_details.get('readonly'):
            print(f"   - {prop_name}: {prop_details.get('title', 'N/A')}")
    
    print("\n5. Conditional fields check:")
    for prop_name, prop_details in contract_info['properties'].items():
        if 'render_if' in prop_details:
            render_if = prop_details['render_if']
            field_ref = render_if.get('field', '')
            if not field_ref.startswith('contractInfo.'):
                print(f"   ⚠️ {prop_name}: render_if field '{field_ref}' might need 'contractInfo.' prefix")
    
    print("\n" + "=" * 60)
    
    # Final verdict
    if always_visible and 'type' in always_visible:
        print("✅ TEST PASSED!")
        print("The 'type' field should be visible, allowing users to select")
        print("between 'pogodba' and 'okvirni sporazum'.")
    else:
        print("❌ TEST FAILED!")
        print("The 'type' field is not configured to be always visible.")
    
    print("=" * 60)
    
    return 'type' in always_visible

if __name__ == "__main__":
    try:
        success = test_contract_full_display()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)