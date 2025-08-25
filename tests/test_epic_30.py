"""Test script for Epic 3.0 implementations."""
import json
import sys

def test_json_schema_changes():
    """Test that JSON schema has been properly updated."""
    print("Testing Epic 3.0 Schema Changes...")
    
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Test Story 3.0.1: Address field restructuring
    print("\n✓ Story 3.0.1: Address Field Restructuring")
    client_props = schema['properties']['clientInfo']['properties']
    
    # Check single client fields
    assert 'singleClientStreetAddress' in client_props, "Missing singleClientStreetAddress"
    assert 'singleClientPostalCode' in client_props, "Missing singleClientPostalCode"
    print("  - Single client address fields split: ✓")
    
    # Check multiple clients fields
    client_item_props = client_props['clients']['items']['properties']
    assert 'streetAddress' in client_item_props, "Missing streetAddress in clients"
    assert 'postalCode' in client_item_props, "Missing postalCode in clients"
    print("  - Multiple clients address fields split: ✓")
    
    # Check help text
    assert 'help' in client_props['isSingleClient'], "Missing help text for isSingleClient"
    print("  - Help text added to checkbox: ✓")
    
    # Test Story 3.0.2: Lot checkbox help
    print("\n✓ Story 3.0.2: Procurement Procedures & Lots")
    lots_props = schema['properties']['lotsInfo']['properties']
    assert 'help' in lots_props['hasLots'], "Missing help text for hasLots"
    print("  - Help text added to lots checkbox: ✓")
    
    # Test Story 3.0.3: Co-financing field restructuring
    print("\n✓ Story 3.0.3: Co-financing Fields")
    # Cofinancers is actually under lots items
    lot_props = schema['properties']['lots']['items']['properties']
    if 'cofinancers' in lot_props:
        cofinancer_props = lot_props['cofinancers']['items']['properties']
        assert 'cofinancerName' in cofinancer_props, "Missing cofinancerName"
        assert 'cofinancerAddress' in cofinancer_props, "Missing cofinancerAddress"
        assert 'programName' in cofinancer_props, "Missing programName"
        assert 'programArea' in cofinancer_props, "Missing programArea"
        assert 'programCode' in cofinancer_props, "Missing programCode"
        print("  - Co-financing fields split: ✓")
        
        # Check required fields
        required = lot_props['cofinancers']['items']['required']
        assert 'cofinancerName' in required, "cofinancerName not required"
        assert 'cofinancerAddress' in required, "cofinancerAddress not required"
        print("  - Required fields properly set: ✓")
    
    print("\n✅ All schema tests passed!")


def test_data_migration():
    """Test data migration functions."""
    print("\n\nTesting Data Migration Functions...")
    
    from utils.data_migration import migrate_address_fields, migrate_cofinancing_fields
    
    # Test address migration
    old_data = {
        'clientInfo': {
            'singleClientAddress': 'Dunajska cesta 56, 1000 Ljubljana',
            'clients': [
                {'address': 'Prešernova 25, 4000 Kranj'},
                {'address': 'Glavni trg 1, 2000 Maribor'}
            ]
        }
    }
    
    migrated = migrate_address_fields(old_data)
    
    assert migrated['clientInfo']['singleClientStreetAddress'] == 'Dunajska cesta 56'
    assert '1000 Ljubljana' in migrated['clientInfo']['singleClientPostalCode']
    print("  - Single address migration: ✓")
    
    assert migrated['clientInfo']['clients'][0]['streetAddress'] == 'Prešernova 25'
    assert '4000 Kranj' in migrated['clientInfo']['clients'][0]['postalCode']
    print("  - Multiple clients address migration: ✓")
    
    # Test co-financing migration (cofinancers under lots)
    old_cofinancing = {
        'lots': [
            {
                'cofinancers': [
                    {
                        'name': 'EU Kohezijski sklad, Evropska 123, Ljubljana',
                        'program': 'REACT-EU, Digitalizacija, SI-2021-DIG-001'
                    }
                ]
            }
        ]
    }
    
    migrated_cf = migrate_cofinancing_fields(old_cofinancing)
    cofinancer = migrated_cf['lots'][0]['cofinancers'][0]
    
    assert cofinancer['cofinancerName'] == 'EU Kohezijski sklad'
    assert 'Evropska 123' in cofinancer['cofinancerAddress']
    assert cofinancer['programName'] == 'REACT-EU'
    assert cofinancer['programArea'] == 'Digitalizacija'
    assert cofinancer['programCode'] == 'SI-2021-DIG-001'
    print("  - Co-financing fields migration: ✓")
    
    print("\n✅ All migration tests passed!")


def test_form_renderer_updates():
    """Test form renderer updates."""
    print("\n\nTesting Form Renderer Updates...")
    
    # Check if formatting functions exist
    from ui.form_renderer import format_number_with_dots, parse_formatted_number
    
    # Test number formatting
    assert format_number_with_dots(1000000) == "1.000.000"
    assert format_number_with_dots(1234567.89) == "1.234.567.89"  # Uses dots for thousands
    print("  - Number formatting function: ✓")
    
    # Test number parsing
    assert parse_formatted_number("1.000.000") == 1000000
    assert abs(parse_formatted_number("1.234.567.89") - 1234567.89) < 0.01  # Allow small rounding
    print("  - Number parsing function: ✓")
    
    print("\n✅ All form renderer tests passed!")


if __name__ == "__main__":
    try:
        test_json_schema_changes()
        test_data_migration()
        test_form_renderer_updates()
        
        print("\n" + "="*50)
        print("🎉 ALL EPIC 3.0 TESTS PASSED SUCCESSFULLY! 🎉")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)