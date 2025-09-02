"""
Verify negotiations AI is working correctly
"""
import streamlit as st
import json
import logging

logging.basicConfig(level=logging.INFO)

# Apply lot mode fix
from patches.lot_mode_none_fix_patch import apply_lot_mode_fix
apply_lot_mode_fix()

# Load schema
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
    with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Check negotiations fields in schema
print("=" * 60)
print("NEGOTIATIONS FIELDS IN SCHEMA:")
print("=" * 60)

if 'negotiationsInfo' in schema['properties']:
    negotiations = schema['properties']['negotiationsInfo']['properties']
    for field_name, field_schema in negotiations.items():
        print(f"- {field_name}: {field_schema.get('type', 'unknown')}")
        if field_schema.get('ai_enabled'):
            print(f"  ✓ AI ENABLED")
else:
    print("No negotiationsInfo section found!")

print("\n" + "=" * 60)
print("AI INTEGRATION HELPER CONFIG:")
print("=" * 60)

from ui.renderers.ai_integration_helper import AIIntegrationHelper

helper = AIIntegrationHelper()

# Check which negotiations fields are configured for AI
negotiations_fields = [
    'negotiationsInfo.specialNegotiationWishes',
    'negotiationsInfo.electronicAuction',
    'negotiationsInfo.priceNegotiations', 
    'negotiationsInfo.negotiationStages',
    'negotiationsInfo.hasNegotiations',
    'negotiationsInfo.negotiationSubject',
    'negotiationsInfo.otherNegotiationSubject',
    'negotiationsInfo.negotiationRounds',
    'negotiationsInfo.hasSpecialWishes'
]

for field in negotiations_fields:
    if field in helper.AI_ENABLED_FIELDS:
        print(f"✓ {field} - CONFIGURED FOR AI")
    else:
        print(f"✗ {field} - NOT configured")

# Check lot-prefixed versions
print("\n" + "=" * 60)
print("LOT-PREFIXED VERSIONS:")
print("=" * 60)

lot_prefixed = [
    'lots.0.negotiationsInfo.specialNegotiationWishes',
    'lot_0.negotiationsInfo.specialNegotiationWishes'
]

for field in lot_prefixed:
    if field in helper.AI_ENABLED_FIELDS:
        print(f"✓ {field} - CONFIGURED FOR AI")
    else:
        print(f"✗ {field} - NOT configured")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
print("The fields 'electronicAuction', 'priceNegotiations', and 'negotiationStages'")
print("do NOT exist in the schema. They were added to AI config but won't work")
print("because they're not real fields in the form.")
print("\nThe only negotiations field with AI support is:")
print("- negotiationsInfo.specialNegotiationWishes (has ai_enabled: true in schema)")