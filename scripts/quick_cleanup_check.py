#!/usr/bin/env python3
"""Quick check for deprecated patterns in key files."""

import os
from pathlib import Path

# Key files to check
files_to_check = [
    'ui/form_renderer.py',
    'ui/dashboard.py', 
    'app.py',
    'database.py',
    'utils/validations.py'
]

# Patterns we're looking for
patterns = [
    'lot_context',
    'has_lots',
    'mode == "general"',
    'mode == "lots"',
    'from ui.form_renderer import'
]

print("Quick Cleanup Check")
print("=" * 50)

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"\nChecking {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_patterns = []
            for pattern in patterns:
                if pattern in content:
                    # Count occurrences
                    count = content.count(pattern)
                    found_patterns.append(f"  - '{pattern}' found {count} times")
            
            if found_patterns:
                print(f"  Found deprecated patterns:")
                for p in found_patterns:
                    print(p)
            else:
                print(f"  ✓ No deprecated patterns found")
                
        except Exception as e:
            print(f"  Error reading file: {e}")
    else:
        print(f"\n{file_path} - File not found")

print("\n" + "=" * 50)
print("Files to be removed (after 30 days):")
files_to_remove = [
    'ui/form_renderer.py',  # After migration complete
    'ui/form_renderer_old.py',
    'ui/form_renderer_backup.py',
    'utils/lot_context.py'
]

for f in files_to_remove:
    if os.path.exists(f):
        print(f"  - {f} (EXISTS)")
    else:
        print(f"  - {f} (not found)")

print("\nRecommendation:")
if os.path.exists('ui/form_renderer.py'):
    print("  Keep ui/form_renderer.py with deprecation warnings for 30 days")
    print("  Monitor usage through logging")
    print("  Remove after confirming no production issues")