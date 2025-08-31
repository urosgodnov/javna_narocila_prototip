# Epic: Financial Field Validations - Brownfield Enhancement

## Epic Goal
Implement comprehensive validation for financial fields (IBAN, SWIFT/BIC, Bank, currency amounts) with integration to the existing bank registry, ensuring data accuracy and consistency for procurement financial information while providing helpful auto-completion features and proper European number formatting.

## Epic Description

### Existing System Context:
- **Current functionality**: Basic text input fields for TRR (IBAN), Bank name, and SWIFT codes without validation
- **Technology stack**: Python, Streamlit, SQLite with newly implemented BankManager
- **Integration points**: 
  - `database.py` - BankManager with bank registry
  - `utils/validations.py` - validation framework
  - `json_files/SEZNAM_POTREBNIH_PODATKOV.json` - form schema
  - Session state management

### Enhancement Details:
- **What's being added/changed**: 
  - IBAN format and checksum validation (mod97 algorithm)
  - SWIFT/BIC format validation
  - Bank name validation with registry lookup
  - Auto-population of bank name from IBAN
  - Auto-population of SWIFT from bank selection
  
- **How it integrates**: 
  - Extend ValidationManager with financial validation methods
  - Leverage existing BankManager for lookups
  - Add UI helpers for auto-completion
  - Implement validation with clear error messages
  
- **Success criteria**: 
  - Invalid IBANs are rejected with clear error messages
  - Valid Slovenian IBANs auto-populate bank name
  - SWIFT codes are validated against pattern
  - Bank names can be selected from registry or entered manually
  - All financial data is validated on entry

## Stories

### Story 1: IBAN Validation and Bank Integration
**Description**: Implement IBAN validation with mod97 checksum and bank registry integration
- Implement `validate_iban()` function with mod97 algorithm
- Support Slovenian IBAN format (SI56 + 15 characters)
- Extract bank code from IBAN and lookup in BankManager
- Auto-populate bank name when valid IBAN entered
- Add formatting helper to display IBAN with spaces (SI56 XXXX XXXX XXXX XXX)
- Handle international IBANs with basic validation

### Story 2: SWIFT/BIC Validation and Registry Lookup
**Description**: Implement SWIFT code validation and bi-directional bank registry integration
- Implement `validate_swift_bic()` with pattern validation
- Support 8 and 11 character formats
- Validate structure: 4 letters (bank) + 2 letters (country) + 2 chars (location) + 3 optional
- When bank selected from registry, auto-populate SWIFT
- When SWIFT entered, validate against registry
- Add validation messages in Slovenian

### Story 3: Currency Format Validation and Display
**Description**: Implement European currency format validation and formatting helpers
- Implement `validate_currency_amount()` for amount fields
- Support format: xxx.xxx.xxx,00 (dots for thousands, comma for decimals)
- Create `format_currency_display()` helper for proper display
- Parse both dot and comma decimal inputs for user convenience
- Validate amounts are positive numbers
- Add validation for maximum reasonable amounts (configurable)
- Apply to fields: estimatedValue, guaranteedFunds, all price fields

## Implementation Approach
- [x] Direct implementation with proper validation from start
- [x] Bank registry integrated into database
- [x] Clean validation functions in ValidationManager
- [x] No legacy constraints or compatibility needs

## Implementation Benefits
- **Data Quality**: Validated financial data from day one
- **Bank Integration**: Direct bank selection from registry
- **Error Prevention**: Invalid codes rejected immediately
- **Clean Implementation**: No legacy format support needed
- **User Experience**: Auto-completion saves time and reduces errors

## Definition of Done
- [ ] All three stories completed with acceptance criteria met
- [ ] IBAN validation works for Slovenian and common EU formats
- [ ] SWIFT validation follows ISO 9362 standard
- [ ] Bank registry integration provides helpful auto-completion
- [ ] Existing financial data remains accessible
- [ ] Validation messages are clear and in Slovenian

### Story 4: Bank Field Integration (Leveraging Existing Implementation)
**Description**: Connect form fields to already implemented bank registry
- Use existing BankManager from database.py (Story 1 of epic_banks.md already implemented)
- Create bank dropdown using registry data
- Auto-populate bank name when valid IBAN entered
- Auto-populate SWIFT when bank selected
- Validate consistency between fields
- **Note**: Admin UI for banks already implemented (Story 2 of epic_banks.md)

## Technical Details

### Currency Format Validation
```python
def validate_currency_amount(value_str):
    # Remove thousand separators (dots)
    # Replace comma with dot for decimal
    # Validate is valid number
    # Format for display: xxx.xxx.xxx,00
    
def format_currency_for_display(amount):
    # Convert number to xxx.xxx.xxx,00 format
    # Add dots for thousands
    # Use comma for decimal separator
    # Always show 2 decimal places
```

### IBAN Validation Algorithm (Mod97)
```python
def validate_iban_checksum(iban):
    # Move first 4 chars to end
    rearranged = iban[4:] + iban[:4]
    # Convert letters to numbers (A=10, B=11, etc.)
    numeric = ''.join(str(10 + ord(c) - ord('A')) if c.isalpha() else c 
                      for c in rearranged)
    # Calculate mod 97
    return int(numeric) % 97 == 1
```

### Slovenian IBAN Structure
- Country: SI (Slovenia)
- Check digits: 56 (always for Slovenia)
- Bank code: 5 digits (maps to BankManager)
- Account: 10 digits

### SWIFT/BIC Structure
- Bank code: 4 letters (e.g., LJBA for NLB)
- Country: 2 letters (SI for Slovenia)
- Location: 2 alphanumeric
- Branch: 3 alphanumeric (optional)

### Bank Registry Integration
```python
# Extract bank from IBAN
bank_code = iban[4:9]  # After SI56
bank = bank_manager.get_bank_by_iban_code(bank_code)

# Auto-populate
if bank:
    st.session_state['bank_name'] = bank['name']
    st.session_state['swift'] = bank['swift']
```

## Dependencies
- **Already Implemented**: BankManager in database.py (from epic_banks.md story 1)
- **Already Implemented**: Bank admin UI (from epic_banks.md story 2)
- Bank registry must be populated (migration script exists)
- No external validation libraries needed

## Estimated Effort
- Story 1: 6-8 hours (IBAN validation and integration)
- Story 2: 4-6 hours (SWIFT validation)
- Story 3: 4-5 hours (Currency format validation)
- Story 4: 2-3 hours (Bank field integration - leveraging existing BankManager)
- **Total**: 16-22 hours (2-3 days)

## Future Enhancements
- Support for foreign bank validation
- BIC directory integration for international banks
- SEPA validation rules
- Payment reference validation (RF reference)

## Notes
- Originally part of validation epic, separated as per epic scope refinement
- Leverages recently implemented bank registry (story_bank_database.md)
- Consider adding IBAN calculator for generating valid test data
- Validation should be educational - explain why IBAN is invalid