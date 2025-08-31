#!/usr/bin/env python3
"""
Debug script to check what session state keys are generated and how they're processed.
This will help identify why fields like estimatedValue and cofinancerShare aren't being saved.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit session state with sample data based on the procurement JSON
class MockSessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)
    
    def keys(self):
        return super().keys()

def debug_session_keys():
    """Debug what keys are in session state and how they should be processed."""
    
    print("=" * 80)
    print("DEBUGGING SESSION STATE KEYS FOR PROCUREMENT ID 8")
    print("=" * 80)
    
    # Create mock session state based on what should be there for the procurement
    # This represents what should be in session state when form is filled
    mock_session_state = MockSessionState({
        # Schema info
        'schema': {
            'properties': {
                'orderType': {'type': 'object'},
                'clientInfo': {'type': 'object'},
                'lots': {'type': 'array'}
            }
        },
        
        # Client data (this seems to work based on JSON)
        'clientInfo.clients.0.name': 'UKC Ljubljana',
        'clientInfo.clients.0.streetAddress': 'Zaloška 44',
        'clientInfo.clients.0.postalCode': '1000 Ljubljana',
        'clientInfo.clients.0.legalRepresentative': 'g. Tadej Hitorito',
        'clientInfo.clients.1.name': 'UKC Maribor',
        'clientInfo.clients.1.streetAddress': 'Mariborska 7',
        'clientInfo.clients.1.postalCode': '2000 Maribor',
        'clientInfo.clients.1.legalRepresentative': 'ga. Mafelda Fikfak',
        
        # Main orderType (general level) - this is missing from JSON!
        'orderType.estimatedValue': 500000.0,  # Should be saved but shows as 0.0
        'orderType.type': 'blago',
        'orderType.deliveryType': 'enkratna dobava',
        'orderType.isCofinanced': False,
        'orderType.guaranteedFunds': 100000.0,
        
        # Lot 0 data with cofinancer
        'lot_0.name': 'Operacijske mize',
        'lot_0.orderType.type': 'blago',
        'lot_0.orderType.estimatedValue': 300000.0,  # Should be saved but shows as 0.0
        'lot_0.orderType.deliveryType': 'enkratna dobava',
        'lot_0.orderType.isCofinanced': True,
        'lot_0.orderType.guaranteedFunds': 50000.0,
        
        # Lot 0 cofinancer data - CRITICAL: these fields are missing from JSON!
        'lot_0.orderType.cofinancers.0.cofinancerName': 'MNZ',
        'lot_0.orderType.cofinancers.0.cofinancerStreetAddress': 'jakovljeva 3',
        'lot_0.orderType.cofinancers.0.cofinancerPostalCode': '1000 Ljubljana',
        'lot_0.orderType.cofinancers.0.programName': 'pomagajmo',
        'lot_0.orderType.cofinancers.0.programArea': 'skrajševanje vrst',
        'lot_0.orderType.cofinancers.0.programCode': 'p130',
        'lot_0.orderType.cofinancers.0.specialRequirements': '',
        # These critical fields are MISSING from the saved JSON:
        'lot_0.orderType.cofinancers.0.estimatedValue': 150000.0,  # ← NOT SAVED
        'lot_0.orderType.cofinancers.0.cofinancerShare': 0.5,      # ← NOT SAVED
        
        # Lot 1 data
        'lot_1.name': 'Oprema za operacijske mize',
        'lot_1.orderType.type': 'blago',
        'lot_1.orderType.estimatedValue': 200000.0,  # Should be saved
        
        # Lot configuration
        'lot_mode': 'multiple',
        'lotsInfo.hasLots': True,
        'lot_names': ['Operacijske mize', 'Oprema za operacijske mize']
    })
    
    print("1. MOCK SESSION STATE KEYS:")
    print("-" * 50)
    for key in sorted(mock_session_state.keys()):
        print(f"  {key} = {mock_session_state[key]}")
    print()
    
    print("2. ANALYZING KEY PATTERNS:")
    print("-" * 50)
    
    # Analyze which keys should be processed as arrays vs regular fields
    array_keys = []
    lot_keys = []
    regular_keys = []
    
    for key in mock_session_state.keys():
        if key.startswith('widget_'):
            continue
        
        # Check for array patterns (contains digit as part)
        if '.' in key and any(part.isdigit() for part in key.split('.')):
            if key.startswith('lot_'):
                lot_keys.append(key)
            else:
                array_keys.append(key)
        else:
            regular_keys.append(key)
    
    print("ARRAY KEYS (should be processed for array reconstruction):")
    for key in sorted(array_keys):
        print(f"  {key}")
    print()
    
    print("LOT-PREFIXED KEYS (special handling needed):")
    for key in sorted(lot_keys):
        print(f"  {key}")
    print()
    
    print("REGULAR KEYS:")
    for key in sorted(regular_keys):
        print(f"  {key}")
    print()
    
    print("3. CRITICAL MISSING FIELDS ANALYSIS:")
    print("-" * 50)
    
    missing_fields = [
        'lot_0.orderType.cofinancers.0.estimatedValue',
        'lot_0.orderType.cofinancers.0.cofinancerShare',
        'orderType.estimatedValue',
        'lot_0.orderType.estimatedValue',
        'lot_1.orderType.estimatedValue'
    ]
    
    for field in missing_fields:
        if field in mock_session_state:
            print(f"  ✓ {field} = {mock_session_state[field]} (should be saved)")
        else:
            print(f"  ✗ {field} = MISSING from session state")
    
    print("\n" + "=" * 80)
    print("CONCLUSION: The problem is that the session state reconstruction")
    print("logic is not properly capturing lot-prefixed cofinancer fields.")
    print("Fields like 'lot_0.orderType.cofinancers.0.estimatedValue' are being lost.")
    print("=" * 80)

if __name__ == '__main__':
    debug_session_keys()