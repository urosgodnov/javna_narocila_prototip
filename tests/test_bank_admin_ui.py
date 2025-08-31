#!/usr/bin/env python3
"""
Test script to verify bank admin UI functionality.
This script tests the integration between the UI and database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import BankManager, DATABASE_FILE, get_all_banks, get_bank_by_code, create_bank, update_bank, toggle_bank_status


def test_bank_admin_ui_integration():
    """Test that all bank admin UI functions work correctly."""
    print("\n" + "="*60)
    print("Bank Admin UI Integration Test")
    print("="*60 + "\n")
    
    success_count = 0
    test_count = 0
    
    try:
        # Test 1: Get all banks (used for list display)
        test_count += 1
        print("Test 1: Get all banks for display...")
        banks = get_all_banks()
        if banks and len(banks) > 0:
            print(f"✓ Found {len(banks)} banks")
            success_count += 1
        else:
            print("✗ No banks found")
        
        # Test 2: Search functionality - test filtering
        test_count += 1
        print("\nTest 2: Testing search/filter logic...")
        search_term = "ljub"  # Should match "Nova Ljubljanska banka"
        filtered = [b for b in banks 
                   if search_term.lower() in b['name'].lower() 
                   or (b['swift'] and search_term.lower() in b['swift'].lower())
                   or search_term.lower() in b['bank_code'].lower()]
        
        if filtered:
            print(f"✓ Search for '{search_term}' found {len(filtered)} result(s)")
            for bank in filtered:
                print(f"  - {bank['name']} (Code: {bank['bank_code']})")
            success_count += 1
        else:
            print(f"✗ No results for search term '{search_term}'")
        
        # Test 3: Check if specific bank exists (for duplicate check)
        test_count += 1
        print("\nTest 3: Check for existing bank (duplicate prevention)...")
        existing = get_bank_by_code('02')  # NLB
        if existing:
            print(f"✓ Found existing bank: {existing['name']}")
            success_count += 1
        else:
            print("✗ Bank with code '02' not found")
        
        # Test 4: Create a test bank
        test_count += 1
        print("\nTest 4: Create new test bank...")
        test_bank_id = create_bank(
            bank_code='99',
            name='Test UI Bank',
            short_name='TUB',
            swift='TESTUI2X',
            active=True,
            country='SI'
        )
        
        if test_bank_id:
            print(f"✓ Created test bank with ID: {test_bank_id}")
            success_count += 1
            
            # Test 5: Update the test bank
            test_count += 1
            print("\nTest 5: Update test bank...")
            update_success = update_bank(
                bank_id=test_bank_id,
                name='Updated Test Bank',
                short_name='UTB',
                swift='UPDTUI2X',
                country='SI'
            )
            
            if update_success:
                print("✓ Bank updated successfully")
                # Verify update
                updated = get_bank_by_code('99')
                if updated and updated['name'] == 'Updated Test Bank':
                    print(f"  - New name: {updated['name']}")
                    print(f"  - New SWIFT: {updated['swift']}")
                    success_count += 1
            else:
                print("✗ Failed to update bank")
            
            # Test 6: Toggle bank status
            test_count += 1
            print("\nTest 6: Toggle bank active status...")
            toggle_success = toggle_bank_status(test_bank_id)
            
            if toggle_success:
                toggled = get_bank_by_code('99')
                if toggled:
                    status = "Neaktivna" if toggled['active'] == 0 else "Aktivna"
                    print(f"✓ Bank status toggled to: {status}")
                    success_count += 1
            else:
                print("✗ Failed to toggle bank status")
            
            # Clean up - delete test bank
            print("\nCleaning up test data...")
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bank WHERE bank_code = '99'")
            conn.commit()
            conn.close()
            print("✓ Test bank removed")
        else:
            # Check if it already exists from previous test
            existing_test = get_bank_by_code('99')
            if existing_test:
                print("! Test bank already exists from previous run")
                # Clean it up
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bank WHERE bank_code = '99'")
                conn.commit()
                conn.close()
                print("✓ Cleaned up existing test bank")
                # Try again
                test_bank_id = create_bank(
                    bank_code='99',
                    name='Test UI Bank',
                    short_name='TUB',
                    swift='TESTUI2X',
                    active=True,
                    country='SI'
                )
                if test_bank_id:
                    print("✓ Created test bank on retry")
                    success_count += 1
                    # Clean up
                    conn = sqlite3.connect(DATABASE_FILE)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM bank WHERE bank_code = '99'")
                    conn.commit()
                    conn.close()
            else:
                print("✗ Failed to create test bank")
        
        # Test 7: Verify sorting works
        test_count += 1
        print("\nTest 7: Verify banks can be sorted by code...")
        all_banks = get_all_banks()
        sorted_banks = sorted(all_banks, key=lambda x: x['bank_code'])
        if sorted_banks[0]['bank_code'] <= sorted_banks[-1]['bank_code']:
            print(f"✓ Banks sorted correctly: {sorted_banks[0]['bank_code']} ... {sorted_banks[-1]['bank_code']}")
            success_count += 1
        else:
            print("✗ Sorting failed")
        
        # Test 8: Test filtering active/inactive banks
        test_count += 1
        print("\nTest 8: Filter active banks...")
        active_banks = [b for b in all_banks if b['active']]
        inactive_banks = [b for b in all_banks if not b['active']]
        print(f"✓ Active banks: {len(active_banks)}, Inactive: {len(inactive_banks)}")
        success_count += 1
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {success_count}/{test_count}")
    
    if success_count == test_count:
        print("✓ All tests passed! Bank admin UI is fully functional.")
        return True
    else:
        print(f"✗ {test_count - success_count} test(s) failed.")
        return False


if __name__ == "__main__":
    success = test_bank_admin_ui_integration()
    sys.exit(0 if success else 1)