#!/usr/bin/env python3
"""Verify there are no duplicate 'Drugo' options between main and social criteria."""

import subprocess
import sys

print("=" * 60)
print("Verifying 'Drugo' options are correctly organized")
print("=" * 60)

# Search for all "Drugo" related titles
result = subprocess.run(
    ['grep', '-n', '"title".*"Drugo', 'json_files/SEZNAM_POTREBNIH_PODATKOV.json'],
    capture_output=True,
    text=True
)

print("\nAll 'Drugo' related options found:")
print("-" * 40)

lines = result.stdout.strip().split('\n')
for line in lines:
    if line:
        line_num, content = line.split(':', 1)
        # Extract the title value
        if '"title":' in content:
            title = content.split('"title":')[1].strip().strip(',').strip('"')
            print(f"Line {line_num:4}: {title}")

print("\n" + "=" * 60)
print("Expected structure:")
print("-" * 40)
print("✅ SOCIAL SUB-OPTIONS (within socialCriteriaOptions):")
print("   - Drugo")
print("   - Drugo, imam predlog") 
print("   - Drugo, prosim predlog AI")
print("\n✅ MAIN CRITERION (outside socialCriteriaOptions):")
print("   - Drugo merilo (ne-socialno)")
print("\n" + "=" * 60)

# Check if we have the right count
if len(lines) == 5:  # 3 social + 1 main + 1 ratio field
    print("✅ Correct number of 'Drugo' options found!")
else:
    print(f"⚠️  Found {len(lines)} 'Drugo' options, expected 5")

print("=" * 60)