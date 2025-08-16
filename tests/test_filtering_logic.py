#!/usr/bin/env python3
"""
Test script to verify the array key extraction logic works correctly.
"""

def test_key_extraction():
    """Test the array key extraction logic"""
    
    # Test cases
    test_cases = [
        {
            "full_key": "orderType.mixedOrderComponents.0.type",
            "expected_parent": "orderType.mixedOrderComponents", 
            "expected_index": 0
        },
        {
            "full_key": "orderType.mixedOrderComponents.1.type",
            "expected_parent": "orderType.mixedOrderComponents",
            "expected_index": 1
        },
        {
            "full_key": "orderType.mixedOrderComponents.2.type", 
            "expected_parent": "orderType.mixedOrderComponents",
            "expected_index": 2
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        full_key = test_case["full_key"]
        expected_parent = test_case["expected_parent"]
        expected_index = test_case["expected_index"]
        
        # Apply the logic from form_renderer.py
        key_parts = full_key.split('.')
        if len(key_parts) >= 3 and key_parts[-1] == "type" and key_parts[-2].isdigit():
            parent_array_key = '.'.join(key_parts[:-2])  # Remove index and "type"
            current_index = int(key_parts[-2])  # Extract the index
        else:
            parent_array_key = None
            current_index = -1
        
        # Verify results
        print(f"Test {i+1}:")
        print(f"  Input: {full_key}")
        print(f"  Expected parent: {expected_parent}")
        print(f"  Actual parent: {parent_array_key}")
        print(f"  Expected index: {expected_index}")
        print(f"  Actual index: {current_index}")
        print(f"  ✅ PASS" if (parent_array_key == expected_parent and current_index == expected_index) else "❌ FAIL")
        print()

def test_filtering_logic():
    """Test the filtering logic with mock session state"""
    
    # Mock session state with mixed order components
    mock_session_state = {
        "orderType.mixedOrderComponents": [
            {"type": "blago", "description": "Računalniki"},
            {"type": "storitve", "description": "Vzdrževanje"},
            {}  # Empty component (being edited)
        ]
    }
    
    # Test filtering for component 2 (index 2, empty)
    all_options = ["blago", "storitve", "gradnje"]
    current_components = mock_session_state["orderType.mixedOrderComponents"]
    current_index = 2  # Editing the 3rd component
    
    # Extract selected types (exclude current)
    selected_types = []
    for i, component in enumerate(current_components):
        if i != current_index and isinstance(component, dict) and 'type' in component:
            selected_types.append(component['type'])
    
    # Filter available options
    available_options = [opt for opt in all_options if opt not in selected_types]
    
    print("Filtering Logic Test:")
    print(f"  All options: {all_options}")
    print(f"  Selected types: {selected_types}")
    print(f"  Available options: {available_options}")
    print(f"  Expected: ['gradnje']")
    print(f"  ✅ PASS" if available_options == ["gradnje"] else "❌ FAIL")
    print()

if __name__ == "__main__":
    print("🧪 Testing Array Key Extraction and Filtering Logic\n")
    test_key_extraction()
    test_filtering_logic()
    print("✅ All tests completed!")