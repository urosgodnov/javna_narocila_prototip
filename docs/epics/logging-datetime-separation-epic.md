# Brownfield Epic: Logging System Date/Time Column Separation

## Epic Title
Separate Date and Time Storage in Logging Tables - Brownfield Enhancement

## Epic Goal
Refactor the logging system to store date and time information in separate dedicated columns instead of combined timestamp strings, improving query performance and filtering capabilities in the Dnevnik admin interface.

## Epic Description

### Existing System Context:
- **Current relevant functionality:** Application logs stored in `application_logs` table with timestamp data in single DATETIME columns
- **Technology stack:** SQLite database, Python logging handlers, Streamlit admin UI
- **Integration points:** 
  - `DatabaseLogHandler` in `utils/database_logger.py`
  - Dnevnik tab in `ui/admin_panel.py:749`
  - Log filtering and display logic

### Enhancement Details:
- **What's being added/changed:** 
  - Split existing timestamp columns into separate DATE and TIME columns
  - Maintain backward compatibility with existing queries
  - Update indexes for optimized date-based filtering
  
- **How it integrates:** 
  - Add new columns alongside existing ones initially
  - Migrate data progressively
  - Update queries to use new columns while maintaining fallback

- **Success criteria:**
  - Date-based filters execute 50% faster
  - Time-range queries simplified
  - No disruption to existing logging
  - Dnevnik UI filters work seamlessly

## Stories

### Story 1: Add Date/Time Columns and Migration Logic
**Description:** Add new `log_date` (DATE) and `log_time` (TIME) columns to `application_logs` table, create migration script to populate from existing timestamps, and add triggers for new records.

**Acceptance Criteria:**
- New columns added without breaking existing queries
- Migration script safely converts 38,000+ existing records
- Triggers ensure new logs populate both old and new columns
- Rollback script prepared

### Story 2: Update DatabaseLogHandler and Queries
**Description:** Modify `DatabaseLogHandler` to write to new columns, update all SELECT queries to use indexed date column for filtering, maintain backward compatibility.

**Acceptance Criteria:**
- Handler writes date/time to new columns
- Existing timestamp column still populated for compatibility
- All queries updated with proper indexes
- Performance improvement measurable

### Story 3: Update Dnevnik UI Filters
**Description:** Enhance the Dnevnik admin panel filters to leverage separate date/time columns for improved filtering performance and user experience.

**Acceptance Criteria:**
- Date range filters use new `log_date` column
- Time-of-day filtering capability added
- Filter performance noticeably improved
- Existing filter behavior preserved

## Compatibility Requirements
- ✅ Existing logging APIs remain unchanged
- ✅ Database schema changes are backward compatible (new columns added, old retained)
- ✅ UI changes follow existing Streamlit patterns
- ✅ Performance impact is positive (improved query speed)
- ✅ Existing queries continue to work during transition

## Risk Mitigation

**Primary Risk:** Data inconsistency between old timestamp and new date/time columns during migration

**Mitigation:** 
- Use database triggers to keep columns synchronized
- Implement verification queries to ensure data integrity
- Gradual rollout with monitoring

**Rollback Plan:** 
- Keep original timestamp columns unchanged
- Remove triggers if issues arise
- Revert code to use original columns via feature flag

## Definition of Done
- ✅ All three stories completed with acceptance criteria met
- ✅ Existing logging functionality verified through testing
- ✅ Date/time filtering working correctly in Dnevnik
- ✅ Performance improvement documented (target: 50% faster date queries)
- ✅ No regression in existing logging features
- ✅ Migration documentation updated

## Validation Checklist

### Scope Validation:
- ✅ Epic can be completed in 3 stories
- ✅ No architectural documentation required (follows existing patterns)
- ✅ Enhancement follows existing database patterns
- ✅ Integration complexity is manageable

### Risk Assessment:
- ✅ Risk to existing system is low (additive changes)
- ✅ Rollback plan is feasible (original columns retained)
- ✅ Testing approach covers existing functionality
- ✅ Team familiar with SQLite and logging system

### Completeness Check:
- ✅ Epic goal is clear and achievable
- ✅ Stories are properly scoped
- ✅ Success criteria are measurable (50% performance improvement)
- ✅ Dependencies identified (database, logging handler, UI)