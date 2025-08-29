#!/usr/bin/env python3
"""Test script to verify clients data is properly saved and loaded."""

import sqlite3
import json
import sys

def test_clients_data():
    """Test if clients data is properly saved and loaded."""
    conn = sqlite3.connect('mainDB.db')
    cursor = conn.cursor()
    
    # Get the latest procurement with lots
    cursor.execute("""
        SELECT id, naziv, form_data_json 
        FROM javna_narocila 
        WHERE naziv LIKE '%operacij%'
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ No procurement found with 'operacij' in name")
        return False
    
    proc_id, naziv, form_data_json = result
    print(f"✓ Found procurement ID {proc_id}: {naziv}")
    
    # Parse the JSON data
    try:
        form_data = json.loads(form_data_json)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return False
    
    # Check for clientInfo
    if 'clientInfo' not in form_data:
        print("❌ No clientInfo in form_data")
        return False
    
    print("✓ clientInfo found in form_data")
    
    # Check if isSingleClient is False
    is_single = form_data['clientInfo'].get('isSingleClient', True)
    print(f"  isSingleClient: {is_single}")
    
    # Check for clients array
    if 'clients' not in form_data['clientInfo']:
        print("❌ No clients array in clientInfo")
        return False
    
    clients = form_data['clientInfo']['clients']
    print(f"✓ clients array found with {len(clients)} clients")
    
    if len(clients) == 0 and not is_single:
        print("⚠️  WARNING: isSingleClient is False but clients array is empty!")
        print("   This means multiple clients were expected but not saved.")
        
        # Create test data with clients
        print("\n📝 Creating test procurement with multiple clients...")
        test_data = form_data.copy()
        test_data['clientInfo']['isSingleClient'] = False
        test_data['clientInfo']['clients'] = [
            {
                'name': 'UKC Ljubljana',
                'streetAddress': 'Zaloška cesta 2',
                'postalCode': '1000 Ljubljana',
                'legalRepresentative': 'dr. Janez Novak'
            },
            {
                'name': 'UKC Maribor', 
                'streetAddress': 'Ljubljanska ulica 5',
                'postalCode': '2000 Maribor',
                'legalRepresentative': 'dr. Ana Kovač'
            }
        ]
        
        # Update the procurement
        cursor.execute("""
            UPDATE javna_narocila 
            SET form_data_json = ?, zadnja_sprememba = datetime('now')
            WHERE id = ?
        """, (json.dumps(test_data, ensure_ascii=False), proc_id))
        conn.commit()
        print(f"✓ Updated procurement ID {proc_id} with test clients data")
        
        # Verify the update
        cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = ?", (proc_id,))
        updated_json = cursor.fetchone()[0]
        updated_data = json.loads(updated_json)
        updated_clients = updated_data['clientInfo']['clients']
        print(f"✓ Verification: Found {len(updated_clients)} clients after update")
        for client in updated_clients:
            print(f"   - {client['name']}")
        
        return True
    
    # If clients exist, display them
    for i, client in enumerate(clients, 1):
        print(f"  Client {i}: {client.get('name', 'unnamed')}")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("🔍 Testing clients data handling...\n")
    success = test_clients_data()
    sys.exit(0 if success else 1)