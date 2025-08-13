# Epic 21: Merila (Criteria) Validation for Input Form - Brownfield Enhancement

## Epic Goal

Implement validation logic in the procurement input form that enforces business rules for "Merila" (selection criteria) based on CPV codes, ensuring that when certain CPV codes are selected, price cannot be the only criterion.

## Epic Description

### Existing System Context

- **Current relevant functionality:** 
  - Admin panel manages CPV codes with criteria restrictions (Merila - cena)
  - Database stores CPV codes that require additional criteria beyond price
  - Input form has selectionCriteria section with checkboxes for various criteria including price
- **Technology stack:** Streamlit UI, SQLite database, Python backend, JSON schema-based forms
- **Integration points:** Form renderer (`ui/form_renderer.py`), CPV selector component, criteria manager (`utils/criteria_manager.py`)

### Enhancement Details

- **What's being added/changed:** Adding real-time validation that checks selected CPV codes against criteria restrictions and enforces/warns when price cannot be the only criterion
- **How it integrates:** Validation hooks into existing form rendering, checks against database criteria mappings, displays warnings/errors in UI
- **Success criteria:** Users are prevented from submitting forms with invalid criteria combinations based on CPV code requirements

## Stories

### Story 21.1: Implement CPV-Based Criteria Validation Logic
**Description:** Create validation functions that check if selected CPV codes have criteria restrictions and determine if current criteria selection is valid.

**Acceptance Criteria:**
- Function to check if any selected CPV code requires additional criteria beyond price
- Function to validate current criteria selection against CPV requirements
- Integration with existing criteria_manager for database queries
- Return clear validation messages explaining what's required
- Handle multiple CPV codes with different requirements

### Story 21.2: Add Real-Time Validation to Form UI
**Description:** Integrate validation into the form renderer to provide immediate feedback when users select CPV codes or modify criteria selections.

**Acceptance Criteria:**
- Validation triggers when CPV codes are selected/changed
- Validation triggers when criteria checkboxes are modified
- Warning/error messages appear near the criteria section
- Clear explanation of which CPV codes require additional criteria
- Visual indicators (colors/icons) for validation state
- Form submission blocked if validation fails

### Story 21.3: Enhanced User Guidance and Auto-Selection
**Description:** Improve UX by providing helpful suggestions and optionally auto-selecting required criteria based on CPV codes.

**Acceptance Criteria:**
- Info box explains why certain criteria are required
- List which specific CPV codes triggered the requirement
- Option to auto-select commonly used additional criteria
- Tooltip/help text for each criterion explaining when it's typically used
- Summary of all active validation rules based on current CPV selection

## Compatibility Requirements

- [x] Existing APIs remain unchanged
- [x] Database schema unchanged (uses existing cpv_criteria tables)
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact minimal (cached validation queries)

## Risk Mitigation

- **Primary Risk:** Validation could block legitimate form submissions if rules are too strict
- **Mitigation:** 
  - Implement as warnings initially, with option to override
  - Clear explanations of why validation failed
  - Admin panel to review/adjust criteria rules
- **Rollback Plan:** 
  - Feature flag to disable validation if issues arise
  - Validation can be set to "warning only" mode
  - All validation is client-side, no database changes

## Definition of Done

- [x] All three stories completed with acceptance criteria met
- [x] Validation correctly enforces CPV-based criteria rules
- [x] User experience is helpful, not frustrating
- [x] Clear documentation of validation rules
- [x] No regression in existing form functionality
- [x] Admin can see/modify which CPV codes trigger validation
- [x] Testing covers various CPV/criteria combinations

## Technical Notes

### Validation Flow
1. User selects CPV codes in form
2. System queries database for criteria restrictions on those codes
3. When user modifies criteria selection, validation runs
4. If price is only criterion but CPV requires more, show warning/error
5. Block form submission until valid or user acknowledges override

### Key Integration Points
- `utils/criteria_manager.py` - Query CPV criteria restrictions
- `ui/form_renderer.py` - Add validation display logic
- `ui/components/cpv_selector.py` - Trigger validation on CPV change
- Session state to track validation status

### Example Validation Message
```
⚠️ Izbrane CPV kode zahtevajo dodatna merila poleg cene:
- 71000000-8 (Architectural services) - cena ne sme biti edino merilo
- 79000000-4 (Business services) - zahteva socialna ali okoljska merila

Prosimo, izberite vsaj eno dodatno merilo.
```

---

## Story Manager Handoff

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is validation enhancement for the existing Streamlit procurement form
- Integration points: Form renderer, CPV selector component, criteria manager database queries
- Existing patterns: Streamlit session state for validation, existing warning/error message patterns
- Critical compatibility: Must not break existing form submission for CPV codes without restrictions
- Each story must verify that forms without restricted CPV codes work normally

The epic should provide helpful validation that guides users to comply with procurement rules based on their CPV code selections."