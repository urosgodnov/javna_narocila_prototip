#!/usr/bin/env python3
"""Test to verify procedure dropdown synchronization between JSON schema and display map."""

import json
import re

print("🔍 Verifying dropdown synchronization...")
print("=" * 60)

# Load JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Get procedures from JSON
json_procedures = schema['properties']['submissionProcedure']['properties']['procedure']['enum']
print("📋 JSON Schema procedures:")
for i, proc in enumerate(json_procedures, 1):
    print(f"  {i}. {proc}")

# Read form_renderer.py to extract the procedure_display_map
with open('ui/form_renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the procedure_display_map
map_pattern = r'procedure_display_map = \{([^}]+)\}'
match = re.search(map_pattern, content, re.DOTALL)

if match:
    map_content = match.group(1)
    # Extract keys from the map
    key_pattern = r'"([^"]+)":'
    display_map_keys = re.findall(key_pattern, map_content)
    
    print("\n📋 Display map keys:")
    for i, key in enumerate(display_map_keys, 1):
        print(f"  {i}. {key}")
    
    print("\n🔍 Checking synchronization:")
    missing = []
    found = []
    
    for proc in json_procedures:
        if proc in display_map_keys:
            found.append(proc)
        else:
            missing.append(proc)
    
    if found:
        print("\n✅ Procedures found in display map:")
        for proc in found:
            print(f"  - {proc}")
    
    if missing:
        print("\n❌ Procedures MISSING from display map:")
        for proc in missing:
            print(f"  - {proc}")
    
    # Special check for the new procedure
    new_proc = "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)"
    if new_proc in json_procedures:
        print(f"\n📌 New procedure in JSON: ✅")
        if new_proc in display_map_keys:
            print(f"📌 New procedure in display map: ✅")
            print(f"🎉 New procedure '{new_proc}' is fully synchronized!")
        else:
            print(f"📌 New procedure in display map: ❌")
            print(f"⚠️ New procedure needs to be added to display map!")
    
    # Summary
    if not missing:
        print("\n✅ All procedures are synchronized! The dropdown will work correctly.")
    else:
        print(f"\n⚠️ {len(missing)} procedure(s) need to be added to display map!")

else:
    print("❌ Could not find procedure_display_map in form_renderer.py")

print("\n" + "=" * 60)
print("✨ Synchronization test complete!")