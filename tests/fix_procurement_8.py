#!/usr/bin/env python3
"""Fix procurement ID 8 with proper test data for both lots."""

import json
import sqlite3
from datetime import datetime

def fix_procurement_8():
    """Update procurement 8 with proper test values for both lots."""
    
    conn = sqlite3.connect('mainDB.db')
    cursor = conn.cursor()
    
    # Get current data
    cursor.execute("SELECT form_data_json FROM javna_narocila WHERE id = 8")
    row = cursor.fetchone()
    
    if not row:
        print("Procurement ID 8 not found!")
        return
    
    data = json.loads(row[0])
    
    print("Current lot values:")
    if 'lots' in data:
        for i, lot in enumerate(data['lots']):
            value = lot.get('orderType', {}).get('estimatedValue', 0)
            print(f"  Lot {i} ({lot.get('name', 'Unknown')}): €{value:,.2f}")
    
    # Fix the data - add proper values and cofinancers to both lots
    if 'lots' in data and len(data['lots']) >= 2:
        # Lot 0 - Operacijske mize
        data['lots'][0]['orderType'] = {
            'type': 'blago',
            'deliveryType': 'sukcesivna dobava',
            'estimatedValue': 1000000.0,  # €1,000,000
            'guaranteedFunds': 800000.0,
            'isCofinanced': True,
            'cofinancers': [
                {
                    'cofinancerName': 'Evropski sklad za regionalni razvoj',
                    'programName': 'Operativni program za izvajanje kohezijske politike',
                    'programCode': 'OP-ESRR-2021-2027',
                    'programArea': 'Zdravstvo',
                    'cofinancerStreetAddress': 'Kotnikova 5',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'specialRequirements': 'Upoštevati pravila EU o vidnosti financiranja'
                },
                {
                    'cofinancerName': 'Ministrstvo za zdravje RS',
                    'programName': 'Program posodobitve zdravstvene opreme',
                    'programCode': 'MZ-2024-OPR',
                    'programArea': 'Zdravstvo',
                    'cofinancerStreetAddress': 'Štefanova 5',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'specialRequirements': ''
                }
            ],
            'includeZJN3Obligations': True
        }
        
        # Lot 1 - Oprema za operacijske mize
        data['lots'][1]['orderType'] = {
            'type': 'blago',
            'deliveryType': 'enkratna dobava',
            'estimatedValue': 500000.0,  # €500,000
            'guaranteedFunds': 500000.0,
            'isCofinanced': True,
            'cofinancers': [
                {
                    'cofinancerName': 'Evropski sklad za regionalni razvoj',
                    'programName': 'Operativni program za izvajanje kohezijske politike',
                    'programCode': 'OP-ESRR-2021-2027',
                    'programArea': 'Zdravstvo',
                    'cofinancerStreetAddress': 'Kotnikova 5',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'specialRequirements': 'Upoštevati pravila EU o vidnosti financiranja'
                }
            ],
            'includeZJN3Obligations': True
        }
        
        # Also ensure lot_X fields are set for backward compatibility
        data['lot_0.orderType.estimatedValue'] = 1000000.0
        data['lot_1.orderType.estimatedValue'] = 500000.0
        
        # Clear any general orderType (shouldn't be used in lot mode)
        if 'orderType' in data:
            del data['orderType']
    
    # Update procurement
    cursor.execute("""
        UPDATE javna_narocila 
        SET form_data_json = ?
        WHERE id = 8
    """, (json.dumps(data, ensure_ascii=False),))
    
    # Calculate and update total value
    total_value = 1000000.0 + 500000.0  # €1,500,000
    cursor.execute("""
        UPDATE javna_narocila 
        SET vrednost = ?
        WHERE id = 8
    """, (total_value,))
    
    conn.commit()
    
    print("\nUpdated lot values:")
    print(f"  Lot 0 (Operacijske mize): €1,000,000.00 with 2 cofinancers")
    print(f"  Lot 1 (Oprema za operacijske mize): €500,000.00 with 1 cofinancer")
    print(f"  Total: €1,500,000.00")
    
    conn.close()

if __name__ == "__main__":
    fix_procurement_8()