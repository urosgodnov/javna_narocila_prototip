# Story 31.3: Build Visual Progress Indicator

## User Story
As a user working with the multi-step form,
I want to see a visual representation of my progress and which steps I can access,
So that I understand where I am in the process and can navigate efficiently.

## Story Context

### Existing System Integration
- **Integrates with:** Form header area in `app.py:render_main_form()`
- **Technology:** Streamlit columns, markdown, custom CSS
- **Follows pattern:** Current step indicator display pattern
- **Touch points:**
  - Step configuration from `config_refactored.py`
  - Completion tracking from Story 31.2
  - Navigation functions from Story 31.2
  - Lot progress info from `utils/lot_utils.py`

## Acceptance Criteria

### Functional Requirements
1. Display all form steps horizontally with visual status indicators
2. Show completed steps with checkmark (✅) in green
3. Highlight current step with blue indicator (🔵)
4. Display locked steps with lock icon (🔒) in gray
5. Completed steps are clickable for navigation
6. Current position clearly visible at all times

### Lot-Specific Requirements
7. For lot-based forms, show branching structure
8. Display which lot is currently active
9. Show completion status per lot
10. Allow navigation through visual indicators

### Integration Requirements
11. Works with existing step configuration
12. Uses completion tracking from Story 31.2
13. Triggers navigation functions when clicked
14. Updates dynamically as user progresses

### Quality Requirements
15. Responsive design that works on different screen sizes
16. Clear visual hierarchy and contrast
17. Smooth transitions when navigating
18. Accessible with proper ARIA labels

## Technical Implementation Details

### Basic Progress Indicator
```python
def render_progress_indicator():
    """Render horizontal progress indicator with navigation."""
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    
    # Create progress container
    st.markdown("### 📊 Napredek obrazca")
    
    # Calculate column widths based on number of steps
    num_steps = len(steps)
    cols = st.columns(num_steps)
    
    for idx, (step, col) in enumerate(zip(steps, cols)):
        with col:
            # Determine step status and styling
            if idx == current:
                status_icon = "🔵"
                status_text = "Trenutni"
                button_type = "primary"
                is_clickable = False
            elif completed.get(idx, False):
                status_icon = "✅"
                status_text = "Dokončan"
                button_type = "secondary"
                is_clickable = True
            elif idx < current:
                # Step was skipped or not validated
                status_icon = "⚠️"
                status_text = "Preskočen"
                button_type = "secondary"
                is_clickable = True
            else:
                status_icon = "🔒"
                status_text = "Zaklenjen"
                button_type = None  # Will render as disabled
                is_clickable = False
            
            # Render step indicator
            if is_clickable:
                if st.button(
                    f"{status_icon}\n{step['title'][:15]}...",
                    key=f"progress_{idx}",
                    use_container_width=True,
                    type=button_type,
                    help=f"{status_text}: {step['title']}"
                ):
                    navigate_to_step(idx)
            else:
                # Render disabled step
                st.markdown(
                    f"""
                    <div style="
                        text-align: center;
                        padding: 8px;
                        border-radius: 5px;
                        background-color: {'#f0f0f0' if idx != current else '#e3f2fd'};
                        color: {'#999' if idx > current else '#333'};
                        min-height: 60px;
                    ">
                        <div style="font-size: 20px;">{status_icon}</div>
                        <div style="font-size: 11px; margin-top: 4px;">
                            {step['title'][:15]}{'...' if len(step['title']) > 15 else ''}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Add progress line between steps
            if idx < num_steps - 1:
                progress = idx < current or completed.get(idx, False)
                st.markdown(
                    f"""
                    <div style="
                        position: relative;
                        top: -40px;
                        left: 50%;
                        width: 100%;
                        height: 2px;
                        background-color: {'#4CAF50' if progress else '#e0e0e0'};
                    "></div>
                    """,
                    unsafe_allow_html=True
                )
```

### Enhanced Progress with Tooltips
```python
def render_enhanced_progress():
    """Enhanced progress indicator with better visuals."""
    import json
    
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    
    # Custom CSS for progress indicator
    st.markdown("""
        <style>
        .progress-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            position: relative;
        }
        .progress-step {
            flex: 1;
            text-align: center;
            position: relative;
        }
        .progress-step-button {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s;
            margin: 0 auto;
        }
        .progress-step-button.completed {
            background: #4CAF50;
            border-color: #4CAF50;
            color: white;
        }
        .progress-step-button.current {
            background: #2196F3;
            border-color: #2196F3;
            color: white;
            box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.3);
        }
        .progress-step-button.locked {
            background: #f5f5f5;
            border-color: #e0e0e0;
            color: #999;
            cursor: not-allowed;
        }
        .progress-step-button:hover:not(.locked):not(.current) {
            transform: scale(1.1);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .progress-line {
            position: absolute;
            top: 50%;
            left: 50%;
            width: calc(100% - 40px);
            height: 2px;
            background: #e0e0e0;
            z-index: -1;
        }
        .progress-line.completed {
            background: #4CAF50;
        }
        .step-title {
            margin-top: 8px;
            font-size: 12px;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Build progress HTML
    progress_html = '<div class="progress-container">'
    
    for idx, step in enumerate(steps):
        # Determine status
        if idx == current:
            status_class = "current"
            icon = "•"
        elif completed.get(idx, False):
            status_class = "completed"
            icon = "✓"
        elif idx < current:
            status_class = "warning"
            icon = "!"
        else:
            status_class = "locked"
            icon = "🔒"
        
        # Add step HTML
        clickable = idx < current or completed.get(idx, False)
        progress_html += f'''
            <div class="progress-step">
                <div class="progress-step-button {status_class}"
                     {'onclick="handleStepClick(' + str(idx) + ')"' if clickable else ''}
                     title="{step['title']}">
                    {idx + 1}
                </div>
                <div class="step-title">{step['title'][:20]}{'...' if len(step['title']) > 20 else ''}</div>
                {'<div class="progress-line ' + ('completed' if idx < current or completed.get(idx, False) else '') + '"></div>' if idx < len(steps) - 1 else ''}
            </div>
        '''
    
    progress_html += '</div>'
    
    # Add JavaScript for navigation
    progress_html += '''
        <script>
        function handleStepClick(stepIndex) {
            // This would trigger Streamlit navigation
            // In practice, we'll use Streamlit buttons
        }
        </script>
    '''
    
    st.markdown(progress_html, unsafe_allow_html=True)
```

