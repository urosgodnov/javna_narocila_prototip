#!/usr/bin/env python3
"""Debug lot detection."""

import json
from database import get_procurement_by_id

existing = get_procurement_by_id(8)
data = json.loads(existing['form_data_json'])

print("Keys starting with 'lot_':")
lot_indices = set()
for key in data.keys():
    if key.startswith('lot_'):
        print(f"  {key}")
        if '.' in key:
            lot_part = key.split('.')[0]
            if '_' in lot_part:
                idx = lot_part.split('_')[1]
                if idx.isdigit():
                    lot_indices.add(int(idx))
                    print(f"    -> Found lot index: {idx}")

print(f"\nDetected lot indices: {sorted(lot_indices)}")
print(f"num_lots would be: {len(lot_indices)}")

print(f"\nlot_mode: {data.get('lot_mode')}")
print(f"num_lots in data: {data.get('num_lots')}")
print(f"lotsInfo.hasLots: {data.get('lotsInfo', {}).get('hasLots')}")
print(f"Number of items in 'lots' array: {len(data.get('lots', []))}")