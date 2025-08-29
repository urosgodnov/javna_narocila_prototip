#!/usr/bin/env python3
"""Test the complete edit flow for procurement with lots."""

import json
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_load_procurement():
    """Test loading procurement ID 8 and converting lots to session fields."""
    
    conn = sqlite3.connect('mainDB.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = 8")
    row = cursor.fetchone()
    
    if not row:
        print("Procurement ID 8 not found!")
        return
    
    data = json.loads(row[0])
    
    print("=" * 80)
    print("RAW DATABASE DATA FOR ID 8:")
    print("=" * 80)
    
    # Show lots array structure
    if 'lots' in data:
        print(f"\nlots array ({len(data['lots'])} items):")
        for i, lot in enumerate(data['lots']):
            print(f"\n  Lot {i}:")
            print(f"    Full structure: {json.dumps(lot, indent=6, ensure_ascii=False)}")
    
    # Show any lot_X fields
    print("\nExisting lot_X fields in database:")
    for key in sorted(data.keys()):
        if key.startswith('lot_'):
            print(f"  {key}: {data[key]}")
    
    print("\n" + "=" * 80)
    print("SIMULATING LOAD_PROCUREMENT_TO_FORM CONVERSION:")
    print("=" * 80)
    
    # Simulate what load_procurement_to_form should do
    session_state = {}
    
    # Copy all non-lots fields
    for key, value in data.items():
        if key != 'lots':
            session_state[key] = value
    
    # Process lots array - convert to lot_X fields
    if 'lots' in data and isinstance(data['lots'], list):
        print(f"\nProcessing {len(data['lots'])} lots...")
        for i, lot in enumerate(data['lots']):
            if isinstance(lot, dict):
                print(f"\n  Converting lot {i}:")
                
                def set_lot_fields(lot_data, prefix, indent=4):
                    for field_key, field_value in lot_data.items():
                        full_key = f'{prefix}.{field_key}'
                        
                        if isinstance(field_value, dict):
                            print(f"{' ' * indent}Dict field: {full_key}")
                            set_lot_fields(field_value, full_key, indent + 2)
                        elif isinstance(field_value, list):
                            print(f"{' ' * indent}Array field: {full_key} = {field_value}")
                            session_state[full_key] = field_value
                            # Also set individual array items
                            for j, item in enumerate(field_value):
                                item_key = f"{full_key}[{j}]"
                                session_state[item_key] = item
                                print(f"{' ' * (indent + 2)}  {item_key} = {item}")
                        else:
                            print(f"{' ' * indent}Simple field: {full_key} = {field_value}")
                            session_state[full_key] = field_value
                
                set_lot_fields(lot, f'lot_{i}')
    
    print("\n" + "=" * 80)
    print("RESULTING SESSION STATE (lot fields only):")
    print("=" * 80)
    
    for key in sorted(session_state.keys()):
        if key.startswith('lot_'):
            if 'estimatedValue' in key or 'cofinancer' in key:
                print(f"  {key}: {session_state[key]}")
    
    print("\n" + "=" * 80)
    print("CHECKING CRITICAL VALUES:")
    print("=" * 80)
    
    # Check what we expect to find
    expected = [
        'lot_0.orderType.estimatedValue',
        'lot_1.orderType.estimatedValue',
        'lot_0.orderType.cofinancers',
        'lot_1.orderType.cofinancers'
    ]
    
    for key in expected:
        value = session_state.get(key, 'NOT FOUND')
        if value == 'NOT FOUND':
            print(f"❌ {key}: NOT FOUND")
        else:
            print(f"✅ {key}: {value}")
    
    conn.close()

if __name__ == "__main__":
    test_load_procurement()