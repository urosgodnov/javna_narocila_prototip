"""CPV codes Excel import module."""
import os
import sqlite3
from typing import List, Dict, Tuple, Optional
import pandas as pd
from utils.cpv_manager import bulk_insert_cpv_codes


def read_cpv_excel(file_path: str) -> List[Tuple[str, str]]:
    """
    Read CPV codes from Excel file.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        List of tuples (code, description)
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Try to identify columns
        # Look for columns that might contain codes and descriptions
        code_col = None
        desc_col = None
        
        # Common column name patterns for CPV codes
        code_patterns = ['code', 'koda', 'cpv', 'cpv_code', 'šifra']
        desc_patterns = ['description', 'opis', 'naziv', 'name', 'desc']
        
        # Find matching columns (case-insensitive)
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
        
        # If columns not found by name, try by position
        if not code_col and not desc_col and len(df.columns) >= 2:
            # Assume first column is code, second is description
            code_col = df.columns[0]
            desc_col = df.columns[1]
        
        if not code_col or not desc_col:
            raise ValueError("Could not identify CPV code and description columns")
        
        # Extract data
        cpv_list = []
        for _, row in df.iterrows():
            code = str(row[code_col]).strip() if pd.notna(row[code_col]) else None
            description = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else None
            
            if code and description:
                # Clean up code format (remove any non-alphanumeric except dash)
                code = ''.join(c for c in code if c.isalnum() or c == '-')
                cpv_list.append((code, description))
        
        return cpv_list
        
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")


def import_cpv_from_excel(file_path: str) -> Dict[str, any]:
    """
    Import CPV codes from Excel file to database.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        Dictionary with import results
    """
    result = {
        'success': False,
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'error': None,
        'total_in_file': 0
    }
    
    try:
        # Read CPV codes from Excel
        cpv_list = read_cpv_excel(file_path)
        result['total_in_file'] = len(cpv_list)
        
        if not cpv_list:
            result['error'] = "No valid CPV codes found in file"
            return result
        
        # Import to database
        import_results = bulk_insert_cpv_codes(cpv_list)
        
        result.update(import_results)
        result['success'] = True
        
    except FileNotFoundError as e:
        result['error'] = f"File not found: {str(e)}"
    except ValueError as e:
        result['error'] = f"Invalid file format: {str(e)}"
    except Exception as e:
        result['error'] = f"Import error: {str(e)}"
    
    return result


def import_cpv_from_uploaded_file(uploaded_file) -> Dict[str, any]:
    """
    Import CPV codes from Streamlit uploaded file.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    
    Returns:
        Dictionary with import results
    """
    result = {
        'success': False,
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'error': None,
        'total_in_file': 0
    }
    
    try:
        # Read Excel file from uploaded file
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Try to identify columns (same logic as read_cpv_excel)
        code_col = None
        desc_col = None
        
        code_patterns = ['code', 'koda', 'cpv', 'cpv_code', 'šifra']
        desc_patterns = ['description', 'opis', 'naziv', 'name', 'desc']
        
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
        
        if not code_col and not desc_col and len(df.columns) >= 2:
            code_col = df.columns[0]
            desc_col = df.columns[1]
        
        if not code_col or not desc_col:
            result['error'] = "Could not identify CPV code and description columns"
            return result
        
        # Extract data
        cpv_list = []
        for _, row in df.iterrows():
            code = str(row[code_col]).strip() if pd.notna(row[code_col]) else None
            description = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else None
            
            if code and description:
                code = ''.join(c for c in code if c.isalnum() or c == '-')
                cpv_list.append((code, description))
        
        result['total_in_file'] = len(cpv_list)
        
        if not cpv_list:
            result['error'] = "No valid CPV codes found in file"
            return result
        
        # Import to database
        import_results = bulk_insert_cpv_codes(cpv_list)
        
        result.update(import_results)
        result['success'] = True
        
    except Exception as e:
        result['error'] = f"Import error: {str(e)}"
    
    return result


def validate_cpv_code_format(code: str) -> bool:
    """
    Validate CPV code format.
    
    CPV codes typically follow format: XXXXXXXX-Y
    Where X is digit and Y is check digit
    
    Args:
        code: CPV code to validate
    
    Returns:
        True if valid format
    """
    # Remove any whitespace
    code = code.strip()
    
    # Basic format check: 8 digits, optionally followed by dash and more digits
    if len(code) < 8:
        return False
    
    # Check if first 8 characters are digits
    if not code[:8].isdigit():
        return False
    
    # If there's more, it should be dash followed by digits
    if len(code) > 8:
        if code[8] != '-':
            return False
        if len(code) > 9 and not code[9:].isdigit():
            return False
    
    return True


def get_sample_cpv_data() -> List[Tuple[str, str]]:
    """
    Get sample CPV data for testing.
    
    Returns:
        List of sample CPV codes with descriptions
    """
    return [
        ("03000000-1", "Kmetijski, kmetijski proizvodi, proizvodi ribištva, gozdarstva in podobni proizvodi"),
        ("09000000-3", "Naftni derivati, goriva, elektrika in drugi viri energije"),
        ("14000000-1", "Rudarski proizvodi, osnovne kovine in sorodni proizvodi"),
        ("15000000-8", "Hrana, pijače, tobak in sorodne snovi"),
        ("18000000-9", "Oblačila, obutev, prtljaga in dodatki"),
        ("30000000-9", "Pisarniški in računalniški stroji, oprema in potrebščine, razen pohištva in programskih paketov"),
        ("33000000-0", "Medicinska oprema, farmacevtski izdelki in izdelki za osebno nego"),
        ("44000000-0", "Gradbene konstrukcije in materiali; pomožni gradbeni proizvodi (razen električnih naprav)"),
        ("45000000-7", "Gradbena dela"),
        ("50000000-5", "Storitve popravil in vzdrževanja"),
        ("60000000-8", "Prevozne storitve (razen odvoza odpadkov)"),
        ("71000000-8", "Arhitekturne, gradbene, inženirske in inšpekcijske storitve"),
        ("72000000-5", "Storitve informacijske tehnologije: svetovanje, razvoj programske opreme, internet in podpora"),
        ("85000000-9", "Zdravstvene in socialne storitve"),
        ("90000000-7", "Storitve odplak in odvoza odpadkov, sanitarne in okoljske storitve")
    ]