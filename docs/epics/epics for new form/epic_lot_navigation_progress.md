# Epic: Advanced Lot Navigation and Progress Tracking System - Brownfield Enhancement

## Epic Goal
Transform the existing sidebar navigation into an intelligent progress tracking system that provides clear visual hierarchy, accurate completion percentages, and optimized space usage for complex multi-lot procurement forms.

## Epic Description

### Existing System Context:
- **Current functionality**: Basic sidebar menu showing all lots
- **Technology stack**: Python, Streamlit, Session state management
- **Integration points**: 
  - Existing sidebar navigation
  - Form step validation system
  - Session state for form data
  - Breadcrumb navigation at top

### Enhancement Details:
- **What's being added/changed**: 
  - Progress percentage for each lot
  - Visual hierarchy with indentation
  - Smart breadcrumb compression
  - Jump-to-completed-step navigation
  - Optimized display for long content
  
- **How it integrates**: 
  - Extends existing sidebar without breaking current navigation
  - Uses validation data to calculate progress
  - Maintains session state compatibility
  - Progressive enhancement approach
  
- **Success criteria**: 
  - Users can see completion % for each lot at a glance
  - Navigation clearly shows current lot context
  - Breadcrumbs don't overflow with multiple lots
  - Quick navigation to any completed section
  - Better space usage for long forms

## Stories

### Story 1: Enhanced Sidebar Navigation with Progress Tracking
**Description**: Transform sidebar to show lot progress and better visual hierarchy
- Display lot number and name prominently when in lot context
- Calculate and show completion percentage for each lot
- Implement progress calculation that works correctly when:
  - Starting fresh form
  - Editing existing form
  - Jumping to specific lot/step
- Add visual indentation for steps within lots (shift right)
- Consider replacing dropdown with:
  - Collapsible tree structure
  - Progress chart/graph visualization
  - Accordion-style expandable sections
- Ensure "jump to step" only works for completed steps

**Technical Requirements:**
```python
def calculate_lot_progress(lot_data, validation_rules):
    """
    Calculate completion percentage for a lot
    - Count required fields
    - Check filled fields
    - Return percentage (0-100)
    """
    
def render_sidebar_navigation():
    """
    Enhanced sidebar with:
    - Lot name and number display
    - Progress bars/percentages
    - Indented step hierarchy
    - Visual indicators for current position
    """
```

### Story 2: Smart Breadcrumb System
**Description**: Optimize breadcrumb display for multi-lot forms
- Show general fields (that apply to all lots) in full
- Compress lot-specific sections to just lot names
- Implement tooltip/hover to see full path
- Consider breadcrumb patterns:
  ```
  Home > Project Info > [Lot 1] > [Lot 2] > [Current Lot: Step X]
  ```
  Instead of:
  ```
  Home > Project Info > Lot 1 > Order Type > Technical Specs > ... (overflow)
  ```
- Add "..." ellipsis with dropdown for hidden items
- Mobile-responsive breadcrumb compression

**Technical Requirements:**
```python
def compress_breadcrumbs(full_path, current_lot):
    """
    Intelligently compress breadcrumb trail:
    - Keep general sections expanded
    - Compress lot-specific sections
    - Always show current position clearly
    """
```

### Story 3: Optimized Display for Long Content Sections
**Description**: Special handling for space-consuming sections
- **Exclusion Criteria Section**:
  - Show summary count instead of all items
  - "Razlogi za izključitev (5 selected)" instead of listing all
  - Expandable detail view on click
  - Consider modal or slide-out panel for details
- **Multiple Cofinancers**:
  - Show count with expand option
  - "Sofinancerji (3)" with dropdown to see names
- **Selection Criteria**:
  - Group related items
  - Show only selected count initially
- Implement consistent collapse/expand patterns

**Visual Mockup:**
```
📊 Sklop 1: Dobava opreme (75% complete)
  ├─ ✅ Vrsta naročila
  ├─ ✅ Tehnične specifikacije  
  ├─ 🔄 Rok izvedbe (50%)
  └─ ⭕ Cena

📊 Sklop 2: Storitve (40% complete)
  ├─ ✅ Vrsta naročila
  ├─ ⭕ Tehnične specifikacije
  └─ ⭕ Rok izvedbe
```

## Implementation Approach
- [x] Progressive enhancement - don't break existing navigation
- [x] Use existing validation system for progress calculation
- [x] Maintain session state structure
- [x] Mobile-first responsive design

## Implementation Benefits
- **Better User Orientation**: Always know where you are and how much is left
- **Faster Navigation**: Jump directly to relevant sections
- **Cleaner Interface**: Optimized space usage for complex forms
- **Progress Visibility**: Clear indication of completion status
- **Reduced Cognitive Load**: Hierarchical display reduces mental mapping

## Definition of Done
- [ ] Progress percentages display correctly for all lots
- [ ] Visual hierarchy clearly shows lot/step relationships
- [ ] Breadcrumbs stay readable even with 5+ lots
- [ ] Jump navigation respects validation rules
- [ ] Long sections have compressed views
- [ ] Mobile responsive design works
- [ ] No regression in existing navigation

## Technical Details

### Progress Calculation Algorithm
```python
# For each lot:
1. Identify all required fields in lot context
2. Check validation status for each field
3. Calculate: (validated_fields / total_required) * 100
4. Cache result in session state
5. Update on field change events
```

### Navigation State Structure
```python
navigation_state = {
    'current_lot': int,
    'current_step': str,
    'lot_progress': {
        'lot_0': 75,  # percentage
        'lot_1': 40,
        # ...
    },
    'completed_steps': set(),  # Steps user can jump to
    'expanded_sections': set()  # For accordion UI
}
```

### Visual Hierarchy Rules
- General sections: No indentation
- Lot headers: Bold with progress indicator
- Steps within lots: 20px left indent
- Current position: Highlighted background
- Completed: ✅ icon
- In progress: 🔄 icon  
- Not started: ⭕ icon

## Dependencies
- Existing sidebar navigation component
- ValidationManager for field requirements
- Session state for form data
- Streamlit's layout capabilities

## Estimated Effort
- Story 1: 8-10 hours (sidebar enhancement)
- Story 2: 4-6 hours (breadcrumb optimization)
- Story 3: 6-8 hours (content compression)
- **Total**: 18-24 hours (2.5-3 days)

## Future Enhancements
- Keyboard shortcuts for navigation
- Progress animation on completion
- Export progress report
- Time estimates for remaining work
- Collaborative progress indicators (multi-user)

## Notes
- This epic addresses navigation UX issues identified during multi-lot form testing
- Consider A/B testing different progress visualization methods
- May need performance optimization for forms with 10+ lots
- Accessibility considerations for screen readers important