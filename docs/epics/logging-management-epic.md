# Epic: Logging Management System with Tiered Retention

## Epic ID: LOG-001
**Created Date:** 2024-01-14  
**Status:** In Planning  
**Type:** Brownfield Enhancement  

## Epic Goal
Implement a comprehensive database-backed logging system with tiered retention periods based on log severity, providing admin panel visibility with organization context and automatic cleanup to maintain optimal system performance.

## Business Value
- **Debugging Capability:** Maintain critical error logs for 7 days while keeping routine logs lightweight
- **Compliance:** Audit trail for form submissions and admin actions (30 days)
- **Performance Monitoring:** Track system usage patterns and identify bottlenecks
- **Cost Efficiency:** Automatic cleanup prevents database bloat
- **Security:** Track admin actions and user access patterns

## Epic Description

### Existing System Context
- **Current Functionality:** Basic Python logging to console/file, existing admin panel, organization management
- **Technology Stack:** Python 3.x, Streamlit, PostgreSQL, session state management
- **Integration Points:** 
  - Admin panel UI (`app.py`)
  - Database operations (`database.py`)
  - Existing logging calls throughout application
  - Session state for organization context

### Enhancement Details
- **What's Being Added:**
  - Database table for log storage with retention metadata
  - Custom DatabaseLogHandler for Python logging framework
  - Admin panel interface for log viewing/management
  - Automatic cleanup job with tiered retention
  
- **How It Integrates:**
  - Intercepts existing Python logging calls
  - Extends admin panel with new "Logs" section
  - Background task for hourly cleanup
  
- **Success Criteria:**
  - All application logs stored in database
  - Logs automatically deleted according to retention policy
  - Admin can search, filter, and export logs
  - No performance degradation

## Tiered Retention Policy

| Log Level | Retention Period | Use Case |
|-----------|-----------------|----------|
| CRITICAL | 30 days | System failures, security issues |
| ERROR | 7 days | Investigation of issues |
| WARNING | 3 days | Recent warnings and alerts |
| INFO | 24 hours | Standard operational logs |
| DEBUG | 6 hours | Active debugging only |

### Special Retention Rules

| Event Type | Retention | Reason |
|------------|-----------|---------|
| form_submission | 30 days | Audit trail |
| validation_error | 3 days | Pattern analysis |
| admin_action | 30 days | Security audit |
| login_event | 7 days | Security review |

## User Stories

### Story 1: Database Infrastructure with Tiered Retention
**Priority:** High  
**Points:** 5  
- Create `application_logs` table with retention support
- Implement retention_hours and expires_at columns
- Add indexes for performance
- Create cleanup function and views

### Story 2: DatabaseLogHandler Implementation
**Priority:** High  
**Points:** 3  
- Create custom logging handler
- Integrate with Python logging framework
- Capture organization context from session
- Apply retention rules based on log level

### Story 3: Admin Panel Log Management Interface
**Priority:** Medium  
**Points:** 5  
- Add "Logs" section to admin panel
- Implement filters (level, organization, time range)
- Add search functionality
- Export to CSV capability
- Delete selected logs option

### Story 4: Automated Retention Management
**Priority:** Medium  
**Points:** 3  
- Implement hourly cleanup job
- Add manual purge option
- Create retention statistics dashboard
- Monitor storage usage

## Technical Requirements

### Database Schema
```sql
CREATE TABLE application_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    organization_id INTEGER REFERENCES organizacija(id) ON DELETE CASCADE,
    organization_name VARCHAR(255),
    log_level VARCHAR(20) NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    message TEXT,
    retention_hours INTEGER NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    additional_context JSONB,
    log_type VARCHAR(50)
);
```

### Performance Considerations
- Indexed queries on timestamp, organization, and log level
- Pagination for large result sets
- Asynchronous logging to prevent blocking
- Automatic partitioning for tables > 1GB

## Acceptance Criteria
- [ ] Logs are stored in database with correct retention periods
- [ ] Each log level follows its retention policy
- [ ] Admin can view logs filtered by organization
- [ ] Search functionality works across message content
- [ ] Automatic cleanup runs without manual intervention
- [ ] Export functionality produces valid CSV
- [ ] No performance impact on main application
- [ ] Existing logging calls continue to work

## Dependencies
- PostgreSQL database access
- Admin authentication system
- Background task scheduler (for cleanup)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| High volume logging fills database | High | Tiered retention, size monitoring, alerts |
| Cleanup job fails | Medium | Manual purge option, monitoring alerts |
| Performance impact from logging | Medium | Async logging, batch inserts, indexes |
| Lost logs during rollback | Low | Export capability, file backup option |

## Rollback Plan
1. Disable DatabaseLogHandler in configuration
2. Revert to file-based logging
3. Export critical logs before dropping table
4. Remove admin panel log section
5. Drop `application_logs` table if needed

## Definition of Done
- [ ] All 4 stories completed and tested
- [ ] Documentation updated
- [ ] Admin panel section functional
- [ ] Retention policies working correctly
- [ ] Performance benchmarks passed
- [ ] Code reviewed and approved
- [ ] Deployed to staging environment
- [ ] Stakeholder approval received

## Notes
- Consider adding log aggregation for analytics in future phase
- May want to integrate with external monitoring tools later
- Archive capability could be added for compliance requirements

## References
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)