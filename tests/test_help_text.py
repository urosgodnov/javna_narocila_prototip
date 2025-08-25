"""Test script to verify help text display for multiple clients."""
import json

def test_help_text():
    print("Testing Help Text Implementation for Multiple Clients...")
    
    # Load JSON schema
    with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Check if help text exists in schema
    client_info = schema['properties']['clientInfo']['properties']['isSingleClient']
    
    print("\n1. JSON Schema Check:")
    if 'help' in client_info:
        print("   ✓ Help text found in schema")
        print(f"   Content: {client_info['help'][:100]}...")
    else:
        print("   ✗ Help text NOT found in schema")
        return False
    
    # Check form_renderer.py implementation
    print("\n2. Form Renderer Implementation:")
    with open('ui/form_renderer.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check if help text extraction is fixed
    if 'prop_details.get("help") or prop_details.get("description")' in content:
        print("   ✓ Form renderer reads 'help' field from schema")
    else:
        print("   ✗ Form renderer doesn't read 'help' field")
        return False
    
    # Check if special handling for isSingleClient exists
    if 'prop_name == "isSingleClient" and not checkbox_value' in content:
        print("   ✓ Special info message for multiple clients implemented")
    else:
        print("   ✗ Special info message NOT implemented")
        return False
    
    # Check hasLots help text
    lots_info = schema['properties']['lotsInfo']['properties']['hasLots']
    if 'help' in lots_info:
        print("\n3. Lots Help Text:")
        print("   ✓ Help text found for hasLots")
        print(f"   Content: {lots_info['help']}")
    
    print("\n✅ All help text implementations verified!")
    print("\nExpected behavior when user unchecks 'Naročnik je eden':")
    print("1. Help icon (?) appears next to checkbox with tooltip")
    print("2. Info box appears below with instructions for multiple clients")
    return True

if __name__ == "__main__":
    test_help_text()