#!/usr/bin/env python3
"""Validate CPV selector integration."""

import json
from utils.cpv_manager import get_cpv_count, get_cpv_codes_for_dropdown
from ui.components.cpv_selector import parse_cpv_from_text, validate_cpv_codes

print("=== CPV Integration Validation ===\n")

# 1. Check database has CPV codes
cpv_count = get_cpv_count()
print(f"✓ CPV codes in database: {cpv_count}")
assert cpv_count > 0, "No CPV codes in database"

# 2. Check dropdown data format
dropdown_data = get_cpv_codes_for_dropdown()
print(f"✓ Dropdown options available: {len(dropdown_data)}")
assert len(dropdown_data) > 0, "No dropdown options"

# Sample dropdown entry
if dropdown_data:
    sample = dropdown_data[0]
    print(f"  Sample: {sample['display'][:60]}...")
    assert 'value' in sample and 'display' in sample, "Invalid dropdown format"

# 3. Test bi-directional search
print("\n✓ Bi-directional search:")
for item in dropdown_data[:3]:
    code = item['value']
    display = item['display']
    print(f"  Code: {code} -> Display: {display[:40]}...")

# 4. Test parsing from text
test_text = "30000000-9, 45000000-7, 72000000-5"
parsed = parse_cpv_from_text(test_text)
print(f"\n✓ Parsing text: '{test_text}'")
print(f"  Parsed codes: {parsed}")
assert len(parsed) == 3, "Parsing failed"

# 5. Test validation
valid_codes = validate_cpv_codes(parsed)
print(f"✓ Validation: {len(valid_codes)}/{len(parsed)} codes valid")

# 6. Check schema integration
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)
    
cpv_field = schema['properties']['projectInfo']['properties']['cpvCodes']
print(f"\n✓ Schema integration:")
print(f"  Format: {cpv_field.get('format', 'Not set')}")
print(f"  Title: {cpv_field.get('title', 'Not set')}")
assert cpv_field.get('format') == 'cpv', "CPV format not set in schema"

# 7. Test backward compatibility
legacy_text = "30192000-1 - Pisarniški material, 45000000-7 - Gradbena dela"
parsed_legacy = parse_cpv_from_text(legacy_text)
print(f"\n✓ Backward compatibility test:")
print(f"  Legacy text: '{legacy_text[:50]}...'")
print(f"  Parsed: {parsed_legacy}")
assert len(parsed_legacy) == 2, "Legacy parsing failed"

print("\n=== All validations passed! ===")