# Admin Module Separation with URL Routing - Brownfield Enhancement

## Epic Goal
Create a secure, URL-separated admin module accessible via `/admin` path with minimalistic design, strong authentication, and future-ready security infrastructure, completely isolated from the main user application.

## Epic Description

### Existing System Context:
- **Current functionality**: Admin panel accessed through main app navigation via "Nastavitve" button in dashboard
- **Technology stack**: Python, Streamlit, SQLite, session-based navigation
- **Integration points**: 
  - `app.py` handles both user and admin routing
  - Session state `current_page` controls navigation
  - Dashboard button triggers admin access
  - No role-based access control
  - No URL-based routing

### Enhancement Details:
- **What's being added/changed**: 
  - URL-based routing: `jana.ai` → user app, `jana.ai/admin` → admin panel
  - Secure admin authentication with password (expandable to MFA)
  - User management interface within admin module
  - Minimalistic, professional admin UI (no large icons)
  - Security policy infrastructure for future expansion
  - Complete separation of user and admin codebases
  
- **How it integrates**: 
  - Query parameter routing for Streamlit (`?page=admin`)
  - Production: nginx reverse proxy for true URL paths
  - Maintains all existing admin functionality
  - Database connections remain shared
  - Session isolation between user and admin
  
- **Success criteria**: 
  - Admin accessible only via `/admin` URL path
  - Strong authentication required for admin access
  - User management interface operational
  - Minimalistic, clean design implemented
  - No admin code loaded for regular users
  - Security infrastructure ready for expansion

## Stories

### Story 1: Implement URL-Based Routing and Entry Points
**Description**: Create URL-based separation between user and admin applications
- Implement query parameter detection (`?page=admin`)
- Create routing logic in main `app.py`
- Set up nginx configuration for production URL paths
- Implement automatic redirects based on URL
- Create separate entry points for user and admin
- Add URL validation and security checks

### Story 2: Build Secure Authentication and User Management
**Description**: Implement robust authentication system with user management interface
- Keep current admin login page design intact (no style changes)
- Enhance security with password hashing and verification
- Add brute force protection (rate limiting)
- Build user management interface in admin:
  - View all administrators
  - Add/remove admin users (future)
  - Set permissions and roles (future)
  - Audit log of admin actions
- Session management with timeout
- Secure cookie handling for "remember me"

### Story 3: Apply Minimalistic Design to Admin Panel and Security Infrastructure
**Description**: Implement clean design for admin panel content (not login) and prepare security framework
- Apply minimalistic design to admin panel content only:
  - Remove oversized icons and buttons in admin panels
  - Create compact table layouts for data management
  - Implement consistent spacing (8px grid) in admin UI
  - Use subtle colors and typography for admin sections
- Keep login page design unchanged
- Build security infrastructure:
  - Audit logging system
  - Permission checking framework
  - API key management (future)
  - 2FA preparation (future)
- Add security headers and CSP policies
- Implement secure session storage
- Add visual indicators for admin mode
- Store admin status in secure session state

### Story 3: Clean Up Navigation and Dependencies
**Description**: Remove cross-dependencies between user and admin modules
- Remove "Nastavitve" button from dashboard
- Clean up `current_page` session state usage
- Separate admin imports from main app
- Add admin-specific navigation menu
- Update documentation for new structure

## Implementation Approach

### URL-Based Routing Architecture (Recommended)

#### Development Environment
```python
# Query parameter routing for Streamlit
# jana.ai → Main application
# jana.ai/?admin=true → Admin panel

# app.py - Main router
import streamlit as st
from urllib.parse import urlparse, parse_qs

def get_route():
    """Detect routing based on URL parameters"""
    query_params = st.experimental_get_query_params()
    
    # Check for admin route
    if query_params.get('admin'):
        return 'admin'
    
    # Default to user app
    return 'user'

def main():
    route = get_route()
    
    if route == 'admin':
        # Require authentication immediately
        if not check_admin_auth():
            render_admin_login()
        else:
            render_admin_panel()
    else:
        render_user_app()
```

