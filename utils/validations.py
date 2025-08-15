"""
Centralized validation module for the procurement form application.
All form validations are consolidated here for better maintainability.
"""

import streamlit as st
from typing import Dict, List, Tuple, Any, Optional


class ValidationManager:
    """Centralized validation management for the application."""
    
    def __init__(self, schema: Dict = None, session_state: Any = None):
        """
        Initialize the validation manager.
        
        Args:
            schema: JSON schema for the form
            session_state: Streamlit session state
        """
        self.schema = schema or {}
        self.session_state = session_state or st.session_state
        self.errors = []
        self.warnings = []
    
    def validate_step(self, step_keys: List[str], step_number: int = None) -> Tuple[bool, List[str]]:
        """
        Main validation entry point for form steps.
        
        Args:
            step_keys: List of field keys for the current step
            step_number: Current step number (optional)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.errors = []
        self.warnings = []
        
        # Expand section keys to field keys
        expanded_keys = self._expand_step_keys(step_keys)
        
        # Run all validations
        self._validate_required_fields(expanded_keys)
        self._validate_dropdowns(expanded_keys)
        self._validate_multiple_entries()
        self._validate_conditional_requirements()
        
        return len(self.errors) == 0, self.errors
    
    def _expand_step_keys(self, step_keys: List[str]) -> List[str]:
        """
        Expand section keys to individual field keys for validation.
        For example, ['clientInfo'] becomes ['clientInfo.field1', 'clientInfo.field2', ...]
        
        Args:
            step_keys: List of potentially nested keys
            
        Returns:
            List of expanded field keys
        """
        expanded_keys = []
        
        for key in step_keys:
            # Skip special keys like lot_context_
            if key.startswith('lot_context_'):
                continue
                
            # If key is a section (like 'clientInfo'), expand to all fields
            if key in self.schema.get('properties', {}):
                section_schema = self.schema['properties'][key]
                
                # Handle $ref references (like selectionCriteria which uses $ref)
                if '$ref' in section_schema:
                    ref_path = section_schema['$ref']
                    # Parse $ref like "#/$defs/selectionCriteriaProperties"
                    if ref_path.startswith('#/$defs/'):
                        def_name = ref_path.replace('#/$defs/', '')
                        if '$defs' in self.schema and def_name in self.schema['$defs']:
                            section_props = self.schema['$defs'][def_name].get('properties', {})
                        else:
                            section_props = {}
                    else:
                        section_props = {}
                else:
                    # Regular properties
                    section_props = section_schema.get('properties', {})
                
                # Expand all properties
                for field_name in section_props:
                    expanded_keys.append(f"{key}.{field_name}")
                    
                # If no properties found, keep original key
                if not section_props:
                    expanded_keys.append(key)
            else:
                # Already a full field key
                expanded_keys.append(key)
        
        return expanded_keys
    
    def _validate_required_fields(self, field_keys: List[str]):
        """
        Validate all required fields have values.
        
        Args:
            field_keys: List of field keys to validate
        """
        # Build a map of required fields from the schema
        required_fields = set()
        
        # Check top-level required fields
        if 'required' in self.schema:
            for field in self.schema.get('required', []):
                required_fields.add(field)
        
        # Check nested required fields
        for section_key, section_schema in self.schema.get('properties', {}).items():
            if isinstance(section_schema, dict) and 'required' in section_schema:
                for field in section_schema.get('required', []):
                    required_fields.add(f"{section_key}.{field}")
        
        for key in field_keys:
            field_value = self.session_state.get(key, '')
            
            # Get field schema - handle nested fields
            field_schema = None
            if '.' in key:
                parts = key.split('.')
                current_schema = self.schema.get('properties', {})
                for part in parts[:-1]:
                    if part in current_schema:
                        current_schema = current_schema[part].get('properties', {})
                if parts[-1] in current_schema:
                    field_schema = current_schema[parts[-1]]
            else:
                field_schema = self.schema.get('properties', {}).get(key, {})
            
            # Check if this field is required
            is_required = key in required_fields
            
            # Also check for individual field required property
            if field_schema:
                is_required = is_required or field_schema.get('required', False)
                
                # Check for required_if conditions
                required_if = field_schema.get('required_if', {})
                if required_if:
                    condition_field = required_if.get('field', '')
                    condition_value = required_if.get('value', '')
                    if self.session_state.get(condition_field) == condition_value:
                        is_required = True
            
            # Critical fields that are always required
            critical_fields = [
                'projectInfo.projectName',
                'projectInfo.projectType', 
                'projectInfo.cpvCodes',
                'clientInfo.singleClientName',
                'clientInfo.singleClientAddress',
                'procedureInfo.procedureType',
                'contractInfo.type'
            ]
            
            if key in critical_fields:
                is_required = True
                
            if is_required:
                # Validate based on field type
                if not field_value:
                    field_title = field_schema.get('title', key) if field_schema else key.split('.')[-1]
                    self.errors.append(f"Polje '{field_title}' je obvezno")
                elif isinstance(field_value, str) and not field_value.strip():
                    field_title = field_schema.get('title', key) if field_schema else key.split('.')[-1]
                    self.errors.append(f"Polje '{field_title}' ne sme biti prazno")
                    
                # Check dropdown selections for invalid values
                if field_schema and field_schema.get('enum') and field_value:
                    if field_value in ['--Izberite--', '--Select--', '']:
                        field_title = field_schema.get('title', key) if field_schema else key.split('.')[-1]
                        self.errors.append(f"Prosimo, izberite veljavno možnost za '{field_title}'")
    
    def _validate_dropdowns(self, field_keys: List[str]):
        """
        Validate all dropdown selections.
        
        Args:
            field_keys: List of field keys to validate
        """
        # List of critical dropdowns that must have valid selection
        critical_dropdowns = [
            ('procedureInfo.procedureType', 'Vrsta postopka'),
            ('clientInfo.singleClientType', 'Vrsta naročnika'),
            ('contractInfo.type', 'Vrsta pogodbe'),
            ('projectInfo.projectType', 'Vrsta naročila'),
            ('submissionInfo.submissionMethod', 'Način oddaje ponudb'),
            ('tenderInfo.evaluationCriteria', 'Merilo za izbor')
        ]
        
        for field_key, field_label in critical_dropdowns:
            if field_key in field_keys or any(field_key in k for k in field_keys):
                value = self.session_state.get(field_key, '')
                if not value or value in ['--Izberite--', '--Select--', '']:
                    self.errors.append(f"Prosimo, izberite '{field_label}'")
    
    def _validate_multiple_entries(self):
        """
        Validate multiple entry requirements.
        For example, when multiple clients are selected, validate that at least 2 are entered.
        """
        # Multiple clients validation
        if self.session_state.get('clientInfo.multipleClients') == 'da':
            # Count complete client entries
            client_count = 0
            for i in range(1, 11):  # Support up to 10 clients
                client_name = self.session_state.get(f'clientInfo.client{i}Name', '').strip()
                client_address = self.session_state.get(f'clientInfo.client{i}Address', '').strip()
                client_type = self.session_state.get(f'clientInfo.client{i}Type', '').strip()
                
                if client_name and client_address and client_type:
                    client_count += 1
            
            if client_count < 2:
                self.errors.append(
                    f"Pri več naročnikih morate vnesti podatke za najmanj 2 naročnika "
                    f"(trenutno: {client_count})"
                )
        
        # Lot validation
        is_lot_divided = self.session_state.get('lotInfo.isLotDivided') == 'da'
        lot_count = self.session_state.get('lotInfo.lotCount', 0)
        
        if is_lot_divided:
            if lot_count < 2:
                self.errors.append("Pri delitvi na sklope morate imeti najmanj 2 sklopa")
            
            # Check actual lot entries
            actual_lots = 0
            for i in range(1, lot_count + 1):
                lot_name = self.session_state.get(f'lot_{i}_name', '').strip()
                if lot_name:
                    actual_lots += 1
            
            if actual_lots < lot_count:
                self.errors.append(
                    f"Vnesite podatke za vse sklope "
                    f"(vneseni: {actual_lots}/{lot_count})"
                )
    
    def _validate_conditional_requirements(self):
        """
        Check conditional field requirements.
        For example, if certain options are selected, related fields become required.
        """
        # Social criteria validation
        if (self.session_state.get('merila.hasSocialCriteria') == 'da' or 
            self.session_state.get('criteria.hasSocialCriteria') == 'da' or
            self.session_state.get('selectionCriteria.socialCriteria', False)):
            
            # Check for any social criteria selection
            social_fields = [
                'merila.socialEmployment',
                'merila.socialInclusion', 
                'merila.socialEquality',
                'merila.socialWorkerRights',
                'criteria.socialEmployment',
                'criteria.socialInclusion',
                'criteria.socialEquality',
                'criteria.socialWorkerRights',
                'selectionCriteria.socialCriteriaOptions.youngEmployeesShare',
                'selectionCriteria.socialCriteriaOptions.elderlyEmployeesShare',
                'selectionCriteria.socialCriteriaOptions.registeredStaffEmployed',
                'selectionCriteria.socialCriteriaOptions.averageSalary',
                'selectionCriteria.socialCriteriaOptions.otherSocial'
            ]
            
            has_selection = any(
                self.session_state.get(field, False) for field in social_fields
            )
            
            if not has_selection:
                self.errors.append("Pri socialnih merilih morate izbrati najmanj eno možnost")
        
        # Environmental criteria validation
        if self.session_state.get('merila.hasEnvironmentalCriteria') == 'da':
            env_fields = [
                'merila.environmentalEmissions',
                'merila.environmentalEnergy',
                'merila.environmentalWaste',
                'merila.environmentalSustainability'
            ]
            
            has_selection = any(
                self.session_state.get(field, False) for field in env_fields
            )
            
            if not has_selection:
                self.errors.append("Pri okoljskih merilih morate izbrati najmanj eno možnost")
        
        # Contract extension validation (Story 24.3)
        if self.session_state.get('contractInfo.canBeExtended') == 'da':
            extension_reasons = self.session_state.get('contractInfo.extensionReasons', '').strip()
            extension_duration = self.session_state.get('contractInfo.extensionDuration', '').strip()
            
            if not extension_reasons:
                self.errors.append("Navedite razloge za možnost podaljšanja pogodbe")
            
            if not extension_duration:
                self.errors.append("Navedite trajanje podaljšanja pogodbe")
        
        # Framework agreement validation (Story 24.1)
        framework_type = self.session_state.get('contractInfo.type', '')
        if framework_type == 'okvirni sporazum':
            framework_duration = self.session_state.get('contractInfo.frameworkDuration', '')
            if framework_duration:
                # Parse the duration string to check if it exceeds 4 years
                import re
                # Look for patterns like "4 leta", "5 let", "48 mesecev", etc.
                years_match = re.search(r'(\d+)\s*let', framework_duration.lower())
                months_match = re.search(r'(\d+)\s*mesec', framework_duration.lower())
                
                if years_match:
                    years = int(years_match.group(1))
                    if years > 4:
                        self.errors.append("Obdobje okvirnega sporazuma ne sme presegati 4 let")
                elif months_match:
                    months = int(months_match.group(1))
                    if months > 48:
                        self.errors.append("Obdobje okvirnega sporazuma ne sme presegati 48 mesecev (4 leta)")
    
    def get_errors(self) -> List[str]:
        """Get current validation errors."""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get current validation warnings."""
        return self.warnings
    
    def add_error(self, message: str):
        """Add a validation error."""
        if message not in self.errors:
            self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        if message not in self.warnings:
            self.warnings.append(message)
    
    def clear_errors(self):
        """Clear all validation errors."""
        self.errors = []
    
    def clear_warnings(self):
        """Clear all validation warnings."""
        self.warnings = []
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def validate_merila(self, step_key: str = 'selectionCriteria') -> Tuple[bool, List[str]]:
        """
        Comprehensive validation for Merila (selection criteria) section.
        
        Requirements:
        1. At least one criterion must be selected
        2. Selected criteria must have points > 0
        3. Social criteria sub-options validation
        4. CPV code requirements validation
        5. Other criteria custom description validation
        6. Additional technical requirements description validation
        7. Environmental criteria validation
        8. Price cannot be sole criterion for certain CPVs
        
        Args:
            step_key: The key for the selection criteria section
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        warnings = []
        
        # Debug logging
        import logging
        logging.info(f"validate_merila called with step_key='{step_key}'")
        
        # Get all selected criteria
        criteria_selected = self._get_selected_criteria(step_key)
        
        # Log which criteria are selected
        selected_list = [k for k, v in criteria_selected.items() if v]
        logging.info(f"Selected criteria: {selected_list}")
        
        # Rule 1: At least one criterion must be selected
        if not any(criteria_selected.values()):
            logging.warning("No criteria selected - adding error")
            errors.append("Izbrati morate vsaj eno merilo za izbor")
        
        # Rule 2: Check points for selected criteria
        total_points = 0
        for criterion, is_selected in criteria_selected.items():
            if is_selected:
                # Map criterion to ratio field with multiple possible patterns
                ratio_keys = [
                    f"{step_key}.{criterion}Ratio",
                    f"general.{step_key}.{criterion}Ratio",
                    f"lot_1_{step_key}.{criterion}Ratio",
                ]
                
                # Handle special case for social criteria - sum all sub-criteria points
                if criterion == 'socialCriteria':
                    # Social criteria has individual ratio fields for each sub-option
                    social_ratio_fields = [
                        'socialCriteriaYoungRatio',     # youngEmployeesShare
                        'socialCriteriaElderlyRatio',   # elderlyEmployeesShare
                        'socialCriteriaStaffRatio',     # registeredStaffEmployed
                        'socialCriteriaSalaryRatio',    # averageSalary
                        'socialCriteriaOtherRatio'      # otherSocial
                    ]
                    
                    # Sum points from all social criteria sub-fields
                    social_points = 0
                    for ratio_field in social_ratio_fields:
                        ratio_keys = [
                            f"{step_key}.{ratio_field}",
                            f"general.{step_key}.{ratio_field}",
                            f"lot_1_{step_key}.{ratio_field}",
                        ]
                        
                        for key in ratio_keys:
                            test_value = self.session_state.get(key, None)
                            if test_value is not None:
                                try:
                                    field_points = float(test_value) if test_value else 0
                                    social_points += field_points
                                    if field_points > 0:
                                        logging.debug(f"Found social criteria points at {key}: {field_points}")
                                except (ValueError, TypeError):
                                    pass
                                break
                    
                    points_str = str(social_points)
                    points = social_points
                    
                    # Skip the normal ratio key lookup for social criteria
                    ratio_keys = []
                
                # For non-social criteria, look up the ratio value
                if criterion != 'socialCriteria':
                    # Also check if step_key already has a prefix
                    if 'general.' in step_key or 'lot_' in step_key:
                        base_key = f"{step_key}.{criterion}Ratio"
                        ratio_keys.insert(0, base_key)
                        
                    # Try to find the points value
                    points_str = '0'
                    for key in ratio_keys:
                        test_value = self.session_state.get(key, None)
                        if test_value is not None:
                            points_str = test_value
                            logging.debug(f"Found points for {criterion} at key {key}: {points_str}")
                            break
                    
                    # Convert to float, handle empty strings
                    try:
                        points = float(points_str) if points_str else 0
                    except (ValueError, TypeError):
                        points = 0
                
                # Validate points are positive numbers
                if points < 0:
                    criterion_name = self._get_criterion_name(criterion)
                    errors.append(f"Točke za '{criterion_name}' morajo biti pozitivne")
                elif points == 0:
                    criterion_name = self._get_criterion_name(criterion)
                    errors.append(f"Točke za '{criterion_name}' ne smejo biti 0")
                
                total_points += points
        
        # Warning if total points != 100 (but only if we have selected criteria)
        if any(criteria_selected.values()) and total_points > 0 and total_points != 100:
            warnings.append(
                f"Skupna vsota točk je {total_points:.0f}. "
                f"Priporočamo skupno vsoto 100 točk."
            )
        
        # Rule 3: Social criteria sub-options validation
        if criteria_selected.get('socialCriteria'):
            if not self._has_social_suboptions(step_key):
                errors.append("Pri socialnih merilih morate izbrati vsaj eno možnost")
        
        # Rule 4: Other criteria custom description validation
        if criteria_selected.get('otherCriteriaCustom'):
            description = self.session_state.get(f"{step_key}.otherCriteriaDescription", '').strip()
            if not description:
                errors.append("Pri drugih merilih morate navesti opis")
        
        # Rule 5: Additional technical requirements description validation
        if criteria_selected.get('additionalTechnicalRequirements'):
            description = self.session_state.get(f"{step_key}.technicalRequirementsDescription", '').strip()
            if not description:
                errors.append("Pri dodatnih tehničnih zahtevah morate navesti opis")
        
        # Rule 6: Cost efficiency description validation
        if criteria_selected.get('costEfficiency'):
            description = self.session_state.get(f"{step_key}.costEfficiencyDescription", '').strip()
            if not description:
                errors.append("Pri stroškovni učinkovitosti morate navesti konkretizacijo")
        
        # Rule 7: CPV validation (includes price-only validation)
        cpv_errors, cpv_warnings = self._validate_cpv_requirements(criteria_selected)
        errors.extend(cpv_errors)
        warnings.extend(cpv_warnings)
        
        # Rule 8: Price cannot be sole criterion warning (general best practice)
        if criteria_selected.get('price') and sum(criteria_selected.values()) == 1:
            warnings.append(
                "Cena kot edino merilo se priporoča le pri standardiziranih nakupih. "
                "Razmislite o dodajanju kvalitativnih meril."
            )
        
        # Store warnings for potential display
        self.warnings = warnings
        
        return len(errors) == 0, errors
    
    def _get_selected_criteria(self, step_key: str) -> Dict[str, bool]:
        """
        Get all selected criteria from the form.
        
        Args:
            step_key: The key for the selection criteria section
            
        Returns:
            Dictionary mapping criterion name to selection status
        """
        criteria = {
            'price': False,
            'additionalReferences': False,
            'additionalTechnicalRequirements': False,
            'shorterDeadline': False,
            'longerWarranty': False,
            'costEfficiency': False,
            'socialCriteria': False,
            'otherCriteriaCustom': False
        }
        
        # Debug logging
        import logging
        
        for criterion in criteria:
            # Try different possible key patterns
            possible_keys = [
                f"{step_key}.{criterion}",  # Standard: selectionCriteria.price
                f"general.{step_key}.{criterion}",  # General lot: general.selectionCriteria.price
                f"lot_1_{step_key}.{criterion}",  # Specific lot: lot_1_selectionCriteria.price
            ]
            
            # Also check if step_key already has a prefix
            if 'general.' in step_key:
                possible_keys.append(f"{step_key}.{criterion}")
            elif 'lot_' in step_key:
                possible_keys.append(f"{step_key}.{criterion}")
            
            value = False
            actual_key = None
            
            # Try each possible key pattern, prioritizing True values
            for key in possible_keys:
                test_value = self.session_state.get(key, None)
                if test_value is not None:
                    # Convert to boolean for comparison
                    if isinstance(test_value, bool):
                        bool_value = test_value
                    elif isinstance(test_value, str):
                        bool_value = test_value.lower() in ['da', 'true', '1', 'yes']
                    else:
                        bool_value = bool(test_value)
                    
                    # If we find a True value, use it immediately
                    if bool_value:
                        value = test_value
                        actual_key = key
                        break
                    # Otherwise, remember the first non-None value
                    elif actual_key is None:
                        value = test_value
                        actual_key = key
            
            # If no key found, use default False
            if actual_key is None:
                logging.debug(f"Criterion '{criterion}' not found in any key pattern")
                criteria[criterion] = False
                continue
            
            # Log the raw value for debugging
            logging.debug(f"Criterion '{criterion}' key='{actual_key}' raw_value='{value}' type={type(value)}")
            
            # Handle different value types
            if value is None or value == '':
                criteria[criterion] = False
            elif isinstance(value, bool):
                criteria[criterion] = value
            elif isinstance(value, str):
                # Handle string values like 'da', 'true', 'True', '1'
                criteria[criterion] = value.lower() in ['da', 'true', '1', 'yes']
            else:
                criteria[criterion] = bool(value)
        
        # Log the final criteria for debugging
        logging.debug(f"Final selected criteria: {criteria}")
        
        return criteria
    
    def _get_criterion_name(self, criterion: str) -> str:
        """
        Get human-readable name for a criterion.
        
        Args:
            criterion: The criterion key
            
        Returns:
            Human-readable name
        """
        names = {
            'price': 'Cena',
            'additionalReferences': 'Dodatne reference',
            'additionalTechnicalRequirements': 'Dodatne tehnične zahteve',
            'shorterDeadline': 'Krajši rok dobave',
            'longerWarranty': 'Daljša garancijska doba',
            'costEfficiency': 'Stroškovna učinkovitost',
            'socialCriteria': 'Socialna merila',
            'otherCriteriaCustom': 'Druga merila'
        }
        return names.get(criterion, criterion)
    
    def _has_social_suboptions(self, step_key: str) -> bool:
        """
        Check if social criteria has selected sub-options.
        
        Args:
            step_key: The key for the selection criteria section
            
        Returns:
            True if at least one sub-option is selected
        """
        import logging
        social_options = [
            'youngEmployeesShare',
            'elderlyEmployeesShare',
            'registeredStaffEmployed',
            'averageSalary',
            'otherSocial'
        ]
        
        # Also check if any social criteria has points assigned
        social_ratio_fields = [
            'socialCriteriaYoungRatio',
            'socialCriteriaElderlyRatio', 
            'socialCriteriaStaffRatio',
            'socialCriteriaSalaryRatio',
            'socialCriteriaOtherRatio'
        ]
        
        for option in social_options:
            # Try different key patterns for the checkbox
            possible_keys = [
                f"{step_key}.socialCriteriaOptions.{option}",
                f"general.{step_key}.socialCriteriaOptions.{option}",
                f"lot_1_{step_key}.socialCriteriaOptions.{option}",
            ]
            
            for key in possible_keys:
                value = self.session_state.get(key, None)
                if value is not None:
                    # Handle string 'da' values
                    if isinstance(value, str) and value.lower() == 'da':
                        return True
                    elif value:
                        return True
        
        # Also check if any ratio field has points > 0
        for ratio_field in social_ratio_fields:
            possible_keys = [
                f"{step_key}.{ratio_field}",
                f"general.{step_key}.{ratio_field}",
                f"lot_1_{step_key}.{ratio_field}",
            ]
            
            for key in possible_keys:
                value = self.session_state.get(key, None)
                if value is not None:
                    try:
                        points = float(value) if value else 0
                        if points > 0:
                            logging.debug(f"Found social sub-option with points at {key}: {points}")
                            return True
                    except (ValueError, TypeError):
                        pass
        
        return False
    
    def _validate_cpv_requirements(self, selected_criteria: Dict[str, bool]) -> Tuple[List[str], List[str]]:
        """
        Validate criteria selection against CPV code requirements.
        
        Args:
            selected_criteria: Dictionary of selected criteria
            
        Returns:
            Tuple of (errors, warnings)
        """
        from utils.criteria_validation import (
            check_cpv_requires_social_criteria,
            check_cpv_requires_additional_criteria
        )
        
        errors = []
        warnings = []
        
        # Get CPV codes from session state
        cpv_codes = self._get_cpv_codes()
        
        if not cpv_codes:
            return errors, warnings
        
        # Check if CPV requires social criteria
        social_required = check_cpv_requires_social_criteria(cpv_codes)
        
        if social_required and not selected_criteria.get('socialCriteria'):
            # Check if override is enabled
            override_key = "selectionCriteria_validation_override"
            if not self.session_state.get(override_key, False):
                # Create user-friendly message
                cpv_list = list(social_required.keys())
                if len(cpv_list) > 3:
                    cpv_display = ", ".join(cpv_list[:3]) + f" in še {len(cpv_list) - 3} drugih"
                else:
                    cpv_display = ", ".join(cpv_list)
                
                errors.append(
                    f"CPV kode ({cpv_display}) zahtevajo socialna merila. "
                    f"Prosimo, izberite socialna merila ali omogočite preglasitev."
                )
        
        # Check if CPV requires additional criteria besides price
        additional_required = check_cpv_requires_additional_criteria(cpv_codes)
        
        if additional_required:
            price_selected = selected_criteria.get('price', False)
            # Check if ONLY price is selected
            other_criteria = [k for k, v in selected_criteria.items() if k != 'price' and v]
            
            if price_selected and not other_criteria:
                # Check if override is enabled
                override_key = "selectionCriteria_validation_override"
                if not self.session_state.get(override_key, False):
                    # Create user-friendly message
                    cpv_list = list(additional_required.keys())
                    if len(cpv_list) > 3:
                        cpv_display = ", ".join(cpv_list[:3]) + f" in še {len(cpv_list) - 3} drugih"
                    else:
                        cpv_display = ", ".join(cpv_list)
                    
                    errors.append(
                        f"CPV kode ({cpv_display}) zahtevajo dodatna merila poleg cene. "
                        f"Prosimo, izberite vsaj eno dodatno merilo ali omogočite preglasitev."
                    )
        
        return errors, warnings
    
    def _get_cpv_codes(self) -> List[str]:
        """
        Get CPV codes from session state.
        
        Returns:
            List of CPV codes
        """
        cpv_string = self.session_state.get('projectInfo.cpvCodes', '')
        if not cpv_string:
            return []
        
        # Parse CPV codes (they might be comma-separated)
        cpv_codes = []
        for code in cpv_string.split(','):
            code = code.strip()
            if code:
                # Extract just the code part (before any description)
                if ' ' in code:
                    code = code.split(' ')[0]
                cpv_codes.append(code)
        
        return cpv_codes
    
    def validate_criteria_real_time(self, cpv_codes: List[str], selected_criteria: Dict[str, bool]) -> Tuple[bool, List[str], List[str], Dict]:
        """
        Real-time validation for criteria selection based on CPV codes.
        Used by form renderer for immediate feedback.
        
        Args:
            cpv_codes: List of CPV codes
            selected_criteria: Dictionary of selected criteria
            
        Returns:
            Tuple of (is_valid, errors, warnings, restricted_info)
        """
        errors = []
        warnings = []
        restricted_info = {}
        
        # Check if any criteria is selected
        if not any(selected_criteria.values()):
            warnings.append("Niste izbrali nobenih meril. Pri odpiranju konkurence morate imeti definirana merila.")
            return True, errors, warnings, restricted_info  # Just warning, not error
        
        # Check CPV requirements using existing methods
        cpv_errors, cpv_warnings = self._validate_cpv_requirements(selected_criteria)
        errors.extend(cpv_errors)
        warnings.extend(cpv_warnings)
        
        # Get restriction information for display
        from utils.criteria_validation import (
            check_cpv_requires_social_criteria,
            check_cpv_requires_additional_criteria
        )
        
        restricted_info['social_required'] = check_cpv_requires_social_criteria(cpv_codes)
        restricted_info['additional_required'] = check_cpv_requires_additional_criteria(cpv_codes)
        
        return len(errors) == 0, errors, warnings, restricted_info
    
    def validate_database_record(self, table_name: str, record: Dict[str, Any], 
                                is_update: bool = False, record_id: int = None) -> Tuple[bool, List[str]]:
        """
        Validate database record before insert/update.
        
        Args:
            table_name: Name of the database table
            record: Dictionary of field values
            is_update: Whether this is an update operation
            record_id: ID of record being updated
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Table-specific validation
        if table_name == 'cpv_codes':
            if not self._validate_cpv_code_format(record.get('code')):
                errors.append("Neveljavna oblika CPV kode (npr. 12345678-9)")
        
        elif table_name == 'javna_narocila':
            if record.get('vrednost', 0) < 0:
                errors.append("Vrednost pogodbe ne more biti negativna")
            
            # Validate status
            valid_statuses = ['Osnutek', 'Objavljeno', 'Zaključeno', 'Preklicano']
            if record.get('status') and record['status'] not in valid_statuses:
                errors.append(f"Neveljaven status. Dovoljen: {', '.join(valid_statuses)}")
        
        elif table_name == 'application_logs':
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if record.get('log_level') not in valid_levels:
                errors.append(f"Neveljaven nivo zapisa. Dovoljen: {', '.join(valid_levels)}")
        
        elif table_name == 'drafts':
            # Validate JSON format
            if 'form_data_json' in record:
                try:
                    import json
                    if isinstance(record['form_data_json'], str):
                        json.loads(record['form_data_json'])
                except json.JSONDecodeError:
                    errors.append("Neveljavna JSON oblika podatkov")
        
        # Foreign key validation
        fk_errors = self._validate_foreign_keys(table_name, record)
        errors.extend(fk_errors)
        
        # Unique constraint validation
        unique_errors = self._validate_unique_constraints(table_name, record, is_update, record_id)
        errors.extend(unique_errors)
        
        # Required field validation
        required_errors = self._validate_required_database_fields(table_name, record)
        errors.extend(required_errors)
        
        return len(errors) == 0, errors
    
    def _validate_cpv_code_format(self, code: str) -> bool:
        """
        Validate CPV code format.
        
        Args:
            code: CPV code to validate
            
        Returns:
            True if valid format
        """
        if not code:
            return False
        
        import re
        # CPV code format: 8 digits, hyphen, 1 check digit (e.g., 12345678-9)
        pattern = r'^\d{8}-\d$'
        return bool(re.match(pattern, code))
    
    def _validate_foreign_keys(self, table_name: str, record: Dict[str, Any]) -> List[str]:
        """
        Validate foreign key constraints.
        
        Args:
            table_name: Name of the table
            record: Record data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Define foreign key relationships
        foreign_keys = {
            'cpv_criteria': [
                ('cpv_code', 'cpv_codes', 'code'),
                ('criteria_type_id', 'criteria_types', 'id')
            ],
            'application_logs': [
                ('organization_id', 'organizacija', 'id')
            ]
        }
        
        if table_name in foreign_keys:
            import sqlite3
            import database
            
            try:
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    
                    for fk_field, ref_table, ref_field in foreign_keys[table_name]:
                        if fk_field in record and record[fk_field]:
                            # Check if referenced record exists
                            cursor.execute(
                                f"SELECT COUNT(*) FROM {ref_table} WHERE {ref_field} = ?",
                                (record[fk_field],)
                            )
                            
                            if cursor.fetchone()[0] == 0:
                                errors.append(
                                    f"Tuji ključ kršitev: {fk_field}={record[fk_field]} "
                                    f"ne obstaja v {ref_table}.{ref_field}"
                                )
            
            except Exception as e:
                errors.append(f"Napaka pri preverjanju tujih ključev: {str(e)}")
        
        return errors
    
    def _validate_unique_constraints(self, table_name: str, record: Dict[str, Any], 
                                    is_update: bool = False, record_id: int = None) -> List[str]:
        """
        Validate unique constraints.
        
        Args:
            table_name: Name of the table
            record: Record data
            is_update: Whether this is an update
            record_id: ID of record being updated
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Define unique fields per table
        unique_fields = {
            'cpv_codes': ['code'],
            'criteria_types': ['name'],
            'cpv_criteria': [('cpv_code', 'criteria_type_id')],  # Composite unique
        }
        
        if table_name in unique_fields:
            import sqlite3
            import database
            
            try:
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    
                    for field in unique_fields[table_name]:
                        if isinstance(field, tuple):
                            # Composite unique constraint
                            values = [record.get(f) for f in field]
                            if all(values):
                                where_clause = ' AND '.join([f"{f} = ?" for f in field])
                                query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
                                
                                if is_update and record_id:
                                    query += f" AND id != {record_id}"
                                
                                cursor.execute(query, values)
                                
                                if cursor.fetchone()[0] > 0:
                                    errors.append(
                                        f"Kombinacija {', '.join(field)} že obstaja"
                                    )
                        else:
                            # Single field unique constraint
                            if field in record and record[field]:
                                query = f"SELECT COUNT(*) FROM {table_name} WHERE {field} = ?"
                                
                                if is_update and record_id:
                                    query += f" AND id != {record_id}"
                                
                                cursor.execute(query, (record[field],))
                                
                                if cursor.fetchone()[0] > 0:
                                    errors.append(
                                        f"Vrednost '{record[field]}' za polje '{field}' že obstaja"
                                    )
            
            except Exception as e:
                errors.append(f"Napaka pri preverjanju unikatnosti: {str(e)}")
        
        return errors
    
    def _validate_required_database_fields(self, table_name: str, record: Dict[str, Any]) -> List[str]:
        """
        Validate required fields for database tables.
        
        Args:
            table_name: Name of the table
            record: Record data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Define required fields per table (excluding auto-generated fields)
        required_fields = {
            'drafts': ['timestamp', 'form_data_json'],
            'javna_narocila': ['naziv', 'form_data_json'],
            'cpv_codes': ['code', 'description'],
            'criteria_types': ['name'],
            'cpv_criteria': ['cpv_code', 'criteria_type_id'],
            'organizacija': ['naziv'],
            'application_logs': ['log_level']
        }
        
        if table_name in required_fields:
            for field in required_fields[table_name]:
                if field not in record or not record[field]:
                    errors.append(f"Polje '{field}' je obvezno")
        
        return errors
    
    def _validate_data_types(self, table_name: str, record: Dict[str, Any]) -> List[str]:
        """
        Validate data types for table fields.
        
        Args:
            table_name: Name of the table
            record: Record data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Define expected types for critical fields
        type_definitions = {
            'javna_narocila': {
                'vrednost': (float, int),
                'datum_objave': str,  # Should be date format
            },
            'application_logs': {
                'retention_hours': (int,),
                'line_number': (int,),
            },
            'cpv_criteria': {
                'criteria_type_id': (int,),
            }
        }
        
        if table_name in type_definitions:
            for field, expected_types in type_definitions[table_name].items():
                if field in record and record[field] is not None:
                    if not isinstance(record[field], expected_types):
                        errors.append(
                            f"Polje '{field}' mora biti tipa {expected_types}"
                        )
        
        return errors