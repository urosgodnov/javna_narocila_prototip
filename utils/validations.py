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
    
    def _safe_strip(self, value):
        """Safely strip whitespace from a value, handling both strings and non-strings."""
        if isinstance(value, str):
            return value.strip()
        return value
    
    def _find_selection_criteria_key(self, step_keys):
        """Find the selectionCriteria key from the step keys (might be prefixed)."""
        for key in step_keys:
            if 'selectionCriteria' in key:
                return key
        return 'selectionCriteria'  # Default fallback
    
    def _collect_array_data(self):
        """
        Collect array data from individual session state fields into proper array structure.
        For example, collect clientInfo.clients.0.name, clientInfo.clients.1.name etc. 
        into clientInfo.clients array.
        """
        # Check for clients array data
        if not self.session_state.get('clientInfo.isSingleClient', True):
            # Multiple clients mode - collect array data
            clients = []
            i = 0
            while True:
                # Check if this index exists
                name_key = f'clientInfo.clients.{i}.name'
                if name_key not in self.session_state:
                    break
                    
                # Collect data for this client
                client = {
                    'name': self.session_state.get(f'clientInfo.clients.{i}.name', ''),
                    'address': self.session_state.get(f'clientInfo.clients.{i}.address', ''),
                    'legalRepresentative': self.session_state.get(f'clientInfo.clients.{i}.legalRepresentative', ''),
                    'type': self.session_state.get(f'clientInfo.clients.{i}.type', '')
                }
                clients.append(client)
                i += 1
                
            # Update the array in session state
            self.session_state['clientInfo.clients'] = clients
        
        # Collect legal basis array data
        if self.session_state.get('legalBasis.useAdditional', False):
            legal_bases = []
            i = 0
            while True:
                field_key = f'legalBasis.additionalLegalBases.{i}'
                if field_key not in self.session_state:
                    break
                basis_text = self.session_state.get(field_key, '')
                if basis_text:  # Include even empty strings to preserve order
                    legal_bases.append(basis_text)
                i += 1
            
            if legal_bases:
                self.session_state['legalBasis.additionalLegalBases'] = legal_bases
        
        # Collect lots array data
        if self.session_state.get('lotsInfo.hasLots', False):
            lots = []
            i = 0
            while True:
                name_key = f'lots.{i}.name'
                if name_key not in self.session_state:
                    break
                
                lot = {
                    'name': self.session_state.get(f'lots.{i}.name', ''),
                    'description': self.session_state.get(f'lots.{i}.description', ''),
                    'cpvCodes': self.session_state.get(f'lots.{i}.cpvCodes', ''),
                    'estimatedValue': self.session_state.get(f'lots.{i}.estimatedValue', '')
                }
                lots.append(lot)
                i += 1
            
            if lots:
                self.session_state['lots'] = lots
        
        # Collect cofinancers array data
        if self.session_state.get('orderType.isCofinanced', False):
            cofinancers = []
            i = 0
            while True:
                name_key = f'orderType.cofinancers.{i}.name'
                if name_key not in self.session_state:
                    break
                
                cofinancer = {
                    'name': self.session_state.get(f'orderType.cofinancers.{i}.name', ''),
                    'program': self.session_state.get(f'orderType.cofinancers.{i}.program', ''),
                    'logo': self.session_state.get(f'orderType.cofinancers.{i}.logo', ''),
                    'specialRequirements': self.session_state.get(f'orderType.cofinancers.{i}.specialRequirements', '')
                }
                cofinancers.append(cofinancer)
                i += 1
            
            if cofinancers:
                self.session_state['orderType.cofinancers'] = cofinancers
    
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
        
        # Collect array data from individual fields
        self._collect_array_data()
        
        # Map step numbers to screen-specific validation methods
        screen_validators = {
            0: self.validate_screen_1_customers,  # Step 0 = Screen 1 (clientInfo)
            2: self.validate_screen_3_legal_basis,  # Step 2 = Screen 3 (legalBasis)
            4: self.validate_screen_5_lots,  # Step 4 = Screen 5 (lotsInfo)
            5: self.validate_order_type,  # Step 5 = Screen 6 (orderType)
            6: self.validate_screen_7_technical_specs,  # Step 6 = Screen 7 (technicalSpecs)
            7: self.validate_execution_deadline,  # Step 7 = Screen 8 (executionDeadline)
            8: self.validate_price_info,  # Step 8 = Screen 9 (priceInfo)
            9: self.validate_inspection_negotiations,  # Step 9 = Screen 10 (inspectionInfo, negotiationsInfo)
            10: self.validate_participation_conditions,  # Step 10 = Screen 11 (participationAndExclusion, participationConditions)
            11: self.validate_financial_guarantees,  # Step 11 = Screen 12 (financialGuarantees, variantOffers)
            12: lambda: self.validate_merila(self._find_selection_criteria_key(step_keys)),  # Step 12 = Screen 13 (selectionCriteria/Merila)
            13: self.validate_contract_info  # Step 13 = Screen 14 (contractInfo, otherInfo)
        }
        
        # Call screen-specific validator if available
        if step_number in screen_validators:
            is_valid, screen_errors = screen_validators[step_number]()
            self.errors.extend(screen_errors)
        
        # Expand section keys to field keys
        expanded_keys = self._expand_step_keys(step_keys)
        
        # Run generic validations (skip _validate_required_fields for step 0 to avoid duplicates)
        if step_number != 0:
            self._validate_required_fields(expanded_keys, step_number)
        self._validate_dropdowns(expanded_keys)
        
        # Always run _validate_multiple_entries - it handles multiple clients and lots
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
    
    def _validate_required_fields(self, field_keys: List[str], step_number: int = None):
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
            # Skip single client fields if in multiple client mode
            is_single_client = self.session_state.get('clientInfo.isSingleClient', True)
            if not is_single_client and key.startswith('clientInfo.singleClient'):
                continue
            
            # Skip multiple client fields if in single client mode  
            if is_single_client and key == 'clientInfo.clients':
                continue
            
            field_value = self.session_state.get(key, '')
            
            # Get field schema - handle nested fields
            field_schema = None
            is_required = False  # Initialize is_required
            
            if '.' in key:
                parts = key.split('.')
                current_schema = self.schema.get('properties', {})
                
                # Special handling for array items (e.g., clientInfo.clients.0.legalRepresentative)
                if len(parts) >= 3 and parts[1] == 'clients' and parts[2].isdigit():
                    # This is a client array item
                    # Get the clients array schema
                    if 'clientInfo' in current_schema and 'clients' in current_schema['clientInfo'].get('properties', {}):
                        clients_schema = current_schema['clientInfo']['properties']['clients']
                        if 'items' in clients_schema and 'properties' in clients_schema['items']:
                            field_name = parts[3] if len(parts) > 3 else ''
                            field_schema = clients_schema['items']['properties'].get(field_name, {})
                            # Check if this field is required in the items schema
                            if field_name in clients_schema['items'].get('required', []):
                                is_required = True
                else:
                    # Normal nested field handling
                    for part in parts[:-1]:
                        if part in current_schema:
                            current_schema = current_schema[part].get('properties', {})
                    if parts[-1] in current_schema:
                        field_schema = current_schema[parts[-1]]
            else:
                field_schema = self.schema.get('properties', {}).get(key, {})
            
            # Check if this field is required (if not already determined by array handling)
            if not is_required:
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
                'projectInfo.cpvCodes',
                'submissionProcedure.procedure',
                'contractInfo.type'
            ]
            
            # Add conditional client fields based on mode
            is_single_client = self.session_state.get('clientInfo.isSingleClient', True)
            if is_single_client:
                critical_fields.extend([
                    'clientInfo.singleClientName',
                    'clientInfo.singleClientAddress',
                    'clientInfo.singleClientLegalRepresentative'
                ])
            
            # Screen-specific required fields (excluding optional ones)
            # Screen 2: All fields except internal number (based on actual schema)
            screen_2_required = [
                'projectInfo.projectName',
                'projectInfo.projectSubject',
                'projectInfo.cpvCodes'
                # internalProjectNumber is optional
            ]
            
            # Screen 4: All fields except reason description  
            screen_4_required = [
                # Note: procedureType moved to submissionProcedure.procedure
                'procedureInfo.submissionDeadline',
                'procedureInfo.openingDate'
            ]
            
            # Screen 6: Required fields for general order
            screen_6_required = [
                # estimatedValue handled in validate_order_type with proper message
                'orderType.deliveryLocation',
                'orderType.deliveryDeadline',
                'orderType.paymentTerms',
                'orderType.contractDuration'
            ]
            
            # Add screen-specific fields to critical if we're on that screen
            # Note: Steps are 0-indexed (step 1 = second screen with projectInfo)
            # Use step_number parameter if available, otherwise fall back to current_step
            current_step = step_number if step_number is not None else self.session_state.get('current_step')
            
            if current_step == 1:  # Step 1 = Screen 2 (projectInfo)
                critical_fields.extend([f for f in screen_2_required if f not in critical_fields])
            elif current_step == 3:  # Step 3 = Screen 4 (procedureInfo)
                critical_fields.extend([f for f in screen_4_required if f not in critical_fields])
            elif current_step == 5:  # Step 5 = Screen 6 (generalOrder)
                critical_fields.extend([f for f in screen_6_required if f not in critical_fields])
            
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
            ('submissionProcedure.procedure', 'Postopek oddaje javnega naročila'),
            ('contractInfo.type', 'Vrsta pogodbe'),
            ('submissionInfo.submissionMethod', 'Način oddaje ponudb'),
            ('tenderInfo.evaluationCriteria', 'Merilo za izbor')
        ]
        
        # Note: singleClientType doesn't exist in modern schema - removed
        
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
        # Multiple clients validation - check if NOT single client mode
        is_single_client = self.session_state.get('clientInfo.isSingleClient', True)
        if not is_single_client:
            # Check if we have clients array (as per JSON schema)
            clients_array = self.session_state.get('clientInfo.clients', [])
            
            if clients_array:
                # Array structure - validate each client
                client_count = 0
                incomplete_clients = []
                
                for idx, client in enumerate(clients_array):
                    if isinstance(client, dict):
                        name = client.get('name', '').strip()
                        address = client.get('address', '').strip()
                        legal_rep = client.get('legalRepresentative', '').strip()
                        
                        # Check if all required fields are present
                        missing = []
                        if not name:
                            missing.append('naziv')
                        if not address:
                            missing.append('naslov')
                        if not legal_rep:
                            missing.append('zakoniti zastopnik')
                        
                        if not missing:
                            client_count += 1
                        elif name or address or legal_rep:  # Partially filled
                            incomplete_clients.append(f"Naročnik {idx+1}: manjka {', '.join(missing)}")
                
                if client_count < 2:
                    self.errors.append(
                        f"Pri več naročnikih morate vnesti podatke za najmanj 2 naročnika "
                        f"(trenutno popolnih: {client_count})"
                    )
                    for incomplete in incomplete_clients:
                        self.errors.append(incomplete)
            else:
                # No clients array - maybe error or not initialized
                self.errors.append("Pri več naročnikih morate vnesti podatke za najmanj 2 naročnika")
        
        # Note: Lot validation moved to validate_screen_5_lots() to use correct field names
    
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
            extension_reasons = self._safe_strip(self.session_state.get('contractInfo.extensionReasons', ''))
            extension_duration = self._safe_strip(self.session_state.get('contractInfo.extensionDuration', ''))
            
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
    
    # ============ SCREEN-SPECIFIC VALIDATION METHODS ============
    
    def validate_screen_1_customers(self) -> Tuple[bool, List[str]]:
        """
        Validate customer data for screen 1.
        Requirements:
        - Single customer: all fields required
        - Multiple customers: minimum 2 complete entries (handled by _validate_multiple_entries)
        - Logo upload: file required if option selected
        """
        errors = []
        
        # For multiple customers, the validation is already handled in _validate_multiple_entries()
        # We just need to handle single customer here
        if self.session_state.get('clientInfo.multipleClients') != 'da':
            # Single customer validation
            required_fields = {
                'clientInfo.singleClientName': 'Ime naročnika',
                'clientInfo.singleClientAddress': 'Naslov naročnika', 
                'clientInfo.singleClientLegalRepresentative': 'Zakoniti zastopnik (ime in priimek)'
            }
            
            for field_key, field_label in required_fields.items():
                value = self._safe_strip(self.session_state.get(field_key, '')) if self.session_state.get(field_key) else ''
                if not value:
                    errors.append(f"{field_label} je obvezno polje")
        
        # Logo validation - check if user wants logo but hasn't uploaded file
        if self.session_state.get('clientInfo.wantsLogo', False):
            # Check both direct key (Streamlit widget) and file_info key (saved metadata)
            logo_file = self.session_state.get('clientInfo.logo')
            logo_file_info = self.session_state.get('clientInfo.logo_file_info')
            
            if not logo_file and not logo_file_info:
                errors.append("Pri dodajanju logotipov morate naložiti datoteko")
        
        return len(errors) == 0, errors
    
    def validate_screen_3_legal_basis(self) -> Tuple[bool, List[str]]:
        """
        Validate legal basis for screen 3.
        Requirement: If additional legal basis selected, at least one entry required.
        """
        errors = []
        
        # Check boolean field (modern schema)
        if self.session_state.get('legalBasis.useAdditional', False):
            # Check array field (additionalLegalBases)
            legal_bases = self.session_state.get('legalBasis.additionalLegalBases', [])
            
            # Also check for individual fields (form renderer might store as separate fields)
            if not legal_bases:
                # Try to collect from individual fields
                collected_bases = []
                i = 0
                while True:
                    field_key = f'legalBasis.additionalLegalBases.{i}'
                    if field_key in self.session_state:
                        basis_text = self.session_state.get(field_key, '').strip()
                        if basis_text:
                            collected_bases.append(basis_text)
                        i += 1
                    else:
                        break
                legal_bases = collected_bases
            
            # Check if we have at least one non-empty entry
            valid_bases = [b for b in legal_bases if b and b.strip()]
            
            if len(valid_bases) < 1:
                errors.append("Pri dodatni pravni podlagi morate vnesti najmanj eno podlago")
        
        return len(errors) == 0, errors
    
    def validate_screen_5_lots(self) -> Tuple[bool, List[str]]:
        """
        Validate lot division for screen 5.
        Requirements:
        - If divided into lots, minimum 2 lots required
        - Each lot must have required fields filled
        """
        errors = []
        
        # Check boolean field (modern schema)
        has_lots = self.session_state.get('lotsInfo.hasLots', False)
        
        if has_lots:
            # Get lots array (might need collection first)
            lots = self.session_state.get('lots', [])
            
            # If lots array is empty, try to collect from individual fields
            if not lots:
                collected_lots = []
                i = 0
                while True:
                    name_key = f'lots.{i}.name'
                    if name_key not in self.session_state:
                        break
                    
                    lot = {
                        'name': self.session_state.get(f'lots.{i}.name', ''),
                        'description': self.session_state.get(f'lots.{i}.description', ''),
                        'cpvCodes': self.session_state.get(f'lots.{i}.cpvCodes', ''),
                        'estimatedValue': self.session_state.get(f'lots.{i}.estimatedValue', '')
                    }
                    collected_lots.append(lot)
                    i += 1
                lots = collected_lots
            
            # Check minimum 2 lots requirement
            if len(lots) < 2:
                errors.append("Pri delitvi na sklope morate imeti najmanj 2 sklopa")
            
            # Check each lot has required fields
            complete_lots = 0
            for idx, lot in enumerate(lots):
                if isinstance(lot, dict):
                    name = lot.get('name', '').strip()
                    description = lot.get('description', '').strip()
                    cpv = lot.get('cpvCodes', '').strip()
                    # estimatedValue might be optional
                    
                    if name and description and cpv:
                        complete_lots += 1
                    elif name or description or cpv:  # Partially filled
                        errors.append(f"Sklop {idx+1}: izpolnite vse obvezne podatke (naziv, opis, CPV kode)")
            
            if complete_lots < len(lots) and len(lots) >= 2:
                # Only show this if we have enough lots but some are incomplete
                pass  # Individual errors already added above
        
        return len(errors) == 0, errors
    
    def validate_order_type(self) -> Tuple[bool, List[str]]:
        """
        Validate order type fields (step 5/6).
        Requirements:
        - estimatedValue is required
        - If cofinanced, require cofinancer details
        """
        errors = []
        
        # Check estimated value - try multiple possible keys
        estimated_value = None
        
        # Try different possible keys where the value might be stored
        possible_keys = [
            'general.orderType.estimatedValue',  # General mode key (no lots)
            'orderType.estimatedValue',           # Direct key (fallback)
        ]
        
        # Add keys for all possible lots
        lots = self.session_state.get('lots', [])
        for i in range(len(lots)):
            possible_keys.append(f'lot_{i}.orderType.estimatedValue')
        
        for key in possible_keys:
            if key in self.session_state:
                estimated_value = self.session_state.get(key)
                break
        
        # If still not found, search for any key with estimatedValue
        if estimated_value is None:
            for key in self.session_state.__dict__.keys() if hasattr(self.session_state, '__dict__') else []:
                if 'estimatedValue' in key and self.session_state.get(key):
                    estimated_value = self.session_state.get(key)
                    break
        
        # Check if value exists and is greater than 0
        if estimated_value is None or estimated_value == '':
            errors.append("Ocenjena vrednost javnega naročila (EUR brez DDV) ne sme biti prazno")
        else:
            # Convert to float for comparison
            try:
                value_float = float(estimated_value)
                if value_float <= 0:
                    errors.append("Ocenjena vrednost javnega naročila mora biti večja od 0")
            except (ValueError, TypeError):
                errors.append("Ocenjena vrednost javnega naročila mora biti številka")
        
        # Check cofinancing - try multiple possible keys
        is_cofinanced = False
        cofinanced_keys = [
            'general.orderType.isCofinanced',     # General mode key (no lots)
            'orderType.isCofinanced',              # Direct key (fallback)
        ]
        
        # Add keys for all possible lots
        for i in range(len(lots)):
            cofinanced_keys.append(f'lot_{i}.orderType.isCofinanced')
        
        import logging
        
        for key in cofinanced_keys:
            if key in self.session_state:
                value = self.session_state.get(key, False)
                logging.info(f"[validate_order_type] Checking {key}: {value} (type: {type(value)})")
                # Handle both boolean and string values
                if value == True or value == 'true' or value == 'da':
                    is_cofinanced = True
                    break
        
        # If checkbox not found but we have cofinancers, assume it's cofinanced
        if not is_cofinanced:
            # Check if we have any cofinancer data
            prefixes = ['general.orderType', 'orderType']
            # Add lot prefixes
            for i in range(len(lots)):
                prefixes.append(f'lot_{i}.orderType')
            
            for prefix in prefixes:
                # Check for array
                array_key = f'{prefix}.cofinancers'
                if array_key in self.session_state and self.session_state.get(array_key):
                    logging.info(f"[validate_order_type] Found cofinancers array at {array_key}, assuming cofinanced")
                    is_cofinanced = True
                    break
                
                # Check for individual fields
                name_key = f'{prefix}.cofinancers.0.name'
                if name_key in self.session_state and self.session_state.get(name_key):
                    logging.info(f"[validate_order_type] Found cofinancer data at {name_key}, assuming cofinanced")
                    is_cofinanced = True
                    break
        
        logging.info(f"[validate_order_type] Final is_cofinanced: {is_cofinanced}")
        
        if is_cofinanced:
            # Check cofinancers array - try multiple possible keys
            cofinancers = []
            cofinancer_keys = [
                'general.orderType.cofinancers',
                'orderType.cofinancers',
                'lot_0.orderType.cofinancers'
            ]
            
            for key in cofinancer_keys:
                if key in self.session_state:
                    cofinancers = self.session_state.get(key, [])
                    logging.info(f"[validate_order_type] Found cofinancers at {key}: {cofinancers}")
                    break
            
            # Try to collect from individual fields if array is empty
            if not cofinancers:
                logging.info("[validate_order_type] Trying to collect cofinancers from individual fields")
                collected_cofinancers = []
                # Try different key patterns
                prefixes = ['general.orderType', 'orderType', 'lot_0.orderType']
                for prefix in prefixes:
                    i = 0
                    while True:
                        name_key = f'{prefix}.cofinancers.{i}.name'
                        if name_key not in self.session_state:
                            break
                        
                        name_value = self.session_state.get(f'{prefix}.cofinancers.{i}.name', '')
                        program_value = self.session_state.get(f'{prefix}.cofinancers.{i}.program', '')
                        logging.info(f"[validate_order_type] Found cofinancer {i}: name={name_value}, program={program_value}")
                        
                        cofinancer = {
                            'name': name_value,
                            'program': program_value
                        }
                        collected_cofinancers.append(cofinancer)
                        i += 1
                    
                    if collected_cofinancers:
                        logging.info(f"[validate_order_type] Collected {len(collected_cofinancers)} cofinancers with prefix {prefix}")
                        break  # Found cofinancers with this prefix
                
                cofinancers = collected_cofinancers
            
            # Validate at least one cofinancer with required fields
            has_valid_cofinancer = False
            
            # If we have placeholder objects, check the actual field values
            if cofinancers and all(not c or c == {} for c in cofinancers):
                logging.info("[validate_order_type] Found placeholder objects, checking individual fields")
                # We have placeholder objects, check individual fields
                for idx in range(len(cofinancers)):
                    # Try to find the actual values in session state
                    name = None
                    program = None
                    
                    # Try different key patterns
                    for prefix in ['general.orderType', 'orderType', 'lot_0.orderType']:
                        name_key = f'{prefix}.cofinancers.{idx}.name'
                        program_key = f'{prefix}.cofinancers.{idx}.program'
                        
                        if name_key in self.session_state:
                            name = self.session_state.get(name_key, '')
                            program = self.session_state.get(program_key, '')
                            logging.info(f"[validate_order_type] Found cofinancer {idx} at {prefix}: name={name}, program={program}")
                            break
                    
                    if name and program:
                        if name.strip() and program.strip():
                            has_valid_cofinancer = True
                    elif name or program:  # Partially filled
                        if not name or not name.strip():
                            errors.append(f"Sofinancer {idx+1}: Vnesite polni naziv in naslov sofinancerja")
                        if not program or not program.strip():
                            errors.append(f"Sofinancer {idx+1}: Vnesite naziv, področje in oznako programa/projekta")
            else:
                # Normal validation for properly structured cofinancers
                for idx, cofinancer in enumerate(cofinancers):
                    if isinstance(cofinancer, dict):
                        name = cofinancer.get('name', '').strip()
                        program = cofinancer.get('program', '').strip()
                        
                        if name and program:
                            has_valid_cofinancer = True
                        elif name or program:  # Partially filled
                            if not name:
                                errors.append(f"Sofinancer {idx+1}: Vnesite polni naziv in naslov sofinancerja")
                            if not program:
                                errors.append(f"Sofinancer {idx+1}: Vnesite naziv, področje in oznako programa/projekta")
            
            if not has_valid_cofinancer:
                errors.append("Pri sofinanciranem naročilu morate vnesti podatke o vsaj enem sofinancerju")
        
        return len(errors) == 0, errors
    
    def validate_screen_7_technical_specs(self) -> Tuple[bool, List[str]]:
        """
        Validate technical specifications for screen 7.
        Requirements:
        - Technical specs field is required
        - If specs exist, minimum 1 document required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Try different possible keys for hasSpecifications field
        has_specs = None
        possible_keys = [
            'general.technicalSpecifications.hasSpecifications',  # General mode
            'technicalSpecifications.hasSpecifications',          # Direct key
        ]
        
        # Add lot-specific keys
        for i in range(len(lots)):
            possible_keys.append(f'lot_{i}.technicalSpecifications.hasSpecifications')
        
        for key in possible_keys:
            if key in self.session_state:
                has_specs = self.session_state.get(key)
                break
        
        if not has_specs or has_specs not in ['da', 'ne']:
            errors.append("Polje 'Naročnik že ima pripravljene tehnične zahteve / specifikacije' je obvezno")
        elif has_specs == 'da':
            # Check document count - also try multiple keys
            doc_count = 0
            doc_keys = [
                'general.technicalSpecifications.documentCount',
                'technicalSpecifications.documentCount',
            ]
            
            for i in range(len(lots)):
                doc_keys.append(f'lot_{i}.technicalSpecifications.documentCount')
            
            for key in doc_keys:
                if key in self.session_state:
                    doc_count = self.session_state.get(key, 0)
                    break
            
            if isinstance(doc_count, str):
                try:
                    doc_count = int(doc_count)
                except ValueError:
                    doc_count = 0
            
            if doc_count < 1:
                errors.append("Pri obstoječih tehničnih zahtevah morate naložiti najmanj 1 dokument")
        
        return len(errors) == 0, errors
    
    def validate_execution_deadline(self) -> Tuple[bool, List[str]]:
        """
        Validate execution deadline fields.
        Requirements:
        - Type selection is required
        - For date type: start and end dates required
        - For duration types: positive integer required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Try different possible keys for type field
        deadline_type = None
        type_keys = [
            'general.executionDeadline.type',  # General mode
            'executionDeadline.type',           # Direct key
        ]
        
        # Add lot-specific keys
        for i in range(len(lots)):
            type_keys.append(f'lot_{i}.executionDeadline.type')
        
        for key in type_keys:
            if key in self.session_state:
                deadline_type = self.session_state.get(key)
                break
        
        if not deadline_type or deadline_type == '':
            errors.append("Prosimo izberite način določitve roka izvedbe")
            return len(errors) == 0, errors
        
        # Get the prefix where we found the type
        prefix = None
        for key in type_keys:
            if key in self.session_state and self.session_state.get(key) == deadline_type:
                prefix = key.replace('.type', '')
                break
        
        # Validate based on selected type
        if deadline_type == 'datumsko':
            # Check start and end dates
            start_date = self.session_state.get(f'{prefix}.startDate')
            end_date = self.session_state.get(f'{prefix}.endDate')
            
            if not start_date:
                errors.append("Datum začetka je obvezen pri datumskem roku")
            if not end_date:
                errors.append("Datum konca je obvezen pri datumskem roku")
                
        elif deadline_type == 'v dnevih':
            days = self.session_state.get(f'{prefix}.days')
            if days is None or days == '':
                errors.append("Število dni je obvezno")
            else:
                try:
                    days_int = int(days)
                    if days_int <= 0:
                        errors.append("Število dni mora biti pozitivno celo število")
                    elif days_int != float(days):
                        errors.append("Število dni mora biti celo število (brez decimalnih mest)")
                except (ValueError, TypeError):
                    errors.append("Število dni mora biti veljavno celo število")
                    
        elif deadline_type == 'v mesecih':
            months = self.session_state.get(f'{prefix}.months')
            if months is None or months == '':
                errors.append("Število mesecev je obvezno")
            else:
                try:
                    months_int = int(months)
                    if months_int <= 0:
                        errors.append("Število mesecev mora biti pozitivno celo število")
                    elif months_int != float(months):
                        errors.append("Število mesecev mora biti celo število (brez decimalnih mest)")
                except (ValueError, TypeError):
                    errors.append("Število mesecev mora biti veljavno celo število")
                    
        elif deadline_type == 'v letih':
            years = self.session_state.get(f'{prefix}.years')
            if years is None or years == '':
                errors.append("Število let je obvezno")
            else:
                try:
                    years_int = int(years)
                    if years_int <= 0:
                        errors.append("Število let mora biti pozitivno celo število")
                    elif years_int != float(years):
                        errors.append("Število let mora biti celo število (brez decimalnih mest)")
                except (ValueError, TypeError):
                    errors.append("Število let mora biti veljavno celo število")
        
        return len(errors) == 0, errors
    
    def validate_price_info(self) -> Tuple[bool, List[str]]:
        """
        Validate price info fields (Step 8).
        Requirements:
        - Price clause selection is required
        - If 'drugo' selected, description required
        - If prepared estimate exists, document required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Try different possible keys for price clause
        price_clause = None
        clause_keys = [
            'general.priceInfo.priceClause',  # General mode
            'priceInfo.priceClause',           # Direct key
        ]
        
        # Add lot-specific keys
        for i in range(len(lots)):
            clause_keys.append(f'lot_{i}.priceInfo.priceClause')
        
        prefix = None
        for key in clause_keys:
            if key in self.session_state:
                price_clause = self.session_state.get(key)
                prefix = key.replace('.priceClause', '')
                break
        
        if not price_clause or price_clause == '':
            errors.append("Katero cenovno klavzulo bi želeli imeti v pogodbi je obvezno")
        elif price_clause == 'drugo':
            # Check for other description
            other_desc = self.session_state.get(f'{prefix}.priceClauseOther', '').strip()
            if not other_desc:
                errors.append("Pri izbiri 'drugo' morate vnesti opis cenovne klavzule")
        
        # Check if prepared estimate exists - correct field name
        has_estimate = self.session_state.get(f'{prefix}.hasOfferBillOfQuantities')
        if has_estimate == True or has_estimate == 'true':  # Boolean field
            # Check if document is uploaded
            doc_field = f'{prefix}.offerBillOfQuantitiesDocument'
            doc_uploaded = self.session_state.get(doc_field)
            
            # Also check for file info in session
            file_info_key = f'{doc_field}_file_info'
            has_file_info = file_info_key in self.session_state
            
            if not doc_uploaded and not has_file_info:
                errors.append("Pri pripravljenem ponudbenem predračunu morate naložiti dokument")
        
        return len(errors) == 0, errors
    
    def validate_inspection_negotiations(self) -> Tuple[bool, List[str]]:
        """
        Validate inspection and negotiations (Step 9).
        Requirements:
        - If site visit organized, minimum 1 appointment required
        - If negotiations included, topic and rounds required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Check inspection info - correct field name is hasInspection
        organized_visit = None
        inspection_keys = [
            'general.inspectionInfo.hasInspection',
            'inspectionInfo.hasInspection',
        ]
        
        for i in range(len(lots)):
            inspection_keys.append(f'lot_{i}.inspectionInfo.hasInspection')
        
        inspection_prefix = None
        for key in inspection_keys:
            if key in self.session_state:
                organized_visit = self.session_state.get(key)
                inspection_prefix = key.replace('.hasInspection', '')
                break
        
        if organized_visit == True or organized_visit == 'true':
            # Check for inspection dates array or individual fields
            dates_found = False
            
            # Try to find inspection dates
            dates_array_key = f'{inspection_prefix}.inspectionDates'
            if dates_array_key in self.session_state:
                dates = self.session_state.get(dates_array_key, [])
                if len(dates) > 0:
                    dates_found = True
                    # Check each date has required fields
                    # Arrays might be stored as empty dicts with data in separate keys
                    for i in range(len(dates)):
                        # Check for date and time in separate session keys
                        date_key = f'{inspection_prefix}.inspectionDates.{i}.date'
                        time_key = f'{inspection_prefix}.inspectionDates.{i}.time'
                        
                        date_value = self.session_state.get(date_key)
                        time_value = self.session_state.get(time_key)
                        
                        if not date_value:
                            errors.append(f"Vnesite datum za {i+1}. termin ogleda")
                        if not time_value:
                            errors.append(f"Vnesite uro za {i+1}. termin ogleda")
            
            # Try individual fields
            if not dates_found:
                date_key = f'{inspection_prefix}.inspectionDates.0.date'
                if date_key in self.session_state and self.session_state.get(date_key):
                    dates_found = True
            
            if not dates_found:
                errors.append("Pri organiziranem ogledu morate dodati najmanj 1 termin")
            
            # Check inspection location
            location = self.session_state.get(f'{inspection_prefix}.inspectionLocation', '').strip()
            if not location:
                errors.append("Kam naj pridejo potencialni ponudniki za ogled je obvezno polje")
        
        # Check negotiations - correct field name is hasNegotiations
        include_negotiations = None
        negotiation_keys = [
            'general.negotiationsInfo.hasNegotiations',
            'negotiationsInfo.hasNegotiations',
        ]
        
        for i in range(len(lots)):
            negotiation_keys.append(f'lot_{i}.negotiationsInfo.hasNegotiations')
        
        negotiation_prefix = None
        for key in negotiation_keys:
            if key in self.session_state:
                include_negotiations = self.session_state.get(key)
                negotiation_prefix = key.replace('.hasNegotiations', '')
                break
        
        if include_negotiations == True or include_negotiations == 'true':
            # Check topic - correct field name is negotiationSubject
            topic = self.session_state.get(f'{negotiation_prefix}.negotiationSubject')
            if not topic:
                errors.append("V zvezi s čim bi se želeli pogajati je obvezno")
            elif topic == 'drugo':
                other_topic = self.session_state.get(f'{negotiation_prefix}.otherNegotiationSubject', '').strip()
                if not other_topic:
                    errors.append("Pri izbiri 'drugo' morate vnesti opis teme pogajanj")
            
            # Check rounds - this is a string enum field, not integer
            rounds = self.session_state.get(f'{negotiation_prefix}.negotiationRounds')
            if not rounds:
                errors.append("Označite koliko krogov pogajanj boste izvedli")
            
            # Check special wishes if set
            has_wishes = self.session_state.get(f'{negotiation_prefix}.hasSpecialWishes')
            if has_wishes == True or has_wishes == 'true':
                wishes_text = self.session_state.get(f'{negotiation_prefix}.specialNegotiationWishes', '').strip()
                if not wishes_text:
                    errors.append("Pri posebnih željah v zvezi s pogajanji morate vnesti besedilo")
        
        return len(errors) == 0, errors
    
    def validate_participation_conditions(self) -> Tuple[bool, List[str]]:
        """
        Validate participation and exclusion conditions (Step 10).
        Requirements:
        - Exclusion reasons selection required
        - If specific conditions, descriptions required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Check exclusion reasons - using correct field name from schema
        exclusion_type = None
        exclusion_keys = [
            'general.participationAndExclusion.exclusionReasonsSelection',
            'participationAndExclusion.exclusionReasonsSelection',
        ]
        
        for i in range(len(lots)):
            exclusion_keys.append(f'lot_{i}.participationAndExclusion.exclusionReasonsSelection')
        
        exclusion_prefix = None
        for key in exclusion_keys:
            if key in self.session_state:
                exclusion_type = self.session_state.get(key)
                exclusion_prefix = key.replace('.exclusionReasonsSelection', '')
                break
        
        if not exclusion_type:
            errors.append("Prosimo označite vse neobvezne razloge za izključitev")
        elif exclusion_type == 'specifični razlogi':
            # Check for at least one specific reason selected
            # Based on the actual field names in the JSON schema
            specific_reasons = [
                'exclusionReason_a',  # Criminal conviction
                'exclusionReason_b',  # Tax obligations
                'exclusionReason_c',  # Social security
                'exclusionReason_ch', # Insolvency
                'exclusionReason_d',  # Professional misconduct
                'exclusionReason_e',  # Conflict of interest
                'exclusionReason_f',  # Contract deficiencies
                'exclusionReason_g',  # Comparable sanctions
                'exclusionReason_h'   # Other
            ]
            
            selected_count = 0
            for reason in specific_reasons:
                if self.session_state.get(f'{exclusion_prefix}.{reason}'):
                    selected_count += 1
            
            if selected_count < 1:
                errors.append("Pri specifičnih razlogih morate izbrati najmanj eno možnost")
        
        # Check participation conditions - using correct field name from schema
        condition_type = None
        condition_keys = [
            'general.participationConditions.participationSelection',
            'participationConditions.participationSelection',
        ]
        
        for i in range(len(lots)):
            condition_keys.append(f'lot_{i}.participationConditions.participationSelection')
        
        condition_prefix = None
        for key in condition_keys:
            if key in self.session_state:
                condition_type = self.session_state.get(key)
                condition_prefix = key.replace('.participationSelection', '')
                break
        
        if not condition_type:
            errors.append("Ali želite vključiti pogoje za sodelovanje je obvezno")
        elif condition_type == 'da, specifični pogoji':
            # Check each section for selected fields
            # Professional Activity Section fields
            prof_fields = [
                'professionalRegister', 'businessRegister', 'specificLicense',
                'organizationMembership', 'professionalOther', 'professionalAI'
            ]
            
            # Economic Financial Section fields
            econ_fields = [
                'generalTurnover', 'specificTurnover', 'averageTurnover',
                'averageSpecificTurnover', 'financialRatio', 'professionalInsurance',
                'accountNotBlocked', 'otherEconomic', 'economicAI'
            ]
            
            # Technical Professional Section fields
            tech_fields = [
                'companyReferences', 'staffReferences', 'staffRequirements',
                'qualityCertificates', 'technicalOther', 'technicalAI'
            ]
            
            # Check if at least one field is selected in any section
            has_professional = any(
                self.session_state.get(f'{condition_prefix}.professionalActivitySection.{field}')
                for field in prof_fields
            )
            
            has_economic = any(
                self.session_state.get(f'{condition_prefix}.economicFinancialSection.{field}')
                for field in econ_fields
            )
            
            has_technical = any(
                self.session_state.get(f'{condition_prefix}.technicalProfessionalSection.{field}')
                for field in tech_fields
            )
            
            # Check if at least one section has selections
            if not (has_professional or has_economic or has_technical):
                errors.append("Pri specifičnih pogojih morate izbrati najmanj eno možnost v katerikoli sekciji")
            
            # Check for required descriptions where fields are selected
            # Professional Activity checks
            for field in prof_fields:
                if field == 'professionalAI':
                    continue  # AI field doesn't need description
                if self.session_state.get(f'{condition_prefix}.professionalActivitySection.{field}'):
                    detail_field = field + 'Details'
                    desc = self.session_state.get(f'{condition_prefix}.professionalActivitySection.{detail_field}', '').strip()
                    if not desc:
                        errors.append(f"Vnesite opis za izbrano polje v sekciji 'Ustreznost za opravljanje poklicne dejavnosti'")
                        break  # Only show one error per section
            
            # Economic Financial checks
            for field in econ_fields:
                if field == 'economicAI':
                    continue  # AI field doesn't need description
                if self.session_state.get(f'{condition_prefix}.economicFinancialSection.{field}'):
                    detail_field = field + 'Details'
                    desc = self.session_state.get(f'{condition_prefix}.economicFinancialSection.{detail_field}', '').strip()
                    if not desc:
                        errors.append(f"Vnesite opis za izbrano polje v sekciji 'Ekonomski in finančni položaj'")
                        break  # Only show one error per section
            
            # Technical Professional checks
            for field in tech_fields:
                if field == 'technicalAI':
                    continue  # AI field doesn't need description
                if self.session_state.get(f'{condition_prefix}.technicalProfessionalSection.{field}'):
                    detail_field = field + 'Details'
                    desc = self.session_state.get(f'{condition_prefix}.technicalProfessionalSection.{detail_field}', '').strip()
                    if not desc:
                        errors.append(f"Vnesite opis za izbrano polje v sekciji 'Tehnična in strokovna sposobnost'")
                        break  # Only show one error per section
        
        return len(errors) == 0, errors
    
    def validate_financial_guarantees(self) -> Tuple[bool, List[str]]:
        """
        Validate financial guarantees and variant offers (Step 11).
        Requirements:
        - Financial guarantees selection required
        - If guarantees required, details needed
        - Variant offers selection required
        """
        errors = []
        
        # Get lots for dynamic key generation
        lots = self.session_state.get('lots', [])
        
        # Check financial guarantees - using correct field name from schema
        guarantees_required = None
        guarantee_keys = [
            'general.financialGuarantees.requiresFinancialGuarantees',
            'financialGuarantees.requiresFinancialGuarantees',
        ]
        
        for i in range(len(lots)):
            guarantee_keys.append(f'lot_{i}.financialGuarantees.requiresFinancialGuarantees')
        
        guarantee_prefix = None
        for key in guarantee_keys:
            if key in self.session_state:
                guarantees_required = self.session_state.get(key)
                guarantee_prefix = key.replace('.requiresFinancialGuarantees', '')
                break
        
        if not guarantees_required:
            errors.append("Ali zahtevate finančna zavarovanja je obvezno")
        elif guarantees_required == 'da, zahtevamo finančna zavarovanja':
            # Check guarantee types - using correct field names from schema
            guarantee_types = [
                ('fzSeriousness', 'Zavarovanje za resnost ponudbe'),
                ('fzPerformance', 'Zavarovanje za dobro izvedbo'),
                ('fzWarranty', 'Zavarovanje za odpravo napak')
            ]
            
            selected_guarantees = 0
            for g_type, g_label in guarantee_types:
                if self.session_state.get(f'{guarantee_prefix}.{g_type}.required'):
                    selected_guarantees += 1
                    
                    # Check instrument/method
                    instrument = self.session_state.get(f'{guarantee_prefix}.{g_type}.instrument')
                    if not instrument:
                        errors.append(f"Izberite instrument zavarovanja za {g_label}")
                    elif instrument == 'denarni depozit':
                        # Check deposit fields - they are nested under depositDetails
                        deposit_fields = [
                            ('iban', 'TRR naročnika (IBAN)'),
                            ('bank', 'Banka naročnika'),
                            ('swift', 'BIC (SWIFT)')
                        ]
                        
                        for field_key, field_label in deposit_fields:
                            field_value = self.session_state.get(f'{guarantee_prefix}.{g_type}.depositDetails.{field_key}', '')
                            # Handle both string and non-string values
                            if isinstance(field_value, str):
                                field_value = field_value.strip()
                            if not field_value:
                                errors.append(f"{field_label} je obvezno za denarni depozit ({g_label})")
                    
                    # Check amount field (it's directly under the guarantee type)
                    amount = self.session_state.get(f'{guarantee_prefix}.{g_type}.amount', '')
                    # Handle both string and numeric values
                    if isinstance(amount, str):
                        amount = amount.strip()
                    if not amount and amount != 0:
                        errors.append(f"Višina zavarovanja je obvezna za {g_label}")
                    else:
                        try:
                            amount_float = float(amount)
                            if amount_float <= 0:
                                errors.append(f"Višina zavarovanja mora biti pozitivna ({g_label})")
                        except ValueError:
                            errors.append(f"Višina zavarovanja mora biti številka ({g_label})")
            
            if selected_guarantees < 1:
                errors.append("Pri finančnih zavarovanjih morate izbrati najmanj eno vrsto")
        
        # Check variant offers - using correct field name from schema
        variants_allowed = None
        variant_keys = [
            'general.variantOffers.allowVariants',
            'variantOffers.allowVariants',
        ]
        
        for i in range(len(lots)):
            variant_keys.append(f'lot_{i}.variantOffers.allowVariants')
        
        variant_prefix = None
        for key in variant_keys:
            if key in self.session_state:
                variants_allowed = self.session_state.get(key)
                variant_prefix = key.replace('.allowVariants', '')
                break
        
        if not variants_allowed:
            errors.append("Ali dopuščate predložitev variantnih ponudb je obvezno")
        elif variants_allowed == 'da':
            # Check for minimal requirements field (correct field name from schema)
            min_req = self.session_state.get(f'{variant_prefix}.minimalRequirements', '')
            # Handle both string and non-string values
            if isinstance(min_req, str):
                min_req = min_req.strip()
            
            if not min_req:
                errors.append("Pri variantnih ponudbah morate navesti minimalne zahteve")
        
        return len(errors) == 0, errors
    
    def validate_contract_info(self) -> Tuple[bool, List[str]]:
        """
        Validate contract info (Step 13 - last step).
        Requirements:
        - Framework agreement dates validation
        - Contract extension details if allowed
        """
        errors = []
        
        # Contract info is not lot-specific, it's global
        contract_type = self.session_state.get('contractInfo.type')
        
        # Debug logging to understand what's happening
        import logging
        logging.info(f"[validate_contract_info] contract_type value: '{contract_type}'")
        
        # First, ensure we have a contract type selected
        if not contract_type:
            errors.append("Vrsta sklenitve je obvezna")
            return len(errors) == 0, errors
        
        # Validate based on contract type
        if contract_type == 'pogodba':
            # For regular contracts, check contract validity
            contract_period_type = self.session_state.get('contractInfo.contractPeriodType', '')
            if contract_period_type == 'z veljavnostjo':
                validity = self._safe_strip(self.session_state.get('contractInfo.contractValidity', ''))
                if not validity:
                    errors.append("Veljavnost pogodbe je obvezna")
            elif contract_period_type == 'za obdobje od-do':
                # Use correct field names from JSON schema
                start_date = self.session_state.get('contractInfo.contractDateFrom')
                end_date = self.session_state.get('contractInfo.contractDateTo')
                if not start_date:
                    errors.append("Obdobje od je obvezno")
                if not end_date:
                    errors.append("Obdobje do je obvezno")
                
                # Validate date logic if both dates are present
                if start_date and end_date:
                    # Handle both date objects and strings
                    from datetime import datetime, date
                    try:
                        # Convert to comparable format
                        if isinstance(start_date, date):
                            start = start_date
                        else:
                            start = datetime.strptime(str(start_date), '%Y-%m-%d').date()
                        
                        if isinstance(end_date, date):
                            end = end_date
                        else:
                            end = datetime.strptime(str(end_date), '%Y-%m-%d').date()
                        
                        if end < start:
                            errors.append("Končni datum ne more biti pred začetnim datumom")
                    except (ValueError, TypeError) as e:
                        logging.debug(f"Date validation error: {e}")
        
        elif contract_type == 'okvirni sporazum':
            # Check framework duration (text field, not dates)
            duration = self._safe_strip(self.session_state.get('contractInfo.frameworkDuration', ''))
            if not duration:
                errors.append("Obdobje okvirnega sporazuma je obvezno")
            
            # Check framework agreement type
            framework_type = self.session_state.get('contractInfo.frameworkType', '')
            if not framework_type:
                errors.append("Vrsta okvirnega sporazuma je obvezna")
            
            # If competition reopening, check frequency
            if framework_type and 'odpiranjem konkurence' in framework_type:
                frequency = self._safe_strip(self.session_state.get('contractInfo.competitionFrequency', ''))
                if not frequency:
                    errors.append("Pogostost odpiranja konkurence je obvezna pri tej vrsti okvirnega sporazuma")
        
        
        # Check contract extension
        if self.session_state.get('contractInfo.canBeExtended') == 'da':
            reasons = self._safe_strip(self.session_state.get('contractInfo.extensionReasons', ''))
            duration = self._safe_strip(self.session_state.get('contractInfo.extensionDuration', ''))
            
            if not reasons:
                errors.append("Navedite razloge za možnost podaljšanja pogodbe")
            if not duration:
                errors.append("Navedite trajanje podaljšanja pogodbe")
        
        return len(errors) == 0, errors
    
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