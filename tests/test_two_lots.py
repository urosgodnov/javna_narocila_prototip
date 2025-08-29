#!/usr/bin/env python3
"""Create a test procurement with 2 lots to verify everything works."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from database import create_procurement, get_procurement_by_id

# Create test data with 2 lots
form_data = {
    "projectInfo": {
        "projectName": "Testno naročilo z 2 sklopoma"
    },
    "orderType": {
        "type": "blago",
        "estimatedValue": 0.0  # Total will be sum of lots
    },
    "lotsInfo": {
        "hasLots": True
    },
    "lot_mode": "multiple",
    "num_lots": 2,
    "lots": [
        {
            "name": "Sklop 1 - Računalniška oprema",
            "orderType": {
                "type": "blago",
                "estimatedValue": 500000.0
            }
        },
        {
            "name": "Sklop 2 - Pisarniško pohištvo", 
            "orderType": {
                "type": "blago",
                "estimatedValue": 250000.0
            }
        }
    ],
    # Add lot-specific fields as they would be in session
    "lot_0.orderType.estimatedValue": 500000.0,
    "lot_0.orderType.type": "blago",
    "lot_1.orderType.estimatedValue": 250000.0,
    "lot_1.orderType.type": "blago"
}

print("=" * 80)
print("CREATING TEST PROCUREMENT WITH 2 LOTS")
print("=" * 80)

print("\nTest data:")
print(f"  Project: {form_data['projectInfo']['projectName']}")
print(f"  Lot 1: {form_data['lots'][0]['name']} - €{form_data['lots'][0]['orderType']['estimatedValue']:,.2f}")
print(f"  Lot 2: {form_data['lots'][1]['name']} - €{form_data['lots'][1]['orderType']['estimatedValue']:,.2f}")
print(f"  Expected total: €{750000.0:,.2f}")

# Create procurement
procurement_id = create_procurement(form_data)
print(f"\n✓ Created procurement with ID: {procurement_id}")

# Load it back
loaded = get_procurement_by_id(procurement_id)

if loaded:
    print(f"\n✓ Successfully loaded procurement ID {procurement_id}")
    print(f"  Naziv: {loaded['naziv']}")
    print(f"  Vrednost (from DB): €{loaded['vrednost']:,.2f}")
    
    # Parse JSON to check lot data
    loaded_data = json.loads(loaded['form_data_json'])
    
    if 'lots' in loaded_data:
        print(f"\n✓ Found {len(loaded_data['lots'])} lots in saved data:")
        for i, lot in enumerate(loaded_data['lots']):
            if isinstance(lot, dict):
                lot_name = lot.get('name', f'Sklop {i+1}')
                lot_value = lot.get('orderType', {}).get('estimatedValue', 0)
                print(f"    Lot {i+1}: {lot_name} - €{lot_value:,.2f}")
    
    # Check lot-specific fields
    lot_fields = [k for k in loaded_data.keys() if k.startswith('lot_')]
    if lot_fields:
        print(f"\n✓ Found {len(lot_fields)} lot-specific fields")
        # Check estimated values
        for i in range(2):
            key = f"lot_{i}.orderType.estimatedValue"
            if key in loaded_data:
                print(f"    {key}: €{loaded_data[key]:,.2f}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    if loaded['vrednost'] == 750000.0:
        print("✅ SUCCESS: Total value correctly calculated from lots!")
    else:
        print(f"❌ FAIL: Expected €750,000 but got €{loaded['vrednost']:,.2f}")
        
    # Check if individual lot values are preserved
    success = True
    if 'lots' in loaded_data and len(loaded_data['lots']) == 2:
        if loaded_data['lots'][0].get('orderType', {}).get('estimatedValue') != 500000.0:
            print(f"❌ FAIL: Lot 1 value incorrect")
            success = False
        if loaded_data['lots'][1].get('orderType', {}).get('estimatedValue') != 250000.0:
            print(f"❌ FAIL: Lot 2 value incorrect")
            success = False
            
    if success and loaded['vrednost'] == 750000.0:
        print("✅ ALL TESTS PASSED!")
else:
    print("❌ ERROR: Could not load procurement!")

print("=" * 80)