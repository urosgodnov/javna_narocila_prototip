#!/usr/bin/env python3
"""Test that cofinancers persist after re-editing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from database import get_procurement_by_id, update_procurement

print("=" * 80)
print("TEST: ALI SOFINANCERJI OSTANEJO PO PONOVNEM UREJANJU")
print("=" * 80)

# Load procurement ID 8 which now has cofinancers
existing = get_procurement_by_id(8)
existing_data = json.loads(existing['form_data_json'])

print("\n1. TRENUTNO STANJE:")
cofinancers = existing_data.get('orderType', {}).get('cofinancers', [])
print(f"   Sofinancerji: {len(cofinancers)}")
for i, cof in enumerate(cofinancers):
    if isinstance(cof, dict):
        print(f"   {i+1}. {cof.get('cofinancerName', 'NO NAME')}")

print("\n2. SIMULIRAM UREJANJE (spremenim samo naziv projekta)...")
# Change only project name, keep everything else
existing_data['projectInfo'] = existing_data.get('projectInfo', {})
existing_data['projectInfo']['projectName'] = 'Nove operacijske hale - POSODOBLJENO'

print("   Spreminjam samo naziv, sofinancerji naj ostanejo!")

# Update
print("\n3. SHRANJUJEM...")
success = update_procurement(8, existing_data)

if not success:
    print("   ❌ Posodobitev ni uspela!")
    exit(1)

print("   ✓ Shranjeno!")

# Reload and check
print("\n4. PREVERJAM PO SHRANJEVANJU...")
updated = get_procurement_by_id(8)
updated_data = json.loads(updated['form_data_json'])

# Check project name changed
new_name = updated_data.get('projectInfo', {}).get('projectName', '')
print(f"   Nov naziv: {new_name}")
if 'POSODOBLJENO' in new_name:
    print("   ✅ Naziv pravilno posodobljen")
else:
    print("   ❌ Naziv ni posodobljen")

# Check cofinancers still there
saved_cofinancers = updated_data.get('orderType', {}).get('cofinancers', [])
print(f"\n   Sofinancerji po posodobitvi: {len(saved_cofinancers)}")

if len(saved_cofinancers) == len(cofinancers):
    print("   ✅ Število sofinancerjev ohranjeno!")
    
    # Check details
    for i, cof in enumerate(saved_cofinancers):
        if isinstance(cof, dict):
            name = cof.get('cofinancerName', 'NO NAME')
            program = cof.get('programName', 'NO PROGRAM')
            print(f"   {i+1}. {name} - {program}")
            
    # Verify all fields preserved
    if saved_cofinancers and len(saved_cofinancers) > 0:
        first = saved_cofinancers[0]
        if all(field in first and first[field] for field in 
               ['cofinancerName', 'cofinancerStreetAddress', 'cofinancerPostalCode',
                'programName', 'programArea', 'programCode']):
            print("\n   ✅ Vsi podatki sofinancerjev ohranjeni!")
        else:
            print("\n   ❌ Nekateri podatki sofinancerjev izgubljeni!")
else:
    print(f"   ❌ Sofinancerji izgubljeni! Prej: {len(cofinancers)}, sedaj: {len(saved_cofinancers)}")

print("\n" + "=" * 80)
print("ZAKLJUČEK:")
if len(saved_cofinancers) == 2 and 'POSODOBLJENO' in new_name:
    print("✅ USPEH: Sofinancerji se ohranijo pri urejanju!")
else:
    print("❌ NAPAKA: Sofinancerji se ne ohranijo pravilno!")
print("=" * 80)