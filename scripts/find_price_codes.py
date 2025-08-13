#!/usr/bin/env python3
"""Find actual CPV codes for price criteria."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.cpv_manager import get_all_cpv_codes

def find_codes_in_range(start_base, end_base, db_codes):
    """Find all codes in database within a numeric range."""
    start_num = int(start_base.split('-')[0])
    end_num = int(end_base.split('-')[0])
    
    found_codes = []
    for code in db_codes:
        try:
            code_num = int(code.split('-')[0])
            if start_num <= code_num <= end_num:
                found_codes.append(code)
        except:
            continue
    
    return sorted(found_codes)

def main():
    print("Finding Price Criteria Codes")
    print("=" * 70)
    
    # Get all codes from database
    all_codes, _ = get_all_cpv_codes(page=1, per_page=15000)
    db_codes = [cpv['code'] for cpv in all_codes]
    
    # Main range 71000000-8 to 72000000-5
    found = find_codes_in_range("71000000-8", "72000000-5", db_codes)
    print(f"Range 71000000-8 to 72000000-5: {len(found)} codes found")
    
    # Additional specific codes from story
    additional = [
        "79530000-8",
        "66122000-1", "66170000-2", "66171000-9", "66519310-7", "66523000-2",
        "71210000-3", "71241000-9", "71310000-4", "71311000-1", "71311200-3",
        "71311210-6", "71311300-4", "71312000-8", "71313000-5", "71313100-6",
        "71313200-7", "71314300-5", "71315100-0", "71315200-1", "71315210-4",
        "71316000-6", "71317000-3", "71317100-4", "71317210-8", "71318000-0",
        "71321300-7", "71321400-8", "71351200-5", "71351210-8", "71351220-1",
        "71530000-2", "71600000-4", "71621000-7", "71800000-6", "72000000-5",
        "72100000-6", "72110000-9", "72120000-2", "72130000-5", "72140000-8",
        "72150000-1", "72200000-7", "72220000-3", "72221000-0", "72224000-1",
        "72226000-5", "72227000-2", "72228000-9", "72246000-1", "72266000-7",
        "72413000-8", "72415000-2", "72600000-6", "73000000-2", "73200000-4",
        "73210000-7", "73220000-0", "79000000-4", "79110000-8", "79111000-5",
        "79120000-1", "79121000-8", "79121100-9", "79140000-7", "79221000-9",
        "79341100-7", "79400000-8", "79410000-1", "79411000-8", "79411100-9",
        "79412000-5", "79413000-2", "79414000-9", "79415000-6", "79415200-8",
        "79416200-5", "79417000-0", "79418000-7", "79419000-4", "85141220-7",
        "85312300-2", "85312320-8", "90490000-8", "90492000-2", "90713000-8",
        "90713100-9", "90732400-1", "90742400-4", "98200000-5"
    ]
    
    # Check which additional codes exist
    existing_additional = [c for c in additional if c in db_codes]
    missing_additional = [c for c in additional if c not in db_codes]
    
    print(f"\nAdditional codes: {len(existing_additional)}/{len(additional)} found")
    if missing_additional:
        print(f"Missing: {missing_additional[:10]}...")
    
    # Combine all
    all_price_codes = list(set(found + existing_additional))
    all_price_codes.sort()
    
    print(f"\nTOTAL PRICE CRITERIA CODES: {len(all_price_codes)}")
    
    # Print as Python list for copying
    print("\nPython list format:")
    print("[")
    for i in range(0, len(all_price_codes), 5):
        chunk = all_price_codes[i:i+5]
        print("    " + ", ".join(f'"{c}"' for c in chunk) + ",")
    print("]")
    
    return all_price_codes

if __name__ == "__main__":
    codes = main()