# Epic: Form Validation System Enhancement - Brownfield

## Epic Goal
Extend the existing ValidationManager in `utils/validations.py` to implement comprehensive validation for all 14 screens of the procurement form, adding screen-specific conditional logic, field type improvements, and centralized validation rules.

## Epic Description

### Existing System Context
- **Current functionality**: `ValidationManager` class with partial validation for some screens
- **Technology stack**: Python, Streamlit, SQLite, existing validation framework
- **Integration points**: `utils/validations.py` contains ValidationManager, form_renderer.py uses it

### Enhancement Details
- **What's being added**: Complete validation coverage for all 14 screens with conditional logic
- **How it integrates**: Extend existing ValidationManager methods, add new screen-specific validators
- **Success criteria**: All 14 screens validated per requirements, appropriate input types implemented

## Stories

### Story 1: Extend ValidationManager for Screens 1-7
- Add validation methods for customer data (Screen 1)
- Implement document upload validation
- Add legal basis and procedure validations
- Implement lot division rules (min 2 lots)

### Story 2: Extend ValidationManager for Screens 8-14
- Add deadline and time-based validations
- Implement financial guarantee validations
- Add contract extension and framework agreement rules
- Implement negotiation round validations

### Story 3: Enhance Input Fields and User Experience
- Convert time inputs to time pickers
- Implement proper number inputs for amounts
- Add dynamic field width adjustments
- Implement real-time validation feedback

## Detailed Validation Requirements by Screen

### Screen 1 - Naročniki (Customers)
**Validation Rules:**
- Single customer mode: All customer data fields required (name, address, type)
- Multiple customers mode: Minimum 2 customers required, all fields required for each
- Logo upload: If option selected, file upload is required

**Implementation:**
```python
def validate_screen_1_customers(self) -> Tuple[bool, List[str]]:
    """Screen 1: Customer validation"""
    errors = []
    
    if self.session_state.get('clientInfo.multipleClients') == 'da':
        # Count complete client entries
        client_count = 0
        for i in range(1, 11):
            client_name = self.session_state.get(f'clientInfo.client{i}Name', '').strip()
            client_address = self.session_state.get(f'clientInfo.client{i}Address', '').strip()
            client_type = self.session_state.get(f'clientInfo.client{i}Type', '').strip()
            
            if client_name and client_address and client_type:
                client_count += 1
        
        if client_count < 2:
            errors.append(f"Pri več naročnikih morate vnesti podatke za najmanj 2 naročnika (trenutno: {client_count})")
    else:
        # Validate single customer fields
        required = ['clientInfo.singleClientName', 
                   'clientInfo.singleClientAddress',
                   'clientInfo.singleClientType']
        for field in required:
            if not self.session_state.get(field, '').strip():
                field_name = field.split('.')[-1].replace('singleClient', '').replace('Name', ' ime')
                errors.append(f"Polje '{field_name}' je obvezno")
    
    # Logo upload validation
    if self.session_state.get('clientInfo.addLogos') == 'da':
        if not self.session_state.get('clientInfo.logoFile'):
            errors.append("Naložiti morate datoteko z logotipi")
    
    return len(errors) == 0, errors
```

### Screen 2 - CPV & Projekt Info
**Validation Rules:**
- CPV validation: Already exists (keep as-is)
- All fields required except "Interna številka javnega naročila"

**Implementation:** Already covered by existing `_validate_required_fields()`

### Screen 3 - Pravna Podlaga (Legal Basis)
**Validation Rules:**
- If additional legal basis selected → minimum 1 legal basis required

**Implementation:**
```python
def validate_screen_3_legal_basis(self) -> Tuple[bool, List[str]]:
    """Screen 3: Legal basis validation"""
    errors = []
    
    if self.session_state.get('legalBasis.additionalBasis') == 'da':
        basis_count = 0
        for i in range(1, 6):
            if self.session_state.get(f'legalBasis.basis_{i}', '').strip():
                basis_count += 1
        
        if basis_count < 1:
            errors.append("Pri dodatni pravni podlagi morate vnesti najmanj eno podlago")
    
    return len(errors) == 0, errors
```

