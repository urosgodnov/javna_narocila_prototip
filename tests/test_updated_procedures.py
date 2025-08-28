#!/usr/bin/env python3
"""Test that both negotiation procedures are properly updated and clarified."""

import json
import re

print("🔍 Verifying updated procedure names...")
print("=" * 60)

# Load JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Get procedures from JSON
json_procedures = schema['properties']['submissionProcedure']['properties']['procedure']['enum']

print("📋 Updated procedures in JSON Schema:")
for i, proc in enumerate(json_procedures, 1):
    if "zgolj za javno naročanje" in proc:
        print(f"  {i}. ✅ {proc}")
    else:
        print(f"  {i}. {proc}")

# Check form_renderer.py for display map
with open('ui/form_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the procedure_display_map
map_pattern = r'procedure_display_map = \{([^}]+)\}'
match = re.search(map_pattern, content, re.DOTALL)

if match:
    map_content = match.group(1)
    key_pattern = r'"([^"]+)":'
    display_map_keys = re.findall(key_pattern, map_content)
    
    print("\n📋 Display map keys (should match JSON):")
    for i, key in enumerate(display_map_keys, 1):
        if "zgolj za javno naročanje" in key:
            print(f"  {i}. ✅ {key}")
        else:
            print(f"  {i}. {key}")

print("\n🔍 Checking the two negotiation procedures:")

# Check general public procurement procedure
general_proc = "konkurenčni postopek s pogajanji (zgolj za javno naročanje na splošnem področju)"
if general_proc in json_procedures:
    print(f"✅ General procedure in JSON: '{general_proc}'")
    if general_proc in display_map_keys:
        print(f"✅ General procedure in display map")
        # Extract its display text
        pattern = f'"{re.escape(general_proc)}": "([^"]+)"'
        display_match = re.search(pattern, content)
        if display_match:
            print(f"   Display text: '{display_match.group(1)}'")
else:
    print(f"❌ General procedure NOT in JSON")

# Check infrastructure procedure  
infra_proc = "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)"
if infra_proc in json_procedures:
    print(f"\n✅ Infrastructure procedure in JSON: '{infra_proc}'")
    if infra_proc in display_map_keys:
        print(f"✅ Infrastructure procedure in display map")
        # Extract its display text
        pattern = f'"{re.escape(infra_proc)}": "([^"]+)"'
        display_match = re.search(pattern, content)
        if display_match:
            print(f"   Display text: '{display_match.group(1)}'")
else:
    print(f"\n❌ Infrastructure procedure NOT in JSON")

print("\n" + "=" * 60)
print("✨ Updated procedure names:")
print("1. Konkurenčni postopek s pogajanji - clarified for GENERAL public procurement (44. člen)")
print("2. Postopek s pogajanji z objavo - clarified for INFRASTRUCTURE procurement (45. člen)")
print("\n⚠️ Remember to restart the Streamlit app to see the changes!")