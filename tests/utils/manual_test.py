#!/usr/bin/env python3
"""Manual test to verify validation logic."""

import sys
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

# Set up mock session state
class MockSessionState:
    def __init__(self):
        self.data = {
            'current_step': 12,
            'step_12_validation_enabled': True,
            'global_validation_enabled': False,
            'orderType.cpvCodes': '50700000-2 - Repair and maintenance',
            'selectionCriteria.price': True,
            'selectionCriteria.socialCriteria': False,
            'selectionCriteria_validation': False,
            'selectionCriteria_validation_override': False,
            'schema': {'properties': {}}
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data[key]

# Mock streamlit
class MockSt:
    session_state = MockSessionState()
    
    @staticmethod
    def error(msg):
        print(f"ERROR: {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"WARNING: {msg}")
    
    @staticmethod
    def info(msg):
        print(f"INFO: {msg}")

# Replace streamlit
import sys
sys.modules['streamlit'] = MockSt
st = MockSt

# Import after mocking
from app import validate_step, should_validate

print("=" * 60)
print("Testing validate_step function")
print("=" * 60)

# Test data
step_keys = ['selectionCriteria']
schema = {'properties': {}}

print(f"Step keys: {step_keys}")
print(f"CPV codes: {st.session_state.get('orderType.cpvCodes')}")
print(f"Price selected: {st.session_state.get('selectionCriteria.price')}")
print(f"Social criteria selected: {st.session_state.get('selectionCriteria.socialCriteria')}")
print()

# Test validation
result = validate_step(step_keys, schema)

print()
print(f"Validation result: {result}")
print()

if result:
    print("❌ PROBLEM: Validation returned True (allowing navigation)")
    print("   Expected: False (blocking navigation)")
else:
    print("✅ SUCCESS: Validation returned False (blocking navigation)")