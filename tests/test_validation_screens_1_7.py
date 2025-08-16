#!/usr/bin/env python3
"""
Test script for Story 001: Validation for Screens 1-7
Tests the new validation methods in ValidationManager
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager
from typing import Dict, Any

def create_test_session_state() -> Dict[str, Any]:
    """Create a mock session state for testing"""
    return {}

def test_screen_1_single_customer():
    """Test Screen 1: Single customer validation"""
    print("\n=== Testing Screen 1: Single Customer ===")
    
    # Test 1: Missing all fields
    validator = ValidationManager()
    validator.session_state = {
        'clientInfo.multipleClients': 'ne'
    }
    
    is_valid, errors = validator.validate_screen_1_customers()
    print(f"Empty single customer - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail with empty customer data"
    assert len(errors) == 4, "Should have 4 errors for missing fields (including legal representative)"
    
    # Test 2: Complete single customer
    validator.session_state = {
        'clientInfo.multipleClients': 'ne',
        'clientInfo.singleClientName': 'Test Company',
        'clientInfo.singleClientAddress': 'Test Address 123',
        'clientInfo.singleClientType': 'public',
        'clientInfo.singleClientLegalRepresentative': 'Janez Novak'
    }
    
    is_valid, errors = validator.validate_screen_1_customers()
    print(f"\nComplete single customer - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass with complete customer data"
    assert len(errors) == 0, "Should have no errors"
    
    print("✅ Screen 1 single customer tests passed")

def test_screen_1_multiple_customers():
    """Test Screen 1: Multiple customers validation"""
    print("\n=== Testing Screen 1: Multiple Customers ===")
    
    # Test 1: Only one customer when multiple selected
    validator = ValidationManager()
    validator.session_state = {
        'clientInfo.multipleClients': 'da',
        'clientInfo.client1Name': 'Company 1',
        'clientInfo.client1Address': 'Address 1',
        'clientInfo.client1Type': 'public',
        'clientInfo.client1LegalRepresentative': 'Janez Novak'
        # Missing second client
    }
    
    # Need to test through validate_step to trigger _validate_multiple_entries
    is_valid, errors = validator.validate_step(['clientInfo'], step_number=1)
    print(f"One customer when multiple required - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail with only one customer"
    assert any('najmanj 2' in error for error in errors), "Should require minimum 2 customers"
    
    # Test 2: Two complete customers  
    validator.session_state = {
        'clientInfo.multipleClients': 'da',
        'clientInfo.client1Name': 'Company 1',
        'clientInfo.client1Address': 'Address 1',
        'clientInfo.client1Type': 'public',
        'clientInfo.client1LegalRepresentative': 'Marko Novak',
        'clientInfo.client2Name': 'Company 2',
        'clientInfo.client2Address': 'Address 2',
        'clientInfo.client2Type': 'private',
        'clientInfo.client2LegalRepresentative': 'Ana Kovač'
    }
    
    is_valid, errors = validator.validate_step(['clientInfo'], step_number=1)
    print(f"\nTwo complete customers - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass with two complete customers"
    
    print("✅ Screen 1 multiple customers tests passed")

def test_screen_1_logo_upload():
    """Test Screen 1: Logo upload validation"""
    print("\n=== Testing Screen 1: Logo Upload ===")
    
    # Test: Logo option selected but no file
    validator = ValidationManager()
    validator.session_state = {
        'clientInfo.multipleClients': 'ne',
        'clientInfo.singleClientName': 'Test Company',
        'clientInfo.singleClientAddress': 'Test Address',
        'clientInfo.singleClientType': 'public',
        'clientInfo.singleClientLegalRepresentative': 'Peter Kranjc',
        'clientInfo.wantsLogo': True
    }
    
    is_valid, errors = validator.validate_screen_1_customers()
    print(f"Logo required but missing - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail without logo file"
    assert any('logotip' in error.lower() for error in errors), "Should mention logo"
    
    print("✅ Screen 1 logo upload tests passed")

def test_screen_3_legal_basis():
    """Test Screen 3: Legal basis validation"""
    print("\n=== Testing Screen 3: Legal Basis ===")
    
    # Test 1: Additional basis selected but no entries
    validator = ValidationManager()
    validator.session_state = {
        'legalBasis.additionalBasis': 'da'
    }
    
    is_valid, errors = validator.validate_screen_3_legal_basis()
    print(f"Additional basis without entries - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail without legal basis entries"
    
    # Test 2: Additional basis with one entry
    validator.session_state = {
        'legalBasis.additionalBasis': 'da',
        'legalBasis.basis_1': 'Legal basis text here'
    }
    
    is_valid, errors = validator.validate_screen_3_legal_basis()
    print(f"\nAdditional basis with entry - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass with at least one basis"
    
    # Test 3: No additional basis selected
    validator.session_state = {
        'legalBasis.additionalBasis': 'ne'
    }
    
    is_valid, errors = validator.validate_screen_3_legal_basis()
    print(f"\nNo additional basis - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass when additional basis not selected"
    
    print("✅ Screen 3 legal basis tests passed")

def test_screen_5_lots():
    """Test Screen 5: Lot division validation"""
    print("\n=== Testing Screen 5: Lot Division ===")
    
    # Test 1: Lots selected but count < 2
    validator = ValidationManager()
    validator.session_state = {
        'lotInfo.isLotDivided': 'da',
        'lotInfo.lotCount': 1
    }
    
    is_valid, errors = validator.validate_screen_5_lots()
    print(f"One lot when divided - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail with less than 2 lots"
    
    # Test 2: Two lots but incomplete data
    validator.session_state = {
        'lotInfo.isLotDivided': 'da',
        'lotInfo.lotCount': 2,
        'lot_1_name': 'Lot 1',
        'lot_1_description': 'Description 1',
        'lot_1_cpv': '12345678-9',
        'lot_1_value': 10000,
        'lot_2_name': 'Lot 2'  # Missing other fields
    }
    
    is_valid, errors = validator.validate_screen_5_lots()
    print(f"\nIncomplete lot data - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail with incomplete lot data"
    
    # Test 3: Two complete lots
    validator.session_state = {
        'lotInfo.isLotDivided': 'da',
        'lotInfo.lotCount': 2,
        'lot_1_name': 'Lot 1',
        'lot_1_description': 'Description 1',
        'lot_1_cpv': '12345678-9',
        'lot_1_value': 10000,
        'lot_2_name': 'Lot 2',
        'lot_2_description': 'Description 2',
        'lot_2_cpv': '98765432-1',
        'lot_2_value': 20000
    }
    
    is_valid, errors = validator.validate_screen_5_lots()
    print(f"\nTwo complete lots - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass with complete lot data"
    
    print("✅ Screen 5 lot division tests passed")

def test_screen_7_technical_specs():
    """Test Screen 7: Technical specifications validation"""
    print("\n=== Testing Screen 7: Technical Specifications ===")
    
    # Test 1: Field not answered
    validator = ValidationManager()
    validator.session_state = {}
    
    is_valid, errors = validator.validate_screen_7_technical_specs()
    print(f"No answer - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail without answer"
    
    # Test 2: Has specs but no documents
    validator.session_state = {
        'technicalSpecs.hasExisting': 'da',
        'technicalSpecs.documentCount': 0
    }
    
    is_valid, errors = validator.validate_screen_7_technical_specs()
    print(f"\nHas specs but no docs - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail without documents"
    assert any('dokument' in error.lower() for error in errors), "Should mention document"
    
    # Test 3: Has specs with documents
    validator.session_state = {
        'technicalSpecs.hasExisting': 'da',
        'technicalSpecs.documentCount': 2
    }
    
    is_valid, errors = validator.validate_screen_7_technical_specs()
    print(f"\nHas specs with docs - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass with documents"
    
    # Test 4: No existing specs
    validator.session_state = {
        'technicalSpecs.hasExisting': 'ne'
    }
    
    is_valid, errors = validator.validate_screen_7_technical_specs()
    print(f"\nNo existing specs - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert is_valid, "Should pass when no specs exist"
    
    print("✅ Screen 7 technical specs tests passed")

def test_validate_step_integration():
    """Test integration with validate_step method"""
    print("\n=== Testing validate_step Integration ===")
    
    # Test Screen 1 through validate_step
    validator = ValidationManager()
    validator.session_state = {
        'clientInfo.multipleClients': 'ne',
        'current_step': 1
    }
    
    is_valid, errors = validator.validate_step(['clientInfo'], step_number=1)
    print(f"Screen 1 via validate_step - Valid: {is_valid}")
    print(f"Errors: {errors[:2]}...")  # Show first 2 errors
    assert not is_valid, "Should fail with incomplete customer data"
    
    # Test Screen 5 through validate_step
    validator.session_state = {
        'lotInfo.isLotDivided': 'da',
        'lotInfo.lotCount': 1,
        'current_step': 5
    }
    
    is_valid, errors = validator.validate_step(['lotInfo'], step_number=5)
    print(f"\nScreen 5 via validate_step - Valid: {is_valid}")
    print(f"Errors: {errors}")
    assert not is_valid, "Should fail with only 1 lot"
    
    print("✅ Integration tests passed")

def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("VALIDATION TESTS FOR SCREENS 1-7")
    print("=" * 60)
    
    try:
        test_screen_1_single_customer()
        test_screen_1_multiple_customers()
        test_screen_1_logo_upload()
        test_screen_3_legal_basis()
        test_screen_5_lots()
        test_screen_7_technical_specs()
        test_validate_step_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)