#### Production Environment (nginx)
```nginx
# nginx configuration for true URL paths
server {
    listen 80;
    server_name jana.ai;

    # User application (default)
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Admin application (protected path)
    location /admin {
        # Add IP whitelist or basic auth here
        auth_basic "Admin Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://localhost:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Admin-Access "true";
    }
}
```

## Compatibility Requirements
- [x] All existing admin functions remain available
- [x] Database operations unchanged
- [x] Authentication system preserved
- [x] No data migration required
- [x] Existing templates and drafts accessible

## Risk Mitigation
- **Primary Risk:** Users losing access to admin functions
- **Mitigation:** Implement gradual transition with both access methods available initially
- **Rollback Plan:** Keep original navigation as fallback option during transition period

## Definition of Done
- [ ] Admin module runs independently from main form
- [ ] Role-based access control implemented
- [ ] No admin code loaded for regular users
- [ ] Clean separation of concerns achieved
- [ ] Documentation updated with new access patterns
- [ ] All existing admin functionality preserved
- [ ] Performance improved by not loading unnecessary modules

## Technical Implementation Notes

### Secure Authentication System
```python
# security/auth_manager.py
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional

class AdminAuthManager:
    """Minimalistic secure authentication for admin"""
    
    # Rate limiting
    failed_attempts = {}
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = 300  # 5 minutes
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Secure password hashing"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
    
    @staticmethod
    def verify_admin(password: str) -> bool:
        """Verify admin password with rate limiting"""
        ip = get_client_ip()
        
        # Check rate limiting
        if AdminAuthManager.is_locked_out(ip):
            return False
        
        # Verify password
        stored_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        salt = os.environ.get('ADMIN_SALT', 'default_salt')
        
        if AdminAuthManager.hash_password(password, salt) == stored_hash:
            AdminAuthManager.failed_attempts.pop(ip, None)
            return True
        
        # Record failed attempt
        AdminAuthManager.record_failed_attempt(ip)
        return False
    
    @staticmethod
    def is_locked_out(ip: str) -> bool:
        """Check if IP is locked out"""
        if ip in AdminAuthManager.failed_attempts:
            attempts, first_attempt = AdminAuthManager.failed_attempts[ip]
            if attempts >= AdminAuthManager.MAX_ATTEMPTS:
                if time.time() - first_attempt < AdminAuthManager.LOCKOUT_TIME:
                    return True
                else:
                    # Reset after lockout period
                    del AdminAuthManager.failed_attempts[ip]
        return False
```

### Enhanced Admin Login Security (Keep Current Design)
```python
# admin_login.py - Enhanced security, same design
import streamlit as st
from ui.admin_panel import render_login_form  # Use existing design

def render_secure_admin_login():
    """Enhanced admin login with current design intact"""
    
    # Keep the existing admin login design from admin_panel.py
    # Just enhance the backend security
    
    # Apply unified design system (already exists)
    from ui.admin_module_design import apply_design_system
    apply_design_system()
    
    # Use existing login form layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Keep existing header design
        st.markdown("""
        <div class="login-header">
            <h3>Administracija</h3>
            <p>Vnesite geslo za dostop</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_login_form", clear_on_submit=False):
            password = st.text_input(
                "Geslo administracije",
                type="password",
                help="Vnesite geslo za dostop do administracije",
                placeholder="Geslo"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                remember = st.checkbox("Zapomni si me")
            
            with col2:
                submitted = st.form_submit_button(
                    "Prijava",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Enhanced security verification
                if AdminAuthManager.verify_admin(password):
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_login_time = datetime.now()
                    
                    # Set session timeout based on remember me
                    if remember:
                        st.session_state.session_timeout = datetime.now() + timedelta(hours=24)
                    else:
                        st.session_state.session_timeout = datetime.now() + timedelta(hours=1)
                    
                    audit_log("admin_login", "success")
                    st.rerun()
                else:
                    # Check if locked out
                    if AdminAuthManager.is_locked_out(get_client_ip()):
                        st.error("⛔ Preveč neuspešnih poskusov. Poskusite čez 5 minut.")
                    else:
                        remaining = AdminAuthManager.get_remaining_attempts(get_client_ip())
                        st.error(f"❌ Napačno geslo. Preostalo poskusov: {remaining}")
                    
                    audit_log("admin_login", "failed")
```