### Screen 4 - Postopek (Procedure)
**Validation Rules:**
- "Napišite zakaj želite izvesti ta postopek": Optional
- All other fields: Required

**Implementation:** Use existing `_validate_required_fields()` with field configuration

### Screen 5 - Sklopi (Lots)
**Validation Rules:**
- If "po sklopih" selected → minimum 2 lots required
- Per lot: All fields required except "sofinancirano" and "dokumentacija"

**Implementation:** Already partially exists in `_validate_multiple_entries()`

### Screen 6 - Splošno Naročilo
**Validation Rules:**
- All fields required except "sofinancirano" and "dokumentacija"

**Implementation:** Configure in required fields list

### Screen 7 - Tehnične Specifikacije
**Validation Rules:**
- "Naročnik že ima pripravljene tehnične zahteve": Required
- If "Da" selected → minimum 1 document upload required

**Implementation:**
```python
def validate_screen_7_technical_specs(self) -> Tuple[bool, List[str]]:
    """Screen 7: Technical specifications validation"""
    errors = []
    
    has_specs = self.session_state.get('technicalSpecs.hasExisting')
    if not has_specs:
        errors.append("Polje 'Naročnik že ima pripravljene tehnične zahteve' je obvezno")
    elif has_specs == 'da':
        doc_count = self.session_state.get('technicalSpecs.documentCount', 0)
        if doc_count < 1:
            errors.append("Pri tehničnih zahtevah morate naložiti najmanj 1 dokument")
    
    return len(errors) == 0, errors
```

### Screen 8 - Roki (Deadlines)
**Validation Rules:**
- "Rok izvedbe/trajanje": Required
- Conditional fields based on selection: All visible fields required

**Implementation:**
```python
def validate_screen_8_deadlines(self) -> Tuple[bool, List[str]]:
    """Screen 8: Deadlines validation"""
    errors = []
    
    deadline_type = self.session_state.get('deadlines.type')
    if not deadline_type:
        errors.append("Prosimo navedite rok izvedbe oziroma trajanje javnega naročila")
    else:
        # Validate conditional fields based on type
        if deadline_type == 'specific_date':
            if not self.session_state.get('deadlines.specificDate'):
                errors.append("Vnesite konkreten datum")
        elif deadline_type == 'duration':
            if not self.session_state.get('deadlines.duration'):
                errors.append("Vnesite trajanje")
    
    return len(errors) == 0, errors
```

### Screen 9 - Cene & Predračun
**Validation Rules:**
- "Cenovna klavzula": Required (if "drugo" → text field required)
- "Naročnik želi, da": Required
- If "pripravljen predračun" → "Količine" field + 1 document required

**Implementation:**
```python
def validate_screen_9_pricing(self) -> Tuple[bool, List[str]]:
    """Screen 9: Pricing validation"""
    errors = []
    
    price_clause = self.session_state.get('pricing.clause')
    if not price_clause:
        errors.append("Katero cenovno klavzulo bi želeli imeti v pogodbi je obvezno")
    elif price_clause == 'drugo':
        if not self.session_state.get('pricing.clauseOther', '').strip():
            errors.append("Pri drugi cenovni klavzuli morate vnesti opis")
    
    if not self.session_state.get('pricing.clientWants'):
        errors.append("Polje 'Naročnik želi, da' je obvezno")
    
    if self.session_state.get('pricing.hasEstimate') == 'da':
        if not self.session_state.get('pricing.quantities', '').strip():
            errors.append("Polje 'Količine v ponudbenem predračunu' je obvezno")
        if self.session_state.get('pricing.estimateDocCount', 0) < 1:
            errors.append("Naložiti morate najmanj 1 dokument predračuna")
    
    return len(errors) == 0, errors
```

