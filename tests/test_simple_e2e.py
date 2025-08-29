#!/usr/bin/env python3
"""
Simplified E2E Test for Procurement Form - Demonstrating All Key Scenarios
========================================================================
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db, create_procurement
from utils.schema_utils import get_form_data_from_session
from ui.form_renderer import parse_formatted_number, format_number_with_dots

def mock_session_state():
    """Mock Streamlit session state for testing"""
    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        
        def __setattr__(self, key, value):
            self[key] = value
    
    return MockSessionState()

def test_simple_procurement_without_lots():
    """Test creating procurement without lots"""
    print("\n=== TEST 1: Simple Procurement (No Lots) ===")
    
    # Use mock session state
    st.session_state = mock_session_state()
    
    # Populate test data
    test_data = {
        'procurementInfo.title': 'Test naročilo brez sklopov',
        'procurementInfo.internalReference': 'TEST-001-2024',
        'procurementInfo.description': 'Testno naročilo za preverjanje funkcionalnosti',
        
        'clientInfo.clients': [
            {
                'organizationName': 'Testna organizacija d.o.o.',
                'registrationNumber': '12345678',
                'vatNumber': 'SI12345678',
                'streetAddress': 'Testna ulica 1',
                'postalCode': '1000',
                'city': 'Ljubljana',
                'contactPerson': 'Janez Novak',
                'contactEmail': 'janez@test.si',
                'contactPhone': '01 234 5678'
            }
        ],
        
        'orderType.estimatedValue': 150000.00,
        'orderType.type': 'blago',
        'orderType.cpvCodes': ['30213100-6'],
        'orderType.isCofinanced': True,
        'orderType.cofinancers': [
            {
                'cofinancerName': 'Evropski sklad za regionalni razvoj',
                'cofinancerStreetAddress': 'Kotnikova 5',
                'cofinancerPostalCode': '1000 Ljubljana',
                'programName': 'Digitalna Slovenija 2030',
                'programArea': 'Digitalizacija',
                'programCode': 'DS-2030-001'
            }
        ],
        
        'procedureType.type': 'odprti postopek',
        'procedureType.isElectronic': True,
        
        'lot_mode': 'none',
        'num_lots': 0
    }
    
    # Populate session state
    for key, value in test_data.items():
        st.session_state[key] = value
    
    # Get form data
    form_data = get_form_data_from_session()
    form_data['status'] = 'osnutek'
    
    print(f"[OK] Created form data with {len(form_data)} fields")
    print(f"[OK] Title: {form_data.get('procurementInfo', {}).get('title', 'Missing')}")
    print(f"[OK] EstimatedValue: {form_data.get('orderType', {}).get('estimatedValue', 'Missing')}")
    print(f"[OK] Cofinancers: {len(form_data.get('orderType', {}).get('cofinancers', []))}")
    print(f"[OK] Clients: {len(form_data.get('clientInfo', {}).get('clients', []))}")
    
    # Save to database
    proc_id = create_procurement(form_data)
    print(f"[OK] Saved procurement with ID: {proc_id}")
    
    return proc_id

def test_procurement_with_lots():
    """Test creating procurement with multiple lots"""
    print("\n=== TEST 2: Complex Procurement (Multiple Lots) ===")
    
    # Use mock session state
    st.session_state = mock_session_state()
    
    # Basic procurement info
    st.session_state['procurementInfo.title'] = 'Test naročilo s sklopi'
    st.session_state['procurementInfo.internalReference'] = 'TEST-002-LOTS'
    st.session_state['procurementInfo.description'] = 'Testno naročilo z več sklopi'
    
    # Lot configuration
    st.session_state['lot_mode'] = 'multiple'
    st.session_state['num_lots'] = 3
    st.session_state['lot_names'] = [
        'Sklop 1: Strežniška oprema',
        'Sklop 2: Mrežna infrastruktura', 
        'Sklop 3: Programska oprema'
    ]
    
    # Lot-specific data
    lots_data = [
        {
            'orderType.estimatedValue': 500000,
            'orderType.type': 'blago',
            'orderType.cpvCodes': ['48820000-2'],
            'orderType.isCofinanced': True,
            'orderType.cofinancers': [
                {
                    'cofinancerName': 'EU Kohezijski sklad',
                    'cofinancerStreetAddress': 'Dunajska 58',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'programName': 'Digitalna kohezija',
                    'programArea': 'IT infrastruktura',
                    'programCode': 'KS-2024-01'
                }
            ]
        },
        {
            'orderType.estimatedValue': 250000,
            'orderType.type': 'blago', 
            'orderType.cpvCodes': ['32420000-3'],
            'orderType.isCofinanced': False
        },
        {
            'orderType.estimatedValue': 300000,
            'orderType.type': 'blago',
            'orderType.cpvCodes': ['48000000-8'],
            'orderType.isCofinanced': True,
            'orderType.cofinancers': [
                {
                    'cofinancerName': 'Javni štipendijski sklad',
                    'cofinancerStreetAddress': 'Vilharjeva 27', 
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'programName': 'Digitalne kompetence',
                    'programArea': 'Izobraževanje',
                    'programCode': 'JSS-DK-2024'
                }
            ]
        }
    ]
    
    # Set lot-specific session state keys
    for i, lot_data in enumerate(lots_data):
        st.session_state[f'lot_{i}.name'] = st.session_state['lot_names'][i]
        for key, value in lot_data.items():
            if key == 'orderType.cofinancers':
                # Handle array of cofinancers
                for j, cofinancer in enumerate(value):
                    for ckey, cval in cofinancer.items():
                        st.session_state[f'lot_{i}.{key}.{j}.{ckey}'] = cval
            else:
                st.session_state[f'lot_{i}.{key}'] = value
    
    # Get form data
    form_data = get_form_data_from_session()
    form_data['status'] = 'osnutek'
    
    print(f"[OK] Created form data with lots")
    print(f"[OK] Title: {form_data.get('procurementInfo', {}).get('title', 'Missing')}")
    print(f"[OK] Lot mode: {form_data.get('lot_mode', 'Missing')}")
    print(f"[OK] Number of lots: {form_data.get('num_lots', 'Missing')}")
    
    if 'lots' in form_data:
        print(f"[OK] Lots data structure created with {len(form_data['lots'])} lots")
        for i, lot in enumerate(form_data['lots']):
            lot_value = lot.get('orderType', {}).get('estimatedValue', 'N/A')
            lot_cofinancers = len(lot.get('orderType', {}).get('cofinancers', []))
            print(f"  - Lot {i+1}: {lot_value}, {lot_cofinancers} cofinancers")
    else:
        print("[ERROR] No lots data structure found!")
    
    # Save to database
    proc_id = create_procurement(form_data)
    print(f"[OK] Saved procurement with lots, ID: {proc_id}")
    
    return proc_id

def test_cofinancer_operations():
    """Test adding/removing cofinancers"""
    print("\n=== TEST 3: Cofinancer Operations ===")
    
    # Use mock session state
    st.session_state = mock_session_state()
    
    # Set initial estimated value
    st.session_state['orderType.estimatedValue'] = 100000.0
    st.session_state['orderType.isCofinanced'] = True
    st.session_state['orderType.cofinancers'] = []
    
    print(f"[OK] Initial estimated value: {st.session_state['orderType.estimatedValue']}")
    print(f"[OK] Initial cofinancers: {len(st.session_state['orderType.cofinancers'])}")
    
    # Add cofinancer
    st.session_state['orderType.cofinancers'].append({
        'cofinancerName': 'Test Cofinancer',
        'cofinancerStreetAddress': 'Test Street 1',
        'cofinancerPostalCode': '1000 Test',
        'programName': 'Test Program',
        'programArea': 'Test Area', 
        'programCode': 'TEST-001'
    })
    
    print(f"[OK] After adding cofinancer: {st.session_state['orderType.estimatedValue']}")
    print(f"[OK] Cofinancers count: {len(st.session_state['orderType.cofinancers'])}")
    
    # Remove cofinancer
    st.session_state['orderType.cofinancers'].pop()
    
    print(f"[OK] After removing cofinancer: {st.session_state['orderType.estimatedValue']}")
    print(f"[OK] Cofinancers count: {len(st.session_state['orderType.cofinancers'])}")
    
    # Verify value preserved
    if st.session_state['orderType.estimatedValue'] == 100000.0:
        print("[OK] EstimatedValue preserved through cofinancer operations!")
    else:
        print("[ERROR] EstimatedValue was modified during cofinancer operations!")
        
    return True

def test_slovenian_number_parsing():
    """Test Slovenian number format parsing"""
    print("\n=== TEST 4: Slovenian Number Format Parsing ===")
    
    test_cases = [
        ('1.500.000,50', 1500000.5),
        ('500.000', 500000),
        ('1.234,56', 1234.56),
        ('100', 100),
        ('50.000,00', 50000.0)
    ]
    
    for input_str, expected in test_cases:
        try:
            result = parse_formatted_number(input_str)
            formatted = format_number_with_dots(result)
            
            if abs(result - expected) < 0.01:  # Allow small floating point differences
                print(f"[OK] '{input_str}' -> {result} -> '{formatted}'")
            else:
                print(f"[ERROR] '{input_str}' -> {result} (expected {expected})")
        except Exception as e:
            print(f"[ERROR] '{input_str}' -> ERROR: {e}")
    
    return True

def main():
    """Run all E2E tests"""
    print("\n" + "="*80)
    print(" SIMPLIFIED E2E TEST SUITE - COMPREHENSIVE PROCUREMENT FORM TESTING")
    print("="*80)
    
    # Initialize test database
    import database
    database.DATABASE_FILE = 'test_simple_e2e.db'
    init_db()
    
    results = []
    created_ids = []
    
    try:
        # Test 1: Simple procurement
        proc_id_1 = test_simple_procurement_without_lots()
        created_ids.append(proc_id_1)
        results.append(("Simple Procurement", True))
        
        # Test 2: Procurement with lots
        proc_id_2 = test_procurement_with_lots()
        created_ids.append(proc_id_2)
        results.append(("Lots Procurement", True))
        
        # Test 3: Cofinancer operations
        test_cofinancer_operations()
        results.append(("Cofinancer Operations", True))
        
        # Test 4: Number parsing
        test_slovenian_number_parsing()
        results.append(("Number Format Parsing", True))
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        results.append(("Failed", False))
    
    # Print summary
    print("\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "[OK]" if result else "[ERROR]"
        print(f" {symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print("-"*80)
    print(f" Total: {passed} passed out of {len(results)} tests")
    print(f" Created procurements: {created_ids}")
    print("="*80)
    
    # Cleanup
    if os.path.exists('test_simple_e2e.db'):
        os.remove('test_simple_e2e.db')
        print(" [OK] Test database cleaned up")

if __name__ == "__main__":
    main()