#!/usr/bin/env python3
"""Test procurement without lots (general mode) with estimatedValue."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from database import create_procurement, get_procurement_by_id

# Create test data WITHOUT lots (general mode) 
form_data = {
    "projectInfo": {
        "projectName": "Testno naročilo BREZ sklopov"
    },
    "orderType": {
        "type": "gradnje",
        "estimatedValue": 1234567.89,  # This MUST be saved correctly!
        "isCofinanced": True,
        "cofinancers": [
            {
                "cofinancerName": "EU Kohezijski sklad",
                "cofinancerStreetAddress": "Dunajska 58",
                "cofinancerPostalCode": "1000 Ljubljana",
                "programName": "Operativni program",
                "programArea": "Infrastruktura",
                "programCode": "OP-2024"
            }
        ]
    },
    "lotsInfo": {
        "hasLots": False
    },
    "lot_mode": "none",
    "num_lots": 0
}

print("=" * 80)
print("CREATING TEST PROCUREMENT WITHOUT LOTS (GENERAL MODE)")
print("=" * 80)

print("\nTest data:")
print(f"  Project: {form_data['projectInfo']['projectName']}")
print(f"  Type: {form_data['orderType']['type']}")
print(f"  Estimated Value: €{form_data['orderType']['estimatedValue']:,.2f}")
print(f"  Cofinanced: {form_data['orderType']['isCofinanced']}")
if form_data['orderType'].get('cofinancers'):
    print(f"  Cofinancers: {len(form_data['orderType']['cofinancers'])} found")

# Create procurement
procurement_id = create_procurement(form_data)
print(f"\n✓ Created procurement with ID: {procurement_id}")

# Load it back
loaded = get_procurement_by_id(procurement_id)

if loaded:
    print(f"\n✓ Successfully loaded procurement ID {procurement_id}")
    print(f"  Naziv: {loaded['naziv']}")
    print(f"  Vrednost (from DB column): €{loaded['vrednost']:,.2f}")
    
    # Parse JSON to check the actual saved data
    loaded_data = json.loads(loaded['form_data_json'])
    
    # Check estimatedValue
    saved_estimated = loaded_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
    print(f"\n  Checking orderType.estimatedValue: {saved_estimated}")
    
    # Check cofinancers
    saved_cofinancers = loaded_data.get('orderType', {}).get('cofinancers', [])
    print(f"  Checking cofinancers: {len(saved_cofinancers)} found")
    if saved_cofinancers:
        print(f"    First cofinancer: {saved_cofinancers[0].get('cofinancerName', 'NO NAME')}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    
    success = True
    
    # Check estimated value
    if saved_estimated == 1234567.89:
        print("✅ estimatedValue: Correctly saved and loaded!")
    else:
        print(f"❌ estimatedValue: Expected 1234567.89 but got {saved_estimated}")
        success = False
    
    # Check DB column value
    if loaded['vrednost'] == 1234567.89:
        print("✅ DB vrednost column: Correctly calculated!")
    else:
        print(f"❌ DB vrednost column: Expected 1234567.89 but got {loaded['vrednost']}")
        success = False
        
    # Check cofinancers
    if len(saved_cofinancers) == 1 and saved_cofinancers[0].get('cofinancerName') == "EU Kohezijski sklad":
        print("✅ Cofinancers: Correctly saved and loaded!")
    else:
        print(f"❌ Cofinancers: Not saved correctly")
        success = False
        
    if success:
        print("\n🎉 ALL TESTS PASSED FOR GENERAL MODE!")
    else:
        print("\n❌ SOME TESTS FAILED")
else:
    print("❌ ERROR: Could not load procurement!")

print("=" * 80)