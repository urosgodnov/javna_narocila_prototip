"""
Test priceInfo AI functionality
"""
import streamlit as st
import json

# Apply lot mode fix
from patches.lot_mode_none_fix_patch import apply_lot_mode_fix
apply_lot_mode_fix()

# Load schema
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
    with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 60)
print("PRICE INFO FIELDS IN SCHEMA:")
print("=" * 60)

if 'priceInfo' in schema['properties']:
    price_fields = schema['properties']['priceInfo']['properties']
    for field_name, field_schema in price_fields.items():
        field_type = field_schema.get('type', 'unknown')
        print(f"\n- priceInfo.{field_name}: {field_type}")
        
        # Check for AI-related features
        if field_schema.get('ai_enabled'):
            print(f"  ✓ AI ENABLED explicitly")
        
        # Check if it has "prosim za predlog AI" in enum
        if 'enum' in field_schema:
            if 'prosim za predlog AI' in field_schema['enum']:
                print(f"  ✓ Has 'prosim za predlog AI' option")
        
        # Print title to understand the field
        if 'title' in field_schema:
            print(f"  Title: {field_schema['title']}")

print("\n" + "=" * 60)
print("AI CONFIGURATION CHECK:")
print("=" * 60)

from ui.renderers.ai_integration_helper import AIIntegrationHelper
helper = AIIntegrationHelper()

# Check all priceInfo fields
price_fields_to_check = [
    'priceInfo.priceClause',
    'priceInfo.otherPriceClause',
    'priceInfo.priceFixation',
    'priceInfo.otherPriceFixation',
    'priceInfo.aiPriceFixationCustom',
    'priceInfo.valorization',
    'priceInfo.quantitiesType'
]

print("\nDirect fields:")
for field in price_fields_to_check:
    if field in helper.AI_ENABLED_FIELDS:
        config = helper.AI_ENABLED_FIELDS[field]
        print(f"✓ {field} - CONFIGURED (trigger: {config.get('trigger', 'unknown')})")
    else:
        print(f"✗ {field} - NOT configured")

print("\nLot-prefixed fields (lots.0.*):")
for field in price_fields_to_check:
    lot_field = f"lots.0.{field.split('.', 1)[1]}"
    if lot_field in helper.AI_ENABLED_FIELDS:
        config = helper.AI_ENABLED_FIELDS[lot_field]
        print(f"✓ {lot_field} - CONFIGURED (trigger: {config.get('trigger', 'unknown')})")
    else:
        print(f"✗ {lot_field} - NOT configured")

print("\n" + "=" * 60)
print("SPECIAL LOGIC FOR priceFixation:")
print("=" * 60)
print("The priceFixation field has a special enum value 'prosim za predlog AI'")
print("When user selects this option, it should trigger AI suggestions")
print("This is different from other fields that have separate AI fields")
print("\nCurrent enum values for priceFixation:")
if 'priceInfo' in schema['properties'] and 'priceFixation' in schema['properties']['priceInfo']['properties']:
    enum_values = schema['properties']['priceInfo']['properties']['priceFixation'].get('enum', [])
    for i, val in enumerate(enum_values, 1):
        print(f"  {i}. {val}")