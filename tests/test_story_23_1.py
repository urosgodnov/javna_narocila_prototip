#!/usr/bin/env python3
"""Test script for Story 23.1 - Criteria Ratios and Tiebreaker Rules"""

import json
import streamlit as st
from ui.form_renderer import (
    get_selected_criteria_labels,
    display_criteria_ratios_total
)

def test_criteria_labels():
    """Test that selected criteria labels are retrieved correctly."""
    print("Testing get_selected_criteria_labels...")
    
    # Mock session state
    st.session_state['selectionCriteria.price'] = True
    st.session_state['selectionCriteria.additionalReferences'] = True
    st.session_state['selectionCriteria.shorterDeadline'] = False
    
    labels = get_selected_criteria_labels()
    expected = ['Cena', 'Dodatne reference imenovanega kadra']
    
    assert labels == expected, f"Expected {expected}, got {labels}"
    print("✓ Selected criteria labels test passed")


def test_ratio_totals():
    """Test that ratio totals are calculated correctly."""
    print("Testing display_criteria_ratios_total...")
    
    # Mock session state with criteria and ratios
    st.session_state['selectionCriteria.price'] = True
    st.session_state['selectionCriteria.priceRatio'] = 50
    
    st.session_state['selectionCriteria.additionalReferences'] = True
    st.session_state['selectionCriteria.additionalReferencesRatio'] = 30
    
    st.session_state['selectionCriteria.shorterDeadline'] = True
    st.session_state['selectionCriteria.shorterDeadlineRatio'] = 20
    
    # Calculate total (function returns total)
    total = display_criteria_ratios_total()
    expected_total = 100
    
    assert total == expected_total, f"Expected total {expected_total}, got {total}"
    print(f"✓ Ratio totals test passed (total: {total})")


def test_json_schema_structure():
    """Test that JSON schema has the new fields."""
    print("Testing JSON schema structure...")
    
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Check for ratio fields
    selection_props = schema['$defs']['selectionCriteriaProperties']['properties']
    
    assert 'ratiosHeader' in selection_props, "Missing ratiosHeader"
    assert 'priceRatio' in selection_props, "Missing priceRatio"
    assert 'additionalReferencesRatio' in selection_props, "Missing additionalReferencesRatio"
    
    # Check for updated tiebreaker
    assert 'tiebreakerRule' in selection_props, "Missing tiebreakerRule"
    assert selection_props['tiebreakerRule'].get('format') == 'radio', "tiebreakerRule should have radio format"
    assert selection_props['tiebreakerRule']['enum'] == ['žreb', 'prednost po merilu'], "Wrong tiebreaker options"
    
    # Check tiebreakerCriterion has empty enum (to be populated dynamically)
    assert 'tiebreakerCriterion' in selection_props, "Missing tiebreakerCriterion"
    assert selection_props['tiebreakerCriterion']['enum'] == [], "tiebreakerCriterion enum should be empty (dynamic)"
    
    print("✓ JSON schema structure test passed")


def main():
    """Run all tests."""
    print("="*50)
    print("Running Story 23.1 Tests")
    print("="*50)
    
    try:
        test_json_schema_structure()
        test_criteria_labels()
        test_ratio_totals()
        
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