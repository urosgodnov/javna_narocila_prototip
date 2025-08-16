#!/usr/bin/env python3
"""Test navigation validation logic."""

import sys
import os
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

# Simulate session state
class MockSessionState:
    def __init__(self):
        self.data = {
            'current_step': 12,  # Step 13 (0-indexed)
            'orderType.cpvCodes': '50700000-2 - Repair and maintenance services',
            'selectionCriteria.price': True,
            'selectionCriteria.socialCriteria': False,
            'selectionCriteria_validation': False,  # Validation failed
            'selectionCriteria_validation_override': False,
            'step_12_validation_enabled': True
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)

# Mock st.session_state
st_session_state = MockSessionState()

# Test the validation check
step_keys = ["selectionCriteria"]
for key in step_keys:
    print(f"Checking key: {key}")
    print(f"  'selectionCriteria' in key: {'selectionCriteria' in key}")
    
    if 'selectionCriteria' in key:
        validation_key = f"{key}_validation"
        print(f"  Validation key: {validation_key}")
        criteria_valid = st_session_state.get(validation_key, True)
        print(f"  Criteria valid: {criteria_valid}")
        
        override_key = f"{validation_key}_override"
        is_overridden = st_session_state.get(override_key, False)
        print(f"  Override enabled: {is_overridden}")
        
        if not criteria_valid and not is_overridden:
            print("  ❌ VALIDATION SHOULD BLOCK NAVIGATION")
            
            # Check CPV codes
            cpv_key = 'orderType.cpvCodes'
            cpv_codes_raw = st_session_state.get(cpv_key, '')
            print(f"  CPV codes raw: {cpv_codes_raw}")
            
            if cpv_codes_raw:
                cpv_codes = []
                if isinstance(cpv_codes_raw, str):
                    for code in cpv_codes_raw.split(','):
                        code = code.strip()
                        if ' - ' in code:
                            code = code.split(' - ')[0].strip()
                        if code:
                            cpv_codes.append(code)
                print(f"  Parsed CPV codes: {cpv_codes}")
                
                # Check social criteria
                social_key = f"{key}.socialCriteria"
                social_selected = st_session_state.get(social_key, False)
                print(f"  Social criteria key: {social_key}")
                print(f"  Social criteria selected: {social_selected}")
                
                if not social_selected:
                    print("  ❌ SOCIAL CRITERIA NOT SELECTED - SHOULD SHOW ERROR")