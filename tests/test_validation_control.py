#!/usr/bin/env python3
"""
Test script for validation control feature (Stories 22.1-22.3)
Run with: python3 tests/test_validation_control.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validation_control import should_validate
import streamlit as st

def test_validation_logic():
    """Test the validation control logic"""
    print("=" * 60)
    print("TESTING VALIDATION CONTROL (Epic 22)")
    print("=" * 60)
    
    # Initialize mock session state
    if 'validation_disabled' not in st.session_state:
        st.session_state['validation_disabled'] = True
    
    print("\n1. Testing default state (master disabled, step disabled)")
    st.session_state['validation_disabled'] = True  # Master OFF (checked)
    st.session_state['step_0_validation_enabled'] = False  # Step OFF
    result = should_validate(0)
    print(f"   Master: Disabled (checked), Step: Disabled")
    print(f"   Should validate: {result}")
    assert result == False, "Should NOT validate when both disabled"
    print("   ✓ Correct: No validation")
    
    print("\n2. Testing master enabled (unchecked)")
    st.session_state['validation_disabled'] = False  # Master ON (unchecked)
    st.session_state['step_0_validation_enabled'] = False  # Step OFF
    result = should_validate(0)
    print(f"   Master: Enabled (unchecked), Step: Disabled")
    print(f"   Should validate: {result}")
    assert result == True, "Should validate when master enabled"
    print("   ✓ Correct: Validation active (global)")
    
    print("\n3. Testing step override of master")
    st.session_state['validation_disabled'] = True  # Master OFF (checked)
    st.session_state['step_0_validation_enabled'] = True  # Step ON
    result = should_validate(0)
    print(f"   Master: Disabled (checked), Step: Enabled")
    print(f"   Should validate: {result}")
    assert result == True, "Should validate when step overrides"
    print("   ✓ Correct: Step override works")
    
    print("\n4. Testing both enabled")
    st.session_state['validation_disabled'] = False  # Master ON (unchecked)
    st.session_state['step_0_validation_enabled'] = True  # Step ON
    result = should_validate(0)
    print(f"   Master: Enabled (unchecked), Step: Enabled")
    print(f"   Should validate: {result}")
    assert result == True, "Should validate when both enabled"
    print("   ✓ Correct: Validation active")
    
    print("\n5. Testing different steps independently")
    st.session_state['validation_disabled'] = True  # Master OFF
    st.session_state['step_0_validation_enabled'] = False
    st.session_state['step_1_validation_enabled'] = True
    st.session_state['step_2_validation_enabled'] = False
    
    print("   Master: Disabled (checked)")
    print(f"   Step 0: {should_validate(0)} (expected: False)")
    print(f"   Step 1: {should_validate(1)} (expected: True)")
    print(f"   Step 2: {should_validate(2)} (expected: False)")
    
    assert should_validate(0) == False
    assert should_validate(1) == True
    assert should_validate(2) == False
    print("   ✓ Correct: Independent step control works")


def test_ui_messages():
    """Test that UI messages are appropriate"""
    print("\n" + "=" * 60)
    print("TESTING UI MESSAGES")
    print("=" * 60)
    
    from utils.validation_control import get_validation_status_message
    
    # Test with validation active
    st.session_state['validation_disabled'] = False
    st.session_state['step_0_validation_enabled'] = False
    msg = get_validation_status_message(0)
    print(f"\n1. Validation active: {msg}")
    assert "aktivna" in msg.lower() or "active" in msg.lower()
    
    # Test with validation skipped
    st.session_state['validation_disabled'] = True
    st.session_state['step_0_validation_enabled'] = False
    msg = get_validation_status_message(0)
    print(f"2. Validation skipped: {msg}")
    assert "preskočena" in msg.lower() or "skipped" in msg.lower()


def test_logic_truth_table():
    """Complete truth table test"""
    print("\n" + "=" * 60)
    print("TRUTH TABLE TEST")
    print("=" * 60)
    print("\n| Master | Step | Result | Expected |")
    print("|--------|------|--------|----------|")
    
    test_cases = [
        (True, False, False),   # Both off = no validation
        (True, True, True),      # Step overrides master
        (False, False, True),    # Master on = validation
        (False, True, True),     # Both on = validation
    ]
    
    for master_disabled, step_enabled, expected in test_cases:
        st.session_state['validation_disabled'] = master_disabled
        st.session_state['step_0_validation_enabled'] = step_enabled
        result = should_validate(0)
        
        master_str = "OFF" if master_disabled else "ON "
        step_str = "ON " if step_enabled else "OFF"
        result_str = "YES" if result else "NO "
        expected_str = "YES" if expected else "NO "
        status = "✓" if result == expected else "✗"
        
        print(f"| {master_str}    | {step_str}  | {result_str}     | {expected_str}      | {status}")
        
        assert result == expected, f"Logic error: master={master_disabled}, step={step_enabled}"
    
    print("\n✅ All truth table tests passed!")


if __name__ == "__main__":
    try:
        test_validation_logic()
        test_ui_messages()
        test_logic_truth_table()
        
        print("\n" + "=" * 60)
        print("ALL VALIDATION CONTROL TESTS PASSED!")
        print("=" * 60)
        print("\nValidation Control System Summary:")
        print("- Master toggle: Checked = OFF (default)")
        print("- Per-step toggles: Unchecked = use master")
        print("- Logic: Validate if master OFF OR step ON")
        print("- All combinations work correctly")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)