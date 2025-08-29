# Story 2: Organizacijska avtentikacija in status management - Brownfield Addition

## User Story
As an **administrator sistema**,  
I want **to set passwords for organizations and manage procurement status inline**,  
So that **organizations have secure access and procurement workflow is clearly visible**.

## Story Context

### Existing System Integration:
- **Integrates with:** ui/admin_panel.py, dashboard.py, mainDB.db
- **Technology:** Python, Streamlit, SQLite, hashlib
- **Follows pattern:** Existing admin forms pattern, dashboard inline editing
- **Touch points:** Organizations table, procurements table, dashboard display

## Acceptance Criteria

### Functional Requirements:
1. ✅ Password field added to organization creation/edit form in admin
2. ✅ Passwords are hashed before storage (never plain text)
3. ✅ Status dropdown appears inline in dashboard procurement rows
4. ✅ Status options: "osnutek", "potrjen", "zaključen"

### Integration Requirements:
5. ✅ Existing organization management continues to work
6. ✅ Existing procurement data remains accessible
7. ✅ Dashboard layout maintains current structure
8. ✅ Database migration is backward compatible

### Quality Requirements:
9. ✅ Password hashing uses hashlib.sha256 or bcrypt
10. ✅ Status change saves immediately without page refresh
11. ✅ Status visible in dashboard without additional clicks

## Technical Notes

### Database Schema Changes:
```sql
-- Add to organizations table
ALTER TABLE organizations ADD COLUMN password_hash TEXT;

-- Add to procurements table  
ALTER TABLE procurements ADD COLUMN status TEXT DEFAULT 'osnutek';
```

### Password Hashing Implementation:
```python
# In admin_panel.py
import hashlib

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

# In organization form
password = st.text_input("Geslo organizacije", type="password")
if password:
    org_data['password_hash'] = hash_password(password)
```

### Status Management Implementation:
```python
# In dashboard.py, in procurement row
status_options = ["osnutek", "potrjen", "zaključen"]
current_status = procurement.get('status', 'osnutek')
new_status = st.selectbox(
    "Status",
    options=status_options,
    index=status_options.index(current_status),
    key=f"status_{procurement['id']}"
)
if new_status != current_status:
    database.update_procurement_status(procurement['id'], new_status)
    st.success("Status posodobljen")
```

### Existing Pattern Reference:
- Follow admin form patterns from ui/admin_panel.py
- Use database helper functions pattern from database.py

### Key Constraints:
- Passwords must be hashed, never stored in plain text
- Status change must be immediate (no submit button needed)
- Default status for existing records is "osnutek"

## Implementation Checklist

### Database Updates:
- [ ] Add password_hash column to organizations table
- [ ] Add status column to procurements table with default
- [ ] Create migration script for existing data

### Admin Panel:
- [ ] Add password field to organization form
- [ ] Implement password hashing function
- [ ] Update save logic to include password_hash

### Dashboard:
- [ ] Add status selectbox to procurement row
- [ ] Implement update_procurement_status() function
- [ ] Style status display (consider using colored badges)

### Security:
- [ ] Verify passwords are never logged
- [ ] Ensure password field uses type="password"
- [ ] Add password strength requirements (optional)

## Definition of Done
- [ ] Password field functional in admin organization form
- [ ] Passwords stored as hash in database
- [ ] Status dropdown visible in dashboard
- [ ] Status changes save immediately
- [ ] Database migration completed successfully
- [ ] Existing data remains intact
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated

## Risk and Compatibility Check

### Minimal Risk Assessment:
- **Primary Risk:** Password security vulnerability
- **Mitigation:** Use proven hashing algorithm, never store plain text
- **Rollback:** Remove password_hash column if issues arise

### Compatibility Verification:
- [x] No breaking changes to existing APIs
- [x] Database changes are additive only
- [x] UI changes follow existing patterns
- [x] Performance impact is negligible