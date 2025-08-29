# Story 1: Direktno kopiranje naročil - Brownfield Addition

## User Story
As a **uporabnik sistema javnih naročil**,  
I want **to copy an existing procurement with one click**,  
So that **I can quickly create similar procurements without re-entering all data**.

## Story Context

### Existing System Integration:
- **Integrates with:** dashboard.py, database.py (create_procurement function)
- **Technology:** Python, Streamlit, SQLite
- **Follows pattern:** Existing database operations pattern using direct SQL queries
- **Touch points:** Dashboard table display, procurement data structure

## Acceptance Criteria

### Functional Requirements:
1. ✅ Copy button appears in each row of the procurement dashboard
2. ✅ Clicking copy creates a new procurement with all data from original
3. ✅ New procurement name is automatically set to "{original_name} (kopija)"

### Integration Requirements:
4. ✅ Existing dashboard functionality continues to work unchanged
5. ✅ New functionality follows existing button/action pattern from dashboard
6. ✅ Integration with database.create_procurement() maintains current behavior

### Quality Requirements:
7. ✅ Copy operation completes within 2 seconds
8. ✅ Success message shows after successful copy
9. ✅ No regression in existing dashboard functionality verified

## Technical Notes

### Integration Approach:
```python
# In dashboard.py, add to procurement row:
if st.button("📋 Kopiraj", key=f"copy_{procurement['id']}"):
    # Load full procurement data
    original_data = database.get_procurement(procurement['id'])
    # Modify name
    original_data['projectInfo']['name'] = f"{original_data['projectInfo']['name']} (kopija)"
    # Create new procurement
    new_id = database.create_procurement(original_data)
    if new_id:
        st.success(f"Naročilo kopirano! ID: {new_id}")
        st.rerun()
```

### Existing Pattern Reference:
- Follow the edit/delete button pattern in dashboard.py
- Use existing database.create_procurement() without modifications

### Key Constraints:
- Must not open form editor
- Must preserve all data including lots
- Must generate new ID and timestamp automatically

## Implementation Checklist

### Database Operations:
- [ ] Add get_procurement() function if missing
- [ ] Ensure create_procurement() handles all fields including lots

### Dashboard UI:
- [ ] Add copy button to procurement row
- [ ] Style button consistently with existing buttons
- [ ] Add success/error feedback

### Data Handling:
- [ ] Deep copy all procurement data
- [ ] Update name field with "(kopija)" suffix
- [ ] Remove ID field to allow auto-generation

## Definition of Done
- [ ] Copy button visible and functional in dashboard
- [ ] Procurement copied with all data intact
- [ ] Name automatically appended with "(kopija)"
- [ ] New ID and timestamp generated
- [ ] Success message displayed
- [ ] Dashboard refreshes to show new procurement
- [ ] Existing procurements remain unchanged
- [ ] No errors in console

## Risk and Compatibility Check

### Minimal Risk Assessment:
- **Primary Risk:** Data corruption during copy
- **Mitigation:** Use transaction or verify data before insert
- **Rollback:** Delete copied procurement if issues detected

### Compatibility Verification:
- [x] No breaking changes to existing APIs
- [x] Database changes are additive only (new rows)
- [x] UI changes follow existing button patterns
- [x] Performance impact is negligible