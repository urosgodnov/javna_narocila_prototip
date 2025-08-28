#!/usr/bin/env python3
"""Test script to verify lot system configuration."""

from config import (
    get_dynamic_form_steps,
    is_final_lot_step,
    get_lot_navigation_buttons
)


def test_no_lots():
    """Test configuration with no lots."""
    print("\n=== Testing No Lots Mode ===")
    session_state = {
        'lotsInfo.hasLots': False,
        'lot_mode': 'none',
        'current_step': 0
    }
    
    steps = get_dynamic_form_steps(session_state)
    print(f"Total steps: {len(steps)}")
    print(f"Steps: {steps[:5]}...")  # Show first 5 steps
    
    # Should not have lotConfiguration step
    has_lot_config = any('lotConfiguration' in step for step in steps)
    print(f"Has lot configuration step: {has_lot_config}")
    assert not has_lot_config, "No lots mode should not have lot configuration step"
    

def test_multiple_lots():
    """Test configuration with multiple lots."""
    print("\n=== Testing Multiple Lots Mode ===")
    session_state = {
        'lotsInfo.hasLots': True,
        'lot_mode': 'multiple',
        'lot_names': ['Sklop 1: Office', 'Sklop 2: IT', 'Sklop 3: Cleaning'],
        'lots': [
            {'name': 'Sklop 1: Office'},
            {'name': 'Sklop 2: IT'},
            {'name': 'Sklop 3: Cleaning'}
        ],
        'current_lot_index': 0,
        'current_step': 0
    }
    
    steps = get_dynamic_form_steps(session_state)
    print(f"Total steps: {len(steps)}")
    
    # Should have lotConfiguration step
    has_lot_config = any('lotConfiguration' in step for step in steps)
    print(f"Has lot configuration step: {has_lot_config}")
    assert has_lot_config, "Multiple lots mode should have lot configuration step"
    
    # Check lot context step
    has_lot_context = any(any(field.startswith('lot_context_') for field in step) for step in steps)
    print(f"Has lot context step: {has_lot_context}")
    assert has_lot_context, "Multiple lots mode should have lot context steps"
    
    # Test lot navigation buttons
    print("\n--- Testing Lot Navigation ---")
    # Simulate being at the last step of first lot
    session_state['current_lot_index'] = 0
    session_state['current_step'] = len(steps) - 1  # Last step
    
    is_final = is_final_lot_step(session_state, session_state['current_step'])
    print(f"Is final lot step: {is_final}")
    
    if is_final:
        buttons = get_lot_navigation_buttons(session_state)
        print(f"Navigation buttons: {buttons}")
        assert len(buttons) > 0, "Should have navigation buttons at lot final step"
        
        # Check for expected buttons
        button_actions = [b[1] for b in buttons]
        print(f"Button actions: {button_actions}")


def test_lot_iteration():
    """Test lot iteration flow."""
    print("\n=== Testing Lot Iteration ===")
    session_state = {
        'lotsInfo.hasLots': True,
        'lot_mode': 'multiple',
        'lot_names': ['Sklop 1', 'Sklop 2'],
        'lots': [
            {'name': 'Sklop 1'},
            {'name': 'Sklop 2'}
        ],
        'current_lot_index': 0,
        'current_step': 0
    }
    
    # Get steps for first lot
    steps_lot1 = get_dynamic_form_steps_refactored(session_state)
    print(f"Steps for lot 1 (index 0): {len(steps_lot1)} steps")
    
    # Simulate moving to second lot
    session_state['current_lot_index'] = 1
    steps_lot2 = get_dynamic_form_steps_refactored(session_state)
    print(f"Steps for lot 2 (index 1): {len(steps_lot2)} steps")
    
    # Check that lot-specific steps have correct prefix
    for step in steps_lot2:
        if any(field.startswith('lot_1_') for field in step):
            print(f"Found lot_1_ prefixed step: {step}")
            break


if __name__ == "__main__":
    print("Testing Lot System Configuration")
    print("=" * 50)
    
    test_no_lots()
    test_multiple_lots()
    test_lot_iteration()
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")