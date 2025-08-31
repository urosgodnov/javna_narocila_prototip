"""
Financial and address validations for Slovenian public procurement system.
Includes IBAN, SWIFT/BIC, and postal code validations.
"""

import re
from typing import Tuple, Optional


def validate_slovenian_postal_code(postal_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Slovenian postal code (4 digits, 1000-9999).
    
    Args:
        postal_code: String to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not postal_code:
        return False, "Poštna številka je obvezna"
    
    # Remove spaces
    postal_code = postal_code.strip()
    
    # Check if it's 4 digits
    if not re.match(r'^[0-9]{4}$', postal_code):
        return False, "Poštna številka mora vsebovati točno 4 številke"
    
    # Check range (Slovenian postal codes are 1000-9999)
    code_num = int(postal_code)
    if code_num < 1000 or code_num > 9999:
        return False, "Poštna številka mora biti med 1000 in 9999"
    
    return True, None


def validate_iban(iban: str) -> Tuple[bool, Optional[str]]:
    """
    Validate IBAN format and checksum using mod97 algorithm.
    Special handling for Slovenian IBANs (SI56).
    
    Args:
        iban: IBAN string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not iban:
        return True, None  # IBAN is optional
    
    # Remove spaces and convert to uppercase
    iban = iban.replace(' ', '').replace('-', '').upper()
    
    # Check basic format
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', iban):
        return False, "IBAN mora začeti z 2 črkama države in 2 številkama (npr. SI56)"
    
    # Check length for Slovenia (SI = 19 characters)
    if iban.startswith('SI') and len(iban) != 19:
        return False, "Slovenski IBAN mora imeti 19 znakov (SI56 + 15 znakov)"
    
    # General IBAN length check (15-34 characters)
    if len(iban) < 15 or len(iban) > 34:
        return False, f"IBAN mora imeti med 15 in 34 znakov (trenutno: {len(iban)})"
    
    # Validate checksum using mod97 algorithm
    # Move first 4 characters to end
    rearranged = iban[4:] + iban[:4]
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric_iban = ''
    for char in rearranged:
        if char.isdigit():
            numeric_iban += char
        else:
            numeric_iban += str(ord(char) - ord('A') + 10)
    
    # Check mod 97
    if int(numeric_iban) % 97 != 1:
        return False, "Neveljavna kontrolna številka IBAN"
    
    return True, None


def validate_swift_bic(swift: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SWIFT/BIC code format.
    Format: 4 letters (bank) + 2 letters (country) + 2 alphanumeric (location) + optional 3 alphanumeric (branch)
    
    Args:
        swift: SWIFT/BIC code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not swift:
        return True, None  # SWIFT is optional
    
    # Remove spaces and convert to uppercase
    swift = swift.replace(' ', '').upper()
    
    # Check format: 8 or 11 characters
    if len(swift) not in [8, 11]:
        return False, "SWIFT/BIC koda mora imeti 8 ali 11 znakov"
    
    # Validate pattern
    # 4 letters (bank code) + 2 letters (country) + 2 alphanumeric (location) + optional 3 alphanumeric (branch)
    pattern = r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$'
    
    if not re.match(pattern, swift):
        return False, "Nepravilna oblika SWIFT/BIC kode (npr. LJBASIXX ali LJBASIXXABC)"
    
    # Check country code (positions 5-6)
    country_code = swift[4:6]
    # Basic check - should be valid ISO country code
    valid_country_codes = [
        'SI', 'AT', 'DE', 'IT', 'HR', 'HU', 'GB', 'US', 'FR', 'ES', 'NL', 
        'BE', 'CH', 'CZ', 'SK', 'PL', 'RS', 'BA', 'MK', 'ME', 'BG', 'RO'
    ]  # Common country codes, not exhaustive
    
    if country_code not in valid_country_codes:
        # Don't reject, just warn
        pass  # Could add warning in future
    
    return True, None


def validate_bank_name(bank: str) -> Tuple[bool, Optional[str]]:
    """
    Validate bank name (simple check for non-empty).
    
    Args:
        bank: Bank name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not bank or not bank.strip():
        return False, "Naziv banke je obvezen če je vnesen TRR"
    
    if len(bank.strip()) < 3:
        return False, "Naziv banke mora vsebovati vsaj 3 znake"
    
    return True, None


def format_iban_display(iban: str) -> str:
    """
    Format IBAN for display with spaces every 4 characters.
    
    Args:
        iban: IBAN string
        
    Returns:
        Formatted IBAN string
    """
    if not iban:
        return ""
    
    # Remove existing spaces
    iban = iban.replace(' ', '').replace('-', '').upper()
    
    # Add spaces every 4 characters
    formatted = ' '.join([iban[i:i+4] for i in range(0, len(iban), 4)])
    
    return formatted


def get_bank_from_iban(iban: str) -> Optional[str]:
    """
    Get bank name from Slovenian IBAN.
    
    Args:
        iban: IBAN string
        
    Returns:
        Bank name or None if not recognized
    """
    if not iban or not iban.startswith('SI56'):
        return None
    
    # Remove spaces and get bank code (positions 5-6 after SI56)
    iban = iban.replace(' ', '').replace('-', '')
    if len(iban) < 7:
        return None
    
    bank_code = iban[4:6]
    
    # Slovenian bank codes
    banks = {
        '01': 'Banka Slovenije',
        '02': 'Nova Ljubljanska banka',
        '03': 'SKB banka',
        '04': 'Nova KBM',
        '05': 'Abanka',
        '06': 'Banka Celje',
        '07': 'Gorenjska banka',
        '10': 'Banka Koper',
        '12': 'Raiffeisen banka',
        '14': 'Sparkasse',
        '17': 'Deželna banka Slovenije',
        '18': 'NLB',
        '19': 'Delavska hranilnica',
        '20': 'Unicredit banka',
        '24': 'BKS Bank',
        '25': 'Hranilnica LON',
        '26': 'Factor banka',
        '27': 'PBS',
        '28': 'N banka',
        '29': 'Unicredit banka',
        '30': 'Sberbank',
        '33': 'Addiko Bank',
        '34': 'Banka Sparkasse',
        '61': 'Poštna banka Slovenije',
    }
    
    return banks.get(bank_code)


def validate_client_financial_info(client_data: dict) -> Tuple[bool, list]:
    """
    Validate all financial information for a client.
    
    Args:
        client_data: Dictionary with client financial data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check TRR/IBAN
    trr = client_data.get('trr') or client_data.get('singleClientTRR', '')
    if trr:
        is_valid, error = validate_iban(trr)
        if not is_valid:
            errors.append(f"TRR: {error}")
        
        # If IBAN is provided, bank should also be provided
        bank = client_data.get('bank') or client_data.get('singleClientBank', '')
        is_valid, error = validate_bank_name(bank)
        if not is_valid:
            errors.append(error)
    
    # Check SWIFT/BIC
    swift = client_data.get('swift') or client_data.get('singleClientSwift', '')
    if swift:
        is_valid, error = validate_swift_bic(swift)
        if not is_valid:
            errors.append(f"SWIFT: {error}")
    
    return len(errors) == 0, errors


def validate_client_address(client_data: dict) -> Tuple[bool, list]:
    """
    Validate client address fields.
    
    Args:
        client_data: Dictionary with client address data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check street address
    street = client_data.get('streetAddress') or client_data.get('singleClientStreetAddress', '')
    if not street or not street.strip():
        errors.append("Ulica in hišna številka je obvezno polje")
    
    # Check postal code
    postal_code = client_data.get('postalCode') or client_data.get('singleClientPostalCode', '')
    is_valid, error = validate_slovenian_postal_code(postal_code)
    if not is_valid:
        errors.append(error)
    
    # Check city
    city = client_data.get('city') or client_data.get('singleClientCity', '')
    if not city or not city.strip():
        errors.append("Kraj je obvezno polje")
    
    return len(errors) == 0, errors