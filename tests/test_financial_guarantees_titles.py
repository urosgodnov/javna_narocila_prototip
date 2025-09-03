#!/usr/bin/env python3
"""
Test that financialGuarantees sections have proper Slovenian titles
"""
import json
import os

# Load schema
schema_path = os.path.join(os.path.dirname(__file__), '..', 'json_files', 'SEZNAM_POTREBNIH_PODATKOV.json')
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 60)
print("CHECKING FINANCIAL GUARANTEES SECTION TITLES")
print("=" * 60)

# Check financialGuarantees sections
if '$defs' in schema and 'financialGuaranteesProperties' in schema['$defs']:
    fin_guarantees = schema['$defs']['financialGuaranteesProperties']['properties']
    
    sections_to_check = {
        'fzSeriousness': 'Finančno zavarovanje za resnost ponudbe',
        'fzPerformance': 'Finančno zavarovanje za dobro izvedbo pogodbenih obveznosti',
        'fzWarranty': 'Finančno zavarovanje za odpravo napak v garancijski dobi'
    }
    
    all_good = True
    for section_name, expected_title in sections_to_check.items():
        if section_name in fin_guarantees:
            section = fin_guarantees[section_name]
            actual_title = section.get('title', 'NO TITLE FOUND!')
            
            print(f"\n{section_name}:")
            print(f"  Expected: {expected_title}")
            print(f"  Actual:   {actual_title}")
            
            if actual_title == expected_title:
                print("  ✅ Correct title set!")
            else:
                print("  ❌ Missing or incorrect title!")
                all_good = False
        else:
            print(f"\n{section_name}: ❌ Section not found!")
            all_good = False

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if all_good:
        print("All financial guarantee sections have proper Slovenian titles! ✅")
        print("Users will see readable names instead of 'fzSeriousness', 'fzPerformance', 'fzWarranty'")
    else:
        print("Some sections are missing proper titles! ❌")
else:
    print("ERROR: Could not find financialGuaranteesProperties in schema!")