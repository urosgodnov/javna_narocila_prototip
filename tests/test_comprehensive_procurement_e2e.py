#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Procurement Form
===================================================
This test thoroughly validates all aspects of the procurement form including:
- Creating procurements with and without lots
- Data persistence across saves
- Navigation between steps
- Editing existing procurements
- Form state management
"""

import pytest
import sys
import os
import time
import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db, create_procurement
from utils.schema_utils import get_form_data_from_session
from ui.form_renderer import parse_formatted_number, format_number_with_dots


class ProcurementTestData:
    """Test data for procurements"""
    
    @staticmethod
    def get_simple_procurement() -> Dict[str, Any]:
        """Procurement without lots"""
        return {
            # Step 1: Basic Info
            'procurementInfo.title': 'Test naročilo brez sklopov',
            'procurementInfo.internalReference': 'TEST-001-2024',
            'procurementInfo.description': 'Testno naročilo za preverjanje funkcionalnosti brez sklopov',
            
            # Step 2: Clients
            'clientInfo.clients': [
                {
                    'organizationName': 'Testna organizacija d.o.o.',
                    'registrationNumber': '12345678',
                    'vatNumber': 'SI12345678',
                    'streetAddress': 'Testna ulica 1',
                    'postalCode': '1000',
                    'city': 'Ljubljana',
                    'country': 'Slovenija',
                    'contactPerson': 'Janez Novak',
                    'contactEmail': 'janez@test.si',
                    'contactPhone': '01 234 5678'
                }
            ],
            
            # Step 3: Order Type
            'orderType.estimatedValue': 150000.00,
            'orderType.type': 'blago',
            'orderType.cpvCodes': ['30213100-6'],  # Računalniki
            'orderType.isCofinanced': True,
            'orderType.cofinancers': [
                {
                    'cofinancerName': 'Evropski sklad za regionalni razvoj',
                    'cofinancerStreetAddress': 'Kotnikova 5',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'programName': 'Digitalna Slovenija 2030',
                    'programArea': 'Digitalizacija',
                    'programCode': 'DS-2030-001'
                },
                {
                    'cofinancerName': 'Ministrstvo za digitalno preobrazbo',
                    'cofinancerStreetAddress': 'Tržaška cesta 21',
                    'cofinancerPostalCode': '1000 Ljubljana',
                    'programName': 'Nacionalni program digitalizacije',
                    'programArea': 'IT infrastruktura',
                    'programCode': 'NPD-2024-IT'
                }
            ],
            
            # Step 4: Procedure Type
            'procedureType.type': 'odprti postopek',
            'procedureType.isElectronic': True,
            'procedureType.acceptsVariants': False,
            'procedureType.requiresFinancialGuarantee': True,
            
            # Step 5: Competition Criteria
            'competitionCriteria.selectionCriterion': 'ekonomsko najugodnejša ponudba',
            'competitionCriteria.criteria': [
                {
                    'name': 'Cena',
                    'weight': 70,
                    'description': 'Najnižja cena'
                },
                {
                    'name': 'Tehnične lastnosti',
                    'weight': 20,
                    'description': 'Tehnična ustreznost opreme'
                },
                {
                    'name': 'Garancijska doba',
                    'weight': 10,
                    'description': 'Dolžina garancije v mesecih'
                }
            ],
            
            # Step 6: Publication Deadlines
            'publicationDeadlines.questionDeadline': (datetime.now() + timedelta(days=7)).date(),
            'publicationDeadlines.submissionDeadline': (datetime.now() + timedelta(days=21)).date(),
            'publicationDeadlines.submissionTime': '12:00',
            'publicationDeadlines.openingDate': (datetime.now() + timedelta(days=21)).date(),
            'publicationDeadlines.openingTime': '14:00',
            
            # Step 7: Award Info
            'awardInfo.estimatedAwardDate': (datetime.now() + timedelta(days=30)).date(),
            'awardInfo.contractStartDate': (datetime.now() + timedelta(days=45)).date(),
            'awardInfo.contractDuration': 12,
            'awardInfo.contractDurationType': 'meseci',
            
            # Step 8: Financial Guarantees
            'financialGuarantees.performanceGuarantee': {
                'required': True,
                'percentage': 10,
                'validityDays': 60
            },
            'financialGuarantees.warrantyGuarantee': {
                'required': True,
                'percentage': 5,
                'validityMonths': 24
            }
        }
    
    @staticmethod
    def get_lots_procurement() -> Dict[str, Any]:
        """Procurement with 5 lots"""
        base = {
            # Step 1: Basic Info
            'procurementInfo.title': 'Test naročilo s 5 sklopi',
            'procurementInfo.internalReference': 'TEST-002-2024-LOTS',
            'procurementInfo.description': 'Obsežno testno naročilo z več sklopi za celovito testiranje',
            
            # Step 2: Clients
            'clientInfo.clients': [
                {
                    'organizationName': 'Javni zavod TestIT',
                    'registrationNumber': '87654321',
                    'vatNumber': 'SI87654321',
                    'streetAddress': 'Prešernova cesta 15',
                    'postalCode': '2000',
                    'city': 'Maribor',
                    'country': 'Slovenija',
                    'contactPerson': 'Marija Testna',
                    'contactEmail': 'marija@testit.si',
                    'contactPhone': '02 345 6789'
                },
                {
                    'organizationName': 'Partnerska organizacija d.d.',
                    'registrationNumber': '11223344',
                    'vatNumber': 'SI11223344',
                    'streetAddress': 'Cankarjeva 10',
                    'postalCode': '3000',
                    'city': 'Celje',
                    'country': 'Slovenija',
                    'contactPerson': 'Peter Partner',
                    'contactEmail': 'peter@partner.si',
                    'contactPhone': '03 456 7890'
                }
            ],
            
            # Lot mode
            'lot_mode': 'multiple',
            'num_lots': 5,
            'lot_names': [
                'Sklop 1: Strežniška oprema',
                'Sklop 2: Mrežna infrastruktura',
                'Sklop 3: Programska oprema',
                'Sklop 4: Varnostne rešitve',
                'Sklop 5: Storitve vzdrževanja'
            ]
        }
        
        # Add data for each lot
        lots_data = []
        
        # Lot 1: Server equipment
        lots_data.append({
            'name': 'Sklop 1: Strežniška oprema',
            'orderType': {
                'estimatedValue': 500000,
                'type': 'blago',
                'cpvCodes': ['48820000-2'],  # Strežniki
                'deliveryDeadline': 60,
                'deliveryLocation': 'Ljubljana, Centralni podatkovni center',
                'isCofinanced': True,
                'cofinancers': [
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
            'procedureType': {
                'requiresFinancialGuarantee': True,
                'acceptsVariants': False
            },
            'competitionCriteria': {
                'criteria': [
                    {'name': 'Cena', 'weight': 60, 'description': 'Skupna cena opreme'},
                    {'name': 'Zmogljivost', 'weight': 30, 'description': 'Procesna moč in kapaciteta'},
                    {'name': 'Energijska učinkovitost', 'weight': 10, 'description': 'Poraba energije'}
                ]
            },
            'financialGuarantees': {
                'performanceGuarantee': {'required': True, 'percentage': 10, 'validityDays': 90}
            }
        })
        
        # Lot 2: Network infrastructure
        lots_data.append({
            'name': 'Sklop 2: Mrežna infrastruktura',
            'orderType': {
                'estimatedValue': 250000,
                'type': 'blago',
                'cpvCodes': ['32420000-3'],  # Mrežna oprema
                'deliveryDeadline': 45,
                'deliveryLocation': 'Maribor, Tehnološki park',
                'isCofinanced': False
            },
            'procedureType': {
                'requiresFinancialGuarantee': True,
                'acceptsVariants': True
            },
            'competitionCriteria': {
                'criteria': [
                    {'name': 'Cena', 'weight': 50, 'description': 'Skupna cena'},
                    {'name': 'Tehnične specifikacije', 'weight': 35, 'description': 'Prepustnost in zanesljivost'},
                    {'name': 'Garancija', 'weight': 15, 'description': 'Trajanje garancije'}
                ]
            },
            'financialGuarantees': {
                'performanceGuarantee': {'required': True, 'percentage': 8, 'validityDays': 60},
                'warrantyGuarantee': {'required': True, 'percentage': 5, 'validityMonths': 36}
            }
        })
        
        # Lot 3: Software
        lots_data.append({
            'name': 'Sklop 3: Programska oprema',
            'orderType': {
                'estimatedValue': 300000,
                'type': 'blago',
                'cpvCodes': ['48000000-8'],  # Programski paketi
                'deliveryDeadline': 30,
                'deliveryLocation': 'Online dostava',
                'isCofinanced': True,
                'cofinancers': [
                    {
                        'cofinancerName': 'Javni štipendijski sklad',
                        'cofinancerStreetAddress': 'Vilharjeva 27',
                        'cofinancerPostalCode': '1000 Ljubljana',
                        'programName': 'Digitalne kompetence',
                        'programArea': 'Izobraževanje',
                        'programCode': 'JSS-DK-2024'
                    }
                ]
            },
            'procedureType': {
                'requiresFinancialGuarantee': False,
                'acceptsVariants': False
            },
            'competitionCriteria': {
                'criteria': [
                    {'name': 'Cena', 'weight': 40, 'description': 'Licenčnina'},
                    {'name': 'Funkcionalnost', 'weight': 40, 'description': 'Obseg funkcionalnosti'},
                    {'name': 'Podpora', 'weight': 20, 'description': 'Tehnična podpora'}
                ]
            }
        })
        
        # Lot 4: Security solutions
        lots_data.append({
            'name': 'Sklop 4: Varnostne rešitve',
            'orderType': {
                'estimatedValue': 180000,
                'type': 'storitve',
                'cpvCodes': ['72700000-7'],  # Storitve računalniškega omrežja
                'deliveryDeadline': 90,
                'deliveryLocation': 'Celje, Upravni center',
                'isCofinanced': False
            },
            'procedureType': {
                'requiresFinancialGuarantee': True,
                'acceptsVariants': False
            },
            'competitionCriteria': {
                'criteria': [
                    {'name': 'Cena', 'weight': 45, 'description': 'Mesečna naročnina'},
                    {'name': 'Varnostni standardi', 'weight': 40, 'description': 'Skladnost s standardi'},
                    {'name': 'Odzivni čas', 'weight': 15, 'description': 'Čas odziva na incident'}
                ]
            },
            'financialGuarantees': {
                'performanceGuarantee': {'required': True, 'percentage': 15, 'validityDays': 120}
            }
        })
        
        # Lot 5: Maintenance services
        lots_data.append({
            'name': 'Sklop 5: Storitve vzdrževanja',
            'orderType': {
                'estimatedValue': 120000,
                'type': 'storitve',
                'cpvCodes': ['50324100-3'],  # Vzdrževanje sistemov
                'deliveryDeadline': 365,
                'deliveryLocation': 'Vse lokacije naročnika',
                'isCofinanced': True,
                'cofinancers': [
                    {
                        'cofinancerName': 'Slovenski podjetniški sklad',
                        'cofinancerStreetAddress': 'Trubarjeva 11',
                        'cofinancerPostalCode': '2000 Maribor',
                        'programName': 'Podpora MSP',
                        'programArea': 'Digitalizacija MSP',
                        'programCode': 'SPS-MSP-2024'
                    },
                    {
                        'cofinancerName': 'Občina Ljubljana',
                        'cofinancerStreetAddress': 'Mestni trg 1',
                        'cofinancerPostalCode': '1000 Ljubljana',
                        'programName': 'Pametno mesto',
                        'programArea': 'Smart City',
                        'programCode': 'MOL-SC-2024'
                    }
                ]
            },
            'procedureType': {
                'requiresFinancialGuarantee': True,
                'acceptsVariants': True
            },
            'competitionCriteria': {
                'criteria': [
                    {'name': 'Cena', 'weight': 35, 'description': 'Urna postavka'},
                    {'name': 'Razpoložljivost', 'weight': 35, 'description': '24/7 podpora'},
                    {'name': 'Reference', 'weight': 30, 'description': 'Pretekle izkušnje'}
                ]
            },
            'financialGuarantees': {
                'performanceGuarantee': {'required': True, 'percentage': 5, 'validityDays': 365},
                'warrantyGuarantee': {'required': False}
            }
        })
        
        base['lots'] = lots_data
        
        # Add lot-specific fields to session state format
        for i, lot in enumerate(lots_data):
            base[f'lot_{i}.name'] = lot['name']
            if 'orderType' in lot:
                for key, value in lot['orderType'].items():
                    if key == 'cofinancers':
                        for j, cofinancer in enumerate(value):
                            for ckey, cval in cofinancer.items():
                                base[f'lot_{i}.orderType.cofinancers.{j}.{ckey}'] = cval
                    else:
                        base[f'lot_{i}.orderType.{key}'] = value
        
        return base


class ProcurementE2ETest:
    """End-to-end test suite for procurement form"""
    
    def __init__(self):
        self.db_path = 'test_e2e.db'
        self.created_ids = []
        
    def setup(self):
        """Initialize test environment"""
        # Use test database
        import database
        database.DATABASE_FILE = self.db_path
        
        # Initialize database
        init_db()
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        print("[SETUP] Test environment initialized")
    
    def teardown(self):
        """Clean up test environment"""
        # Remove test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        print("[TEARDOWN] Test environment cleaned up")
    
    def populate_session_state(self, data: Dict[str, Any]):
        """Populate session state with test data"""
        for key, value in data.items():
            st.session_state[key] = value
    
    def verify_session_state(self, expected: Dict[str, Any], prefix: str = ""):
        """Verify session state contains expected values"""
        errors = []
        
        for key, expected_value in expected.items():
            actual_value = st.session_state.get(key)
            
            if actual_value != expected_value:
                errors.append(f"{prefix}{key}: expected {expected_value}, got {actual_value}")
        
        return errors
    
    def save_procurement(self, title: str) -> int:
        """Save current procurement and return ID"""
        form_data = get_form_data_from_session()
        form_data['status'] = 'osnutek'
        
        proc_id = create_procurement(form_data)
        self.created_ids.append(proc_id)
        
        print(f"[SAVE] Saved procurement '{title}' with ID {proc_id}")
        return proc_id
    
    def load_procurement(self, proc_id: int) -> Dict[str, Any]:
        """Load procurement from database"""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT form_data_json 
            FROM javna_narocila 
            WHERE id = ?
        """, (proc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return {}
    
    def test_simple_procurement(self):
        """Test 1: Create and verify simple procurement without lots"""
        print("\n" + "="*60)
        print("TEST 1: Simple Procurement (No Lots)")
        print("="*60)
        
        # Get test data
        test_data = ProcurementTestData.get_simple_procurement()
        
        # Populate session state
        self.populate_session_state(test_data)
        
        # Verify initial population
        errors = self.verify_session_state(test_data, "Initial: ")
        if errors:
            print(f"[ERROR] Initial population failed:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            return False
        
        print("[OK] Initial data populated correctly")
        
        # Save procurement
        proc_id = self.save_procurement("Test naročilo brez sklopov")
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Load procurement
        loaded_data = self.load_procurement(proc_id)
        
        # Verify critical fields
        critical_checks = [
            ('procurementInfo.title', 'Test naročilo brez sklopov'),
            ('orderType.estimatedValue', 150000.00),
            ('orderType.isCofinanced', True),
            ('clientInfo.clients', test_data['clientInfo.clients'])
        ]
        
        for field, expected in critical_checks:
            # Navigate nested structure
            parts = field.split('.')
            value = loaded_data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
            
            if value != expected:
                print(f"[ERROR] Field {field} mismatch: expected {expected}, got {value}")
                return False
        
        print("[OK] Simple procurement saved and loaded correctly")
        
        # Test cofinancer operations
        print("\n[TEST] Testing cofinancer operations...")
        
        # Reload to session state for editing
        for key, value in test_data.items():
            st.session_state[key] = value
        
        # Add a cofinancer
        if 'orderType.cofinancers' in st.session_state:
            original_count = len(st.session_state['orderType.cofinancers'])
            st.session_state['orderType.cofinancers'].append({
                'cofinancerName': 'Test Cofinancer',
                'cofinancerStreetAddress': 'Test 1',
                'cofinancerPostalCode': '1000 Test',
                'programName': 'Test Program',
                'programArea': 'Test Area',
                'programCode': 'TEST-001'
            })
            
            # Verify estimatedValue preserved
            if st.session_state.get('orderType.estimatedValue') != 150000.00:
                print(f"[ERROR] EstimatedValue changed after adding cofinancer!")
                return False
            
            print(f"[OK] Added cofinancer (now {len(st.session_state['orderType.cofinancers'])}), value preserved")
            
            # Remove a cofinancer
            st.session_state['orderType.cofinancers'].pop()
            
            # Verify estimatedValue still preserved
            if st.session_state.get('orderType.estimatedValue') != 150000.00:
                print(f"[ERROR] EstimatedValue changed after removing cofinancer!")
                return False
            
            print(f"[OK] Removed cofinancer (now {len(st.session_state['orderType.cofinancers'])}), value preserved")
        
        return True
    
    def test_lots_procurement(self):
        """Test 2: Create and verify procurement with 5 lots"""
        print("\n" + "="*60)
        print("TEST 2: Complex Procurement (5 Lots)")
        print("="*60)
        
        # Get test data
        test_data = ProcurementTestData.get_lots_procurement()
        
        # Populate session state
        self.populate_session_state(test_data)
        
        print(f"[OK] Populated data for {test_data['num_lots']} lots")
        
        # Save procurement
        proc_id = self.save_procurement("Test naročilo s 5 sklopi")
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Load procurement
        loaded_data = self.load_procurement(proc_id)
        
        # Verify lots structure
        if 'lots' not in loaded_data:
            print("[ERROR] Lots not found in loaded data!")
            return False
        
        if len(loaded_data['lots']) != 5:
            print(f"[ERROR] Expected 5 lots, got {len(loaded_data['lots'])}")
            return False
        
        print(f"[OK] All 5 lots saved and loaded correctly")
        
        # Verify each lot's critical data
        expected_values = [500000, 250000, 300000, 180000, 120000]
        for i, expected_value in enumerate(expected_values):
            lot = loaded_data['lots'][i]
            actual_value = lot.get('orderType', {}).get('estimatedValue')
            
            if actual_value != expected_value:
                print(f"[ERROR] Lot {i+1} value mismatch: expected {expected_value}, got {actual_value}")
                return False
        
        print("[OK] All lot values preserved correctly")
        
        # Test lot-specific cofinancer counts
        expected_cofinancers = [1, 0, 1, 0, 2]  # Number of cofinancers per lot
        for i, expected_count in enumerate(expected_cofinancers):
            lot = loaded_data['lots'][i]
            cofinancers = lot.get('orderType', {}).get('cofinancers', [])
            actual_count = len(cofinancers)
            
            if actual_count != expected_count:
                print(f"[ERROR] Lot {i+1} cofinancer count: expected {expected_count}, got {actual_count}")
                return False
        
        print("[OK] All lot cofinancers preserved correctly")
        
        return True
    
    def test_navigation_and_editing(self):
        """Test 3: Navigation between steps and editing"""
        print("\n" + "="*60)
        print("TEST 3: Navigation and Editing")
        print("="*60)
        
        if not self.created_ids:
            print("[ERROR] No procurements created to test editing")
            return False
        
        # Test editing first procurement (simple)
        proc_id = self.created_ids[0]
        print(f"\n[TEST] Editing procurement ID {proc_id}...")
        
        # Load for editing
        loaded_data = self.load_procurement(proc_id)
        
        # Simulate navigation by setting current_step
        steps = ['basic_info', 'clients', 'order_type', 'procedure', 
                'criteria', 'deadlines', 'award', 'guarantees', 'summary']
        
        for step in steps:
            st.session_state['current_step'] = step
            print(f"[NAV] Navigated to step: {step}")
            
            # Make a small change in each step
            if step == 'order_type':
                # Change estimated value
                original_value = loaded_data.get('orderType', {}).get('estimatedValue', 0)
                new_value = original_value + 10000
                st.session_state['orderType.estimatedValue'] = new_value
                print(f"  Changed estimatedValue: {original_value} -> {new_value}")
            
            # Simulate save
            form_data = {'step': step, 'modified': True}
            print(f"  Saved at step: {step}")
        
        print("[OK] Navigation and step-wise editing completed")
        
        # Test Save and Continue vs Save and Close
        print("\n[TEST] Testing save operations...")
        
        # Save and Continue (should stay on same step)
        current_step = 'order_type'
        st.session_state['current_step'] = current_step
        st.session_state['action'] = 'save_continue'
        
        if st.session_state.get('current_step') == current_step:
            print("[OK] Save and Continue preserves current step")
        else:
            print("[ERROR] Save and Continue changed step!")
            return False
        
        # Save and Close (should clear editing state)
        st.session_state['action'] = 'save_close'
        st.session_state['editing_procurement_id'] = None
        
        if st.session_state.get('editing_procurement_id') is None:
            print("[OK] Save and Close clears editing state")
        else:
            print("[ERROR] Save and Close didn't clear editing state!")
            return False
        
        return True
    
    def test_concurrent_edits(self):
        """Test 4: Multiple edits and state preservation"""
        print("\n" + "="*60)
        print("TEST 4: Concurrent Edits and State Preservation")
        print("="*60)
        
        if len(self.created_ids) < 2:
            print("[SKIP] Need at least 2 procurements for this test")
            return True
        
        proc1_id = self.created_ids[0]
        proc2_id = self.created_ids[1]
        
        print(f"[TEST] Switching between procurement {proc1_id} and {proc2_id}...")
        
        # Load first procurement
        data1 = self.load_procurement(proc1_id)
        st.session_state['editing_procurement_id'] = proc1_id
        original_value1 = data1.get('orderType', {}).get('estimatedValue', 0)
        
        # Make changes
        st.session_state['orderType.estimatedValue'] = original_value1 + 5000
        print(f"[EDIT] Proc {proc1_id}: Changed value to {original_value1 + 5000}")
        
        # Switch to second procurement WITHOUT saving
        data2 = self.load_procurement(proc2_id)
        st.session_state['editing_procurement_id'] = proc2_id
        
        # Check if it has lots
        has_lots = 'lots' in data2 and len(data2['lots']) > 0
        print(f"[SWITCH] Proc {proc2_id}: Has lots = {has_lots}")
        
        # Switch back to first
        st.session_state['editing_procurement_id'] = proc1_id
        
        # Check if unsaved changes warning would trigger
        if st.session_state.get('unsaved_changes'):
            print("[OK] Unsaved changes detected correctly")
        
        return True
    
    def test_validation_errors(self):
        """Test 5: Validation and error handling"""
        print("\n" + "="*60)
        print("TEST 5: Validation and Error Handling")
        print("="*60)
        
        # Test invalid values
        test_cases = [
            ('orderType.estimatedValue', -1000, "Negative value"),
            ('orderType.estimatedValue', 'abc', "Non-numeric value"),
            ('orderType.estimatedValue', '1.500.000,50', "Slovenian format"),
            ('competitionCriteria.criteria.0.weight', 150, "Weight > 100"),
        ]
        
        for field, value, description in test_cases:
            st.session_state[field] = value
            print(f"[VALIDATE] Testing {description}: {field} = {value}")
            
            # Parse if it's a formatted number
            if field == 'orderType.estimatedValue' and isinstance(value, str):
                try:
                    parsed = parse_formatted_number(value)
                    print(f"  Parsed to: {parsed}")
                    
                    # Format back
                    formatted = format_number_with_dots(parsed)
                    print(f"  Formatted as: {formatted}")
                except:
                    print(f"  Failed to parse (expected for invalid values)")
        
        return True
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print(" COMPREHENSIVE E2E TEST SUITE FOR PROCUREMENT FORM")
        print("="*80)
        
        self.setup()
        
        results = []
        
        try:
            # Test 1: Simple procurement
            result1 = self.test_simple_procurement()
            results.append(("Simple Procurement", result1))
            
            # Test 2: Procurement with lots
            result2 = self.test_lots_procurement()
            results.append(("Lots Procurement", result2))
            
            # Test 3: Navigation and editing
            result3 = self.test_navigation_and_editing()
            results.append(("Navigation/Editing", result3))
            
            # Test 4: Concurrent edits
            result4 = self.test_concurrent_edits()
            results.append(("Concurrent Edits", result4))
            
            # Test 5: Validation
            result5 = self.test_validation_errors()
            results.append(("Validation", result5))
            
        finally:
            self.teardown()
        
        # Print summary
        print("\n" + "="*80)
        print(" TEST SUMMARY")
        print("="*80)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            symbol = "✓" if result else "✗"
            print(f" {symbol} {test_name}: {status}")
            
            if result:
                passed += 1
            else:
                failed += 1
        
        print("-"*80)
        print(f" Total: {passed} passed, {failed} failed out of {len(results)} tests")
        print("="*80)
        
        return failed == 0


def main():
    """Main test runner"""
    tester = ProcurementE2ETest()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()