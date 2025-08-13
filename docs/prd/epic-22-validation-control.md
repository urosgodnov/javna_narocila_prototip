# Epic 22: Granular Validation Control - Brownfield Enhancement

## Epic Goal

Enable users to globally disable form validation with a master switch on the first step, and provide per-step validation toggles throughout the form, giving users fine-grained control over when validation rules are applied.

## Epic Description

### Existing System Context

- **Current relevant functionality:** 
  - Multi-step form with validation at each step
  - Recently added Merila validation (Epic 21) that validates criteria based on CPV codes
  - Session state management for form data
  - Step-based navigation with validation checks
- **Technology stack:** Streamlit UI, Python backend, session state for form management
- **Integration points:** Form renderer (`ui/form_renderer.py`), step validation logic, app.py main form flow

### Enhancement Details

- **What's being added/changed:** 
  - Master validation toggle on first step (checked by default = validation OFF)
  - Per-step validation toggles on each form step (unchecked by default)
  - Validation only runs when either master is OFF or step-specific is ON
  - Visual indicators showing validation state
- **How it integrates:** 
  - Uses existing session state patterns
  - Modifies validation check logic to respect toggle states
  - Maintains backward compatibility with existing validation
- **Success criteria:** 
  - Users can disable all validation with one toggle
  - Users can selectively enable validation per step
  - Validation state persists across navigation
  - Clear visual feedback on validation status

## Stories

### Story 22.1: Master Validation Toggle
**Description:** Add a master "Izklopljena validacija" (Validation Disabled) checkbox on the first form step that, when checked (default), disables all validation across the form. This provides a global override for users who want to work without validation constraints.

**Acceptance Criteria:**
- Checkbox appears prominently on first step
- Default state is checked (validation disabled)
- State persists in session across navigation
- When checked, all validation is bypassed
- Visual indicator shows global validation state

### Story 22.2: Per-Step Validation Toggles
**Description:** Add "Uveljavi validacijo" (Apply Validation) checkboxes on each form step that allow users to selectively enable validation for specific sections, overriding the master toggle for that step only.

**Acceptance Criteria:**
- Toggle appears on each form step
- Default state is unchecked
- When checked, validation runs for that step regardless of master toggle
- State persists per step in session
- Clear visual feedback when step validation is active

### Story 22.3: Validation Logic Integration
**Description:** Modify the existing validation logic to respect both master and per-step toggle states, ensuring validation only runs when appropriate based on user selections.

**Acceptance Criteria:**
- Validation runs if: master is OFF (unchecked) OR step toggle is ON (checked)
- Existing validation logic remains unchanged
- Merila validation respects toggle states
- Form submission respects validation state
- No regression in existing validation features

## Compatibility Requirements

- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible (no DB changes)
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact is minimal

## Risk Mitigation

- **Primary Risk:** Users might accidentally submit invalid data with validation disabled
- **Mitigation:** 
  - Clear visual warnings when validation is disabled
  - Confirmation dialog on submit when validation is off
  - Log validation state with submissions for audit trail
- **Rollback Plan:** 
  - Feature controlled by session state, can be disabled via config
  - No database changes, easy to revert UI changes
  - Existing validation logic untouched, only wrapped with conditionals

## Definition of Done

- [x] All three stories completed with acceptance criteria met
- [x] Master toggle on first step working correctly
- [x] Per-step toggles functioning as specified
- [x] Validation logic correctly respects toggle states
- [x] Visual feedback clear and consistent
- [x] No regression in existing validation features
- [x] Session state properly managed for all toggles
- [x] Testing confirms all scenarios work correctly

## Technical Notes

### Session State Keys
```python
# Master validation toggle (checked = disabled)
st.session_state['validation_disabled'] = True  # Default

# Per-step validation toggles (checked = enabled)
st.session_state[f'step_{step_num}_validation_enabled'] = False  # Default

# Computed validation state for each step
def should_validate(step_num):
    master_disabled = st.session_state.get('validation_disabled', True)
    step_enabled = st.session_state.get(f'step_{step_num}_validation_enabled', False)
    return (not master_disabled) or step_enabled
```

### UI Layout
```
[Step 1 - Basic Information]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
☑ Izklopljena validacija (Master - affects all steps)
⚠️ Validation is currently DISABLED globally

[Form fields...]

☐ Uveljavi validacijo (Enable for this step only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Other Steps]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Form fields...]

☐ Uveljavi validacijo (Enable for this step only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Integration Points
- Modify `validate_step()` in app.py to check toggle states
- Update form navigation to respect validation toggles
- Enhance visual feedback in form renderer
- Ensure Merila validation respects toggles

---

## Story Manager Handoff

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing Streamlit multi-step form with validation
- Integration points: Form renderer, step validation logic, session state management
- Existing patterns: Streamlit checkboxes, session state for form data, validation functions
- Critical compatibility: Must not break existing validation when toggles are in default state
- Each story must verify that existing validation works when enabled

The epic should provide granular validation control while maintaining form integrity and user experience."