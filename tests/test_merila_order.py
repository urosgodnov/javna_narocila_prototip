#!/usr/bin/env python3
"""Test the new ordering of merila fields."""

import json

# Load the JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get selectionCriteria properties
sel_crit_props = data.get('$defs', {}).get('selectionCriteriaProperties', {}).get('properties', {})

print("=" * 60)
print("FIELD ORDER IN JSON (as they will appear in the form):")
print("=" * 60)

# List all fields in order
for i, (key, val) in enumerate(sel_crit_props.items(), 1):
    prop_type = val.get('type', 'unknown')
    title = val.get('title', key)
    
    # Skip headers and other non-input fields
    if prop_type == 'object' and key.endswith('Header'):
        print(f"\n--- {title} ---")
        continue
    
    # Main criteria (boolean checkboxes)
    if prop_type == 'boolean':
        print(f"{i:2}. ☐ {title:<50} ({key})")
    
    # Nested objects like socialCriteriaOptions
    elif prop_type == 'object' and 'properties' in val:
        print(f"\n{i:2}. {title} (nested object: {key})")
        # Show sub-properties
        for sub_key, sub_val in val.get('properties', {}).items():
            if sub_val.get('type') == 'boolean':
                sub_title = sub_val.get('title', sub_key)
                print(f"      → ☐ {sub_title:<45} ({sub_key})")
    
    # Description fields
    elif 'Description' in key or 'description' in title.lower():
        print(f"      → {title:<50} (text field)")
    
    # Ratio fields
    elif 'Ratio' in key:
        # Skip for now, they appear in section B
        pass

print("\n" + "=" * 60)
print("EXPECTED VISUAL LAYOUT:")
print("=" * 60)
print("""
A. IZBIRA MERIL
---------------
☐ Cena
☐ Dodatne reference imenovanega kadra
☐ Dodatne tehnične zahteve
    → [text field for description if checked]
☐ Krajši rok izvedbe
    → [text field for minimum time if checked]
☐ Garancija daljša od zahtevane
☐ Stroškovna učinkovitost
    → [text field for specification if checked]
☐ Drugo, imam predlog
    → [text field for description if checked]
☐ Drugo, prosim predlog AI
☐ Socialna merila  <-- NOW AT THE END!
    → Izberite socialna merila: (when checked, INDENTED)
        ☐ Delež zaposlenih mladih
        ☐ Delež zaposlenih starejših
        ☐ Priglašeni kader je zaposlen pri ponudniku
        ☐ Povprečna plača priglašenega kadra
        ☐ Drugo
            → [text field for description if checked]

B. RAZMERJA MED IZBRANIMI MERILI
---------------------------------
[Points fields for each selected criterion]
""")