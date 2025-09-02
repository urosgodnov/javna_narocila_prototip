# Brownfield Story: Inspection Dates Validation

## Story Title
**Inspection Dates Validation** - Brownfield Addition

## User Story
As a **procurement officer**,  
I want **the system to require at least one inspection date when inspection is enabled**,  
So that **the procurement process doesn't proceed without scheduled inspection times**.

## Story Context

**Existing System Integration:**
- Integrates with: `inspectionInfo` section in the multi-step form
- Technology: Streamlit, Python session state, existing validation system
- Follows pattern: Existing array validation patterns (like minimum 2 lots validation in `validate_screen_5_lots`)
- Touch points: `ui/renderers/section_renderer.py`, `utils/validations.py`, form controller

## Acceptance Criteria

**Functional Requirements:**
1. When `inspectionInfo.hasInspection` is true and `inspectionDates` array is empty, display validation warning
2. Prevent form progression to next step until at least one inspection date is added
3. Validation message appears in Slovenian: "Dodajte vsaj en datum ogleda"

**Integration Requirements:**
4. Existing inspection functionality continues to work unchanged
5. New validation follows existing array validation pattern (like `validate_screen_5_lots`)
6. Integration with form controller maintains current validation flow

**Quality Requirements:**
7. Validation is covered by unit tests
8. No regression in existing form validation
9. Warning styling matches existing validation warnings

## Technical Notes

**Integration Approach:** 
Add validation method to `utils/validations.py` following the exact pattern of `validate_screen_5_lots()`

**Existing Pattern Reference:** 
The lots validation checks for minimum 2 lots when `hasLots` is true - we'll follow this pattern

**Key Constraints:** 
- Must check both `hasInspection` flag and `inspectionDates` array length
- Must handle lot-scoped keys (e.g., `lots.0.inspectionInfo.inspectionDates`)

**Implementation Pattern:**
```python
def validate_inspection_dates(self):
    """
    Validate that at least one inspection date exists when inspection is enabled.
    Following the pattern of validate_screen_5_lots.
    """
    has_inspection = self.session_state.get('inspectionInfo.hasInspection', False)
    
    if has_inspection:
        # Check for lot-scoped inspection dates (current architecture)
        inspection_dates = self.session_state.get('lots.0.inspectionInfo.inspectionDates', [])
        
        if not inspection_dates or len(inspection_dates) == 0:
            return False, ["Dodajte vsaj en datum ogleda"]
    
    return True, []
```

**Integration Point in Form Controller:**
Add the validation call in the appropriate validation chain, likely in the inspection step validation.

## Definition of Done

- [ ] Validation method implemented in `utils/validations.py`
- [ ] Validation triggers when inspection enabled but no dates
- [ ] Form cannot proceed without adding inspection date
- [ ] Validation message displays in Slovenian
- [ ] Existing inspection functionality unchanged
- [ ] Code follows existing validation patterns
- [ ] Tests pass (existing and new)
- [ ] No regression in form navigation

## Risk and Compatibility Assessment

**Minimal Risk Assessment:**
- **Primary Risk:** Validation might block users who don't need inspection dates
- **Mitigation:** Only validate when `hasInspection` is explicitly true
- **Rollback:** Remove validation method call from form controller

**Compatibility Verification:**
- ✅ No breaking changes to existing APIs
- ✅ No database changes required
- ✅ UI follows existing validation warning patterns
- ✅ Performance impact is negligible (simple array length check)

## Validation Checklist

**Scope Validation:**
- ✅ Story can be completed in one development session (1-2 hours)
- ✅ Integration approach is straightforward (add one validation method)
- ✅ Follows existing validation patterns exactly
- ✅ No design or architecture work required

**Clarity Check:**
- ✅ Story requirements are unambiguous
- ✅ Integration points clearly specified (`validations.py`, form controller)
- ✅ Success criteria are testable (array length check)
- ✅ Rollback approach is simple (remove method call)

## Estimated Effort
**1-2 hours** of focused development work

## Implementation Steps
1. Add `validate_inspection_dates` method to `ValidationManager` class in `utils/validations.py`
2. Identify the correct place in form controller to call this validation
3. Add the validation call to the form controller
4. Test with form flow (mark inspection checkbox, try to proceed without dates)
5. Verify existing validations still work
6. Create unit test for the new validation method

## Notes
- This validation follows the exact pattern established by `validate_screen_5_lots()`
- The lot-scoped key pattern (`lots.0.inspectionInfo.inspectionDates`) is consistent with current architecture
- Validation message is in Slovenian to match existing messages
- This is a minimal, focused enhancement that doesn't require architectural changes