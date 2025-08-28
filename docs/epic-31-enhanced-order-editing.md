# Epic 31: Enhanced Order Form Navigation and Status Management

## Epic Goal
Add a confirmation step with status management and smart navigation controls to the existing multi-step order form, making editing more pleasant and functional.

## User Requirements
1. **Final Confirmation Step**
   - After all insert steps, add a "Potrditev" step with "Potrdi" button to save order to database

2. **Status Management**  
   - Orders saved with "Potrdi" → status "osnutek"
   - Orders saved at any step → status "delno izpolnjen"

3. **Smart Navigation for Editing**
   - Allow direct jump to any step that has been filled
   - Cannot skip to unfilled steps
   - For orders with lots: allow choosing which lot and step to edit

4. **Visual Progress**
   - Graphical display showing which steps can be edited
   - Clear indication of form progress

## User Stories

### Story 1: Add Confirmation Step with Status Management
**As a** user completing an order  
**I want** a confirmation step with "Potrdi" button  
**So that** I can finalize my order with proper status

#### Acceptance Criteria
- New "Potrditev" step appears after all form steps
- "Potrdi" button saves order with status "osnutek"
- Regular save during steps uses status "delno izpolnjen"
- Database includes status field

#### Implementation
```python
# Add to database schema
ALTER TABLE procurements ADD COLUMN status TEXT DEFAULT 'delno izpolnjen';

# Modify save_form_draft in app.py
def save_form_draft(include_files=True, show_success=True, location="navigation", is_confirmation=False):
    # ... existing code ...
    
    # Add status based on save type
    form_data['status'] = 'osnutek' if is_confirmation else 'delno izpolnjen'
    
    # ... rest of save logic ...

# Add confirmation step
def render_confirmation_step():
    """Render the final confirmation step."""
    st.markdown("## 📋 Potrditev naročila")
    st.info("ℹ️ S klikom na 'Potrdi' bo naročilo shranjeno s statusom 'osnutek'")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        if st.button("◀ Nazaj", key="conf_back"):
            st.session_state.current_step -= 1
            st.rerun()
    
    with col3:
        if st.button("✅ Potrdi naročilo", type="primary", key="confirm_order"):
            draft_id = save_form_draft(
                include_files=True,
                show_success=False,
                location="confirmation",
                is_confirmation=True
            )
            if draft_id:
                st.success(f"✅ Naročilo uspešno potrjeno kot osnutek (ID: {draft_id})")
                st.balloons()
```

### Story 2: Implement Smart Navigation
**As a** user editing an order  
**I want** to jump directly to any completed step  
**So that** I can efficiently edit specific sections

#### Acceptance Criteria
- Track which steps have been completed
- Allow navigation only to completed steps
- Block navigation to unfilled steps
- For lots: allow selecting specific lot and step

#### Implementation
```python
# Track step completion in session state
if 'completed_steps' not in st.session_state:
    st.session_state['completed_steps'] = {}

# Mark step as completed when leaving it
def mark_step_completed(step_index):
    st.session_state['completed_steps'][step_index] = True

# Check if step is accessible
def is_step_accessible(step_index):
    # Can access if all previous steps are complete
    for i in range(step_index):
        if not st.session_state.get('completed_steps', {}).get(i, False):
            return False
    return True

# Navigation with validation
def navigate_to_step(target_step):
    if is_step_accessible(target_step):
        st.session_state['current_step'] = target_step
        st.rerun()
    else:
        st.warning("⚠️ Prejšnji koraki niso izpolnjeni")
```

### Story 3: Visual Progress Indicator
**As a** user  
**I want** to see which steps I can access  
**So that** I understand my form progress

#### Acceptance Criteria
- Show all steps with visual status
- Completed steps are green/clickable
- Current step is highlighted
- Locked steps are grayed out
- For lots: show branching structure

#### Implementation
```python
def render_progress_indicator():
    """Render visual progress with navigation."""
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    
    cols = st.columns(len(steps))
    
    for idx, (step, col) in enumerate(zip(steps, cols)):
        with col:
            # Determine status
            if idx == current:
                status = "🔵"  # Current
            elif completed.get(idx, False):
                status = "✅"  # Completed
            else:
                status = "🔒"  # Locked
            
            # Render clickable or disabled
            if completed.get(idx, False) or idx < current:
                if st.button(f"{status} {step['title']}", key=f"nav_{idx}"):
                    navigate_to_step(idx)
            else:
                st.markdown(f"<div style='color: gray;'>{status} {step['title']}</div>", 
                           unsafe_allow_html=True)
```

## Integration Points
- `app.py`: Add confirmation step to form flow
- `app.py`: Modify `save_form_draft()` for status
- `database.py`: Add status column
- `config_refactored.py`: Add confirmation step to steps array

## Technical Notes
- Status field defaults to 'delno izpolnjen' for compatibility
- Step tracking stored in session state
- Navigation validation prevents data inconsistency
- Visual indicators use existing Streamlit components

## Definition of Done
- [ ] Confirmation step with "Potrdi" button works
- [ ] Status correctly set based on save type  
- [ ] Navigation restricted to completed steps
- [ ] Visual progress indicator shows correct states
- [ ] Lot-specific navigation works (if applicable)