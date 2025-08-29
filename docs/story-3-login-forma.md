# Story 3: Login forma z organizacijsko prijavo - Brownfield Addition

## User Story
As a **uporabnik sistema**,  
I want **to select my organization and authenticate before accessing the system**,  
So that **data is secured per organization and access is controlled**.

## Story Context

### Existing System Integration:
- **Integrates with:** app.py (main entry point), database.py, session state management
- **Technology:** Python, Streamlit, SQLite, MCP (21st.dev) for UI
- **Follows pattern:** Streamlit page routing, session state authentication pattern
- **Touch points:** Main app initialization, organization table, session management

## Acceptance Criteria

### Functional Requirements:
1. ✅ Login form appears before any other content when app starts
2. ✅ Organization dropdown shows all available organizations
3. ✅ Default selection is "demo_organizacija" 
4. ✅ Password field for organization authentication
5. ✅ "JAvna NAročila - JANA AI" title prominently displayed
6. ✅ Elegant UI design using MCP magic (21st.dev)

### Integration Requirements:
7. ✅ After successful login, user sees normal dashboard
8. ✅ Session maintains organization context throughout app
9. ✅ Failed login shows appropriate error message
10. ✅ Logout option available in main app

### Quality Requirements:
11. ✅ Login form is visually appealing and professional
12. ✅ Form is responsive and works on mobile
13. ✅ Password field is properly masked
14. ✅ Loading state shown during authentication

## Technical Notes

### Login Flow Implementation:
```python
# In app.py, at the beginning of main()
def show_login_form():
    """Display organization login form."""
    
    # Check if already logged in
    if st.session_state.get('authenticated', False):
        return True
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Title with JANA emphasis
        st.markdown("""
        <h1 style='text-align: center; color: #1f77b4;'>
            <span style='font-size: 1.2em;'>JA</span>vna 
            <span style='font-size: 1.2em;'>NA</span>ročila - 
            <span style='color: #ff7f0e; font-weight: bold;'>JANA AI</span>
        </h1>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Organization selection
        orgs = database.get_all_organizations()
        org_names = [org['name'] for org in orgs]
        
        selected_org = st.selectbox(
            "Izberite organizacijo",
            options=org_names,
            index=org_names.index("demo_organizacija") if "demo_organizacija" in org_names else 0,
            key="login_org"
        )
        
        # Password input
        password = st.text_input(
            "Geslo organizacije",
            type="password",
            key="login_password",
            placeholder="Vnesite geslo"
        )
        
        # Login button
        if st.button("🔐 Prijava", use_container_width=True, type="primary"):
            if authenticate_organization(selected_org, password):
                st.session_state.authenticated = True
                st.session_state.organization = selected_org
                st.success("Uspešna prijava!")
                st.rerun()
            else:
                st.error("Napačno geslo!")
        
        # Demo info
        st.info("Demo organizacija nima nastavljenega gesla - pustite prazno")
    
    return False

def authenticate_organization(org_name: str, password: str) -> bool:
    """Verify organization password."""
    org = database.get_organization_by_name(org_name)
    if not org:
        return False
    
    # Allow empty password for demo
    if org_name == "demo_organizacija" and password == "":
        return True
    
    # Check hashed password
    if org.get('password_hash'):
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == org['password_hash']
    
    return False
```

### UI Enhancement with MCP:
```python
# Use MCP magic for beautiful form
# /ui command to generate elegant login component
# Focus on: clean design, good spacing, professional look
# Color scheme: blue/orange to match JANA branding
```

### Session Management:
```python
# Add logout button in sidebar
if st.sidebar.button("🚪 Odjava"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
```

### Existing Pattern Reference:
- Follow authentication patterns from admin panel
- Use existing database functions for organization queries
- Maintain session state patterns from form navigation

### Key Constraints:
- Must appear before any other content
- Demo organization allows empty password
- Session must persist across page reruns

## Implementation Checklist

### Authentication:
- [ ] Create show_login_form() function
- [ ] Implement authenticate_organization() function
- [ ] Add password verification logic

### UI Design:
- [ ] Design elegant form with MCP magic
- [ ] Add JANA AI branding with proper styling
- [ ] Center form on page
- [ ] Add loading states and feedback

### Session Management:
- [ ] Store organization in session state
- [ ] Add authentication check at app start
- [ ] Implement logout functionality
- [ ] Persist session across navigation

### Integration:
- [ ] Modify main() to show login first
- [ ] Pass organization context to all components
- [ ] Update database queries to filter by organization (future)

## Definition of Done
- [ ] Login form appears on app start
- [ ] Organization dropdown populated with all organizations
- [ ] demo_organizacija selected by default
- [ ] Password authentication working
- [ ] JANA AI branding visible
- [ ] UI is elegant and professional
- [ ] Successful login shows dashboard
- [ ] Failed login shows error
- [ ] Session persists during use
- [ ] Logout functionality available

## Risk and Compatibility Check

### Minimal Risk Assessment:
- **Primary Risk:** Session management breaking existing navigation
- **Mitigation:** Careful testing of all navigation paths
- **Rollback:** Config flag to disable login requirement

### Compatibility Verification:
- [x] No breaking changes to existing APIs  
- [x] Database queries unchanged initially
- [x] UI changes are additive (new login page)
- [x] Performance impact is minimal