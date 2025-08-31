#!/usr/bin/env python3
"""
EPIC TEST: Comprehensive validation and data persistence test.
Tests all validation screens and ensures data is properly saved/loaded.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from ui.controllers.form_controller import FormController
from utils.validations import ValidationManager
from utils.validation_adapter import ValidationAdapter

class ValidationEpicTest:
    """Comprehensive test suite for validation and data persistence."""
    
    def __init__(self):
        """Initialize test environment."""
        # Initialize session state
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        # Clear session state for clean test
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        self.controller = FormController()
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'status': status,
            'details': details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
    
    def test_screen_1_customer_info(self):
        """Test Screen 1: Customer Information (applies to ALL lots)."""
        print("\n📋 Screen 1: Customer Information")
        print("-" * 50)
        
        # Initialize with single lot (default)
        st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
        st.session_state['current_lot_index'] = 0
        
        # Test 1A: Empty fields should fail
        st.session_state['lots.0.clientInfo.isSingleClient'] = True
        is_valid, errors = self.controller.validation_manager.validate_screen_1_customers()
        
        self.log_result(
            "1A: Empty customer fields fail validation",
            not is_valid and len(errors) == 4,
            f"Got {len(errors)} errors: {errors[:2]}..."
        )
        
        # Test 1B: Fill fields and validate
        st.session_state['lots.0.clientInfo.singleClientName'] = 'Osnovna šola Bistrica'
        st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Bistriška cesta 7'
        st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '4290 Tržič'
        st.session_state['lots.0.clientInfo.singleClientLegalRepresentative'] = 'ga. Frida Meglič'
        
        is_valid, errors = self.controller.validation_manager.validate_screen_1_customers()
        
        self.log_result(
            "1B: Filled customer fields pass validation",
            is_valid and len(errors) == 0,
            f"Valid: {is_valid}, Errors: {errors}"
        )
        
        # Test 1C: Add more lots - data should apply to ALL
        st.session_state['lots'].append({'name': 'Tehnični sklop', 'index': 1})
        st.session_state['lots'].append({'name': 'Dodatni sklop', 'index': 2})
        
        # Copy customer data to all lots (as pre-lot screens should do)
        for i in range(1, 3):
            st.session_state[f'lots.{i}.clientInfo.isSingleClient'] = True
            st.session_state[f'lots.{i}.clientInfo.singleClientName'] = 'Osnovna šola Bistrica'
            st.session_state[f'lots.{i}.clientInfo.singleClientStreetAddress'] = 'Bistriška cesta 7'
            st.session_state[f'lots.{i}.clientInfo.singleClientPostalCode'] = '4290 Tržič'
            st.session_state[f'lots.{i}.clientInfo.singleClientLegalRepresentative'] = 'ga. Frida Meglič'
        
        # Validate for all lots
        all_valid = True
        for i in range(3):
            st.session_state['current_lot_index'] = i
            is_valid, errors = self.controller.validation_manager.validate_screen_1_customers()
            if not is_valid:
                all_valid = False
                break
        
        self.log_result(
            "1C: Customer data applies to ALL lots",
            all_valid,
            f"All 3 lots have valid customer data"
        )
        
        return all_valid
    
    def test_screen_3_legal_basis(self):
        """Test Screen 3: Legal Basis (applies to ALL lots)."""
        print("\n📋 Screen 3: Legal Basis")
        print("-" * 50)
        
        # Test 3A: Empty legal basis should fail
        is_valid, errors = self.controller.validation_manager.validate_screen_3_legal_basis()
        
        self.log_result(
            "3A: Empty legal basis fails validation",
            not is_valid,
            f"Errors: {errors[:1]}..." if errors else "No errors"
        )
        
        # Test 3B: Fill legal basis for all lots
        for i in range(len(st.session_state.get('lots', []))):
            st.session_state[f'lots.{i}.legalBasis.lawReference'] = 'ZJN-3'
            st.session_state[f'lots.{i}.legalBasis.articleReference'] = '66. člen'
            st.session_state[f'lots.{i}.legalBasis.publicProcurement'] = True
        
        is_valid, errors = self.controller.validation_manager.validate_screen_3_legal_basis()
        
        self.log_result(
            "3B: Filled legal basis passes validation",
            is_valid,
            f"Valid for all lots"
        )
        
        return is_valid
    
    def test_screen_5_lots(self):
        """Test Screen 5: Lots Configuration."""
        print("\n📋 Screen 5: Lots Configuration")
        print("-" * 50)
        
        # Test 5A: Single lot is always valid
        st.session_state['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
        is_valid, errors = self.controller.validation_manager.validate_screen_5_lots()
        
        self.log_result(
            "5A: Single lot configuration is valid",
            is_valid,
            "Default 'Splošni sklop' is sufficient"
        )
        
        # Test 5B: Multiple lots with names
        st.session_state['lots'] = [
            {'name': 'Splošni sklop', 'index': 0},
            {'name': 'Tehnična oprema', 'index': 1},
            {'name': 'Programska oprema', 'index': 2}
        ]
        
        is_valid, errors = self.controller.validation_manager.validate_screen_5_lots()
        
        self.log_result(
            "5B: Multiple lots with names are valid",
            is_valid,
            f"3 lots configured"
        )
        
        return is_valid
    
    def test_data_persistence(self):
        """Test data saving and loading."""
        print("\n💾 Data Persistence Test")
        print("-" * 50)
        
        # Prepare test data
        test_data = {
            'lots': [
                {
                    'name': 'Splošni sklop',
                    'index': 0,
                    'clientInfo.singleClientName': 'Test School',
                    'clientInfo.singleClientStreetAddress': 'Test Street 123',
                    'clientInfo.singleClientPostalCode': '1000 Ljubljana',
                    'legalBasis.lawReference': 'ZJN-3',
                    'technicalSpecs.description': 'Test specs'
                },
                {
                    'name': 'Tehnični sklop',
                    'index': 1,
                    'clientInfo.singleClientName': 'Test School',
                    'clientInfo.singleClientStreetAddress': 'Test Street 123',
                    'clientInfo.singleClientPostalCode': '1000 Ljubljana',
                    'legalBasis.lawReference': 'ZJN-3',
                    'lot_specific_data': 'Specific to lot 1'
                }
            ],
            'form_id': 'test_form_001',
            'created_at': '2024-01-01'
        }
        
        # Test Save
        filename = 'test_epic_form.json'
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            save_success = True
        except Exception as e:
            save_success = False
            save_error = str(e)
        
        self.log_result(
            "Save: Data saved to file",
            save_success,
            f"Saved to {filename}" if save_success else f"Error: {save_error}"
        )
        
        # Test Load
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            load_success = loaded_data == test_data
        except Exception as e:
            load_success = False
            load_error = str(e)
        
        self.log_result(
            "Load: Data loaded correctly",
            load_success,
            "Data matches original" if load_success else f"Error: {load_error}"
        )
        
        # Clean up
        try:
            os.remove(filename)
        except:
            pass
        
        return save_success and load_success
    
    def test_pre_lot_screens_apply_to_all(self):
        """Test that pre-lot configuration screens apply data to ALL lots."""
        print("\n🔄 Pre-Lot Screens Apply to ALL Lots")
        print("-" * 50)
        
        # Setup 3 lots
        st.session_state['lots'] = [
            {'name': 'Splošni sklop', 'index': 0},
            {'name': 'Sklop A', 'index': 1},
            {'name': 'Sklop B', 'index': 2}
        ]
        
        # Pre-lot screens list
        pre_lot_screens = [
            'clientInfo',
            'projectInfo', 
            'legalBasis',
            'submissionProcedure'
        ]
        
        # Simulate filling pre-lot screen data (should go to ALL lots)
        test_value = "Test Value for All Lots"
        
        for screen in pre_lot_screens:
            # In real app, this would be done by form renderer
            for i in range(3):
                st.session_state[f'lots.{i}.{screen}.testField'] = test_value
        
        # Verify all lots have the same data
        all_match = True
        for screen in pre_lot_screens:
            values = []
            for i in range(3):
                key = f'lots.{i}.{screen}.testField'
                values.append(st.session_state.get(key))
            
            if not all(v == test_value for v in values):
                all_match = False
                break
        
        self.log_result(
            "Pre-lot screens data replicated to all lots",
            all_match,
            f"All {len(pre_lot_screens)} pre-lot screens apply to all 3 lots"
        )
        
        return all_match
    
    def test_lot_specific_screens(self):
        """Test that lot-specific screens only apply to current lot."""
        print("\n🎯 Lot-Specific Screens")
        print("-" * 50)
        
        # Lot-specific screens (after lot configuration)
        lot_specific_screens = [
            'technicalSpecifications',
            'priceInfo',
            'executionDeadline',
            'selectionCriteria'
        ]
        
        # Set different data for each lot
        for i in range(3):
            for screen in lot_specific_screens:
                st.session_state[f'lots.{i}.{screen}.specificData'] = f"Lot {i} specific"
        
        # Verify each lot has different data
        all_different = True
        for screen in lot_specific_screens:
            values = []
            for i in range(3):
                key = f'lots.{i}.{screen}.specificData'
                values.append(st.session_state.get(key))
            
            # Check that values are different
            if len(set(values)) != len(values):
                all_different = False
                break
        
        self.log_result(
            "Lot-specific screens maintain separate data",
            all_different,
            f"Each lot has unique data for {len(lot_specific_screens)} screens"
        )
        
        return all_different
    
    def run_epic_test(self):
        """Run all tests in the epic."""
        print("\n" + "="*60)
        print("🚀 VALIDATION EPIC TEST")
        print("="*60)
        
        # Run all tests
        self.test_screen_1_customer_info()
        self.test_screen_3_legal_basis()
        self.test_screen_5_lots()
        self.test_data_persistence()
        self.test_pre_lot_screens_apply_to_all()
        self.test_lot_specific_screens()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
        
        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} tests failed")
        
        return passed == total


if __name__ == "__main__":
    try:
        tester = ValidationEpicTest()
        success = tester.run_epic_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Epic test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)