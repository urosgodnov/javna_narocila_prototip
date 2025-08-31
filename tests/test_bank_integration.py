#!/usr/bin/env python3
"""
Integration test to verify BankManager works with the main database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import BankManager, DATABASE_FILE


def test_integration():
    """Test BankManager integration with main database."""
    print("\n" + "="*60)
    print("BankManager Integration Test")
    print("="*60 + "\n")
    
    try:
        # Connect to main database
        conn = sqlite3.connect(DATABASE_FILE)
        bank_manager = BankManager(conn)
        
        # Test 1: Verify bank table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bank'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✓ Bank table exists in main database")
        else:
            print("✗ Bank table not found")
            return False
        
        # Test 2: Get all banks
        all_banks = bank_manager.get_all_banks()
        print(f"✓ Total banks in database: {len(all_banks)}")
        
        # Test 3: Get active banks
        active_banks = bank_manager.get_all_banks(active_only=True)
        print(f"✓ Active banks: {len(active_banks)}")
        
        # Test 4: Test specific bank lookups
        test_banks = [
            ('02', 'Nova Ljubljanska banka', 'LJBASI2X'),
            ('03', 'SKB banka', 'SKBASI2X'),
            ('04', 'Nova KBM', 'KBMASI2X')
        ]
        
        print("\nTesting specific bank lookups:")
        print("-" * 40)
        
        for code, expected_name, expected_swift in test_banks:
            bank = bank_manager.get_bank_by_code(code)
            if bank:
                if bank['name'] == expected_name:
                    print(f"✓ Code {code}: {bank['name']}")
                    
                    # Also test SWIFT lookup
                    if expected_swift and bank['swift'] == expected_swift:
                        swift_bank = bank_manager.get_bank_by_swift(expected_swift)
                        if swift_bank and swift_bank['bank_code'] == code:
                            print(f"  └─ SWIFT {expected_swift} lookup works")
                else:
                    print(f"✗ Code {code}: Name mismatch")
            else:
                print(f"✗ Code {code}: Not found")
        
        # Test 5: Test convenience functions
        print("\nTesting convenience functions:")
        print("-" * 40)
        
        # Import convenience functions
        from database import get_all_banks, get_bank_by_code, get_bank_by_swift
        
        # Test get_all_banks convenience function
        all_banks_conv = get_all_banks()
        if len(all_banks_conv) == len(all_banks):
            print(f"✓ get_all_banks() returns {len(all_banks_conv)} banks")
        else:
            print(f"✗ get_all_banks() mismatch")
        
        # Test get_bank_by_code convenience function
        nlb = get_bank_by_code('02')
        if nlb and nlb['name'] == 'Nova Ljubljanska banka':
            print(f"✓ get_bank_by_code('02') returns NLB")
        else:
            print(f"✗ get_bank_by_code('02') failed")
        
        # Test get_bank_by_swift convenience function
        skb = get_bank_by_swift('SKBASI2X')
        if skb and skb['bank_code'] == '03':
            print(f"✓ get_bank_by_swift('SKBASI2X') returns SKB")
        else:
            print(f"✗ get_bank_by_swift('SKBASI2X') failed")
        
        # Test 6: Display sample of banks
        print("\nSample of banks in database:")
        print("-" * 40)
        print(f"{'Code':<6} {'Name':<30} {'SWIFT':<12} {'Active'}")
        print("-" * 60)
        
        for bank in all_banks[:5]:  # Show first 5 banks
            status = "Yes" if bank['active'] else "No"
            swift = bank['swift'] or "-"
            print(f"{bank['bank_code']:<6} {bank['name'][:29]:<30} {swift:<12} {status}")
        
        if len(all_banks) > 5:
            print(f"... and {len(all_banks) - 5} more banks")
        
        print("\n" + "="*60)
        print("✓ Integration test completed successfully!")
        print("="*60)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)