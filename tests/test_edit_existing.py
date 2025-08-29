#!/usr/bin/env python3
"""Test editing existing procurement ID 8 and adding estimatedValue."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import logging
logging.basicConfig(level=logging.INFO)
from database import get_procurement_by_id, update_procurement

print("=" * 80)
print("TEST: UREJANJE OBSTOJEČEGA NAROČILA ID 8")
print("=" * 80)

# First, load the existing procurement
existing = get_procurement_by_id(8)

if not existing:
    print("❌ ERROR: Naročilo ID 8 ne obstaja!")
    exit(1)

print(f"\n1. TRENUTNO STANJE naročila ID 8:")
print(f"   Naziv: {existing['naziv']}")
print(f"   Vrednost v DB: €{existing['vrednost']:,.2f}")

# Parse existing data
existing_data = json.loads(existing['form_data_json'])
current_value = existing_data.get('orderType', {}).get('estimatedValue', 0)
print(f"   orderType.estimatedValue: €{current_value:,.2f}")

# Check if it has lots
has_lots = 'lots' in existing_data and len(existing_data.get('lots', [])) > 0
print(f"   Ima sklope: {'Da' if has_lots else 'Ne'}")

print("\n2. POSODABLJAM VREDNOSTI...")

# Update the estimatedValue
if has_lots:
    # For procurement with lots, update lot values
    print("   Naročilo ima sklope, posodabljam vrednosti sklopov:")
    if 'lots' in existing_data:
        for i, lot in enumerate(existing_data['lots']):
            if isinstance(lot, dict):
                # Set new values for each lot
                if i == 0:
                    new_value = 1000000.0  # 1 million for lot 1
                    lot['orderType'] = lot.get('orderType', {})
                    lot['orderType']['estimatedValue'] = new_value
                    print(f"   - Sklop 1: nastavljam na €{new_value:,.2f}")
                elif i == 1:
                    new_value = 500000.0  # 500k for lot 2
                    lot['orderType'] = lot.get('orderType', {})
                    lot['orderType']['estimatedValue'] = new_value
                    print(f"   - Sklop 2: nastavljam na €{new_value:,.2f}")
        
        # Also update lot-specific fields
        existing_data['lot_0.orderType.estimatedValue'] = 1000000.0
        existing_data['lot_1.orderType.estimatedValue'] = 500000.0
        
        # Test that auto-detect works even with incorrect num_lots
        # existing_data['num_lots'] = 2  # Commented out to test auto-detect
        
    expected_total = 1500000.0
else:
    # For procurement without lots, update main estimatedValue
    print("   Naročilo NIMA sklopov, posodabljam glavno vrednost:")
    new_value = 2500000.0
    existing_data['orderType'] = existing_data.get('orderType', {})
    existing_data['orderType']['estimatedValue'] = new_value
    print(f"   - Nastavljam orderType.estimatedValue na €{new_value:,.2f}")
    expected_total = new_value

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
    print(f"   Naziv: {updated['naziv']}")
    print(f"   Vrednost v DB: €{updated['vrednost']:,.2f}")
    
    # Parse updated data
    updated_data = json.loads(updated['form_data_json'])
    
    if has_lots:
        # Check lot values
        print("\n   Vrednosti sklopov:")
        total_from_lots = 0
        if 'lots' in updated_data:
            for i, lot in enumerate(updated_data['lots']):
                if isinstance(lot, dict):
                    lot_value = lot.get('orderType', {}).get('estimatedValue', 0)
                    print(f"   - Sklop {i+1}: €{lot_value:,.2f}")
                    total_from_lots += lot_value
        print(f"   Skupaj iz sklopov: €{total_from_lots:,.2f}")
        
        # Check lot-specific fields
        for i in range(2):
            key = f"lot_{i}.orderType.estimatedValue"
            if key in updated_data:
                print(f"   {key}: €{updated_data[key]:,.2f}")
    else:
        # Check main estimatedValue
        saved_value = updated_data.get('orderType', {}).get('estimatedValue', 0)
        print(f"   orderType.estimatedValue: €{saved_value:,.2f}")
    
    print("\n" + "=" * 80)
    print("REZULTAT:")
    
    if updated['vrednost'] == expected_total:
        print(f"✅ USPEH: Vrednost pravilno posodobljena na €{expected_total:,.2f}!")
    else:
        print(f"❌ NAPAKA: Pričakoval €{expected_total:,.2f}, dobil €{updated['vrednost']:,.2f}")
        
else:
    print("❌ ERROR: Ne morem naložiti posodobljenega naročila!")

print("=" * 80)