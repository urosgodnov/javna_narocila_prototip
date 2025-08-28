#!/usr/bin/env python3
"""Test what fields are in the merila step according to JSON schema."""

import json

# Load the JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get selectionCriteria properties
sel_crit_props = data.get('$defs', {}).get('selectionCriteriaProperties', {}).get('properties', {})

print("=" * 60)
print("MAIN CRITERIA (should have 9 total):")
print("=" * 60)

main_criteria = []
for key, val in sel_crit_props.items():
    if val.get('type') == 'boolean' and 'Options' not in key:
        title = val.get('title', key)
        main_criteria.append((key, title))

for key, title in sorted(main_criteria):
    print(f"☐ {title} ({key})")

print(f"\nTotal main criteria: {len(main_criteria)}")

# Check for social criteria options
print("\n" + "=" * 60)
print("SOCIAL SUB-OPTIONS (should have 5 total):")
print("=" * 60)

if 'socialCriteriaOptions' in sel_crit_props:
    social_props = sel_crit_props['socialCriteriaOptions'].get('properties', {})
    
    social_options = []
    for key, val in social_props.items():
        if val.get('type') == 'boolean':
            title = val.get('title', key)
            social_options.append((key, title))
    
    for key, title in sorted(social_options):
        print(f"  ☐ {title} ({key})")
    
    print(f"\nTotal social sub-options: {len(social_options)}")
else:
    print("No socialCriteriaOptions found")

# Check for ratio fields
print("\n" + "=" * 60)
print("RATIO FIELDS:")
print("=" * 60)

ratio_fields = []
for key, val in sel_crit_props.items():
    if 'Ratio' in key and val.get('type') == 'number':
        title = val.get('title', key)
        ratio_fields.append((key, title))

for key, title in sorted(ratio_fields):
    print(f"  {title} ({key})")

print(f"\nTotal ratio fields: {len(ratio_fields)}")

# Expected structure
print("\n" + "=" * 60)
print("EXPECTED STRUCTURE:")
print("=" * 60)
print("""
MAIN CRITERIA (9 total):
  ☐ Cena (price)
  ☐ Dodatne reference imenovanega kadra (additionalReferences)
  ☐ Dodatne tehnične zahteve (additionalTechnicalRequirements)
  ☐ Krajši rok izvedbe (shorterDeadline)
  ☐ Garancija daljša od zahtevane (longerWarranty)
  ☐ Stroškovna učinkovitost (costEfficiency)
  ☐ Socialna merila (socialCriteria)
  ☐ Drugo, imam predlog (otherCriteriaCustom)
  ☐ Drugo, prosim predlog AI (otherCriteriaAI)

SOCIAL SUB-OPTIONS (5 total):
  ☐ Delež zaposlenih mladih (youngEmployeesShare)
  ☐ Delež zaposlenih starejših (elderlyEmployeesShare)
  ☐ Priglašeni kader je zaposlen pri ponudniku (registeredStaffEmployed)
  ☐ Povprečna plača priglašenega kadra (averageSalary)
  ☐ Drugo (otherSocial)
""")