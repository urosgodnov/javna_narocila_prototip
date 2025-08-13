#!/usr/bin/env python3
"""Convert CPV Excel file to JSON seed data."""
import json
import pandas as pd
import os
import sys

def convert_cpv_to_json(excel_path='miscellanious/cpv.xlsx', json_path='json_files/cpv_seed_data.json'):
    """
    Convert CPV Excel file to JSON format for seed data.
    
    Args:
        excel_path: Path to Excel file
        json_path: Path to output JSON file
    
    Returns:
        Number of CPV codes converted
    """
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return 0
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path, engine='openpyxl')
        
        # Identify columns (same logic as cpv_importer)
        code_col = None
        desc_col = None
        
        code_patterns = ['code', 'koda', 'cpv', 'cpv_code', 'šifra']
        desc_patterns = ['description', 'opis', 'naziv', 'name', 'desc', 'sl']
        
        for col in df.columns:
            col_lower = str(col).lower()
            if not code_col:
                for pattern in code_patterns:
                    if pattern in col_lower:
                        code_col = col
                        break
            if not desc_col:
                for pattern in desc_patterns:
                    if pattern in col_lower:
                        desc_col = col
                        break
        
        # If columns not found by name, use first two columns
        if not code_col and not desc_col and len(df.columns) >= 2:
            code_col = df.columns[0]
            desc_col = df.columns[1]
        
        if not code_col or not desc_col:
            print("Error: Could not identify CPV code and description columns")
            return 0
        
        # Extract data
        cpv_list = []
        for _, row in df.iterrows():
            code = str(row[code_col]).strip() if pd.notna(row[code_col]) else None
            description = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else None
            
            if code and description:
                # Clean up code format
                code = ''.join(c for c in code if c.isalnum() or c == '-')
                cpv_list.append({
                    "code": code,
                    "description": description
                })
        
        # Ensure json_files directory exists
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        # Save to JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(cpv_list, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted {len(cpv_list)} CPV codes to {json_path}")
        return len(cpv_list)
        
    except Exception as e:
        print(f"Error converting Excel to JSON: {str(e)}")
        return 0


if __name__ == "__main__":
    # Run conversion
    count = convert_cpv_to_json()
    if count > 0:
        print(f"✅ Conversion complete: {count} CPV codes saved to JSON")
        sys.exit(0)
    else:
        print("❌ Conversion failed")
        sys.exit(1)