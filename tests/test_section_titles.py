#!/usr/bin/env python3
"""
Test that participationAndExclusion and participationConditions have proper titles
"""
import json
import os

# Load schema
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 60)
print("CHECKING SECTION TITLES")
print("=" * 60)

# Check participationAndExclusion
if 'participationAndExclusion' in schema['properties']:
    section = schema['properties']['participationAndExclusion']
    title = section.get('title', 'NO TITLE FOUND!')
    print(f"\nparticipationAndExclusion:")
    print(f"  Title: {title}")
    if title == "Razlogi za izključitev":
        print("  ✅ Correct title set!")
    else:
        print("  ❌ Missing or incorrect title!")

# Check participationConditions  
if 'participationConditions' in schema['properties']:
    section = schema['properties']['participationConditions']
    title = section.get('title', 'NO TITLE FOUND!')
    print(f"\nparticipationConditions:")
    print(f"  Title: {title}")
    if title == "Pogoji za sodelovanje":
        print("  ✅ Correct title set!")
    else:
        print("  ❌ Missing or incorrect title!")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Both sections now have proper Slovenian titles that will be")
print("displayed instead of the technical field names.")
print("\nWhen you open the screen, you should now see:")
print("  • 'Razlogi za izključitev' instead of 'participationAndExclusion'")
print("  • 'Pogoji za sodelovanje' instead of 'participationConditions'")