### Screen 10 - Ogled & Pogajanja
**Validation Rules:**
- If "organizira ogled" → minimum 1 appointment (change time to time picker)
- If "vključiti pogajanja" → negotiation topic required, rounds required
- If "posebne želje pogajanja" → text field required

**Implementation:**
```python
def validate_screen_10_negotiations(self) -> Tuple[bool, List[str]]:
    """Screen 10: Site visits and negotiations validation"""
    errors = []
    
    # Site visit validation
    if self.session_state.get('siteVisit.organized') == 'da':
        visit_count = self.session_state.get('siteVisit.appointmentCount', 0)
        if visit_count < 1:
            errors.append("Pri ogledu lokacije morate dodati najmanj 1 termin")
        
        # Validate each appointment has time
        for i in range(1, visit_count + 1):
            if not self.session_state.get(f'siteVisit.appointment{i}_time'):
                errors.append(f"Vnesite uro za {i}. termin ogleda")
    
    # Negotiations validation
    if self.session_state.get('negotiations.include') == 'da':
        topic = self.session_state.get('negotiations.topic')
        if not topic:
            errors.append("Pri pogajanjih morate izbrati temo pogajanj")
        elif topic == 'drugo':
            if not self.session_state.get('negotiations.topicOther', '').strip():
                errors.append("Pri drugi temi pogajanj morate vnesti opis")
        
        rounds = self.session_state.get('negotiations.rounds')
        if not rounds or rounds < 1:
            errors.append("Označite koliko krogov pogajanj boste izvedli")
    
    if self.session_state.get('negotiations.specialRequests') == 'da':
        if not self.session_state.get('negotiations.specialRequestsText', '').strip():
            errors.append("Pri posebnih željah pogajanj morate vnesti besedilo")
    
    return len(errors) == 0, errors
```

### Screen 11 - Pogoji (Conditions)
**Validation Rules:**
- "Neobvezni razlogi za izključitev": Required
- If "specifični razlogi" → minimum 1 option required
- If "specifični pogoji" → minimum 1 option + associated text fields required

**Implementation:**
```python
def validate_screen_11_conditions(self) -> Tuple[bool, List[str]]:
    """Screen 11: Conditions validation"""
    errors = []
    
    exclusion_reasons = self.session_state.get('conditions.exclusionReasons')
    if not exclusion_reasons:
        errors.append("Prosimo označite vse neobvezne razloge za izključitev")
    elif exclusion_reasons == 'specific':
        # Check for at least one specific reason
        specific_count = 0
        for reason in ['financial', 'technical', 'professional']:
            if self.session_state.get(f'conditions.exclusion_{reason}'):
                specific_count += 1
        
        if specific_count < 1:
            errors.append("Pri specifičnih razlogih morate izbrati najmanj eno možnost")
    
    participation = self.session_state.get('conditions.participation')
    if not participation:
        errors.append("Ali želite vključiti pogoje za sodelovanje je obvezno")
    elif participation == 'specific':
        # Check for at least one condition and its text
        condition_count = 0
        for condition in ['economic', 'technical', 'professional']:
            if self.session_state.get(f'conditions.{condition}'):
                condition_count += 1
                # Check for required text field
                if not self.session_state.get(f'conditions.{condition}_text', '').strip():
                    errors.append(f"Vnesite opis za {condition} pogoj")
        
        if condition_count < 1:
            errors.append("Pri specifičnih pogojih morate izbrati najmanj eno možnost")
    
    return len(errors) == 0, errors
```

### Screen 12 - Zavarovanja & Variante
**Validation Rules:**
- "Finančna zavarovanja": Required
- If "da" → minimum 1 option + all revealed fields required
- "Variantne ponudbe": Required (if "da" → both text fields required)