### Lot-Based Progress Tree
```python
def render_lot_progress_tree():
    """Render branching progress for lot-based forms."""
    if st.session_state.get('lot_mode') != 'multiple':
        return render_progress_indicator()
    
    st.markdown("### 📊 Napredek po sklopih")
    
    # Get configuration
    main_steps = get_main_steps()  # Steps before lot branching
    lot_steps = get_lot_specific_steps()  # Steps within each lot
    lot_names = st.session_state.get('lot_names', [])
    current_step = st.session_state.current_step
    current_lot = st.session_state.get('current_lot')
    
    # Render main trunk
    st.markdown("#### 📋 Splošni koraki")
    with st.container():
        render_progress_indicator_for_steps(main_steps, "main")
    
    # Render lot branches
    if lot_names:
        st.markdown("#### 📦 Koraki po sklopih")
        
        # Create tabs for each lot
        tabs = st.tabs([f"Sklop: {name}" for name in lot_names])
        
        for idx, (tab, lot_name) in enumerate(zip(tabs, lot_names)):
            with tab:
                lot_id = f'lot_{idx}'
                lot_completed = st.session_state.get('lot_completed_steps', {}).get(lot_id, {})
                
                # Show lot-specific progress
                lot_cols = st.columns(len(lot_steps))
                for step_idx, (step, col) in enumerate(zip(lot_steps, lot_cols)):
                    with col:
                        # Determine status for this lot's step
                        is_current = (current_lot == lot_id and current_step == step_idx)
                        is_completed = lot_completed.get(step_idx, False)
                        is_accessible = is_step_accessible(step_idx, lot_id)
                        
                        if is_current:
                            status = "🔵 Trenutni"
                            color = "blue"
                        elif is_completed:
                            status = "✅ Dokončan"
                            color = "green"
                        elif is_accessible:
                            status = "⭕ Dostopen"
                            color = "orange"
                        else:
                            status = "🔒 Zaklenjen"
                            color = "gray"
                        
                        # Render step button
                        if is_accessible and not is_current:
                            if st.button(
                                f"{status}\n{step['title']}",
                                key=f"lot_{idx}_step_{step_idx}",
                                use_container_width=True
                            ):
                                navigate_to_step(step_idx, lot_id)
                        else:
                            st.info(f"{status}\n{step['title']}")
```

### Compact Mobile-Friendly Version
```python
def render_compact_progress():
    """Compact progress indicator for mobile/small screens."""
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    total = len(steps)
    
    # Progress metrics
    completed_count = sum(1 for v in completed.values() if v)
    progress_percent = int((current / total) * 100)
    
    # Render compact view
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Korak {current + 1} od {total}**: {steps[current]['title']}")
        st.progress(progress_percent / 100)
        st.caption(f"Dokončani koraki: {completed_count}/{total}")
    
    with col2:
        # Quick jump menu
        accessible = [i for i in range(total) if i <= current or completed.get(i, False)]
        if len(accessible) > 1:
            selected = st.selectbox(
                "Skoči na:",
                options=accessible,
                format_func=lambda x: f"{x+1}. {steps[x]['title'][:20]}",
                index=accessible.index(current),
                key="compact_nav"
            )
            if selected != current:
                navigate_to_step(selected)
```

## Risk and Compatibility

### Risk Assessment
- **Primary Risk:** Complex UI overwhelming users
- **Mitigation:** Provide compact view option, clear visual hierarchy
- **Rollback:** Can disable visual indicator, keep text-based navigation

### Compatibility Verification
- ✅ No changes to underlying navigation logic
- ✅ Works with existing step configuration
- ✅ Responsive design for different screens
- ✅ Graceful degradation if JavaScript disabled

## Definition of Done
- [ ] Basic horizontal progress indicator implemented
- [ ] Visual states for all step conditions (current/completed/locked)
- [ ] Click navigation for accessible steps
- [ ] Progress lines between steps
- [ ] Lot-based branching view (if applicable)
- [ ] Compact mobile view option
- [ ] Tooltips showing full step names
- [ ] Dynamic updates as user progresses
- [ ] Integration with navigation from Story 31.2
- [ ] Tested on different screen sizes
- [ ] No regression in existing UI

## Estimated Effort
- **Development:** 3-4 hours
- **Testing:** 1 hour
- **Total:** 4-5 hours

## Dependencies
- Story 31.2 must be completed (provides navigation functions and tracking)

## Notes
- Consider adding animations for step transitions in future
- Progress can be enhanced with percentage complete
- Consider saving progress visualization preference per user