# Epic 27: Centralized Validation System

## Epic Overview
Create a centralized validation module to consolidate all form validations, improving maintainability and control.

## Business Value
- **Maintainability**: All validations in one place for easier updates
- **Consistency**: Uniform validation approach across the application
- **Control**: Easier to manage and modify validation rules
- **Testing**: Simplified testing with isolated validation logic

## Current State
- Validations scattered across multiple files (app.py, form_renderer.py, criteria_validation.py)
- Difficult to maintain and update validation rules
- Duplicate validation logic in some places
- CPV validation logic separate from other validations

## Desired State
- Single `utils/validations.py` module containing all validation logic
- Clear validation class structure
- Easy to add new validations
- Comprehensive Merila validation with points and selection requirements

## Stories
1. **Story 27.1**: Create centralized validation module
2. **Story 27.2**: Implement Merila validation rules
3. **Story 27.3**: Refactor existing code to use centralized validations

## Success Metrics
- All existing validations working through central module
- No regression in validation functionality
- Merila validation prevents invalid submissions
- Code maintainability improved

## Dependencies
- Existing validation logic in app.py
- CPV validation in criteria_validation.py
- Form rendering in form_renderer.py

## Risks
- **Risk**: Breaking existing validations during migration
- **Mitigation**: Incremental migration with testing
- **Risk**: Performance impact from centralization
- **Mitigation**: Optimize validation functions, use caching where appropriate