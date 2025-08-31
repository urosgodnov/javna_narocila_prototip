# Epic: Input Form Field Enhancement - Brownfield Enhancement

## Epic Goal
Enhance the procurement form's data quality by separating combined address fields into structured components (street, house number) and implementing proper validation for each field, improving data consistency and search capabilities.

## Epic Description

### Existing System Context:
- **Current functionality**: Address data is collected in combined fields (`singleClientStreetAddress`, `streetAddress`)
- **Technology stack**: Python, Streamlit, SQLite, JSON Schema validation
- **Integration points**: 
  - `utils/validations.py` - validation logic
  - `json_files/SEZNAM_POTREBNIH_PODATKOV.json` - form schema
  - Session state management for form data
  - Existing database with combined address data

### Enhancement Details:
- **What's being added/changed**: 
  - Split combined address fields into separate street and house number fields
  - Add specific validation for each field type
  - Implement clean field separation from the start
  - No migration needed due to zero existing data
  
- **How it integrates**: 
  - Extend existing JSON schema with new field definitions
  - Add new validation functions to ValidationManager
  - Create data migration utilities for existing records
  - Update UI components to use new fields while supporting old format
  
- **Success criteria**: 
  - New forms use separated address fields
  - Existing data remains accessible
  - Validation prevents invalid address formats
  - Search and filtering work with both formats

## Stories

### Story 1: Schema and Validation Implementation
**Description**: Define new field structure in JSON schema and implement validation functions for ALL address fields
- **Single Client**: Add `singleClientStreet`, `singleClientHouseNumber`, `singleClientCity` (separate from postal)
- **Clients Array**: Add `street`, `houseNumber`, `city` to each client item
- **Cofinancers**: Add `cofinancerStreet`, `cofinancerHouseNumber`, `cofinancerCity` fields
- **Mixed Order Cofinancers**: Same structure in mixedOrderComponents
- Implement validation functions:
  - `validate_street()` - min 2 chars, not just numbers
  - `validate_house_number()` - pattern: `^[0-9]+[a-zA-Z]?(/[0-9]+[a-zA-Z]?)?$` (e.g., "15", "15a", "15/2")
  - `validate_city()` - min 2 chars, only letters, spaces and hyphens
  - `validate_postal_code()` - exactly 4 digits (1000-9999), pattern: `^[0-9]{4}$`
  - `validate_slovenian_postal_code()` - validates against known Slovenian postal codes
  - `validate_address_fields()` - orchestrator function for all address fields
- Update ValidationManager to use new validators

### Story 2: UI Components and Rendering
**Description**: Update form rendering to display separated fields with proper layout
- Modify field renderer to show street and house number side-by-side
- Add proper labels and help text in Slovenian
- Implement conditional rendering based on schema version
- Ensure responsive layout on different screen sizes
- Add visual indicators for required fields

### Story 3: UI Implementation and Testing
**Description**: Update form UI to use separated fields
- Update form renderer to display separate input fields
- Add proper field labels and placeholders
- Implement real-time validation feedback
- Update field ordering for better UX
- Test all address entry points in the form

## Implementation Approach
- [x] Direct implementation of separated fields (no data to migrate)
- [x] Clean schema design without legacy constraints
- [x] Can optimize database structure if needed
- [x] Follow existing Streamlit patterns for consistency

## Implementation Benefits
- **Clean Start**: No existing data means optimal field design
- **Better Data Quality**: Structured fields from the beginning
- **Improved Search**: Can search by street or house number separately
- **Future Ready**: Proper structure for integrations and reporting
- **No Migration Complexity**: Direct implementation without legacy concerns

## Definition of Done
- [ ] All three stories completed with acceptance criteria met
- [ ] All forms use separated fields with validation
- [ ] Validation rules properly enforce field formats:
  - [ ] Postal codes validated as 4 digits (1000-9999)
  - [ ] Street names require minimum 2 characters
  - [ ] House numbers follow Slovenian format (15, 15a, 15/2)
  - [ ] Cities validated for proper characters
- [ ] No regression in existing address-related functionality
- [ ] User documentation updated with new field requirements

## Technical Details

### Postal Code Validation Details
```python
def validate_postal_code(postal_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validates Slovenian postal code format.
    - Must be exactly 4 digits
    - Range: 1000-9999
    - Examples: 1000 (Ljubljana), 2000 (Maribor), 3000 (Celje), 4000 (Kranj)
    """
    if not re.match(r'^[0-9]{4}$', postal_code):
        return False, "Poštna številka mora vsebovati točno 4 številke"
    
    code = int(postal_code)
    if code < 1000 or code > 9999:
        return False, "Poštna številka mora biti med 1000 in 9999"
    
    return True, None
```

### New Field Structure
```json
{
  "singleClientStreet": {
    "type": "string",
    "title": "Ulica",
    "minLength": 2,
    "description": "Samo ime ulice, brez hišne številke"
  },
  "singleClientHouseNumber": {
    "type": "string", 
    "title": "Hišna številka",
    "pattern": "^[0-9]+[a-zA-Z]?(/[0-9]+[a-zA-Z]?)?$",
    "description": "Hišna številka (npr. 12, 12a, 12/1)"
  }
}
```

### Migration Examples
**Single Client / Clients Array:**
- "Dunajska cesta 56" → street: "Dunajska cesta", houseNumber: "56"
- "Trg revolucije 1" → street: "Trg revolucije", houseNumber: "1"
- "Koroška 12a/2" → street: "Koroška", houseNumber: "12a/2"

**Cofinancers (cofinancerStreetAddress):**
- "Kotnikova 28" → cofinancerStreet: "Kotnikova", cofinancerHouseNumber: "28"
- "Gregorčičeva ulica 20" → cofinancerStreet: "Gregorčičeva ulica", cofinancerHouseNumber: "20"

**Entities Affected:**
- clientInfo.singleClient* fields
- clientInfo.clients[] array items
- orderType.cofinancers[] array items
- orderType.mixedOrderComponents[].cofinancers[] nested arrays

### Validation Rules
1. **Street validation**:
   - Minimum 2 characters
   - Cannot be only numbers
   - Allowed: letters, numbers, spaces, dots, hyphens

2. **House number validation**:
   - Must start with number
   - Optional letter suffix (a-z)
   - Optional slash with additional number/letter

## Dependencies
- No external library dependencies
- Requires coordination with database team for schema migration
- UI changes need review from UX team

## Estimated Effort
- Story 1: 8-10 hours (schema and validation for 4 entity types)
- Story 2: 8-10 hours (UI components for all forms and testing)
- Story 3: 10-12 hours (migration for all entities and compatibility)
- **Total**: 26-32 hours (3-4 days)

**Note**: Increased scope due to address separation needed for:
- Single client fields
- Multiple clients array
- Cofinancers in orderType
- Cofinancers in mixedOrderComponents

## Notes
- This enhancement was originally part of the validation migration epic but was separated for better scope management
- Consider future enhancement for apartment/floor fields if needed
- International address formats out of scope for this epic