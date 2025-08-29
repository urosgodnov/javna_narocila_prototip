#!/usr/bin/env python3
"""Debug what happens when editing procurement ID 8."""

import json
import sqlite3

conn = sqlite3.connect('mainDB.db')
cursor = conn.cursor()

cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = 8")
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    
    print("=" * 80)
    print("NAROČILO ID 8 - PODATKI V BAZI:")
    print("=" * 80)
    
    # Check lot configuration
    print(f"\nlot_mode: {data.get('lot_mode')}")
    print(f"num_lots: {data.get('num_lots')}")
    print(f"lotsInfo.hasLots: {data.get('lotsInfo', {}).get('hasLots')}")
    
    # Check lots array
    if 'lots' in data:
        print(f"\nLots array ({len(data['lots'])} items):")
        for i, lot in enumerate(data['lots']):
            if isinstance(lot, dict):
                name = lot.get('name', f'Sklop {i+1}')
                value = lot.get('orderType', {}).get('estimatedValue', 0)
                print(f"  {i+1}. {name}: €{value:,.2f}")
    
    # Check lot-specific fields
    print("\nLot-specific fields:")
    for key in sorted(data.keys()):
        if key.startswith('lot_'):
            if 'estimatedValue' in key:
                print(f"  {key}: €{data[key]:,.2f}")
            elif 'cofinancers' in key:
                print(f"  {key}: {data[key]}")
    
    # Check orderType (general)
    if 'orderType' in data:
        print(f"\norderType (general):")
        print(f"  estimatedValue: €{data['orderType'].get('estimatedValue', 0):,.2f}")
        cofinancers = data['orderType'].get('cofinancers', [])
        print(f"  cofinancers: {len(cofinancers)} items")
        for cof in cofinancers:
            if isinstance(cof, dict):
                print(f"    - {cof.get('cofinancerName', 'NO NAME')}")
    
    print("\n" + "=" * 80)
    print("WHAT SHOULD BE IN SESSION STATE AFTER LOADING:")
    print("=" * 80)
    
    # For lot mode, values should be in lot_X.orderType.estimatedValue
    if data.get('lot_mode') == 'multiple':
        print("\nFor LOTS mode, these keys should be set:")
        print("  lot_0.orderType.estimatedValue = 1000000.0")
        print("  lot_1.orderType.estimatedValue = 500000.0")
        print("  lot_0.orderType.cofinancers = [array of cofinancers for lot 0]")
        print("  lot_1.orderType.cofinancers = [array of cofinancers for lot 1]")
    else:
        print("\nFor GENERAL mode, these keys should be set:")
        print("  general.orderType.estimatedValue = [value]")
        print("  general.orderType.cofinancers = [array]")

conn.close()