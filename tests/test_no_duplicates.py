#!/usr/bin/env python3
"""Test that there are no duplicate criteria options."""

import json
import sys

print("=" * 60)
print("Checking for duplicate criteria options")
print("=" * 60)

# Load the JSON schema
with open('json_files/SEZNAM_POTREBNIH_PODATKOV.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Get selection criteria properties
selection_criteria = schema['selectionCriteria']['properties']

print("\n1. Main Criteria:")
main_criteria = []
for key, value in selection_criteria.items():
    if isinstance(value, dict) and value.get('type') == 'boolean':
        # Skip sub-objects like socialCriteriaOptions
        if 'Options' not in key and 'Header' not in key:
            title = value.get('title', key)
            main_criteria.append((key, title))
            print(f"   - {key}: {title}")

print("\n2. Social Sub-Options:")
social_options = selection_criteria.get('socialCriteriaOptions', {}).get('properties', {})
social_sub = []
for key, value in social_options.items():
    if isinstance(value, dict) and value.get('type') == 'boolean':
        title = value.get('title', key)
        social_sub.append((key, title))
        print(f"   - {key}: {title}")

print("\n3. Checking for duplicates:")

# Check if any titles appear in both lists
main_titles = {title for _, title in main_criteria}
social_titles = {title for _, title in social_sub}

duplicates = main_titles.intersection(social_titles)

if duplicates:
    print("   ❌ Found duplicate titles:")
    for dup in duplicates:
        print(f"      - {dup}")
else:
    print("   ✅ No duplicate titles found!")

# Check for similar titles that might confuse users
print("\n4. Checking for similar/confusing titles:")
confusing = []

for _, main_title in main_criteria:
    for _, social_title in social_sub:
        # Check if titles are very similar
        if 'Drugo' in main_title and 'Drugo' in social_title:
            if main_title != social_title:  # Not exact duplicates
                confusing.append((main_title, social_title))

if confusing:
    print("   ⚠️  Found potentially confusing similar titles:")
    for main, social in confusing:
        print(f"      Main: '{main}'")
        print(f"      Social: '{social}'")
        print()
else:
    print("   ✅ No confusing similar titles")

print("\n" + "=" * 60)
print("Analysis complete!")
print("=" * 60)