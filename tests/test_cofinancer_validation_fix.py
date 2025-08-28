"""
Test cofinancer validation with proper key prefixes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager

def test_cofinancer_validation_general_mode():
    """Test cofinancer validation when in general mode (lot_mode='none')"""
    
    # Create mock schema
    schema = {
        'properties': {
            'orderType': {
                'properties': {
                    'isCofinanced': {'type': 'boolean'},
                    'cofinancers': {'type': 'array'}
                }
            }
        }
    }
    
    # Test case 1: General mode with cofinancer data
    print("Test 1: General mode with proper cofinancer data")
    session_state = {
        'lot_mode': 'none',
        'current_step': 'general_step_5',
        'general.orderType.estimatedValue': 100000,
        'general.orderType.isCofinanced': True,
        'general.orderType.cofinancerCount': 1,
        'general.orderType.cofinancers.0.name': 'EU Kohezijski sklad',
        'general.orderType.cofinancers.0.cofinancerName': 'EU Kohezijski sklad',
        'general.orderType.cofinancers.0.cofinancerStreetAddress': 'Dunajska 58',
        'general.orderType.cofinancers.0.cofinancerPostalCode': '1000 Ljubljana',
        'general.orderType.cofinancers.0.programName': 'Operativni program 2021-2027'
    }
    
    validator = ValidationManager(schema, session_state)
    is_valid, errors = validator.validate_order_type()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    assert is_valid, f"Should be valid but got errors: {errors}"
    print("  ✓ PASSED\n")
    
    # Test case 2: Missing cofinancer data
    print("Test 2: General mode with missing cofinancer data")
    session_state2 = {
        'lot_mode': 'none',
        'current_step': 'general_step_5',
        'general.orderType.estimatedValue': 100000,
        'general.orderType.isCofinanced': True,
        'general.orderType.cofinancerCount': 0
    }
    
    validator2 = ValidationManager(schema, session_state2)
    is_valid2, errors2 = validator2.validate_order_type()
    print(f"  Valid: {is_valid2}")
    print(f"  Errors: {errors2}")
    assert not is_valid2, "Should be invalid when cofinanced but no cofinancers"
    assert any('sofinancer' in e.lower() for e in errors2), "Should have cofinancer error"
    print("  ✓ PASSED\n")
    
    # Test case 3: Not cofinanced
    print("Test 3: General mode not cofinanced")
    session_state3 = {
        'lot_mode': 'none', 
        'current_step': 'general_step_5',
        'general.orderType.estimatedValue': 100000,
        'general.orderType.isCofinanced': False
    }
    
    validator3 = ValidationManager(schema, session_state3)
    is_valid3, errors3 = validator3.validate_order_type()
    print(f"  Valid: {is_valid3}")
    print(f"  Errors: {errors3}")
    assert is_valid3, f"Should be valid when not cofinanced: {errors3}"
    print("  ✓ PASSED\n")
    
    # Test case 4: Cofinancer with incomplete data
    print("Test 4: General mode with incomplete cofinancer data")
    session_state4 = {
        'lot_mode': 'none',
        'current_step': 'general_step_5',
        'general.orderType.estimatedValue': 100000,
        'general.orderType.isCofinanced': True,
        'general.orderType.cofinancerCount': 1,
        'general.orderType.cofinancers.0.cofinancerName': 'EU Kohezijski sklad',
        # Missing street, postal code and program
    }
    
    validator4 = ValidationManager(schema, session_state4)
    is_valid4, errors4 = validator4.validate_order_type()
    print(f"  Valid: {is_valid4}")
    print(f"  Errors: {errors4}")
    assert not is_valid4, "Should be invalid with incomplete cofinancer"
    assert any('naslov' in e.lower() for e in errors4), "Should mention missing address"
    assert any('poštno' in e.lower() for e in errors4), "Should mention missing postal code"
    assert any('program' in e.lower() for e in errors4), "Should mention missing program"
    print("  ✓ PASSED\n")

if __name__ == '__main__':
    print("Testing cofinancer validation with fixed key prefixes...")
    print("=" * 60)
    test_cofinancer_validation_general_mode()
    print("=" * 60)
    print("All tests passed! ✓")