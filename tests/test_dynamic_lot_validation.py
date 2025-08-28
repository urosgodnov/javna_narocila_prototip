"""
Test validation with dynamic lot numbers (lot_1, lot_2, lot_n)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager

def test_dynamic_lot_numbers():
    """Test validation with different lot numbers"""
    
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
    
    # Test lot_1 with double prefix
    print("Test 1: Lot 1 with double-prefixed keys")
    session_state = {
        'lot_mode': 'multiple',
        'current_step': 6,  # Test with integer step
        'current_lot_index': 1,
        'lot_1.lot_1_orderType.estimatedValue': 200000,
        'lot_1.lot_1_orderType.isCofinanced': True,
        'lot_1.lot_1_orderType.cofinancerCount': 1,
        'lot_1.lot_1_orderType.cofinancers': [{}],
        'lot_1.lot_1_orderType.cofinancers.0.cofinancerName': 'EU Funds',
        'lot_1.lot_1_orderType.cofinancers.0.cofinancerStreetAddress': 'Brussels Street 1',
        'lot_1.lot_1_orderType.cofinancers.0.cofinancerPostalCode': '1000 Brussels',
        'lot_1.lot_1_orderType.cofinancers.0.programName': 'Horizon Europe'
    }
    
    validator = ValidationManager(schema, session_state)
    is_valid, errors = validator.validate_order_type()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    assert is_valid, f"Should be valid for lot_1, but got errors: {errors}"
    print("  ✓ PASSED\n")
    
    # Test lot_2 with normal prefix
    print("Test 2: Lot 2 with normal-prefixed keys")
    session_state2 = {
        'lot_mode': 'multiple',
        'current_step': '7',  # Test with string step
        'current_lot_index': 2,
        'lot_2.orderType.estimatedValue': 300000,
        'lot_2.orderType.isCofinanced': True,
        'lot_2.orderType.cofinancerCount': 1,
        'lot_2.orderType.cofinancers': [{}],
        'lot_2.orderType.cofinancers.0.cofinancerName': 'World Bank',
        'lot_2.orderType.cofinancers.0.cofinancerStreetAddress': 'Pennsylvania Ave',
        'lot_2.orderType.cofinancers.0.cofinancerPostalCode': '20433 Washington',
        'lot_2.orderType.cofinancers.0.programName': 'Infrastructure Fund'
    }
    
    validator2 = ValidationManager(schema, session_state2)
    is_valid2, errors2 = validator2.validate_order_type()
    print(f"  Valid: {is_valid2}")
    print(f"  Errors: {errors2}")
    assert is_valid2, f"Should be valid for lot_2, but got errors: {errors2}"
    print("  ✓ PASSED\n")
    
    # Test lot_10 (double digit) with double prefix
    print("Test 3: Lot 10 with double-prefixed keys")
    session_state3 = {
        'lot_mode': 'multiple',
        'current_step': 'step_8',  # Test with string step containing 'step'
        'current_lot_index': 10,
        'lot_10.lot_10_orderType.estimatedValue': 500000,
        'lot_10.lot_10_orderType.isCofinanced': True,
        'lot_10.lot_10_orderType.cofinancers': [{}],
        'lot_10.lot_10_orderType.cofinancers.0.cofinancerName': 'EIB',
        'lot_10.lot_10_orderType.cofinancers.0.cofinancerStreetAddress': 'Luxembourg 98',
        'lot_10.lot_10_orderType.cofinancers.0.cofinancerPostalCode': '2950 Luxembourg',
        'lot_10.lot_10_orderType.cofinancers.0.programName': 'Green Deal'
    }
    
    validator3 = ValidationManager(schema, session_state3)
    is_valid3, errors3 = validator3.validate_order_type()
    print(f"  Valid: {is_valid3}")
    print(f"  Errors: {errors3}")
    assert is_valid3, f"Should be valid for lot_10, but got errors: {errors3}"
    print("  ✓ PASSED\n")
    
    # Test lot_0 (should still work)
    print("Test 4: Lot 0 with double-prefixed keys (backward compatibility)")
    session_state4 = {
        'lot_mode': 'single',
        'current_step': 6,
        'current_lot_index': 0,
        'lot_0.lot_0_orderType.estimatedValue': 150000,
        'lot_0.lot_0_orderType.isCofinanced': False
    }
    
    validator4 = ValidationManager(schema, session_state4)
    is_valid4, errors4 = validator4.validate_order_type()
    print(f"  Valid: {is_valid4}")
    print(f"  Errors: {errors4}")
    assert is_valid4, f"Should be valid for lot_0, but got errors: {errors4}"
    print("  ✓ PASSED\n")

if __name__ == '__main__':
    print("Testing validation with dynamic lot numbers...")
    print("=" * 60)
    test_dynamic_lot_numbers()
    print("=" * 60)
    print("All tests passed! ✓")