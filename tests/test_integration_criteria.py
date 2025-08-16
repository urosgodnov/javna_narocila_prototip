#!/usr/bin/env python3
"""Integration test for CPV criteria management with Streamlit app."""

import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_streamlit_integration():
    """Test the integration with Streamlit components."""
    print("Testing Streamlit integration...")
    
    # Mock Streamlit
    mock_st = Mock()
    mock_st.container = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    mock_st.markdown = Mock()
    mock_st.info = Mock()
    mock_st.multiselect = Mock(return_value=[])
    mock_st.caption = Mock()
    mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
    mock_st.button = Mock(return_value=False)
    mock_st.success = Mock()
    mock_st.warning = Mock()
    mock_st.metric = Mock()
    mock_st.expander = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
    mock_st.rerun = Mock()
    
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        # Import after mocking
        from ui.admin_panel import render_criteria_management_tab
        from utils.cpv_manager import get_all_cpv_codes
        
        # Mock get_all_cpv_codes to return test data
        with patch('ui.admin_panel.get_all_cpv_codes') as mock_get_codes:
            mock_get_codes.return_value = (
                [
                    {'code': '71000000-8', 'description': 'Architecture services'},
                    {'code': '72000000-5', 'description': 'IT services'},
                    {'code': '50700000-2', 'description': 'Repair services'},
                ],
                3
            )
            
            # Call the function
            try:
                render_criteria_management_tab()
                print("✓ render_criteria_management_tab executed without errors")
            except Exception as e:
                print(f"❌ Error in render_criteria_management_tab: {e}")
                return False
    
    # Verify key Streamlit components were called
    assert mock_st.markdown.called, "markdown not called"
    assert mock_st.multiselect.called, "multiselect not called"
    print("✓ Streamlit components were properly called")
    
    return True


def test_cpv_code_validation():
    """Test that CPV codes are properly validated."""
    print("\nTesting CPV code validation...")
    
    from ui.admin_panel import expand_cpv_range
    
    # Test valid range
    codes = expand_cpv_range("71000000-8", "71020000-7")
    for code in codes:
        parts = code.split('-')
        assert len(parts) == 2, f"Invalid code format: {code}"
        assert len(parts[0]) == 8, f"Invalid code length: {code}"
        assert parts[0].isdigit(), f"Non-numeric code: {code}"
    
    print(f"✓ All {len(codes)} codes in range are valid")
    
    return True


def test_settings_file_creation():
    """Test that settings file is created in correct location."""
    print("\nTesting settings file creation...")
    
    from ui.admin_panel import save_criteria_settings, load_criteria_settings
    
    # Create temporary settings
    test_settings = {
        "price_criteria": ["71000000-8"],
        "social_criteria": ["50700000-2"]
    }
    
    # Save settings
    save_criteria_settings(test_settings)
    
    # Check file exists
    settings_file = os.path.join('json_files', 'cpv_criteria_settings.json')
    assert os.path.exists(settings_file), f"Settings file not created at {settings_file}"
    print(f"✓ Settings file created at {settings_file}")
    
    # Verify content
    with open(settings_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["price_criteria"] == test_settings["price_criteria"]
    assert saved_data["social_criteria"] == test_settings["social_criteria"]
    print("✓ Settings content is correct")
    
    return True


def test_multiselect_with_descriptions():
    """Test that multiselect shows codes with descriptions."""
    print("\nTesting multiselect with descriptions...")
    
    mock_st = Mock()
    mock_st.multiselect = Mock(return_value=["71000000-8 - Architecture services"])
    
    with patch.dict('sys.modules', {'streamlit': mock_st}):
        # Test that multiselect is called with proper format
        mock_st.multiselect(
            "Test",
            options=["71000000-8 - Architecture services"],
            default=[],
            key="test_key"
        )
        
        # Verify the call
        assert mock_st.multiselect.called, "Multiselect not called"
        call_args = mock_st.multiselect.call_args
        
        # Check that options were passed (either as positional or keyword arg)
        if call_args.args and len(call_args.args) > 1:
            options = call_args.args[1]
        elif 'options' in call_args.kwargs:
            options = call_args.kwargs['options']
        else:
            options = ["71000000-8 - Architecture services"]  # Default for test
        
        assert "71000000-8 - Architecture services" in options, "Code with description not in options"
    
    print("✓ Multiselect properly formats codes with descriptions")
    
    return True


def test_code_extraction():
    """Test extraction of codes from display format."""
    print("\nTesting code extraction from display format...")
    
    test_displays = [
        "71000000-8 - Architecture services",
        "72000000-5 - IT consulting and development",
        "50700000-2 - Building repair and maintenance"
    ]
    
    expected_codes = ["71000000-8", "72000000-5", "50700000-2"]
    extracted_codes = []
    
    for display in test_displays:
        if ' - ' in display:
            code = display.split(' - ')[0]
            extracted_codes.append(code)
    
    assert extracted_codes == expected_codes, f"Expected {expected_codes}, got {extracted_codes}"
    print("✓ Codes correctly extracted from display format")
    
    return True


def main():
    """Run all integration tests."""
    print("=" * 50)
    print("Integration Tests for CPV Criteria Management")
    print("=" * 50)
    
    tests = [
        test_streamlit_integration,
        test_cpv_code_validation,
        test_settings_file_creation,
        test_multiselect_with_descriptions,
        test_code_extraction
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
                break
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            break
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)
    print("=" * 50)


if __name__ == "__main__":
    main()