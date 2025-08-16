#!/usr/bin/env python3
"""Test script for CPV criteria management functionality."""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.admin_panel import (
    expand_cpv_range,
    get_default_price_criteria_codes,
    get_default_social_criteria_codes,
    load_criteria_settings,
    save_criteria_settings
)


def test_cpv_range_expansion():
    """Test CPV code range expansion."""
    print("Testing CPV range expansion...")
    
    # Test small range
    result = expand_cpv_range("71000000-8", "71030000-1")
    expected_count = 4  # 71000000, 71010000, 71020000, 71030000
    assert len(result) == expected_count, f"Expected {expected_count} codes, got {len(result)}"
    print(f"✓ Small range expansion: {len(result)} codes")
    
    # Test larger range
    result = expand_cpv_range("50700000-2", "50760000-0")
    print(f"✓ Large range expansion: {len(result)} codes")
    
    # Verify format
    for code in result:
        assert '-' in code, f"Invalid code format: {code}"
        parts = code.split('-')
        assert len(parts) == 2, f"Invalid code format: {code}"
        assert len(parts[0]) == 8, f"Invalid code length: {code}"
        assert parts[0].isdigit(), f"Invalid code digits: {code}"
    print("✓ All codes have valid format")


def test_default_price_criteria():
    """Test default price criteria codes."""
    print("\nTesting default price criteria codes...")
    
    codes = get_default_price_criteria_codes()
    print(f"Total price criteria codes: {len(codes)}")
    
    # Check for specific required codes
    required_codes = [
        "79530000-8",  # Additional specific code
        "66122000-1",  # First additional code
        "98200000-5"   # Last additional code
    ]
    
    for req_code in required_codes:
        assert req_code in codes, f"Missing required code: {req_code}"
    print(f"✓ All required price criteria codes present")
    
    # Check that codes are sorted
    assert codes == sorted(codes), "Codes not sorted"
    print("✓ Codes are sorted")
    
    # Check for duplicates
    assert len(codes) == len(set(codes)), "Duplicate codes found"
    print("✓ No duplicate codes")


def test_default_social_criteria():
    """Test default social criteria codes."""
    print("\nTesting default social criteria codes...")
    
    codes = get_default_social_criteria_codes()
    print(f"Total social criteria codes: {len(codes)}")
    
    # Check for specific required codes
    required_codes = [
        "70330000-3",  # Specific code
        "79713000-5"   # Specific code
    ]
    
    for req_code in required_codes:
        assert req_code in codes, f"Missing required code: {req_code}"
    print(f"✓ All required social criteria codes present")
    
    # Check that codes are sorted
    assert codes == sorted(codes), "Codes not sorted"
    print("✓ Codes are sorted")
    
    # Check for duplicates
    assert len(codes) == len(set(codes)), "Duplicate codes found"
    print("✓ No duplicate codes")


def test_settings_persistence():
    """Test settings save and load functionality."""
    print("\nTesting settings persistence...")
    
    # Test saving settings
    test_settings = {
        "price_criteria": ["71000000-8", "72000000-5"],
        "social_criteria": ["50700000-2", "60100000-9"]
    }
    
    save_criteria_settings(test_settings)
    print("✓ Settings saved")
    
    # Test loading settings
    loaded_settings = load_criteria_settings()
    assert loaded_settings["price_criteria"] == test_settings["price_criteria"]
    assert loaded_settings["social_criteria"] == test_settings["social_criteria"]
    print("✓ Settings loaded correctly")
    
    # Clean up - restore defaults
    default_settings = {
        "price_criteria": get_default_price_criteria_codes(),
        "social_criteria": get_default_social_criteria_codes()
    }
    save_criteria_settings(default_settings)
    print("✓ Default settings restored")


def test_code_overlap():
    """Test for overlap between price and social criteria."""
    print("\nTesting for code overlap...")
    
    price_codes = set(get_default_price_criteria_codes())
    social_codes = set(get_default_social_criteria_codes())
    
    overlap = price_codes & social_codes
    
    if overlap:
        print(f"⚠️  Found {len(overlap)} overlapping codes:")
        for code in sorted(list(overlap)[:5]):
            print(f"   - {code}")
    else:
        print("✓ No overlap between price and social criteria codes")
    
    print(f"Price criteria: {len(price_codes)} codes")
    print(f"Social criteria: {len(social_codes)} codes")
    print(f"Total unique: {len(price_codes | social_codes)} codes")


def main():
    """Run all tests."""
    print("=" * 50)
    print("CPV Criteria Management Tests")
    print("=" * 50)
    
    try:
        test_cpv_range_expansion()
        test_default_price_criteria()
        test_default_social_criteria()
        test_settings_persistence()
        test_code_overlap()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()