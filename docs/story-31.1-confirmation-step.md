# Story 31.1: Add Confirmation Step with Status Management

## User Story
As a user creating a new order,
I want a final confirmation step with a "Potrdi" button,
So that I can finalize my order with the proper "osnutek" status.

## Story Context

### Existing System Integration
- **Integrates with:** Multi-step form wizard in `app.py:render_main_form()`
- **Technology:** Python, Streamlit, SQLite
- **Follows pattern:** Existing step rendering pattern in `config_refactored.py`
- **Touch points:** 
  - `save_form_draft()` function (app.py:102-259)
  - Database save operations in `database.py`
  - Form step configuration in `config_refactored.py`

## Acceptance Criteria

### Functional Requirements
1. A new "Potrditev" step appears after all existing form steps
2. The confirmation step contains a "Potrdi" button that saves the order
3. Orders saved via "Potrdi" receive status "osnutek"
4. Orders saved during intermediate steps receive status "delno izpolnjen"
5. The confirmation step has navigation buttons (Back/Confirm)

### Integration Requirements
6. Existing form steps continue to work unchanged
7. Current save functionality remains available at each step
8. Database migration is non-breaking (adds column with default)
9. Existing orders without status field continue to work

### Quality Requirements
10. Status field is properly persisted to database
11. Confirmation step follows existing UI patterns
12. Success feedback is shown after confirmation
13. Error handling for failed saves is implemented

## Technical Implementation Details

### Database Schema Update
```sql
-- Add status column with default for backward compatibility
ALTER TABLE procurements ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'delno izpolnjen';
```

### Configuration Changes
```python
# In config_refactored.py, add to step list
CONFIRMATION_STEP = {
    "key": "confirmation",
    "title": "Potrditev",
    "description": "Potrdite vnos naročila",
    "schema_path": None,  # No schema validation needed
    "is_confirmation": True
}
```

### Save Function Enhancement
```python
# Modify save_form_draft in app.py
def save_form_draft(include_files=True, show_success=True, location="navigation", is_confirmation=False):
    # Existing code...
    
    # Add status to form data
    form_data['status'] = 'osnutek' if is_confirmation else 'delno izpolnjen'
    
    # Continue with existing save logic...
```

### Confirmation Step Renderer
```python
def render_confirmation_step():
    """Render the final confirmation step."""
    st.markdown("## 📋 Potrditev naročila")
    st.markdown("---")
    
    st.info("ℹ️ S klikom na 'Potrdi' bo naročilo shranjeno s statusom 'osnutek'")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        if st.button("◀ Nazaj", key="conf_back"):
            st.session_state.current_step -= 1
            st.rerun()
    
    with col3:
        if st.button("✅ Potrdi naročilo", type="primary", key="confirm_order"):
            with st.spinner("Shranjujem naročilo..."):
                draft_id = save_form_draft(
                    include_files=True,
                    show_success=False,
                    location="confirmation",
                    is_confirmation=True
                )
                
                if draft_id:
                    st.success(f"✅ Naročilo uspešno potrjeno kot osnutek (ID: {draft_id})")
                    st.balloons()
                    
                    # Show options for next actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📊 Nazaj na pregled", key="to_dashboard"):
                            st.session_state.current_page = 'dashboard'
                            clear_form_data()
                            st.rerun()
                    with col2:
                        if st.button("➕ Novo naročilo", key="new_order"):
                            clear_form_data()
                            st.session_state.current_step = 0
                            st.rerun()
                else:
                    st.error("❌ Napaka pri potrjevanju naročila. Prosim, poskusite znova.")
```

## Risk and Compatibility

### Risk Assessment
- **Primary Risk:** Breaking existing save functionality
- **Mitigation:** Add status parameter as optional with default value
- **Rollback:** Remove status check, system continues with existing behavior

### Compatibility Verification
- ✅ No breaking changes to existing save API (optional parameter)
- ✅ Database change is additive only (new column with default)
- ✅ UI follows existing Streamlit patterns
- ✅ Performance impact negligible (one additional field)

## Definition of Done
- [ ] Database migration script created and tested
- [ ] Confirmation step added to form configuration
- [ ] Save function enhanced with status parameter
- [ ] Confirmation step UI implemented
- [ ] Status correctly saved to database
- [ ] Navigation buttons work correctly
- [ ] Success/error feedback implemented
- [ ] Existing save functionality still works
- [ ] Integration tested with full form flow
- [ ] No regression in existing features

## Estimated Effort
- **Development:** 2-3 hours
- **Testing:** 1 hour
- **Total:** 3-4 hours

## Dependencies
- None - can be implemented independently

## Notes
- This story focuses only on adding the confirmation step and status field
- Navigation restrictions will be implemented in Story 31.2
- Visual indicators will be added in Story 31.3