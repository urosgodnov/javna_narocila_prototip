#!/usr/bin/env python3
"""Check procurement ID 8 data."""

import json
import sqlite3

conn = sqlite3.connect('mainDB.db')
cursor = conn.cursor()

# Get procurement 8
cursor.execute("SELECT id, naziv, vrednost, form_data_json FROM javna_narocila WHERE id = 8")
row = cursor.fetchone()

if row:
    id, naziv, vrednost, form_data_json = row
    print(f"ID: {id}")
    print(f"Naziv: {naziv}")
    print(f"Vrednost in DB: {vrednost}")
    print("-" * 60)
    
    # Parse JSON
    form_data = json.loads(form_data_json)
    
    # Check estimatedValue in different locations
    print("Checking estimatedValue in form_data:")
    
    # Direct in orderType
    orderType_value = form_data.get('orderType', {}).get('estimatedValue', 'NOT FOUND')
    print(f"  orderType.estimatedValue: {orderType_value}")
    
    # With general prefix
    general_value = form_data.get('general.orderType.estimatedValue', 'NOT FOUND')
    print(f"  general.orderType.estimatedValue: {general_value}")
    
    # Check all keys with 'estimatedValue'
    print("\nAll keys containing 'estimatedValue':")
    for key in form_data.keys():
        if 'estimatedValue' in key.lower():
            print(f"  {key}: {form_data[key]}")
    
    # Check orderType structure
    if 'orderType' in form_data:
        print(f"\norderType keys: {list(form_data['orderType'].keys())}")

# Delete test procurements 10 and 11
print("\n" + "=" * 60)
print("Deleting test procurements 10 and 11...")
cursor.execute("DELETE FROM javna_narocila WHERE id IN (10, 11)")
conn.commit()
print(f"Deleted {cursor.rowcount} test procurements")

conn.close()