#!/usr/bin/env python3
"""Find actual CPV codes in the specified ranges."""

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
    print("=" * 70)
    print("Finding Actual CPV Codes in Social Criteria Ranges")
    print("=" * 70)
    
    # Get all codes from database
    all_codes, _ = get_all_cpv_codes(page=1, per_page=15000)
    db_codes = [cpv['code'] for cpv in all_codes]
    
    # Define ranges to check
    ranges = [
        ("50700000-2", "50760000-0", "Repair and maintenance"),
        ("55300000-3", "55400000-4", "Restaurant and catering"),
        ("55410000-7", "55512000-2", "Bar and restaurant"),
        ("55520000-1", "55524000-9", "Catering services"),
        ("60100000-9", "60183000-4", "Road transport"),
        ("90600000-3", "90690000-0", "Cleaning services"),
        ("90900000-6", "90919300-5", "Other cleaning")
    ]
    
    all_social_codes = []
    
    for start, end, desc in ranges:
        found = find_codes_in_range(start, end, db_codes)
        all_social_codes.extend(found)
        print(f"\n{desc} ({start} to {end}):")
        print(f"  Found {len(found)} codes in database")
        if found:
            print(f"  First 5: {found[:5]}")
    
    # Add individual codes
    individual = ["70330000-3", "79713000-5"]
    for code in individual:
        if code in db_codes:
            all_social_codes.append(code)
            print(f"\n✅ Individual code {code} found")
    
    # Remove duplicates
    all_social_codes = sorted(list(set(all_social_codes)))
    
    print("\n" + "=" * 70)
    print(f"TOTAL SOCIAL CRITERIA CODES FOUND: {len(all_social_codes)}")
    print("=" * 70)
    
    # Save to file for reference
    with open('actual_social_codes.txt', 'w') as f:
        for code in all_social_codes:
            cpv = next((c for c in all_codes if c['code'] == code), None)
            if cpv:
                f.write(f"{code} - {cpv['description']}\n")
    
    print("Saved actual codes to actual_social_codes.txt")
    
    return all_social_codes

if __name__ == "__main__":
    codes = main()