### User Management Interface
```python
# admin/user_management.py - Minimalistic user management
def render_user_management():
    """Clean user management interface"""
    
    st.markdown("#### User Management")
    
    # Current admin (for now, single admin)
    st.markdown("""
    <style>
    .user-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .user-table th {
        background: #f5f5f5;
        padding: 8px 12px;
        text-align: left;
        font-weight: 500;
        border-bottom: 1px solid #e0e0e0;
    }
    .user-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    .status-active {
        color: #4caf50;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display current administrator
    st.markdown("""
    <table class="user-table">
        <thead>
            <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Last Login</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>admin</td>
                <td>Administrator</td>
                <td>{}</td>
                <td class="status-active">Active</td>
            </tr>
        </tbody>
    </table>
    """.format(
        st.session_state.get('admin_login_time', 'Never').strftime('%Y-%m-%d %H:%M')
        if hasattr(st.session_state.get('admin_login_time'), 'strftime') else 'Never'
    ), unsafe_allow_html=True)
    
    # Future expansion section
    with st.expander("Security Policy (Future)", expanded=False):
        st.info("""
        **Planned Security Features:**
        - Multi-factor authentication (2FA)
        - Role-based access control (RBAC)
        - API key management
        - IP whitelisting
        - Session management
        - Audit log retention policy
        """, icon=None)
    
    # Audit log section
    st.markdown("#### Recent Admin Activity")
    display_audit_log()

def display_audit_log():
    """Display recent admin actions"""
    logs = get_recent_audit_logs(limit=10)
    
    if logs:
        for log in logs:
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.caption(log['timestamp'])
            with col2:
                st.caption(log['action'])
            with col3:
                st.caption(log['status'])
    else:
        st.caption("No recent activity")
```

### Minimalistic Admin Panel
```python
# admin_panel.py - Clean, efficient design
def render_admin_panel():
    """Minimalistic admin panel"""
    
    # Clean header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### Administration")
    with col2:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.experimental_set_query_params()  # Clear admin param
            st.rerun()
    
    # Minimal tab design
    tab1, tab2, tab3, tab4 = st.tabs([
        "Templates", "Organizations", "Users", "Settings"
    ])
    
    with tab1:
        render_template_management()
    
    with tab2:
        render_organization_management()
    
    with tab3:
        render_user_management()
    
    with tab4:
        render_admin_settings()
```

## Benefits
1. **Security**: Admin functions not exposed to regular users
2. **Performance**: Faster load times by loading only needed modules
3. **Maintainability**: Clear separation of concerns
4. **User Experience**: Cleaner navigation for both user types
5. **Scalability**: Easier to add new admin or user features

## Migration Path
1. **Phase 1**: Implement multipage structure (keep both navigation methods)
2. **Phase 2**: Add role-based access control
3. **Phase 3**: Remove old navigation method
4. **Phase 4**: Optimize imports and dependencies

## Estimated Effort
- Story 1: 4-5 hours (URL routing and entry points)
- Story 2: 5-6 hours (secure authentication and user management)
- Story 3: 3-4 hours (minimalistic design and security infrastructure)
- **Total**: 12-15 hours (2 days)

## Future Considerations
- Consider separate subdomain for admin (admin.example.com)
- Implement audit logging for admin actions
- Add two-factor authentication for admin access
- Create admin API for programmatic access
- Consider admin dashboard with analytics