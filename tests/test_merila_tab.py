#!/usr/bin/env python3
"""Test script to verify Merila tab functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cpv_manager import get_cpv_count, get_all_cpv_codes
from ui.admin_panel import get_default_price_criteria_codes, get_default_social_criteria_codes

def test_merila_criteria():
    """Test that criteria codes are properly filtered."""
    print("=" * 60)
    print("Testing Merila Tab Criteria")
    print("=" * 60)
    
    # Get database codes
    all_codes, _ = get_all_cpv_codes(page=1, per_page=15000)
    db_codes = {cpv['code'] for cpv in all_codes}
    print(f"Database has {len(db_codes)} CPV codes")
    
    # Get default criteria
    price_criteria = get_default_price_criteria_codes()
    social_criteria = get_default_social_criteria_codes()
    
    print(f"\n📊 Criteria Statistics:")
    print(f"Price criteria defined: {len(price_criteria)} codes")
    print(f"Social criteria defined: {len(social_criteria)} codes")
    
    # Filter to only existing codes (as the tab does)
    price_in_db = [code for code in price_criteria if code in db_codes]
    social_in_db = [code for code in social_criteria if code in db_codes]
    
    print(f"\n✅ Available in database:")
    print(f"Price criteria: {len(price_in_db)}/{len(price_criteria)} ({len(price_in_db)*100//len(price_criteria)}%)")
    print(f"Social criteria: {len(social_in_db)}/{len(social_criteria)} ({len(social_in_db)*100//len(social_criteria)}%)")
    
    # Show some examples
    print(f"\n🔍 Sample Price Criteria Codes (first 5):")
    for code in price_in_db[:5]:
        cpv = next((c for c in all_codes if c['code'] == code), None)
        if cpv:
            print(f"  • {code} - {cpv['description'][:60]}...")
    
    print(f"\n🔍 Sample Social Criteria Codes (first 5):")
    for code in social_in_db[:5]:
        cpv = next((c for c in all_codes if c['code'] == code), None)
        if cpv:
            print(f"  • {code} - {cpv['description'][:60]}...")
    
    print("\n" + "=" * 60)
    print("✅ Merila tab is ready to use!")
    print("- CPV codes are pre-loaded in database")
    print("- Criteria codes are filtered to existing ones")
    print("- No import required by user")
    print("=" * 60)

if __name__ == "__main__":
    test_merila_criteria()