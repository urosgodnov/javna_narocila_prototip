"""Validation logic for CPV-based criteria restrictions."""
from typing import List, Dict, Optional
from dataclasses import dataclass
import sqlite3
from utils import criteria_manager
import database


@dataclass
class ValidationResult:
    """Result of criteria validation."""
    is_valid: bool = True
    messages: List[str] = None
    restricted_cpv_codes: List[Dict] = None
    required_criteria: List[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.restricted_cpv_codes is None:
            self.restricted_cpv_codes = []
        if self.required_criteria is None:
            self.required_criteria = []


def get_cpv_info(cpv_code: str) -> Optional[Dict]:
    """Get CPV code information from database."""
    database.init_db()
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT code, description FROM cpv_codes WHERE code = ?",
            (cpv_code,)
        )
        result = cursor.fetchone()
        if result:
            return {'code': result[0], 'description': result[1]}
    return None


def check_cpv_requires_additional_criteria(cpv_codes: List[str]) -> Dict[str, Dict]:
    """
    Check which CPV codes have 'Merila - cena' restrictions.
    
    Args:
        cpv_codes: List of CPV codes to check
        
    Returns:
        Dictionary with CPV codes that require additional criteria
        Format: {cpv_code: {'code': str, 'description': str, 'restriction': str}}
    """
    if not cpv_codes:
        return {}
    
    # Get the 'Merila - cena' criteria type
    price_criteria_type = criteria_manager.get_criteria_type_by_name("Merila - cena")
    if not price_criteria_type:
        return {}
    
    # Get all CPV codes with price restrictions
    restricted_codes = criteria_manager.get_cpv_for_criteria(price_criteria_type['id'])
    
    # Find intersection with provided CPV codes
    result = {}
    for code in cpv_codes:
        if code in restricted_codes:
            cpv_info = get_cpv_info(code)
            if cpv_info:
                result[code] = {
                    'code': code,
                    'description': cpv_info['description'],
                    'restriction': 'Cena ne sme biti edino merilo'
                }
    
    return result


def validate_criteria_selection(cpv_codes: List[str], selected_criteria: Dict) -> ValidationResult:
    """
    Validate if selected criteria meet requirements for given CPV codes.
    
    Args:
        cpv_codes: List of selected CPV codes
        selected_criteria: Dictionary of selected criteria (key: criterion name, value: bool)
        
    Returns:
        ValidationResult with validation status and messages
    """
    result = ValidationResult()
    
    if not cpv_codes:
        # No CPV codes selected, any criteria selection is valid
        return result
    
    # Check which CPV codes have restrictions
    restricted_cpv = check_cpv_requires_additional_criteria(cpv_codes)
    
    if not restricted_cpv:
        # No restrictions for selected CPV codes
        return result
    
    # Check if only price is selected
    price_selected = selected_criteria.get('price', False)
    
    # List of non-price criteria
    non_price_criteria = [
        'additionalReferences',
        'additionalTechnicalRequirements', 
        'shorterDeadline',
        'longerWarranty',
        'environmentalCriteria',
        'socialCriteria'
    ]
    
    # Check if any non-price criteria are selected
    has_other_criteria = any(
        selected_criteria.get(criterion, False) 
        for criterion in non_price_criteria
    )
    
    # Validation fails if price is selected and no other criteria
    if price_selected and not has_other_criteria:
        result.is_valid = False
        result.restricted_cpv_codes = list(restricted_cpv.values())
        
        # Create user-friendly message
        cpv_list = [f"{code}" for code in restricted_cpv.keys()]
        if len(cpv_list) > 3:
            cpv_display = ", ".join(cpv_list[:3]) + f" in še {len(cpv_list) - 3} drugih"
        else:
            cpv_display = ", ".join(cpv_list)
        
        result.messages.append(
            f"Izbrane CPV kode ({cpv_display}) zahtevajo dodatna merila poleg cene. "
            f"Prosimo, izberite vsaj eno dodatno merilo."
        )
        result.required_criteria = ['Vsaj eno dodatno merilo mora biti izbrano']
    
    # Also check if no criteria at all are selected when we have restricted CPV codes
    elif not price_selected and not has_other_criteria and restricted_cpv:
        # Warning: CPV codes with restrictions but no criteria selected
        result.messages.append(
            "Opozorilo: Izbrane CPV kode imajo posebne zahteve glede meril. "
            "Prosimo, izberite ustrezna merila za izbor."
        )
    
    return result


def get_validation_summary(cpv_codes: List[str]) -> Dict:
    """
    Get a summary of all validation rules for given CPV codes.
    
    Args:
        cpv_codes: List of CPV codes
        
    Returns:
        Dictionary with summary of applicable rules
    """
    summary = {
        'has_restrictions': False,
        'rules': [],
        'restricted_count': 0
    }
    
    if not cpv_codes:
        return summary
    
    restricted_cpv = check_cpv_requires_additional_criteria(cpv_codes)
    
    if restricted_cpv:
        summary['has_restrictions'] = True
        summary['restricted_count'] = len(restricted_cpv)
        summary['rules'].append(
            f"Dodatna merila poleg cene obvezna ({len(restricted_cpv)} kod)"
        )
    
    return summary