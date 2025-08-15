# Epic: Database Management Tools - Brownfield Enhancement

## Epic Goal
Add comprehensive database visualization and management capabilities to the admin module, enabling administrators to view database schema diagrams and perform CRUD operations on all SQLite tables through an intuitive tabbed interface.

## Epic Description

### Existing System Context:
- **Current relevant functionality:** Admin panel (`ui/admin_panel.py`) with tabbed interface for various management tasks
- **Technology stack:** Python, Streamlit, SQLite database
- **Integration points:** Existing "Baza podatkov" tab (currently shows ChromaDB placeholder), SQLite connection through `database.py`

### Enhancement Details:
- **What's being added/changed:** 
  - Database schema visualization showing all tables and relationships
  - Interactive table management interface with CRUD operations
  - New separate file for database management components
- **How it integrates:** 
  - Replaces current placeholder content in "Baza podatkov" tab
  - Uses existing SQLite connection patterns from `database.py`
  - Follows existing Streamlit UI patterns from admin panel
- **Success criteria:**
  - Database diagram displays all 7 tables with relationships
  - Each table accessible through tabs/accordion with full CRUD functionality
  - Code organized in separate file for maintainability

## Stories

### Story 1: Database Schema Visualization
- Create ERD diagram showing all SQLite tables and their relationships
- Use mermaid or graphviz for diagram generation
- Display in the admin panel's database tab

### Story 2: Table Data Management Interface
- Create tabbed/accordion interface for all database tables
- Implement data viewing with pagination and search
- Add create, update, and delete functionality for each table

### Story 3: Module Integration and Testing
- Create new `ui/database_manager.py` file for all database management code
- Integrate with existing admin panel
- Ensure data integrity and validation

## Compatibility Requirements
- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible
- [x] UI changes follow existing patterns
- [x] Performance impact is minimal

## Risk Mitigation
- **Primary Risk:** Direct database manipulation could corrupt data or break referential integrity
- **Mitigation:** Implement validation, use transactions, show warnings for destructive operations
- **Rollback Plan:** Database operations are transactional; failed operations automatically rollback

## Definition of Done
- [ ] All stories completed with acceptance criteria met
- [ ] Existing functionality verified through testing
- [ ] Integration points working correctly
- [ ] Documentation updated appropriately
- [ ] No regression in existing features

## Technical Details

### Database Tables to Manage:
1. **drafts** - Form drafts storage
2. **javna_narocila** - Main procurement records
3. **cpv_codes** - CPV classification codes
4. **criteria_types** - Criteria type definitions
5. **cpv_criteria** - CPV-criteria associations
6. **organizacija** - Organization records
7. **application_logs** - System logging

### Implementation Notes:
- Use Streamlit's native components (st.tabs, st.expander, st.dataframe)
- Implement pagination for large tables
- Add search/filter capabilities
- Include data export options (CSV)
- Show foreign key relationships in diagram
- Add confirmation dialogs for destructive operations

### File Structure:
```
ui/
├── admin_panel.py          # Existing admin interface (to be modified)
└── database_manager.py     # New file for database management (to be created)
```

## Story Manager Handoff

Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing system running Python/Streamlit/SQLite
- Integration points: Existing admin_panel.py tab structure, database.py connection utilities
- Existing patterns to follow: Streamlit form patterns, tab-based UI organization, session state management
- Critical compatibility requirements: Must not break existing database operations, follow existing UI styling
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering comprehensive database management tools for administrators.