**Implementation:**
```python
def validate_screen_12_guarantees(self) -> Tuple[bool, List[str]]:
    """Screen 12: Financial guarantees validation"""
    errors = []
    
    guarantees = self.session_state.get('guarantees.required')
    if not guarantees:
        errors.append("Ali zahtevate finančna zavarovanja je obvezno")
    elif guarantees == 'da':
        guarantee_types = ['tender', 'performance', 'warranty']
        selected_count = 0
        
        for g_type in guarantee_types:
            if self.session_state.get(f'guarantees.{g_type}'):
                selected_count += 1
                
                method = self.session_state.get(f'guarantees.{g_type}_method')
                if not method:
                    errors.append(f"Izberite način zavarovanja za {g_type}")
                elif method == 'deposit':
                    # Validate deposit fields
                    required_fields = {
                        'trr': 'TRR',
                        'bank': 'Banka naročnika',
                        'bic': 'BIC',
                        'amount': 'Višina zavarovanja'
                    }
                    for field, label in required_fields.items():
                        if not self.session_state.get(f'guarantees.{g_type}_{field}'):
                            errors.append(f"{label} je obvezno pri denarnem depozitu")
        
        if selected_count < 1:
            errors.append("Pri finančnih zavarovanjih morate izbrati najmanj eno opcijo")
    
    # Variant offers validation
    variants = self.session_state.get('variants.allowed')
    if not variants:
        errors.append("Ali dopuščate predložitev variantnih ponudb je obvezno")
    elif variants == 'da':
        if not self.session_state.get('variants.description', '').strip():
            errors.append("Pri variantnih ponudbah morate izpolniti opis")
        if not self.session_state.get('variants.requirements', '').strip():
            errors.append("Pri variantnih ponudbah morate izpolniti zahteve")
    
    return len(errors) == 0, errors
```

### Screen 13 - Merila (Criteria)
**Validation Rules:**
- Existing validation (keep as-is in `validate_merila()`)

### Screen 14 - Pogodbe (Contracts)
**Validation Rules:**
- Framework agreement: end_date >= start_date, period text required
- If "odpiranje konkurence" → frequency field required
- If extension possible → reasons and duration required
- "Dodatne informacije": Optional

**Implementation:**
```python
def validate_screen_14_contracts(self) -> Tuple[bool, List[str]]:
    """Screen 14: Contract validation"""
    errors = []
    
    contract_type = self.session_state.get('contractInfo.type')
    
    if contract_type == 'okvirni sporazum':
        start_date = self.session_state.get('contractInfo.frameworkStartDate')
        end_date = self.session_state.get('contractInfo.frameworkEndDate')
        
        if start_date and end_date:
            from datetime import datetime
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if end < start:
                    errors.append("Datum konca okvirnega sporazuma ne more biti pred datumom začetka")
            except:
                pass
        
        if not self.session_state.get('contractInfo.frameworkPeriod', '').strip():
            errors.append("Obdobje okvirnega sporazuma je obvezno")
    
    elif contract_type == 'odpiranje konkurence':
        if not self.session_state.get('contractInfo.competitionFrequency', '').strip():
            errors.append("Pogostost odpiranja konkurence je obvezna")
    
    # Extension validation
    if self.session_state.get('contractInfo.canBeExtended') == 'da':
        if not self.session_state.get('contractInfo.extensionReasons', '').strip():
            errors.append("Navedite razloge za možnost podaljšanja pogodbe")
        if not self.session_state.get('contractInfo.extensionDuration', '').strip():
            errors.append("Navedite trajanje podaljšanja pogodbe")
    
    # Additional info is optional - no validation needed
    
    return len(errors) == 0, errors
```

## Field Type Improvements

### Proposed Field Type Changes

| Field | Current Type | New Type | Reason |
|-------|-------------|----------|---------|
| `siteVisit.appointmentTime` | Text | Time Picker | Better UX, prevents format errors |
| `guarantees.*_amount` | Text | Number (currency) | Clear formatting, validation |
| `negotiations.rounds` | Text | Number (1-10) | Ensure valid range |
| `deadlines.duration` | Text | Number + Unit Select | Clear time specification |
| `pricing.quantities` | Text | Number (min=0) | Positive values only |
| `contractInfo.extensionDuration` | Text | Text (pattern) | Structured duration input |
| All description fields | Text | Textarea (5 rows) | Better visibility |
| Short codes/IDs | Text | Text (maxlength) | Prevent overflow |

