#!/usr/bin/env python3
"""Simple test: Does estimatedValue persist through save and reload?"""

import json
import sqlite3

# Check what's in procurement 8
conn = sqlite3.connect('mainDB.db')
cursor = conn.cursor()

cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = 8")
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    
    print("PROCUREMENT 8 DATA:")
    print("-" * 40)
    
    # Check lots array
    if 'lots' in data and isinstance(data['lots'], list):
        for i, lot in enumerate(data['lots']):
            name = lot.get('name', f'Lot {i}')
            value = lot.get('orderType', {}).get('estimatedValue', 0)
            cofinancers = lot.get('orderType', {}).get('cofinancers', [])
            print(f"Lot {i}: {name}")
            print(f"  Value: €{value:,.2f}")
            print(f"  Cofinancers: {len(cofinancers)}")
            for c in cofinancers:
                if isinstance(c, dict) and c.get('cofinancerName'):
                    print(f"    - {c['cofinancerName']}")
    
    # Check if lot_X fields exist
    print("\nLot_X fields:")
    for key in data:
        if key.startswith('lot_') and 'estimatedValue' in key:
            print(f"  {key}: €{data[key]:,.2f}")

conn.close()