#!/usr/bin/env python3
"""Test editing cofinancers in existing procurement."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import logging
logging.basicConfig(level=logging.INFO)
from database import get_procurement_by_id, update_procurement

print("=" * 80)
print("TEST: SOFINANCERJI PRI UREJANJU NAROČILA")
print("=" * 80)

# Test on procurement ID 8
existing = get_procurement_by_id(8)

if not existing:
    print("❌ ERROR: Naročilo ID 8 ne obstaja!")
    exit(1)

print(f"\n1. TRENUTNO STANJE naročila ID 8:")
print(f"   Naziv: {existing['naziv']}")

# Parse existing data
existing_data = json.loads(existing['form_data_json'])

# Check current cofinancers
current_cofinancers = existing_data.get('orderType', {}).get('cofinancers', [])
print(f"   Trenutni sofinancerji: {len(current_cofinancers)}")
if current_cofinancers:
    for i, cof in enumerate(current_cofinancers):
        if isinstance(cof, dict):
            print(f"     {i+1}. {cof.get('cofinancerName', 'NO NAME')}")

print("\n2. DODAJAM SOFINANCERJE...")

# Add/Update cofinancers
existing_data['orderType'] = existing_data.get('orderType', {})
existing_data['orderType']['isCofinanced'] = True
existing_data['orderType']['cofinancers'] = [
    {
        'cofinancerName': 'Evropski sklad za regionalni razvoj',
        'cofinancerStreetAddress': 'Kotnikova 5',
        'cofinancerPostalCode': '1000 Ljubljana',
        'programName': 'Operativni program 2021-2027',
        'programArea': 'Digitalizacija',
        'programCode': 'OP-ESRR-2024'
    },
    {
        'cofinancerName': 'Ministrstvo za zdravje RS',
        'cofinancerStreetAddress': 'Štefanova 5',
        'cofinancerPostalCode': '1000 Ljubljana', 
        'programName': 'Program razvoja zdravstva',
        'programArea': 'Infrastruktura',
        'programCode': 'MZ-2024-INF'
    }
]

# Also set individual cofinancer fields as form would do
for i, cofinancer in enumerate(existing_data['orderType']['cofinancers']):
    for field_name, field_value in cofinancer.items():
        key = f'orderType.cofinancers.{i}.{field_name}'
        existing_data[key] = field_value
        
print("   Dodal 2 sofinancerja:")
print("   - Evropski sklad za regionalni razvoj")
print("   - Ministrstvo za zdravje RS")

# Perform the update
print("\n3. SHRANJUJEM POSODOBLJENO NAROČILO...")
success = update_procurement(8, existing_data)

if success:
    print("   ✓ Uspešno posodobljeno!")
else:
    print("   ❌ Posodobitev ni uspela!")
    exit(1)

# Reload and verify
print("\n4. PREVERJAM SHRANJENE PODATKE...")
updated = get_procurement_by_id(8)

if updated:
    # Parse updated data
    updated_data = json.loads(updated['form_data_json'])
    
    # Check cofinancers
    saved_cofinancers = updated_data.get('orderType', {}).get('cofinancers', [])
    print(f"   Shranjeni sofinancerji: {len(saved_cofinancers)}")
    
    if saved_cofinancers:
        for i, cof in enumerate(saved_cofinancers):
            if isinstance(cof, dict):
                name = cof.get('cofinancerName', 'NO NAME')
                program = cof.get('programName', 'NO PROGRAM')
                print(f"     {i+1}. {name}")
                print(f"        Program: {program}")
                print(f"        Naslov: {cof.get('cofinancerStreetAddress', '')}, {cof.get('cofinancerPostalCode', '')}")
    
    # Check individual fields
    print("\n   Preverjam individualna polja:")
    for i in range(2):
        key = f'orderType.cofinancers.{i}.cofinancerName'
        if key in updated_data:
            print(f"   ✓ {key}: {updated_data[key]}")
        else:
            print(f"   ❌ {key}: NOT FOUND")
    
    print("\n" + "=" * 80)
    print("REZULTAT:")
    
    success = True
    
    # Check if we have 2 cofinancers
    if len(saved_cofinancers) != 2:
        print(f"❌ NAPAKA: Pričakoval 2 sofinancerja, dobil {len(saved_cofinancers)}")
        success = False
    else:
        print("✅ Število sofinancerjev: 2")
    
    # Check names
    if saved_cofinancers:
        if saved_cofinancers[0].get('cofinancerName') == 'Evropski sklad za regionalni razvoj':
            print("✅ Prvi sofinancer pravilno shranjen")
        else:
            print(f"❌ Prvi sofinancer napačen: {saved_cofinancers[0].get('cofinancerName')}")
            success = False
            
        if len(saved_cofinancers) > 1 and saved_cofinancers[1].get('cofinancerName') == 'Ministrstvo za zdravje RS':
            print("✅ Drugi sofinancer pravilno shranjen")
        else:
            print(f"❌ Drugi sofinancer napačen")
            success = False
    
    # Check all fields are preserved
    if saved_cofinancers and len(saved_cofinancers) > 0:
        first_cof = saved_cofinancers[0]
        required_fields = ['cofinancerName', 'cofinancerStreetAddress', 'cofinancerPostalCode', 
                          'programName', 'programArea', 'programCode']
        missing = [f for f in required_fields if f not in first_cof or not first_cof[f]]
        if missing:
            print(f"❌ Manjkajo polja: {missing}")
            success = False
        else:
            print("✅ Vsi podatki sofinancerjev ohranjeni")
    
    if success:
        print("\n🎉 VSI TESTI ZA SOFINANCERJE USPEŠNI!")
    else:
        print("\n❌ NEKATERI TESTI NISO USPELI")
        
else:
    print("❌ ERROR: Ne morem naložiti posodobljenega naročila!")

print("=" * 80)