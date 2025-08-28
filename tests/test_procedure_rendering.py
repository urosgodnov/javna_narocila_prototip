#!/usr/bin/env python3
"""Test if the procedure rendering works correctly with the display map."""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Get procedure properties
procedure_props = schema['properties']['submissionProcedure']['properties']['procedure']
enum_options = procedure_props['enum']

print("🔍 Testing procedure rendering...")
print("=" * 60)

print("\n📋 Enum options from schema:")
for i, opt in enumerate(enum_options, 1):
    print(f"  {i}. {opt}")

# Simulate the display mapping (copied from form_renderer.py)
procedure_display_map = {
    "odprti postopek": "odprti postopek (40. člen ZJN-3)",
    "omejeni postopek": "omejeni postopek (41. člen ZJN-3)",
    "konkurenčni dialog": "konkurenčni dialog (42. člen ZJN-3)",
    "partnerstvo za inovacije": "partnerstvo za inovacije (43. člen ZJN-3)",
    "konkurenčni postopek s pogajanji": "konkurenčni postopek s pogajanji (44. člen ZJN-3)",
    "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)": "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju) (45. člen ZJN-3)",
    "postopek s pogajanji brez predhodne objave": "postopek s pogajanji brez predhodne objave (46. člen ZJN-3)",
    "postopek naročila male vrednosti": "postopek naročila male vrednosti (47. člen ZJN-3)",
    "vseeno": "vseeno"
}

print("\n📋 Display options (what user sees in dropdown):")
display_options = [procedure_display_map.get(opt, opt) for opt in enum_options]
for i, display in enumerate(display_options, 1):
    print(f"  {i}. {display}")

# Check if new procedure is mapped
new_proc = "postopek s pogajanji z objavo (zgolj za javno naročanje na infrastrukturnem področju)"
print(f"\n🔍 Checking new procedure '{new_proc}':")
if new_proc in enum_options:
    print("  ✅ Found in enum options")
    display_text = procedure_display_map.get(new_proc)
    if display_text:
        print(f"  ✅ Mapped to: '{display_text}'")
        if display_text in display_options:
            print(f"  ✅ Will appear in dropdown at position {display_options.index(display_text) + 1}")
    else:
        print("  ❌ NOT found in display map!")
else:
    print("  ❌ NOT found in enum options!")

print("\n" + "=" * 60)
print("✨ Test complete!")