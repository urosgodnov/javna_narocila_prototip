#!/usr/bin/env python3
"""Check all procurements in database."""

import json
import sqlite3

conn = sqlite3.connect('mainDB.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, naziv, vrednost, status, datum_objave 
    FROM javna_narocila 
    ORDER BY id DESC 
    LIMIT 10
""")

print("=" * 80)
print("ZADNJIH 10 NAROČIL V BAZI:")
print("=" * 80)
print(f"{'ID':<5} {'Naziv':<40} {'Vrednost':>15} {'Status':<15} {'Datum':<12}")
print("-" * 80)

for row in cursor.fetchall():
    id, naziv, vrednost, status, datum = row
    # Truncate long names
    if len(naziv) > 37:
        naziv = naziv[:37] + "..."
    print(f"{id:<5} {naziv:<40} €{vrednost:>14,.2f} {status:<15} {datum:<12}")

print("=" * 80)

# Check specific IDs
print("\nPODROBNO ZA TESTNA NAROČILA:")
print("-" * 80)

for test_id in [8, 12, 13]:
    cursor.execute("""
        SELECT id, naziv, vrednost, form_data_json 
        FROM javna_narocila 
        WHERE id = ?
    """, (test_id,))
    
    row = cursor.fetchone()
    if row:
        id, naziv, vrednost, form_data_json = row
        data = json.loads(form_data_json)
        
        print(f"\nID {id}: {naziv}")
        print(f"  DB vrednost: €{vrednost:,.2f}")
        
        # Check estimatedValue in form_data
        if 'orderType' in data and 'estimatedValue' in data['orderType']:
            print(f"  orderType.estimatedValue: €{data['orderType']['estimatedValue']:,.2f}")
        else:
            print(f"  orderType.estimatedValue: NOT FOUND")
            
        # Check for lots
        if 'lots' in data and data['lots']:
            print(f"  Sklopi: {len(data['lots'])}")
            total_from_lots = 0
            for i, lot in enumerate(data['lots']):
                if isinstance(lot, dict):
                    lot_value = lot.get('orderType', {}).get('estimatedValue', 0)
                    total_from_lots += lot_value
                    print(f"    Sklop {i+1}: €{lot_value:,.2f}")
            print(f"  Skupaj iz sklopov: €{total_from_lots:,.2f}")

conn.close()