### Implementation of Field Types

```python
def get_field_type_config(field_key: str) -> dict:
    """Get appropriate input type configuration for a field"""
    
    field_configs = {
        # Time fields
        'siteVisit.appointmentTime': {
            'type': 'time',
            'format': 'HH:MM',
            'help': 'Format: UU:MM'
        },
        
        # Currency fields
        'guarantees.tender_amount': {
            'type': 'number',
            'min': 0,
            'step': 0.01,
            'format': 'currency',
            'suffix': 'EUR'
        },
        'guarantees.performance_amount': {
            'type': 'number',
            'min': 0,
            'step': 0.01,
            'format': 'currency',
            'suffix': 'EUR'
        },
        'guarantees.warranty_amount': {
            'type': 'number',
            'min': 0,
            'step': 0.01,
            'format': 'currency',
            'suffix': 'EUR'
        },
        
        # Integer fields
        'negotiations.rounds': {
            'type': 'number',
            'min': 1,
            'max': 10,
            'step': 1,
            'help': 'Število krogov (1-10)'
        },
        'pricing.quantities': {
            'type': 'number',
            'min': 0,
            'step': 1
        },
        
        # Large text areas
        'negotiations.specialRequestsText': {
            'type': 'textarea',
            'rows': 5,
            'maxlength': 2000
        },
        'contractInfo.extensionReasons': {
            'type': 'textarea',
            'rows': 4,
            'maxlength': 1000
        },
        'variants.description': {
            'type': 'textarea',
            'rows': 5,
            'maxlength': 1500
        },
        'variants.requirements': {
            'type': 'textarea',
            'rows': 5,
            'maxlength': 1500
        },
        'contractInfo.additionalInfo': {
            'type': 'textarea',
            'rows': 6,
            'maxlength': 3000
        },
        
        # Short text fields with limits
        'projectInfo.internalNumber': {
            'type': 'text',
            'maxlength': 50,
            'required': False
        },
        'guarantees.tender_trr': {
            'type': 'text',
            'pattern': 'SI56 \\d{4} \\d{4} \\d{4} \\d{3}',
            'placeholder': 'SI56 XXXX XXXX XXXX XXX'
        },
        'guarantees.tender_bic': {
            'type': 'text',
            'maxlength': 11,
            'pattern': '[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?'
        }
    }
    
    # Default configuration for unspecified fields
    default_config = {'type': 'text'}
    
    return field_configs.get(field_key, default_config)
```

## Integration with Form Renderer

### Updating form_renderer.py

```python
# In form_renderer.py, update field rendering logic:

def render_field(field_key, field_schema, value=None):
    """Render a form field with appropriate input type"""
    
    # Get field type configuration
    field_config = get_field_type_config(field_key)
    
    if field_config['type'] == 'time':
        return st.time_input(
            field_schema.get('title', field_key),
            value=value,
            help=field_config.get('help')
        )
    
    elif field_config['type'] == 'number':
        col1, col2 = st.columns([4, 1])
        with col1:
            value = st.number_input(
                field_schema.get('title', field_key),
                min_value=field_config.get('min', None),
                max_value=field_config.get('max', None),
                step=field_config.get('step', 1),
                value=value or field_config.get('min', 0),
                help=field_config.get('help')
            )
        with col2:
            if field_config.get('suffix'):
                st.write("")  # Spacing
                st.write(field_config['suffix'])
        return value
    
    elif field_config['type'] == 'textarea':
        return st.text_area(
            field_schema.get('title', field_key),
            value=value or '',
            height=field_config.get('rows', 3) * 30,
            max_chars=field_config.get('maxlength'),
            help=field_config.get('help')
        )
    
    else:  # Default text input
        return st.text_input(
            field_schema.get('title', field_key),
            value=value or '',
            max_chars=field_config.get('maxlength'),
            placeholder=field_config.get('placeholder'),
            help=field_config.get('help')
        )
```

