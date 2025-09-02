"""
Verify which negotiations fields exist and should have AI
"""
import json

# Load schema
import os
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 60)
print("ALL NEGOTIATIONS FIELDS IN SCHEMA:")
print("=" * 60)

if 'negotiationsInfo' in schema['properties']:
    negotiations = schema['properties']['negotiationsInfo']['properties']
    
    for field_name, field_schema in negotiations.items():
        field_type = field_schema.get('type', 'unknown')
        print(f"\n{field_name}:")
        print(f"  Type: {field_type}")
        print(f"  Title: {field_schema.get('title', 'No title')}")
        
        # Check what makes it AI-eligible
        if field_type == 'string':
            if 'enum' in field_schema:
                print(f"  → DROPDOWN/ENUM (NO AI button)")
                print(f"     Options: {field_schema['enum']}")
            elif field_schema.get('format') == 'textarea':
                print(f"  → TEXTAREA (CAN have AI button)")
                if field_schema.get('ai_enabled'):
                    print(f"     ✅ HAS ai_enabled: true")
                else:
                    print(f"     ❌ MISSING ai_enabled: true")
            else:
                print(f"  → TEXT INPUT (CAN have AI button)")
                if field_schema.get('ai_enabled'):
                    print(f"     ✅ HAS ai_enabled: true")
                else:
                    print(f"     ❌ MISSING ai_enabled: true")
        elif field_type == 'boolean':
            print(f"  → CHECKBOX (NO AI button)")
        elif field_type == 'object':
            print(f"  → OBJECT/SECTION (NO AI button)")

print("\n" + "=" * 60)
print("FIELDS THAT SHOULD HAVE AI:")
print("=" * 60)
print("✅ otherNegotiationSubject - text input (appears when 'drugo' selected)")
print("✅ specialNegotiationWishes - textarea (appears when checkbox checked)")
print("\nFields that DON'T need AI:")
print("❌ negotiationRounds - dropdown/enum field")
print("❌ negotiationSubject - dropdown/enum field") 
print("❌ hasNegotiations - checkbox")
print("❌ hasSpecialWishes - checkbox")
print("❌ negotiationsNotAllowed - warning object")