#!/usr/bin/env python3
"""Test script for Story 23.2 - Improve Criteria Display Specificity"""

import json
import streamlit as st
from ui.form_renderer import (
    get_social_criteria_specific_labels,
    get_selected_criteria_labels,
    display_criteria_ratios_total
)

def test_info_icons_removed():
    """Test that info icons have been removed from JSON schema."""
    print("Testing info icon removal...")
    
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    selection_props = schema['$defs']['selectionCriteriaProperties']['properties']
    
    # Check that priceInfo is gone
    assert 'priceInfo' not in selection_props, "priceInfo should be removed"
    
    # Check that no ℹ️ icons remain in titles
    for key, value in selection_props.items():
        if isinstance(value, dict) and 'title' in value:
            assert 'ℹ️' not in value['title'], f"Info icon found in {key}"
    
    print("✓ Info icons successfully removed")


def test_social_criteria_specific_labels():
    """Test that social criteria specific labels are generated correctly."""
    print("Testing social criteria specific labels...")
    
    # Mock session state
    st.session_state['selectionCriteria.socialCriteriaOptions.youngEmployeesShare'] = True
    st.session_state['selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare'] = True
    st.session_state['selectionCriteria.socialCriteriaOptions.registeredStaffEmployed'] = False
    
    labels = get_social_criteria_specific_labels()
    expected = [
        'Socialna merila - Delež zaposlenih mladih',
        'Socialna merila - Delež zaposlenih starejših'
    ]
    
    assert labels == expected, f"Expected {expected}, got {labels}"
    print("✓ Social criteria specific labels test passed")


def test_tiebreaker_dropdown_labels():
    """Test that tiebreaker dropdown includes specific social criteria."""
    print("Testing tiebreaker dropdown labels...")
    
    # Mock session state
    st.session_state['selectionCriteria.price'] = True
    st.session_state['selectionCriteria.socialCriteria'] = True
    st.session_state['selectionCriteria.socialCriteriaOptions.youngEmployeesShare'] = True
    st.session_state['selectionCriteria.socialCriteriaOptions.averageSalary'] = True
    
    labels = get_selected_criteria_labels()
    
    # Should include price and specific social criteria
    assert 'Cena' in labels, "Should include Cena"
    assert 'Socialna merila - Delež zaposlenih mladih' in labels, "Should include specific social criteria"
    assert 'Socialna merila - Povprečna plača priglašenega kadra' in labels, "Should include salary social criteria"
    
    print(f"✓ Tiebreaker dropdown test passed. Labels: {labels}")


def test_json_schema_social_fields():
    """Test that JSON schema has specific social criteria ratio and points fields."""
    print("Testing JSON schema social criteria fields...")
    
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    selection_props = schema['$defs']['selectionCriteriaProperties']['properties']
    
    # Check for specific social ratio fields
    assert 'socialCriteriaYoungRatio' in selection_props, "Missing socialCriteriaYoungRatio"
    assert 'socialCriteriaElderlyRatio' in selection_props, "Missing socialCriteriaElderlyRatio"
    assert 'socialCriteriaStaffRatio' in selection_props, "Missing socialCriteriaStaffRatio"
    
    # Check for specific social points fields
    assert 'socialCriteriaYoungPoints' in selection_props, "Missing socialCriteriaYoungPoints"
    assert 'socialCriteriaElderlyPoints' in selection_props, "Missing socialCriteriaElderlyPoints"
    
    # Verify render_if conditions
    young_ratio = selection_props['socialCriteriaYoungRatio']
    assert young_ratio['render_if']['field'] == 'selectionCriteria.socialCriteriaOptions.youngEmployeesShare'
    
    print("✓ JSON schema social fields test passed")


def test_ratio_totals_with_social():
    """Test that ratio totals include specific social criteria."""
    print("Testing ratio totals with social criteria...")
    
    # Mock session state
    st.session_state['selectionCriteria.price'] = True
    st.session_state['selectionCriteria.priceRatio'] = 50
    
    st.session_state['selectionCriteria.socialCriteriaOptions.youngEmployeesShare'] = True
    st.session_state['selectionCriteria.socialCriteriaYoungRatio'] = 30
    
    st.session_state['selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare'] = True
    st.session_state['selectionCriteria.socialCriteriaElderlyRatio'] = 20
    
    total = display_criteria_ratios_total()
    expected_total = 100
    
    assert total == expected_total, f"Expected total {expected_total}, got {total}"
    print(f"✓ Ratio totals with social criteria test passed (total: {total})")


def main():
    """Run all tests."""
    print("="*50)
    print("Running Story 23.2 Tests")
    print("="*50)
    
    try:
        test_info_icons_removed()
        test_json_schema_social_fields()
        test_social_criteria_specific_labels()
        test_tiebreaker_dropdown_labels()
        test_ratio_totals_with_social()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()