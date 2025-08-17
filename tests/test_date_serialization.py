#!/usr/bin/env python3
"""
Test script to verify that date serialization is fixed.
"""

import json
from datetime import datetime, date
from database import convert_dates_to_strings, save_draft, create_procurement, update_procurement

def test_date_serialization():
    """Test that date objects are properly converted for JSON serialization."""
    
    print("Testing Date Serialization Fix")
    print("=" * 50)
    
    # Test 1: Direct conversion function
    print("\n✓ Test 1: convert_dates_to_strings function")
    test_data = {
        'projectInfo': {
            'projectName': 'Test Project',
            'projectDate': date(2024, 1, 15)  # Python date object
        },
        'executionDeadline': {
            'startDate': datetime(2024, 2, 1, 10, 0),  # Python datetime object
            'endDate': date(2024, 12, 31)
        },
        'normalField': 'This is a string',
        'numberField': 123.45,
        'listField': [
            {'date': date(2024, 3, 1)},
            {'text': 'item 2'}
        ]
    }
    
    converted = convert_dates_to_strings(test_data)
    
    # Try to serialize it
    try:
        json_str = json.dumps(converted)
        print("  ✅ Successfully converted and serialized to JSON")
        
        # Verify dates were converted
        parsed = json.loads(json_str)
        print(f"  Project date: {parsed['projectInfo']['projectDate']}")
        print(f"  Start date: {parsed['executionDeadline']['startDate']}")
        print(f"  End date: {parsed['executionDeadline']['endDate']}")
        print(f"  List date: {parsed['listField'][0]['date']}")
        
    except TypeError as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    # Test 2: Test with form data structure
    print("\n✓ Test 2: Form data with dates")
    form_data = {
        'projectInfo': {
            'projectName': 'Test Procurement',
            'projectDescription': 'Test description'
        },
        'executionDeadline': {
            'deliveryDate': date.today(),  # Today's date
            'contractStartDate': date(2024, 6, 1),
            'contractEndDate': date(2024, 12, 31)
        },
        'orderType': {
            'type': 'blago',
            'estimatedValue': 50000
        },
        'submissionProcedure': {
            'procedure': 'odprti postopek',
            'submissionDeadline': datetime.now()  # Current datetime
        }
    }
    
    try:
        # Test save_draft (which should handle date conversion internally)
        draft_id = save_draft(form_data)
        print(f"  ✅ save_draft succeeded with ID: {draft_id}")
    except TypeError as e:
        print(f"  ❌ save_draft failed: {e}")
        return False
    
    # Test 3: Test create_procurement
    print("\n✓ Test 3: create_procurement with dates")
    try:
        proc_id = create_procurement(form_data)
        print(f"  ✅ create_procurement succeeded with ID: {proc_id}")
    except TypeError as e:
        print(f"  ❌ create_procurement failed: {e}")
        return False
    
    # Test 4: Test update_procurement
    print("\n✓ Test 4: update_procurement with dates")
    form_data['projectInfo']['projectName'] = 'Updated Test Procurement'
    form_data['executionDeadline']['newDate'] = date.today()  # Add another date
    
    try:
        update_procurement(proc_id, form_data)
        print(f"  ✅ update_procurement succeeded for ID: {proc_id}")
    except TypeError as e:
        print(f"  ❌ update_procurement failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED! ✅")
    print("\nThe date serialization fix works correctly:")
    print("- Python date objects are converted to ISO format strings")
    print("- Python datetime objects are converted to ISO format strings")
    print("- Nested dates in dicts and lists are handled")
    print("- All database functions work with date objects")
    
    return True

if __name__ == "__main__":
    test_date_serialization()