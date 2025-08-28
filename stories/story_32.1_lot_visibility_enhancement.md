# Story 32.1: Enhanced Lot Visibility in Multi-Lot Form

## Story Title
**Lot Context Visibility Enhancement - Brownfield Addition**

## User Story
As a **user filling out a multi-lot procurement form**,  
I want **to clearly see which lot I'm currently editing at all times**,  
So that **I don't accidentally enter data for the wrong lot and can confidently navigate between lots**.

## Story Context

### Existing System Integration
- **Integrates with:** Current multi-step form wizard (`app.py`, `render_main_form()`)
- **Technology:** Streamlit, Python, session state management
- **Follows pattern:** Existing navigation and form rendering patterns
- **Touch points:**
  - Quick navigation sidebar (`render_quick_navigation()`)
  - Main form header area
  - Step progression indicator
  - Session state `current_lot_index`

## Acceptance Criteria

### Functional Requirements
1. Display current lot name/number prominently in the main form header when in lot mode
2. Update quick navigation to show lot context for each step (e.g., "7. Merila - Sklop 1")
3. Add visual lot indicator/badge that persists across all form steps

### Integration Requirements
4. Existing general mode (no lots) continues to work unchanged
5. New lot indicators follow existing Streamlit component patterns
6. Integration with session state maintains current behavior
7. Navigation between lots preserves all entered data

### Quality Requirements
8. Lot visibility changes are consistent across all form steps
9. No regression in existing form validation or navigation
10. Visual indicators are clear without cluttering the interface

## Technical Notes

### Integration Approach
```python
# Enhance existing header in render_main_form()
if st.session_state.get('current_lot_index') is not None:
    lot_index = st.session_state['current_lot_index']
    lot_name = st.session_state.get('lots', [])[lot_index].get('name', f'Sklop {lot_index + 1}')
    st.info(f"🎯 Trenutno urejate: **{lot_name}**")

# Update quick navigation labels
if lot_context and lot_context['mode'] == 'lots':
    step_label = f"{idx+1}. {step_name} - {lot_context['lot_name']}"
```

### Existing Pattern Reference
- Current lot context handling: `utils/lot_utils.py:get_current_lot_context()`
- Navigation rendering: `app.py:render_quick_navigation()`
- Header styling: Uses Streamlit's built-in `st.info()` and `st.columns()`

### Key Constraints
- Must not break existing session state structure
- Must work with both general and lot modes
- Cannot change existing navigation logic, only enhance display

## Implementation Details

### Required Changes

1. **app.py - render_main_form() enhancement:**
   - Add lot indicator after main title
   - Show lot name from session state
   - Position: After main header, before form content

2. **app.py - render_quick_navigation() enhancement:**
   - Append lot name to step labels when in lot mode
   - Format: "Step Number. Step Name - Lot Name"
   - Use existing lot_context to determine display

3. **Visual consistency:**
   - Use 🎯 emoji for current lot indicator
   - Use consistent color (st.info blue) for lot context
   - Keep lot name format consistent: "Sklop X: [name]"

### Code Locations to Modify

1. **`app.py:render_main_form()` (around line 1000-1100)**
   - Add lot indicator after progress bar
   - Check session state for current_lot_index

2. **`app.py:render_quick_navigation()` (around line 1700-1800)**
   - Modify step label generation
   - Include lot context in navigation items

3. **Optional: `app.py:render_lot_selector()` (if exists)**
   - Highlight currently selected lot

## Definition of Done

- [ ] Current lot clearly visible in main form header
- [ ] Quick navigation shows lot context for each step
- [ ] Visual indicators consistent across all steps
- [ ] General mode (no lots) unchanged
- [ ] Existing validation continues to work
- [ ] Navigation between lots preserves data
- [ ] No regression in form functionality
- [ ] Code follows existing patterns
- [ ] Manual testing completed for both modes

## Risk and Compatibility Check

### Risk Assessment
- **Primary Risk:** Session state key conflicts or navigation state corruption
- **Mitigation:** Only add display logic, don't modify existing state management
- **Rollback:** Remove display enhancements, core functionality unchanged

### Compatibility Verification
- [ ] No changes to session state structure
- [ ] No database or API changes
- [ ] UI changes use existing Streamlit patterns
- [ ] Performance impact negligible (display only)

## Testing Checklist

### Manual Testing Required
1. **General Mode:**
   - [ ] Form displays without lot indicators
   - [ ] Navigation works as before
   - [ ] No visual errors or warnings

2. **Single Lot Mode:**
   - [ ] Lot name appears in header
   - [ ] Quick navigation shows lot context
   - [ ] Switching steps maintains lot indicator

3. **Multi-Lot Mode:**
   - [ ] Correct lot shown when switching between lots
   - [ ] Each lot's data remains separate
   - [ ] Navigation updates correctly for each lot

4. **Edge Cases:**
   - [ ] Empty lot name handled gracefully
   - [ ] Very long lot names don't break layout
   - [ ] Switching modes (general ↔ lots) works correctly

## Estimation
- **Development:** 2-3 hours
- **Testing:** 1 hour
- **Total:** 3-4 hours (single session)

## Notes
- This is a UI/UX enhancement only - no business logic changes
- If implementation reveals complexity beyond display changes, escalate to full story
- Consider adding lot progress indicator in future iteration (e.g., "Lot 2 of 5")

---
*Created: 2025-08-28*  
*Type: Brownfield Enhancement*  
*Priority: Medium*  
*Status: Ready for Development*