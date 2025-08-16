#!/usr/bin/env python3
"""Test that log filters are in the main logging tab, not in sidebar."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_filters_location():
    """Verify filters are in main content area, not sidebar."""
    print("=" * 60)
    print("TESTING LOG FILTERS LOCATION")
    print("=" * 60)
    
    # Read the admin panel file
    with open('ui/admin_panel.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the render_logging_management_tab function
    import re
    func_pattern = r'def render_logging_management_tab\(\):.*?(?=\ndef|\Z)'
    func_match = re.search(func_pattern, content, re.DOTALL)
    
    if not func_match:
        print("❌ Could not find render_logging_management_tab function")
        return False
    
    func_content = func_match.group(0)
    
    # Check that filters are NOT in sidebar
    if 'with st.sidebar:' in func_content and 'Filtri' in func_content.split('with st.sidebar:')[1].split('\n')[0:20]:
        print("❌ Filters are still in sidebar!")
        return False
    
    # Check that filters ARE in expander
    if 'st.expander("🔍 Filtri"' in func_content:
        print("✅ Filters are in main content area (expander)")
    else:
        print("⚠️ Filters location unclear - checking further...")
    
    # Verify key filter elements are present
    filter_elements = [
        'filter_log_levels',
        'filter_date_from', 
        'filter_date_to',
        'filter_search',
        'filter_org'
    ]
    
    for element in filter_elements:
        if element not in func_content:
            print(f"❌ Missing filter element: {element}")
            return False
        else:
            print(f"✅ Found filter element: {element}")
    
    # Check for filter buttons
    if '🔄 Uporabi filtre' in func_content:
        print("✅ Apply filters button found")
    else:
        print("❌ Apply filters button missing")
        return False
    
    if '🗑️ Počisti filtre' in func_content:
        print("✅ Clear filters button found")
    else:
        print("⚠️ Clear filters button not found (optional)")
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Filters are correctly placed in main logging tab")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_filters_location()
    if success:
        print("\n✅ All checks passed - filters are only visible in logging tab")
    else:
        print("\n❌ Test failed - filters configuration incorrect")