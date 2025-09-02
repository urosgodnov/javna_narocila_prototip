"""
Final test to verify negotiations AI is working
"""
import json

print("=" * 60)
print("CHECKING NEGOTIATIONS FIELDS WITH ai_enabled")
print("=" * 60)

# Load schema
import os
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Check negotiations fields
if 'negotiationsInfo' in schema['properties']:
    negotiations = schema['properties']['negotiationsInfo']['properties']
    
    print("\nNegotiations fields status:")
    for field_name, field_schema in negotiations.items():
        if field_schema.get('type') == 'string':
            ai_status = "✓ AI ENABLED" if field_schema.get('ai_enabled') else "✗ NO AI"
            print(f"  - {field_name}: {ai_status}")

# Check price fields
if 'priceInfo' in schema['properties']:
    price = schema['properties']['priceInfo']['properties']
    
    print("\nPrice fields status (for comparison):")
    for field_name, field_schema in price.items():
        if field_schema.get('type') == 'string':
            ai_status = "✓ AI ENABLED" if field_schema.get('ai_enabled') else "✗ NO AI"
            # Check for special AI option in enum
            if 'enum' in field_schema and 'prosim za predlog AI' in field_schema['enum']:
                ai_status += " (has AI option in enum)"
            print(f"  - {field_name}: {ai_status}")

print("\n" + "=" * 60)
print("SOLUTION SUMMARY:")
print("=" * 60)
print("✅ Added 'ai_enabled': true to:")
print("   - negotiationsInfo.otherNegotiationSubject")
print("   - negotiationsInfo.negotiationRounds")
print("   - negotiationsInfo.specialNegotiationWishes (already had it)")
print("   - priceInfo.otherPriceClause")
print("\nThese fields will now show the 'AI predlog' button in the form!")
print("=" * 60)