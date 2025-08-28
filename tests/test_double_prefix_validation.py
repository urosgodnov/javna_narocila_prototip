"""
Test validation with double-prefixed keys (lot_0.lot_0_orderType pattern)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import ValidationManager

def test_double_prefixed_cofinancer_validation():
    """Test validation when keys have double prefix like lot_0.lot_0_orderType"""
    
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
    
    # Test case 1: Double-prefixed keys with complete cofinancer data
    print("Test 1: Double-prefixed keys with complete cofinancer data")
    session_state = {
        'lot_mode': 'single',
        'current_step': '6',
        'current_lot_index': 0,
        # Double-prefixed keys as seen in logs
        'lot_0.lot_0_orderType.estimatedValue': 100000,
        'lot_0.lot_0_orderType.isCofinanced': True,
        'lot_0.lot_0_orderType.cofinancerCount': 1,
        'lot_0.lot_0_orderType.cofinancers': [{}],
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerName': 'Ministrstvo za zdravje',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerStreetAddress': 'Zdravstvena 17',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerPostalCode': '1000 Ljubljana',
        'lot_0.lot_0_orderType.cofinancers.0.programName': 'Skrajševanje časovnih vrst',
        'lot_0.lot_0_orderType.cofinancers.0.specialRequirements': 'Da ni korupcije.',
        'lot_0.lot_0_orderType.cofinancers.0.programArea': 'Skrajševanje časovnih vrst'
    }
    
    validator = ValidationManager(schema, session_state)
    is_valid, errors = validator.validate_order_type()
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    assert is_valid, f"Should be valid with complete double-prefixed cofinancer data, but got errors: {errors}"
    print("  ✓ PASSED\n")
    
    # Test case 2: Widget keys (as shown in logs)
    print("Test 2: Widget-prefixed keys with cofinancer data")
    session_state2 = {
        'lot_mode': 'single',
        'current_step': '6',
        'current_lot_index': 0,
        # Mix of widget and non-widget keys as in logs
        'widget_lot_0.lot_0_orderType.isCofinanced': True,
        'lot_0.lot_0_orderType.estimatedValue': 100000,
        'lot_0.lot_0_orderType.isCofinanced': True,
        'lot_0.lot_0_orderType.cofinancers': [{}],
        'widget_lot_0.lot_0_orderType.cofinancers.0.cofinancerName': 'Ministrstvo za zdravje',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerName': 'Ministrstvo za zdravje',
        'widget_lot_0.lot_0_orderType.cofinancers.0.cofinancerStreetAddress': 'Zdravstvena 17',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerStreetAddress': 'Zdravstvena 17',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerPostalCode': '1000 Ljubljana',
        'lot_0.lot_0_orderType.cofinancers.0.programName': 'Skrajševanje časovnih vrst',
        'widget_lot_0.lot_0_orderType.cofinancers.0.specialRequirements': 'Da ni korupcije.',
        'lot_0.lot_0_orderType.cofinancers.0.programArea': 'Skrajševanje časovnih vrst'
    }
    
    validator2 = ValidationManager(schema, session_state2)
    is_valid2, errors2 = validator2.validate_order_type()
    print(f"  Valid: {is_valid2}")
    print(f"  Errors: {errors2}")
    assert is_valid2, f"Should be valid with mixed widget/non-widget keys, but got errors: {errors2}"
    print("  ✓ PASSED\n")
    
    # Test case 3: Missing program name (required field)
    print("Test 3: Double-prefixed keys with missing program name")
    session_state3 = {
        'lot_mode': 'single',
        'current_step': '6',
        'current_lot_index': 0,
        'lot_0.lot_0_orderType.estimatedValue': 100000,
        'lot_0.lot_0_orderType.isCofinanced': True,
        'lot_0.lot_0_orderType.cofinancers': [{}],
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerName': 'Ministrstvo za zdravje',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerStreetAddress': 'Zdravstvena 17',
        'lot_0.lot_0_orderType.cofinancers.0.cofinancerPostalCode': '1000 Ljubljana',
        # Missing programName - should fail
    }
    
    validator3 = ValidationManager(schema, session_state3)
    is_valid3, errors3 = validator3.validate_order_type()
    print(f"  Valid: {is_valid3}")
    print(f"  Errors: {errors3}")
    assert not is_valid3, "Should be invalid when program name is missing"
    assert any('program' in e.lower() for e in errors3), f"Should mention missing program, got: {errors3}"
    print("  ✓ PASSED\n")

if __name__ == '__main__':
    print("Testing validation with double-prefixed keys...")
    print("=" * 60)
    test_double_prefixed_cofinancer_validation()
    print("=" * 60)
    print("All tests passed! ✓")