## Centralized Validation Call

### Main validation orchestrator in ValidationManager

```python
def validate_all_screens(self) -> Dict[int, Tuple[bool, List[str]]]:
    """Validate all screens and return results by screen number"""
    
    validation_methods = {
        1: self.validate_screen_1_customers,
        2: lambda: self._validate_required_fields(['projectInfo']),
        3: self.validate_screen_3_legal_basis,
        4: lambda: self._validate_required_fields(['procedure']),
        5: lambda: (self._validate_multiple_entries(), self.errors),
        6: lambda: self._validate_required_fields(['generalOrder']),
        7: self.validate_screen_7_technical_specs,
        8: self.validate_screen_8_deadlines,
        9: self.validate_screen_9_pricing,
        10: self.validate_screen_10_negotiations,
        11: self.validate_screen_11_conditions,
        12: self.validate_screen_12_guarantees,
        13: self.validate_merila,
        14: self.validate_screen_14_contracts
    }
    
    results = {}
    for screen_num, validator in validation_methods.items():
        try:
            results[screen_num] = validator()
        except Exception as e:
            results[screen_num] = (False, [f"Napaka validacije: {str(e)}"])
    
    return results
```

## Compatibility Requirements

- ✅ Extends existing ValidationManager class without breaking changes
- ✅ Maintains existing validation method signatures
- ✅ Integrates with current session state structure
- ✅ Compatible with existing error display system
- ✅ Preserves existing validation logic for CPV, merila, and database

## Risk Mitigation

- **Primary Risk:** Breaking existing validation logic
- **Mitigation:** Add new methods without modifying existing ones, use feature flags for gradual rollout
- **Rollback Plan:** Comment out new validation calls in form_renderer, keep old logic intact

## Testing Strategy

1. **Unit Tests for Each Validation Method**
   - Test each screen validation independently
   - Test conditional logic branches
   - Test edge cases (empty values, invalid formats)

2. **Integration Tests**
   - Test full form flow with valid data
   - Test validation triggers at appropriate times
   - Test error message display

3. **Regression Tests**
   - Ensure existing CPV validation works
   - Ensure merila validation unchanged
   - Ensure database validation intact

## Definition of Done

- ✅ All 14 screens have validation methods in ValidationManager
- ✅ Conditional logic implemented for all requirements
- ✅ Field type improvements integrated with form_renderer
- ✅ All validation messages in Slovenian
- ✅ Existing validations continue to work
- ✅ Integration tested with complete form flow
- ✅ Documentation updated with validation rules
- ✅ No performance regression in form rendering

## Implementation Priority

1. **High Priority (Story 1)**
   - Screen 1: Customer validation (complex logic)
   - Screen 5: Lot validation (already partial)
   - Screen 7: Document upload validation

2. **Medium Priority (Story 2)**
   - Screen 10: Negotiations (complex conditional)
   - Screen 12: Financial guarantees (nested conditions)
   - Screen 14: Contract dates validation

3. **Lower Priority (Story 3)**
   - Field type improvements
   - Real-time validation feedback
   - UI/UX enhancements

## Success Metrics

- Zero validation bypasses for required fields
- 100% coverage of business rules from requirements
- <100ms validation execution time per screen
- Clear, actionable error messages for all validation failures
- No regression in existing functionality

---

## Story Manager Handoff

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This enhances the existing ValidationManager class in utils/validations.py
- Integration points: Existing validate_step() method, session state structure, form_renderer.py
- Existing patterns: Conditional validation with _validate_conditional_requirements(), multi-entry with _validate_multiple_entries()
- Critical compatibility: Must not break existing validation logic, extend rather than replace
- Each story must verify existing validation features remain functional

The epic should maintain the current validation architecture while adding comprehensive coverage for all 14 screens per the detailed requirements specified above. Pay special attention to the conditional validation logic where field requirements change based on user selections."