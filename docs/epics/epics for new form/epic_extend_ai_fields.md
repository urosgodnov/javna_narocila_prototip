# Epic: Extend AI Management for Additional Form Fields - Brownfield Enhancement

## Epic Goal
Extend the existing AI management system in the admin module to support AI assistance for additional cofinancer and requirement fields across all order types (blago, storitve, gradnje, mešano).

## Epic Description

### Existing System Context:
- **Current functionality**: AI management tab exists in admin panel with prompt management for select fields
- **Technology stack**: Python, Streamlit, SQLite with ai_system_prompts table
- **Integration points**: 
  - `ui/ai_manager.py` - existing AI management interface
  - `PROMPT_SECTIONS` dictionary defines available fields
  - Database table stores prompts with versioning
  - Currently supports: `posebne_zahteve_sofinancerja` and 3 other fields

### Enhancement Details:
- **What's being added/changed**: 
  - Add new fields to PROMPT_SECTIONS configuration
  - Extend field coverage for all cofinancer contexts
  - Support mixed order components
  - Ensure all order types are covered
  
- **How it integrates**: 
  - Simply extends existing PROMPT_SECTIONS dictionary
  - Uses existing database schema and UI
  - No structural changes needed
  
- **Success criteria**: 
  - All cofinancer requirement fields have AI support
  - Works for regular and mixed orders
  - Admins can manage prompts through existing interface
  - Consistent field naming with form schema

## Stories

### Story 1: Extend PROMPT_SECTIONS Configuration
**Description**: Add new field definitions to support all cofinancer requirements
- Update PROMPT_SECTIONS in ai_manager.py:
  ```python
  PROMPT_SECTIONS = {
      'vrsta_narocila': {
          'title': 'Vrsta javnega naročila',
          'fields': [
              'posebne_zahteve_sofinancerja',  # Existing
              'specialRequirements',            # New - for new form structure
              'useAIForRequirements'            # New - checkbox support
          ]
      },
      'mesano_narocilo': {                    # New section
          'title': 'Mešano javno naročilo',
          'fields': [
              'mixedOrder_specialRequirements',
              'mixedOrder_cofinancer_requirements'
          ]
      },
      # Keep existing sections...
  }
  ```
- Ensure field keys match JSON schema field names
- Add support for all order types

### Story 2: Default Prompts and Field Mappings
**Description**: Create default prompts for new fields and update field type mappings
- Extend get_default_prompt() function for new fields
- Add prompts that understand context:
  - Order type (blago/storitve/gradnje/mešano)
  - Program information (name, area, code)
  - Cofinancer type
- Update field type detection for new fields
- Ensure prompts work in Slovenian with proper terminology

### Story 3: Testing and Documentation
**Description**: Test new fields through admin interface and document usage
- Test prompt creation for each new field
- Verify prompts can be edited and versioned
- Test AI generation with sample data
- Create admin guide for new fields:
  - Which fields are available
  - Best practices for prompts
  - Example prompts for common scenarios
- Update help text in admin interface

## New Fields to Add

### Cofinancer Fields (all order types):
- `specialRequirements` - Main requirements field
- `useAIForRequirements` - AI assistance toggle
- `programName` - Context for AI
- `programArea` - Context for AI
- `programCode` - Context for AI

### Mixed Order Specific:
- `mixedOrderComponents[].cofinancers[].specialRequirements`
- `mixedOrderComponents[].cofinancers[].useAIForRequirements`

### Field Mapping Example:
```python
# Add to PROMPT_SECTIONS
'vrsta_narocila': {
    'title': 'Vrsta javnega naročila',
    'fields': [
        'posebne_zahteve_sofinancerja',     # Legacy name
        'cofinancer_special_requirements',   # New unified name
        'cofinancer_program_requirements',   # Program-specific
        'cofinancer_eu_requirements',        # EU funding specific
        'cofinancer_reporting_requirements'  # Reporting needs
    ]
}
```

## Implementation Approach
- [x] Extend existing PROMPT_SECTIONS configuration
- [x] Use existing database schema (no changes needed)
- [x] Leverage existing UI and prompt management
- [x] Clean implementation without legacy concerns

## Implementation Benefits
- **Minimal Effort**: Just configuration changes, no new code
- **Proven System**: Uses existing, working AI management
- **Immediate Value**: New fields get AI support quickly
- **No Risk**: Simple configuration that can be adjusted anytime

## Definition of Done
- [ ] All cofinancer requirement fields added to PROMPT_SECTIONS
- [ ] Default prompts created for new fields
- [ ] Fields work through existing admin interface
- [ ] Prompts generate appropriate content
- [ ] Documentation updated with new fields
- [ ] Testing confirms all order types supported

## Technical Notes

### Current Fields in System:
```python
# Already implemented
'posebne_zahteve_sofinancerja'
'posebne_zelje_pogajanja'
'ustreznost_poklicna_drugo'
'ekonomski_polozaj_drugo'
'tehnicna_sposobnost_drugo'
'merila_drugo'
```

### Fields to Add:
```python
# Cofinancer requirements (all contexts)
'specialRequirements'
'useAIForRequirements'
# Mixed order specific
'mixedOrder_cofinancer_requirements'
# Additional context fields
'technical_specifications_ai'
'evaluation_criteria_ai'
```

## Dependencies
- Existing ai_manager.py structure
- ai_system_prompts database table
- No new dependencies needed

## Estimated Effort
- Story 1: 2-3 hours (configuration updates)
- Story 2: 3-4 hours (prompts and mappings)
- Story 3: 2-3 hours (testing and documentation)
- **Total**: 7-10 hours (1-1.5 days)

## Future Considerations
- Consider unified field naming convention
- May need field aliasing for backward compatibility
- Could add field grouping for better organization
- Potential for prompt inheritance for similar fields

## Notes
- This is a configuration extension, not architectural change
- Leverages all existing AI management infrastructure
- Admin training may be needed for new fields
- Consider adding field descriptions in UI