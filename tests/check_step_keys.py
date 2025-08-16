#!/usr/bin/env python3
"""Check what step keys are used for step 13."""

import sys
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

from config import get_dynamic_form_steps

# Mock session state
class MockSessionState:
    def __init__(self):
        self.data = {
            'lotsInfo.hasLots': False,  # No lots
            'lots': []
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)

session_state = MockSessionState()

# Get dynamic form steps
form_steps = get_dynamic_form_steps(session_state)

print("Total steps:", len(form_steps))
print("\nAll steps:")
for i, step in enumerate(form_steps):
    print(f"  Step {i}: {step}")

print(f"\nStep 12 (13th step): {form_steps[12]}")
print(f"  Keys in step: {form_steps[12]}")

# Check if 'selectionCriteria' is in the keys
for key in form_steps[12]:
    if 'selectionCriteria' in key:
        print(f"  ✓ Found 'selectionCriteria' in key: {key}")
    else:
        print(f"  ✗ 'selectionCriteria' NOT in key: {key}")