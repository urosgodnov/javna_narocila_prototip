#!/usr/bin/env python3
"""Check which social criteria codes are missing from CPV database."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.cpv_manager import get_all_cpv_codes
from ui.admin_panel import expand_cpv_range

def get_all_social_criteria_codes():
    """Get all social criteria codes including ranges."""
    codes = []
    
    # Ranges as specified
    ranges = [
        ("50700000-2", "50760000-0"),
        ("55300000-3", "55400000-4"),
        ("55410000-7", "55512000-2"),
        ("55520000-1", "55524000-9"),
        ("60100000-9", "60183000-4"),
        ("90600000-3", "90690000-0"),
        ("90900000-6", "90919300-5")
    ]
    
    for start, end in ranges:
        codes.extend(expand_cpv_range(start, end))
    
    # Individual codes
    codes.extend(["70330000-3", "79713000-5"])
    
    return sorted(list(set(codes)))

def check_missing_codes():
    """Check which codes are missing."""
    print("=" * 70)
    print("Checking Social Criteria Codes in Database")
    print("=" * 70)
    
    # Get all codes from database
    all_codes, _ = get_all_cpv_codes(page=1, per_page=15000)
    db_codes = {cpv['code'] for cpv in all_codes}
    print(f"Total codes in database: {len(db_codes)}")
    
    # Get all social criteria codes that should exist
    social_codes = get_all_social_criteria_codes()
    print(f"Total social criteria codes expected: {len(social_codes)}")
    
    # Check which ones exist
    found = []
    missing = []
    
    for code in social_codes:
        if code in db_codes:
            found.append(code)
        else:
            missing.append(code)
    
    print(f"\n✅ Found in database: {len(found)}/{len(social_codes)}")
    print(f"❌ Missing from database: {len(missing)}/{len(social_codes)}")
    
    if missing:
        print("\n🔍 Missing codes by range:")
        
        # Check each range
        ranges = [
            ("50700000-2", "50760000-0", "Repair and maintenance services"),
            ("55300000-3", "55400000-4", "Restaurant and catering services"),
            ("55410000-7", "55512000-2", "Bar and restaurant services"),
            ("55520000-1", "55524000-9", "Catering services"),
            ("60100000-9", "60183000-4", "Road transport services"),
            ("90600000-3", "90690000-0", "Cleaning services"),
            ("90900000-6", "90919300-5", "Other cleaning services")
        ]
        
        for start, end, desc in ranges:
            range_codes = expand_cpv_range(start, end)
            range_missing = [c for c in range_codes if c in missing]
            if range_missing:
                print(f"\n  Range {start} to {end} ({desc}):")
                print(f"    Expected: {len(range_codes)} codes")
                print(f"    Missing: {len(range_missing)} codes")
                print(f"    First missing: {range_missing[:3]}")
        
        # Check individual codes
        individual = ["70330000-3", "79713000-5"]
        for code in individual:
            if code in missing:
                print(f"\n  ❌ Individual code {code} is missing")
            else:
                print(f"\n  ✅ Individual code {code} found")
    
    # Check if the missing codes might have different check digits
    print("\n🔍 Checking for similar codes (different check digits):")
    for code in missing[:10]:  # Check first 10 missing
        base = code.split('-')[0]
        similar = [c for c in db_codes if c.startswith(base)]
        if similar:
            print(f"  {code} not found, but found: {similar[:3]}")
    
    return found, missing

def check_excel_content():
    """Check what's actually in the Excel file."""
    print("\n" + "=" * 70)
    print("Checking Excel File Content")
    print("=" * 70)
    
    import pandas as pd
    try:
        df = pd.read_excel('miscellanious/cpv.xlsx', engine='openpyxl')
        
        # Get codes from Excel
        excel_codes = set()
        for _, row in df.iterrows():
            code = str(row['CODE']).strip() if pd.notna(row['CODE']) else None
            if code:
                code = ''.join(c for c in code if c.isalnum() or c == '-')
                excel_codes.add(code)
        
        print(f"Excel contains {len(excel_codes)} unique codes")
        
        # Check if our missing social codes are in Excel
        social_codes = get_all_social_criteria_codes()
        social_in_excel = [c for c in social_codes if c in excel_codes]
        social_not_in_excel = [c for c in social_codes if c not in excel_codes]
        
        print(f"\nSocial criteria codes in Excel: {len(social_in_excel)}/{len(social_codes)}")
        print(f"Social criteria codes NOT in Excel: {len(social_not_in_excel)}/{len(social_codes)}")
        
        if social_not_in_excel:
            print(f"\nFirst 10 codes not in Excel: {social_not_in_excel[:10]}")
        
    except Exception as e:
        print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    found, missing = check_missing_codes()
    check_excel_content()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Social criteria codes found: {len(found)}")
    print(f"Social criteria codes missing: {len(missing)}")
    print("\nThe missing codes are likely not in the source Excel file.")
    print("These codes were generated from ranges but don't exist in the CPV standard.")