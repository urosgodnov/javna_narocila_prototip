#!/usr/bin/env python3
"""Test validation logic for CPV criteria."""

import sys
import os
sys.path.insert(0, '/mnt/c/Programiranje/Python/javna_narocila_prototip')

# Mock Streamlit
class MockSt:
    class session_state:
        data = {
            'current_step': 12,  # Step 13 (0-indexed)
            'orderType.cpvCodes': '50700000-2 - Repair and maintenance services',
            'selectionCriteria.price': True,
            'selectionCriteria.socialCriteria': False,
            'step_12_validation_enabled': True,  # Validation enabled for step
            'global_validation_enabled': False,  # Global validation disabled
        }
        
        @classmethod
        def get(cls, key, default=None):
            return cls.data.get(key, default)
    
    @staticmethod
    def error(msg):
        print(f"ERROR: {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"WARNING: {msg}")
    
    @staticmethod
    def info(msg):
        print(f"INFO: {msg}")

# Replace streamlit import
import sys
sys.modules['streamlit'] = MockSt
st = MockSt

# Now import the functions
from utils.validations import validate_criteria_selection, check_cpv_requires_social_criteria

# Import the validate_step function (need to handle other dependencies)
def should_validate(step_number):
    """Check if validation should run for a given step."""
    # Check global validation toggle
    global_enabled = st.session_state.get("global_validation_enabled", True)
    
    # Check per-step validation override
    step_key = f"step_{step_number}_validation_enabled"
    step_override = st.session_state.get(step_key, None)
    
    # If step has specific override, use it
    if step_override is not None:
        return step_override
    
    # Otherwise use global setting
    return global_enabled

def get_text(key, **kwargs):
    """Mock localization function."""
    return f"[{key}]"

# Test the validation
print("=" * 60)
print("Testing validation logic for CPV 50700000-2")
print("=" * 60)

# Test 1: Check if should validate
current_step = 12
if should_validate(current_step):
    print(f"✓ Validation is enabled for step {current_step}")
else:
    print(f"✗ Validation is disabled for step {current_step}")

# Test 2: Check CPV requires social criteria
cpv_codes = ['50700000-2']
social_required = check_cpv_requires_social_criteria(cpv_codes)
if social_required:
    print(f"✓ CPV code {cpv_codes[0]} requires social criteria")
    print(f"  Required criteria: {social_required}")
else:
    print(f"✗ CPV code {cpv_codes[0]} does not require social criteria")

# Test 3: Validate criteria selection
selected_criteria = {
    'price': True,
    'socialCriteria': False,
}
validation_result = validate_criteria_selection(cpv_codes, selected_criteria)
print(f"\nValidation result: is_valid={validation_result.is_valid}")
if validation_result.messages:
    print("Validation messages:")
    for msg in validation_result.messages:
        print(f"  - {msg}")

# Test 4: Simulate what happens in validate_step
print("\n" + "=" * 60)
print("Simulating validate_step function")
print("=" * 60)

step_keys = ['selectionCriteria']
is_valid = True

# Check for selectionCriteria validation
for key in step_keys:
    print(f"Checking key: {key}")
    if 'selectionCriteria' in key:
        print("  → selectionCriteria found in key")
        
        # Get CPV codes from session state
        cpv_key = 'orderType.cpvCodes'
        cpv_codes_raw = st.session_state.get(cpv_key, '')
        print(f"  → CPV codes raw: {cpv_codes_raw}")
        
        if cpv_codes_raw:
            # Parse CPV codes
            cpv_codes = []
            if isinstance(cpv_codes_raw, str):
                for code in cpv_codes_raw.split(','):
                    code = code.strip()
                    if ' - ' in code:
                        code = code.split(' - ')[0].strip()
                    if code:
                        cpv_codes.append(code)
            print(f"  → Parsed CPV codes: {cpv_codes}")
            
            # Get selected criteria
            selected_criteria = {
                'price': st.session_state.get(f"{key}.price", False),
                'additionalReferences': st.session_state.get(f"{key}.additionalReferences", False),
                'additionalTechnicalRequirements': st.session_state.get(f"{key}.additionalTechnicalRequirements", False),
                'shorterDeadline': st.session_state.get(f"{key}.shorterDeadline", False),
                'longerWarranty': st.session_state.get(f"{key}.longerWarranty", False),
                'environmentalCriteria': st.session_state.get(f"{key}.environmentalCriteria", False),
                'socialCriteria': st.session_state.get(f"{key}.socialCriteria", False),
            }
            print(f"  → Selected criteria: {selected_criteria}")
            
            # Validate
            validation_result = validate_criteria_selection(cpv_codes, selected_criteria)
            print(f"  → Validation result: is_valid={validation_result.is_valid}")
            
            # Update validation state
            validation_key = f"{key}_validation"
            st.session_state.data[validation_key] = validation_result.is_valid
            print(f"  → Stored validation state in '{validation_key}': {validation_result.is_valid}")
            
            # Check if override is enabled
            override_key = f"{validation_key}_override"
            is_overridden = st.session_state.get(override_key, False)
            print(f"  → Override key '{override_key}': {is_overridden}")
            
            if not validation_result.is_valid and not is_overridden:
                print("  → VALIDATION FAILED - Should block navigation")
                # Show validation messages
                if validation_result.messages:
                    for message in validation_result.messages:
                        st.error(message)
                
                # Check specifically for social criteria requirement
                social_cpv = check_cpv_requires_social_criteria(cpv_codes)
                if social_cpv:
                    st.warning(f"CPV koda {', '.join(social_cpv.keys())} zahteva vključitev socialnih meril.")
                    st.info("Prosimo, označite 'Socialna merila' ali uporabite možnost 'Prezri opozorilo' za nadaljevanje.")
                
                is_valid = False

print(f"\n→ Final validation result: is_valid={is_valid}")
if not is_valid:
    print("✓ Navigation should be BLOCKED")
else:
    print("✗ Navigation would be ALLOWED")