# Epic 3.0: Form Validation and UX Improvements - Brownfield Enhancement

## Epic Goal
Enhance the existing procurement form with improved validation, better field organization, and clearer user guidance to reduce errors and improve data entry efficiency.

## Epic Description

### Existing System Context:
- **Current functionality:** Multi-step Streamlit form for public procurement data entry with 13+ steps
- **Technology stack:** Python/Streamlit, SQLite database, dynamic form rendering
- **Integration points:** `ui/form_renderer.py`, `json_files/SEZNAM_POTREBNIH_PODATKOV.json`, validation system

### Enhancement Details:
- **What's being added/changed:** 
  - Restructured address fields for better data capture
  - Enhanced help text and tooltips system
  - Improved conditional validation logic
  - Better visual feedback for lot management
  - Automatic number formatting for financial fields
  - Enhanced co-financing validation rules

- **How it integrates:** 
  - Modifications to existing form renderer
  - Updates to JSON schema structure
  - Extension of current validation system
  - Leveraging existing session state management

- **Success criteria:**
  - All field restructuring implemented without data loss
  - Validation messages appear in correct context
  - Help tooltips functional across all form steps
  - Financial fields display formatted numbers
  - Co-financing validation enforces required fields conditionally

## Stories

### Story 3.0.1: Address Field Restructuring and Client Help System
**Description:** Restructure address fields into separate components and add comprehensive help system for multiple clients scenario.

**Key Tasks:**
- Split "Naslov (ulica, hišna številka, poštna številka in kraj)" into two fields:
  - "Naslov (ulica/cesta in hišna številka)" 
  - "Poštna številka in kraj"
- Make both fields required
- Add help tooltip (?) for multiple clients with text: "V kolikor je naročnikov več, odkljukajte polje in za vsakega naročnika kliknite na polje 'dodaj naročnika' ter zanj vpišite podatke. V polje 'Naročnik 1' vpišite naročnika, kateremu so ostali naročniki dali pooblastilo za izvedbo oddaje javnega naročila."
- Fix validation message appearing on wrong step (Step 2 showing Step 1 validation)

**Acceptance Criteria:**
- [ ] Address fields properly split in schema
- [ ] Both new address fields marked as required
- [ ] Help tooltip displays correct text
- [ ] Validation messages only appear on relevant steps
- [ ] Existing data migration handled correctly

### Story 3.0.2: Procurement Procedure Enhancements and Lot Management
**Description:** Add legal article references to procurement procedures and improve lot management UX.

**Key Tasks:**
- Add ZJN-3 article references to all procurement procedures:
  - odprti postopek (40. člen)
  - omejeni postopek (41. člen)
  - konkurenčni dialog (42. člen)
  - partnerstvo za inovacije (43. člen)
  - konkurenčni postopek s pogajanji (44. člen)
  - postopek s pogajanji z objavo (45. člen)
  - postopek s pogajanji brez predhodne objave (46. člen)
  - postopek naročila male vrednosti (47. člen)
- Add explanation for lot checkbox: "Obkljukajte, če je naročilo razdeljeno na sklope"
- Optimize lot data entry to avoid duplication between Step 5 and Step 7
- Display "Sklop X - [naziv]" header on all lot-specific forms
- Keep only "Naziv sklopa" in Step 5, move other fields to Step 7

**Acceptance Criteria:**
- [ ] All procedures show legal article references
- [ ] Lot checkbox has clear explanation text
- [ ] No duplicate data entry between steps
- [ ] Lot identification visible on all relevant forms
- [ ] Data structure maintains backward compatibility

### Story 3.0.3: Financial Fields Formatting and Co-financing Validation
**Description:** Implement automatic number formatting for financial fields and conditional validation for co-financing data.

**Key Tasks:**
- Add automatic thousand separators (dots) to:
  - "višina zagotovljenih sredstev"
  - "ocenjena vrednost javnega naročila"
- Make co-financing fields required when co-financing is selected:
  - Polni naziv sofinancerja (required)
  - Naslov sofinancerja (required)
  - Naziv programa/projekta (required)
  - Področje programa/projekta (required)
  - Oznaka programa/projekta (required)
  - Logotipi (optional)
  - Posebne zahteve sofinancerja (optional but must be considered in document generation if filled)
- Implement real-time formatting as user types

**Acceptance Criteria:**
- [ ] Numbers display with thousand separators
- [ ] Formatting doesn't interfere with calculations
- [ ] Co-financing fields validate conditionally
- [ ] Optional fields clearly marked
- [ ] Special requirements field integrated with document generation

## Compatibility Requirements
- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact is minimal
- [x] Session state management preserved

## Risk Mitigation
- **Primary Risk:** Breaking existing form submissions with validation changes
- **Mitigation:** Implement changes incrementally with feature flags, thorough testing of each step
- **Rollback Plan:** Version control allows reverting individual story changes if issues arise

## Definition of Done
- [ ] All three stories completed with acceptance criteria met
- [ ] Existing form submissions continue to work
- [ ] Field restructuring doesn't lose existing data
- [ ] Help system integrated consistently across form
- [ ] Financial formatting works across browsers
- [ ] Co-financing validation logic tested thoroughly
- [ ] No regression in form navigation or data saving
- [ ] Documentation updated with new field structures

## Testing Strategy
1. **Unit Tests:** Validation logic for each new rule
2. **Integration Tests:** Form submission with new fields
3. **Migration Tests:** Existing data compatibility
4. **UI Tests:** Playwright tests for tooltips and formatting
5. **Regression Tests:** Complete form flow validation

## Story Manager Handoff:
"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing Streamlit form system running Python/SQLite
- Integration points: form_renderer.py, JSON schema, existing validation system
- Existing patterns to follow: Session state management, dynamic field rendering, conditional validation
- Critical compatibility requirements: Maintain backward compatibility with existing submissions
- Each story must include verification that existing form functionality remains intact

The epic should maintain system integrity while delivering improved validation and user experience for procurement form data entry."

---

## Implementation Notes:
- Leverage existing `render_if` conditional rendering pattern
- Use Streamlit's native tooltip functionality where possible
- Maintain consistency with existing validation message styling
- Consider using Streamlit's number_input formatting options
- Ensure all text changes are in Slovenian language