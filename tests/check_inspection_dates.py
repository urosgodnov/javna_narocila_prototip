#!/usr/bin/env python3
"""Check inspection dates in procurement 8."""

import json
import sqlite3

conn = sqlite3.connect('mainDB.db')
cursor = conn.cursor()

cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = 8")
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    
    print("INSPECTION DATES IN DATABASE:")
    print("-" * 40)
    
    # Check for inspection fields
    for key in sorted(data.keys()):
        if 'inspection' in key.lower():
            print(f"{key}: {data[key]}")
    
    # Check in lots array
    if 'lots' in data:
        for i, lot in enumerate(data['lots']):
            if isinstance(lot, dict):
                for field in lot:
                    if 'inspection' in field.lower():
                        print(f"lots[{i}].{field}: {lot[field]}")
                
                # Check nested fields
                if 'inspectionInfo' in lot:
                    print(f"\nLot {i} inspectionInfo:")
                    print(json.dumps(lot['inspectionInfo'], indent=2, ensure_ascii=False))

conn.close()