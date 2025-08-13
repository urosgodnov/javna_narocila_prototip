# Epic 21: Procurement Configuration Export/Import - Brownfield Enhancement

## Epic Goal

Enable administrators to export and import procurement configurations (CPV criteria settings, templates, and system preferences) to facilitate data backup, sharing between organizations, and system migration scenarios.

## Epic Description

### Existing System Context

- **Current relevant functionality:** The system manages CPV codes, criteria relationships, and procurement templates through an admin panel with database persistence
- **Technology stack:** Streamlit (UI), SQLite (database), Python (backend), JSON schemas for configuration
- **Integration points:** Admin panel UI (`ui/admin_panel.py`), database layer (`database.py`, `utils/criteria_manager.py`), CPV management system

### Enhancement Details

- **What's being added/changed:** Adding export/import functionality for procurement configurations including CPV criteria mappings, custom settings, and optionally templates
- **How it integrates:** New buttons in admin panel that trigger export to JSON/ZIP and import from uploaded files, utilizing existing database access patterns
- **Success criteria:** Administrators can successfully export all configuration data, import it to another instance, and have the system function identically

## Stories

### Story 21.1: Export Configuration Data
**Description:** Implement functionality to export all procurement configuration data (CPV criteria mappings, system settings) to a downloadable JSON file with metadata including export timestamp and version information.

**Acceptance Criteria:**
- Export button in admin panel creates downloadable JSON file
- File includes all CPV criteria relationships from database
- File includes metadata (export date, version, organization)
- Export process handles large datasets efficiently
- User receives confirmation of successful export

### Story 21.2: Import Configuration Data
**Description:** Implement functionality to import previously exported configuration data with validation, conflict resolution options, and rollback capability in case of errors.

**Acceptance Criteria:**
- Import button in admin panel accepts JSON file upload
- System validates file format and version compatibility
- Preview shows what will be imported before confirmation
- Option to merge with or replace existing data
- Rollback capability if import fails
- Import log shows what was imported/skipped

### Story 21.3: Template Backup Integration
**Description:** Extend export/import to optionally include Word templates and other document assets, packaging everything into a ZIP archive for complete configuration backup.

**Acceptance Criteria:**
- Option to include templates in export (creates ZIP instead of JSON)
- Import handles both JSON and ZIP formats
- Templates are correctly placed in expected directories
- File size limitations are clearly communicated
- Progress indicator for large file operations

## Compatibility Requirements

- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible (no schema changes required)
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact is minimal (async operations for large datasets)

## Risk Mitigation

- **Primary Risk:** Data corruption during import could break the system configuration
- **Mitigation:** 
  - Validate all data before import
  - Create automatic backup before import
  - Provide rollback mechanism
  - Show preview before confirming import
- **Rollback Plan:** 
  - Automatic database backup created before import
  - One-click restore to pre-import state
  - Import operations wrapped in database transaction

## Definition of Done

- [x] All three stories completed with acceptance criteria met
- [x] Existing functionality verified through testing
- [x] Export/import round-trip testing successful
- [x] Documentation updated with export/import procedures
- [x] No regression in existing admin panel features
- [x] Error handling for edge cases (corrupted files, version mismatches)
- [x] User feedback messages are clear and helpful

## Technical Notes

### File Format Structure
```json
{
  "version": "1.0",
  "export_date": "2024-01-15T10:30:00Z",
  "organization": "organization_name",
  "data": {
    "cpv_criteria": [...],
    "criteria_types": [...],
    "settings": {...}
  },
  "metadata": {
    "total_cpv_codes": 1000,
    "total_criteria_mappings": 150
  }
}
```

### Integration Points
- Utilize existing `criteria_manager.py` functions for data access
- Follow established Streamlit UI patterns from `admin_panel.py`
- Use existing database transaction patterns for atomicity
- Leverage current file handling patterns from template management

---

## Story Manager Handoff

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing Streamlit-based procurement system
- Integration points: Admin panel UI, SQLite database layer, existing CPV criteria management
- Existing patterns to follow: Streamlit session state management, database transaction handling, file upload/download patterns already in admin panel
- Critical compatibility requirements: Must not modify existing database schema, must maintain backward compatibility
- Each story must include verification that existing CPV management functionality remains intact

The epic should maintain system integrity while delivering robust export/import capabilities for procurement configurations."