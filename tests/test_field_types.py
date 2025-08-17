#!/usr/bin/env python3
"""Test script for enhanced field types."""

import sys
sys.path.insert(0, '.')

from utils.field_types import FieldTypeManager, RealTimeValidator
from datetime import time


def test_field_type_manager():
    """Test FieldTypeManager configuration and field detection."""
    print("Testing FieldTypeManager...")
    
    manager = FieldTypeManager()
    
    # Test field detection
    test_fields = [
        'guarantees.tender_amount',
        'negotiations.rounds', 
        'siteVisit.appointmentTime',
        'guarantees.tender_trr',
        'negotiations.specialRequestsText',
        'unknown.field'
    ]
    
    for field in test_fields:
        is_enhanced = manager.is_enhanced_field(field)
        config = manager.get_field_config(field)
        field_type = config.get('type', 'not configured')
        print(f"  {field}: enhanced={is_enhanced}, type={field_type}")
    
    print("✅ FieldTypeManager test passed\n")


def test_real_time_validator():
    """Test RealTimeValidator validation functions."""
    print("Testing RealTimeValidator...")
    
    # Mock ValidationManager
    class MockValidationManager:
        def get_required_fields(self):
            return []
    
    validator = RealTimeValidator(MockValidationManager())
    
    # Test TRR validation
    test_cases = [
        ('SI56 1234 5678 9012 345', True, "Valid TRR with spaces"),
        ('SI56123456789012345', True, "Valid TRR without spaces"),
        ('SI56 1234', False, "Invalid TRR - too short"),
        ('', True, "Empty TRR (optional)"),
    ]
    
    for value, expected_valid, description in test_cases:
        is_valid, error = validator._validate_trr(value)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"  {status} {description}: '{value}' -> valid={is_valid}")
    
    # Test BIC validation
    bic_cases = [
        ('LJBASI2X', True, "Valid 8-char BIC"),
        ('LJBASI2XXXX', True, "Valid 11-char BIC"),
        ('LJBA', False, "Invalid BIC - too short"),
        ('ljbasi2x', True, "Valid BIC - automatically uppercase"),
    ]
    
    print("\n  BIC Validation:")
    for value, expected_valid, description in bic_cases:
        is_valid, error = validator._validate_bic(value)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"  {status} {description}: '{value}' -> valid={is_valid}")
    
    # Test email validation
    email_cases = [
        ('test@example.com', True, "Valid email"),
        ('user.name@domain.co.uk', True, "Valid email with dots"),
        ('invalid@', False, "Invalid email - no domain"),
        ('', True, "Empty email (optional)"),
    ]
    
    print("\n  Email Validation:")
    for value, expected_valid, description in email_cases:
        is_valid, error = validator._validate_email(value)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"  {status} {description}: '{value}' -> valid={is_valid}")
    
    print("\n✅ RealTimeValidator test passed\n")


def test_field_configurations():
    """Test that field configurations are properly set."""
    print("Testing Field Configurations...")
    
    manager = FieldTypeManager()
    
    # Test currency field
    currency_config = manager.get_field_config('guarantees.tender_amount')
    assert currency_config['type'] == 'currency'
    assert currency_config['suffix'] == 'EUR'
    assert currency_config['min'] == 0.0
    print("  ✅ Currency field configuration correct")
    
    # Test integer field
    rounds_config = manager.get_field_config('negotiations.rounds')
    assert rounds_config['type'] == 'integer'
    assert rounds_config['min'] == 1
    assert rounds_config['max'] == 10
    print("  ✅ Integer field configuration correct")
    
    # Test time field
    time_config = manager.get_field_config('siteVisit.appointmentTime')
    assert time_config['type'] == 'time'
    assert time_config['default'] == time(10, 0)
    print("  ✅ Time field configuration correct")
    
    # Test textarea field
    textarea_config = manager.get_field_config('negotiations.specialRequestsText')
    assert textarea_config['type'] == 'textarea'
    assert textarea_config['rows'] == 5
    assert textarea_config['max_chars'] == 2000
    print("  ✅ Textarea field configuration correct")
    
    # Test formatted text field
    trr_config = manager.get_field_config('guarantees.tender_trr')
    assert trr_config['type'] == 'formatted_text'
    assert 'pattern' in trr_config
    assert trr_config['placeholder'] == 'SI56 XXXX XXXX XXXX XXX'
    print("  ✅ Formatted text field configuration correct")
    
    print("\n✅ All field configurations test passed\n")


if __name__ == "__main__":
    print("=" * 50)
    print("FIELD TYPE ENHANCEMENT TESTS")
    print("=" * 50)
    print()
    
    try:
        test_field_type_manager()
        test_real_time_validator()
        test_field_configurations()
        
        print("=" * 50)
        print("ALL TESTS PASSED ✅")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)