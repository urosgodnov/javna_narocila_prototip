#!/usr/bin/env python3
"""Test script to verify no regression in existing functionality."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from ui.admin_panel import (
            render_admin_header,
            render_login_form,
            render_template_management_tab,
            render_draft_management_tab,
            render_database_management_tab,
            render_organization_management_tab,
            render_cpv_management_tab,
            render_criteria_management_tab,
            render_admin_panel
        )
        print("✓ All admin panel functions imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        from utils.cpv_manager import (
            get_all_cpv_codes, get_cpv_by_id, create_cpv_code,
            update_cpv_code, delete_cpv_code, get_cpv_count
        )
        print("✓ CPV manager functions imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        from utils.cpv_importer import (
            import_cpv_from_uploaded_file, import_cpv_from_excel,
            get_sample_cpv_data
        )
        print("✓ CPV importer functions imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        from ui.components.cpv_selector import (
            render_cpv_selector,
            render_cpv_selector_with_chips
        )
        print("✓ CPV selector components imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True


def test_function_signatures():
    """Test that existing functions have expected signatures."""
    print("\nTesting function signatures...")
    
    from ui.admin_panel import (
        render_template_management_tab,
        render_cpv_management_tab,
        render_admin_panel
    )
    import inspect
    
    # Check that tab functions take no arguments
    tab_functions = [
        render_template_management_tab,
        render_cpv_management_tab
    ]
    
    for func in tab_functions:
        sig = inspect.signature(func)
        if len(sig.parameters) != 0:
            print(f"❌ {func.__name__} has unexpected parameters")
            return False
    
    print("✓ All tab functions have correct signatures")
    
    # Check render_admin_panel takes no arguments
    sig = inspect.signature(render_admin_panel)
    if len(sig.parameters) != 0:
        print("❌ render_admin_panel has unexpected parameters")
        return False
    
    print("✓ render_admin_panel has correct signature")
    
    return True


def test_file_structure():
    """Test that required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        "ui/admin_panel.py",
        "utils/cpv_manager.py",
        "utils/cpv_importer.py",
        "ui/components/cpv_selector.py",
        "json_files/organizations.json"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file_path}")
            return False
    
    print("✓ All required files exist")
    
    # Check that json_files directory exists
    if not os.path.exists("json_files"):
        print("❌ json_files directory missing")
        return False
    
    print("✓ json_files directory exists")
    
    return True


def test_new_functionality():
    """Test that new functionality is available."""
    print("\nTesting new functionality...")
    
    from ui.admin_panel import (
        expand_cpv_range,
        get_default_price_criteria_codes,
        get_default_social_criteria_codes,
        load_criteria_settings,
        save_criteria_settings,
        render_criteria_management_tab
    )
    
    # Test that new functions exist and are callable
    functions = [
        expand_cpv_range,
        get_default_price_criteria_codes,
        get_default_social_criteria_codes,
        load_criteria_settings,
        save_criteria_settings,
        render_criteria_management_tab
    ]
    
    for func in functions:
        if not callable(func):
            print(f"❌ {func.__name__} is not callable")
            return False
    
    print("✓ All new functions are callable")
    
    # Test that default codes are generated
    price_codes = get_default_price_criteria_codes()
    social_codes = get_default_social_criteria_codes()
    
    if not price_codes:
        print("❌ No default price criteria codes")
        return False
    
    if not social_codes:
        print("❌ No default social criteria codes")
        return False
    
    print(f"✓ Default codes generated: {len(price_codes)} price, {len(social_codes)} social")
    
    return True


def main():
    """Run all regression tests."""
    print("=" * 50)
    print("Regression Tests for CPV Criteria Management")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_function_signatures,
        test_file_structure,
        test_new_functionality
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            break
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All regression tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
    print("=" * 50)


if __name__ == "__main__":
    main()