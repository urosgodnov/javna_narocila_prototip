#!/usr/bin/env python3
"""
Migration script to populate the bank table with Slovenian banks.
This script is idempotent - it can be run multiple times safely.
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import BankManager, DATABASE_FILE

# Complete list of Slovenian banks with their codes and SWIFT/BIC codes
SLOVENIAN_BANKS = [
    {"code": "01", "name": "Banka Slovenije", "short_name": "BS", "swift": "BSLJSI2X"},
    {"code": "02", "name": "Nova Ljubljanska banka", "short_name": "NLB", "swift": "LJBASI2X"},
    {"code": "03", "name": "SKB banka", "short_name": "SKB", "swift": "SKBASI2X"},
    {"code": "04", "name": "Nova KBM", "short_name": "NKBM", "swift": "KBMASI2X"},
    {"code": "05", "name": "Abanka", "short_name": "Abanka", "swift": "ABANSI2X"},
    {"code": "06", "name": "Banka Celje", "short_name": "Banka Celje", "swift": None},
    {"code": "10", "name": "Banka Intesa Sanpaolo", "short_name": "Intesa", "swift": "BAKOSI2X"},
    {"code": "12", "name": "Raiffeisen banka", "short_name": "Raiffeisen", "swift": None},
    {"code": "14", "name": "Sparkasse", "short_name": "Sparkasse", "swift": "KSPKSI22"},
    {"code": "17", "name": "Deželna banka Slovenije", "short_name": "DBS", "swift": "SZKBSI2X"},
    {"code": "19", "name": "Delavska hranilnica", "short_name": "DH", "swift": "HDELSI22"},
    {"code": "24", "name": "BKS Bank", "short_name": "BKS", "swift": None},
    {"code": "25", "name": "Hranilnica LON", "short_name": "LON", "swift": None},
    {"code": "26", "name": "Factor banka", "short_name": "Factor", "swift": None},
    {"code": "27", "name": "Primorska hranilnica Vipava", "short_name": "PHV", "swift": None},
    {"code": "28", "name": "N banka", "short_name": "N banka", "swift": None},
    {"code": "30", "name": "Sberbank", "short_name": "Sberbank", "swift": "SABRSI2X"},
    {"code": "33", "name": "Addiko Bank", "short_name": "Addiko", "swift": "HAABSI22"},
    {"code": "34", "name": "Banka Sparkasse", "short_name": "Sparkasse", "swift": "KSPKSI22"},
    {"code": "61", "name": "Poštna banka Slovenije", "short_name": "PBS", "swift": "PBSLSI22"},
]


def populate_banks():
    """
    Populate the bank table with Slovenian banks.
    This function is idempotent - it checks for existing banks before inserting.
    """
    print(f"\n{'='*60}")
    print(f"Bank Population Script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Initialize database connection
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        bank_manager = BankManager(conn)
        
        # Ensure bank table exists
        bank_manager.create_bank_table()
        print("✓ Bank table verified/created\n")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False
    
    # Statistics
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    print("Processing banks...")
    print("-" * 40)
    
    for bank_data in SLOVENIAN_BANKS:
        try:
            # Check if bank already exists
            existing_bank = bank_manager.get_bank_by_code(bank_data["code"])
            
            if existing_bank:
                print(f"- Bank already exists: {bank_data['name']} (code: {bank_data['code']})")
                skipped_count += 1
            else:
                # Prepare bank data for insertion
                bank_to_insert = {
                    "code": bank_data["code"],  # Changed from bank_code to code
                    "name": bank_data["name"],
                    "short_name": bank_data.get("short_name"),
                    "swift": bank_data.get("swift"),
                    "active": True,
                    "country": "SI"
                }
                
                # Insert new bank
                try:
                    bank_id = bank_manager.insert_bank(bank_to_insert)
                    
                    if bank_id:
                        swift_info = f" (SWIFT: {bank_data['swift']})" if bank_data.get('swift') else ""
                        print(f"✓ Added bank: {bank_data['name']}{swift_info}")
                        added_count += 1
                    else:
                        print(f"✗ Failed to add bank: {bank_data['name']}")
                        error_count += 1
                except Exception as insert_error:
                    print(f"✗ Failed to add bank: {bank_data['name']} - Error: {insert_error}")
                    error_count += 1
                    
        except Exception as e:
            print(f"✗ Error processing bank {bank_data['name']}: {e}")
            error_count += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Banks added:    {added_count}")
    print(f"- Banks skipped:  {skipped_count}")
    print(f"✗ Errors:         {error_count}")
    print(f"─" * 30)
    print(f"Total processed:  {len(SLOVENIAN_BANKS)}")
    
    # Verify final state
    try:
        all_banks = bank_manager.get_all_banks()
        active_banks = bank_manager.get_all_banks(active_only=True)
        print(f"\nDatabase state:")
        print(f"  Total banks:   {len(all_banks)}")
        print(f"  Active banks:  {len(active_banks)}")
    except Exception as e:
        print(f"\n✗ Error verifying database state: {e}")
    finally:
        # Close database connection
        conn.close()
    
    print("\n" + "=" * 60)
    
    return error_count == 0


if __name__ == "__main__":
    """
    Run the migration script when executed directly.
    """
    success = populate_banks()
    
    if success:
        print("\n✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Migration completed with errors. Please review the output above.")
        sys.exit(1)