#!/usr/bin/env python3
"""Test number parsing function."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.form_renderer import parse_formatted_number

test_cases = [
    "1.500.000,00",
    "1500000",
    "1500000.00",
    "1,500,000.00",
    "0",
    "",
    None
]

print("Testing parse_formatted_number:")
print("=" * 60)

for test in test_cases:
    result = parse_formatted_number(test)
    print(f"Input: '{test}' -> Output: {result}")