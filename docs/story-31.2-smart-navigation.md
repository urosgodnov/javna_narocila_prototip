# Story 31.2: Implement Smart Step Navigation Controls

## User Story
As a user editing an order,
I want to jump directly to any previously completed step,
So that I can efficiently edit specific sections without going through all steps sequentially.

## Story Context

### Existing System Integration
- **Integrates with:** Step navigation in `app.py:render_main_form()`
- **Technology:** Python, Streamlit session state management
- **Follows pattern:** Current navigation button pattern (Naprej/Nazaj)
- **Touch points:**
  - Form step navigation logic
  - Session state step tracking
  - Lot navigation handling in `utils/lot_navigation.py`
  - Step validation in `app.py:validate_step()`

## Acceptance Criteria

### Functional Requirements
1. Track completion status for each form step in session state
2. Allow direct navigation to any completed step
3. Block navigation attempts to incomplete steps with warning message
4. Mark steps as completed when user advances past them
5. For lot-based forms, track completion per lot

### Integration Requirements
6. Existing linear navigation (Naprej/Nazaj) continues to work
7. Step validation still runs when leaving a step
8. Current step indicator remains accurate
9. Lot navigation maintains its current behavior

### Quality Requirements
10. Completion tracking persists during session
11. Navigation restrictions are clearly communicated
12. Performance is not impacted by tracking
13. Edge cases handled (first step, last step, lot switches)

## Technical Implementation Details

### Session State Tracking Structure
```python
# Initialize tracking in app.py or during form setup
def initialize_step_tracking():
    """Initialize step completion tracking."""
    if 'completed_steps' not in st.session_state:
        st.session_state['completed_steps'] = {}
    
    # For lot-based forms
    if st.session_state.get('lot_mode') == 'multiple':
        if 'lot_completed_steps' not in st.session_state:
            st.session_state['lot_completed_steps'] = {}
```

### Step Completion Marking
```python
def mark_step_completed(step_index, lot_id=None):
    """Mark a step as completed when moving forward."""
    if lot_id:
        if lot_id not in st.session_state['lot_completed_steps']:
            st.session_state['lot_completed_steps'][lot_id] = {}
        st.session_state['lot_completed_steps'][lot_id][step_index] = True
    else:
        st.session_state['completed_steps'][step_index] = True
```

### Navigation Validation
```python
def is_step_accessible(step_index, lot_id=None):
    """Check if a step can be accessed based on completion history."""
    # Allow access to current and previous steps
    current_step = st.session_state.get('current_step', 0)
    if step_index <= current_step:
        return True
    
    # Check completion tracking
    if lot_id:
        lot_steps = st.session_state.get('lot_completed_steps', {}).get(lot_id, {})
        completed = lot_steps
    else:
        completed = st.session_state.get('completed_steps', {})
    
    # Verify all previous steps are completed
    for i in range(step_index):
        if not completed.get(i, False):
            return False
    
    return completed.get(step_index, False)

def navigate_to_step(target_step, lot_id=None):
    """Navigate to a specific step with validation."""
    if is_step_accessible(target_step, lot_id):
        # Mark current step as completed if moving forward
        current = st.session_state.get('current_step', 0)
        if target_step > current:
            mark_step_completed(current, lot_id)
        
        # Update navigation
        if lot_id:
            st.session_state['current_lot'] = lot_id
        st.session_state['current_step'] = target_step
        st.rerun()
    else:
        st.warning("⚠️ Ne morete skočiti na ta korak - prejšnji koraki niso izpolnjeni")
```

### Integration with Existing Navigation
```python
# Modify existing "Naprej" button handler
def handle_next_button():
    """Enhanced next button with completion tracking."""
    current_step = st.session_state.current_step
    
    # Validate current step
    if validate_step(step_keys, schema):
        # Mark current step as completed
        lot_id = st.session_state.get('current_lot') if st.session_state.get('lot_mode') == 'multiple' else None
        mark_step_completed(current_step, lot_id)
        
        # Move to next step
        st.session_state.current_step += 1
        st.rerun()
```

### Quick Navigation Menu
```python
def render_quick_navigation():
    """Render quick navigation dropdown for completed steps."""
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    
    # Build accessible steps list
    accessible_steps = []
    for idx, step in enumerate(steps):
        if idx < current or completed.get(idx, False):
            accessible_steps.append((idx, step['title']))
    
    if accessible_steps:
        with st.sidebar:
            st.markdown("### 🧭 Hitra navigacija")
            selected = st.selectbox(
                "Skoči na korak:",
                options=[idx for idx, _ in accessible_steps],
                format_func=lambda x: next(title for idx, title in accessible_steps if idx == x),
                index=accessible_steps.index((current, steps[current]['title'])) if current < len(steps) else 0
            )
            
            if st.button("Pojdi", key="quick_nav"):
                navigate_to_step(selected)
```

### Lot-Specific Navigation
```python
def render_lot_navigation():
    """Enhanced lot navigation with step selection."""
    if st.session_state.get('lot_mode') != 'multiple':
        return
    
    lot_names = st.session_state.get('lot_names', [])
    if not lot_names:
        return
    
    with st.sidebar:
        st.markdown("### 📦 Navigacija po sklopih")
        
        # Lot selector
        selected_lot_idx = st.selectbox(
            "Izberi sklop:",
            options=range(len(lot_names)),
            format_func=lambda x: lot_names[x]
        )
        
        lot_id = f'lot_{selected_lot_idx}'
        
        # Step selector for the lot
        lot_steps = get_lot_specific_steps()
        completed_in_lot = st.session_state.get('lot_completed_steps', {}).get(lot_id, {})
        
        accessible_lot_steps = []
        for idx, step in enumerate(lot_steps):
            if is_step_accessible(idx, lot_id):
                accessible_lot_steps.append((idx, step['title']))
        
        if accessible_lot_steps:
            selected_step = st.selectbox(
                "Izberi korak:",
                options=[idx for idx, _ in accessible_lot_steps],
                format_func=lambda x: next(title for idx, title in accessible_lot_steps if idx == x)
            )
            
            if st.button("Pojdi na sklop", key="lot_nav"):
                navigate_to_step(selected_step, lot_id)
```

## Risk and Compatibility

### Risk Assessment
- **Primary Risk:** Incorrect completion tracking leading to blocked navigation
- **Mitigation:** Allow override option for administrators, clear tracking on form reset
- **Rollback:** Disable smart navigation, revert to linear only

### Compatibility Verification
- ✅ No breaking changes to existing navigation buttons
- ✅ Session state additions don't affect existing data
- ✅ UI additions are progressive enhancements
- ✅ Performance impact minimal (session state checks)

## Definition of Done
- [ ] Step completion tracking implemented in session state
- [ ] Navigation validation function created
- [ ] Current navigation enhanced with completion marking
- [ ] Quick navigation menu implemented in sidebar
- [ ] Lot-specific navigation with step selection
- [ ] Warning messages for blocked navigation
- [ ] Integration with existing Naprej/Nazaj buttons
- [ ] Edge cases handled (first/last step)
- [ ] Testing with both simple and lot-based forms
- [ ] No regression in existing navigation

## Estimated Effort
- **Development:** 3-4 hours
- **Testing:** 1-2 hours
- **Total:** 4-6 hours

## Dependencies
- Story 31.1 should be completed first (for testing with confirmation step)

## Notes
- Completion tracking is session-based (not persisted to database)
- Visual indicators for navigation will be added in Story 31.3
- Consider adding admin override for blocked navigation in future iteration