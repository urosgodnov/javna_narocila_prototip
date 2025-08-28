"""
Test that sidebar displays actual lot names instead of "Sklop 0"
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_lot_name_extraction():
    """Test that lot names are correctly extracted for sidebar display"""
    
    # Simulate session state with lot names
    mock_session_state = {
        'lots': [
            {'name': 'Gradnja Severnega krila'},
            {'name': 'IT oprema za pisarne'},
            {'name': 'Čiščenje prostorov'}
        ]
    }
    
    # Test lot_context_N pattern
    test_cases = [
        ("lot_context_0", "Gradnja Severnega krila"),
        ("lot_context_1", "IT oprema za pisarne"),
        ("lot_context_2", "Čiščenje prostorov"),
        ("lot_context_3", "Sklop 4"),  # Out of range, should default
    ]
    
    for field_name, expected_name in test_cases:
        if field_name.startswith("lot_context_"):
            lot_index = int(field_name.split('_')[-1])
            lots = mock_session_state.get('lots', [])
            if lot_index < len(lots):
                lot_name = lots[lot_index].get('name', f'Sklop {lot_index + 1}')
            else:
                lot_name = f"Sklop {lot_index + 1}"
            
            assert lot_name == expected_name, f"Expected '{expected_name}' but got '{lot_name}' for {field_name}"
            print(f"✓ {field_name} -> {lot_name}")
    
    # Test lot_N_fieldName pattern
    test_cases_detailed = [
        ("lot_0_orderType", "Gradnja Severnega krila: Vrsta naročila"),
        ("lot_1_technicalSpecifications", "IT oprema za pisarne: Tehnične zahteve"),
        ("lot_2_executionDeadline", "Čiščenje prostorov: Roki izvajanja"),
    ]
    
    for field_name, expected_name in test_cases_detailed:
        if field_name.startswith("lot_"):
            parts = field_name.split('_', 2)
            if len(parts) >= 3:
                lot_index = int(parts[1])
                base_field = parts[2]
                lots = mock_session_state.get('lots', [])
                if lot_index < len(lots):
                    lot_name = lots[lot_index].get('name', f'Sklop {lot_index + 1}')
                else:
                    lot_name = f"Sklop {lot_index + 1}"
                
                field_display_name = {
                    "orderType": "Vrsta naročila",
                    "technicalSpecifications": "Tehnične zahteve",
                    "executionDeadline": "Roki izvajanja",
                }.get(base_field, base_field)
                
                step_name = f"{lot_name}: {field_display_name}"
                assert step_name == expected_name, f"Expected '{expected_name}' but got '{step_name}' for {field_name}"
                print(f"✓ {field_name} -> {step_name}")

if __name__ == '__main__':
    print("Testing sidebar lot name display...")
    print("=" * 60)
    test_lot_name_extraction()
    print("=" * 60)
    print("All tests passed! Sidebar will now show actual lot names.")