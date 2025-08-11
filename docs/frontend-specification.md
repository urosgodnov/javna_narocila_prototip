# Front-End Specification Document
## Public Procurement Document Generation System

### Project Overview

**Project Name**: Public Procurement Document Generation System (Javna Naročila Prototip)  
**Technology Stack**: Streamlit-based web application  
**Primary Users**: Government procurement officers, administrative staff, compliance reviewers  
**Purpose**: Generate standardized public procurement documents through guided form interfaces

---

## 1. Design System

### 1.1 Typography

The application uses a carefully selected typography hierarchy to ensure readability and professional appearance:

**Primary Font Family**: Inter (Google Fonts)
- **H1 (Main Titles)**: 2.5rem, 700 weight, used for page titles and major sections
- **H2 (Section Headers)**: 2rem, 600 weight, used for form step titles and major subsections
- **H3 (Subsections)**: 1.5rem, 600 weight, used for form group labels and minor sections
- **Body Text**: 1rem, 400 weight, 1.6 line-height for optimal readability
- **Helper Text**: 0.875rem, used for field descriptions, validation messages, and secondary information

### 1.2 Color Palette

**Primary Colors**:
- `#1e3a8a` - Dark blue (primary dark)
- `#1d4ed8` - Medium blue (primary medium) 
- `#3b82f6` - Base blue (primary base)
- `#1f4e79` - Header gradient start
- `#2e6da4` - Header gradient end

**Neutral Colors**:
- `#111827` - Dark text (primary text color)
- `#6b7280` - Muted text (secondary text, labels)
- `#f3f4f6` - Light backgrounds
- `#f8f9fa` - Card backgrounds
- `#e1e5e9` - Border colors

**Semantic Colors**:
- `#059669` - Success green (confirmation messages)
- `#d97706` - Warning orange (attention messages)
- `#dc2626` - Error red (validation errors)
- `#d4edda` - Success background
- `#155724` - Success text

### 1.3 Component Design Principles

**Form Components**:
- 2px borders with smooth transitions
- 0.5rem (8px) border-radius for modern rounded appearance
- Enhanced focus states with colored borders and subtle shadows
- Consistent spacing and padding throughout

**Interactive Elements**:
- Gradient buttons with hover animations
- Smooth color transitions (0.3s ease)
- Visual feedback for user interactions
- Accessibility-compliant contrast ratios

---

## 2. Layout Architecture

### 2.1 Grid System

The application uses Streamlit's column system with a primary 3:1 ratio layout:

```
┌─────────────────────────┬─────────┐
│                         │         │
│    Main Form Area       │ Sidebar │
│    (3 units wide)       │(1 unit) │
│                         │         │
└─────────────────────────┴─────────┘
```

**Main Content Area**:
- Form header with progress indicators
- Step-by-step form sections
- Navigation controls
- Breadcrumb navigation

**Sidebar**:
- Draft management
- Progress overview
- Administrative controls

### 2.2 Navigation Structure

**Multi-Step Form Flow**:
1. Client Information
2. Project Information  
3. Legal Basis
4. Submission Procedure
5. Lots Configuration
6. Per-Lot Specifications (dynamic based on lot count)
7. Contract Information
8. Additional Information

**Dynamic Lot Handling**:
- General mode: Single set of specifications
- Lots mode: Repeated specification steps per lot
- Context-aware step indicators

---

## 3. Component Specifications

### 3.1 Form Header Component

**Visual Design**:
```css
.form-header {
    background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

**Content Elements**:
- Application title (H1)
- Current lot context (H3 with emoji indicators)
- Step indicator with current/total steps
- Progress percentage display

### 3.2 Progress Indicators

**Linear Progress Bar**:
- Custom gradient styling matching primary colors
- Text overlay showing current step/total steps
- Smooth animation transitions

**Step Breadcrumbs**:
- Horizontal layout with flexible wrapping
- Three states: completed (green), current (blue), pending (gray)
- Clickable navigation (future enhancement)

```css
.breadcrumb-item {
    padding: 0.5rem 1rem;
    margin: 0.25rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.3s ease;
}
```

### 3.3 Form Fields

**Input Field Styling**:
```css
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    border-radius: 8px !important;
    border: 2px solid #e1e5e9 !important;
    transition: border-color 0.3s ease !important;
}
```

**Focus States**:
- Blue border color (`#1f4e79`)
- Subtle box shadow (`0 0 0 0.2rem rgba(31, 78, 121, 0.25)`)
- Smooth transition effects

**Field Types**:
- Text inputs with placeholder text
- Textareas for long-form content
- Select dropdowns with placeholder options
- Number inputs with validation
- Date pickers with DD.MM.YYYY format
- File uploaders with type restrictions
- Multi-select for array fields
- Dynamic array management with add/remove buttons

### 3.4 Dynamic Array Components

**Array Item Management**:
- Bordered containers for each array item
- Header row with item title and remove button
- Add button with contextual text (e.g., "➕ Dodaj naročnika")
- Smooth animations for add/remove operations

**Validation and Feedback**:
- Real-time validation for required fields
- Contextual error messages in Slovenian
- Success confirmations for completed actions
- Warning messages for edge cases

### 3.5 Navigation Controls

**Button Styling**:
- Primary buttons: Blue gradient background
- Secondary buttons: Gray background with blue text  
- Full-width buttons in navigation areas
- Icon integration (arrows, emojis for context)

**Navigation Logic**:
- Back button: Enabled when not on first step
- Next button: Enabled with validation check
- Submit button: Final step with form data display

---

## 4. Streamlit Integration

### 4.1 Custom CSS Implementation

The application enhances default Streamlit styling through embedded CSS:

```python
def add_custom_css():
    st.markdown("""
    <style>
    /* Enhanced form fields */
    .stTextInput > div > div > input:focus {
        border-color: #1f4e79 !important;
        box-shadow: 0 0 0 0.2rem rgba(31, 78, 121, 0.25) !important;
    }
    
    /* Progress bar customization */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
    }
    </style>
    """, unsafe_allow_html=True)
```

### 4.2 State Management

**Session State Structure**:
- Form field values with scoped keys
- Current step tracking
- Lot-specific data organization  
- Draft management state
- Validation status tracking

**Lot-Scoped Keys**:
- General mode: `field_name`
- Lot mode: `lot_0_field_name`, `lot_1_field_name`, etc.
- Global fields: Always use original keys (not lot-scoped)

### 4.3 Responsive Behavior

**Column Layouts**:
- Main content adapts to screen size
- Sidebar collapses on mobile
- Form fields stack vertically on narrow screens
- Button layouts adjust for touch interfaces

**Performance Optimizations**:
- Conditional rendering based on `render_if` conditions
- Efficient state updates with `st.rerun()`
- Minimal re-rendering through proper key management

---

## 5. User Experience Features

### 5.1 Localization

**Language Support**:
- Full Slovenian language interface
- Contextual help text and tooltips
- Proper grammar handling for dynamic content
- Cultural considerations for date formats and terminology

### 5.2 Accessibility

**WCAG Compliance Features**:
- Sufficient color contrast ratios
- Keyboard navigation support
- Screen reader compatible labels
- Focus indicators for all interactive elements
- Proper heading hierarchy

### 5.3 Error Handling and Validation

**Real-time Validation**:
- Required field indicators (*)
- Format validation for numbers and dates
- Enum value filtering for dependent fields
- Custom validation messages in Slovenian

**User Feedback**:
- Success messages for completed actions
- Warning messages for potential issues
- Error messages with clear resolution steps
- Progress saving confirmations

### 5.4 Advanced Interactions

**Smart Form Behavior**:
- Auto-completion for procedure types
- Dynamic field filtering (e.g., mixed order components)
- Context-aware help text
- Conditional field display

**Draft Management**:
- Automatic state persistence
- Draft loading with timestamp display
- Clear visual feedback for save operations
- Data integrity preservation

---

## 6. Technical Implementation

### 6.1 Component Architecture

**Modular Design**:
- `form_renderer.py`: Core form rendering logic
- `admin_panel.py`: Administrative interface
- `lot_utils.py`: Lot-specific functionality
- `localization.py`: Text and translation management

**Separation of Concerns**:
- Presentation layer: Streamlit components
- Business logic: Form validation and state management
- Data layer: Session state and database operations

### 6.2 Styling Pipeline

**CSS Integration**:
1. Define styles in Python functions
2. Inject via `st.markdown()` with `unsafe_allow_html=True`
3. Target Streamlit-generated classes
4. Override default styling with `!important` declarations

**Style Organization**:
- Global styles applied in main application
- Component-specific styles in relevant modules
- Consistent naming conventions for CSS classes
- Maintainable style definitions

### 6.3 Performance Considerations

**Optimization Strategies**:
- Minimal DOM manipulation
- Efficient state updates
- Conditional component rendering
- Streamlined CSS selectors

**Loading Performance**:
- Progressive form loading
- Efficient schema parsing
- Optimized asset delivery
- Minimal external dependencies

---

## 7. Browser Compatibility

### 7.1 Supported Browsers

**Primary Support**:
- Chrome 90+ 
- Firefox 88+
- Safari 14+
- Edge 90+

**Mobile Support**:
- Mobile Chrome (Android)
- Mobile Safari (iOS)
- Responsive design for tablet and phone screens

### 7.2 Graceful Degradation

**Fallback Strategies**:
- Basic styling for unsupported browsers
- Essential functionality preservation
- Progressive enhancement approach
- Clear error messaging for compatibility issues

---

## 8. Maintenance and Updates

### 8.1 Style Guide Adherence

**Design Consistency**:
- Standardized color usage across components
- Consistent spacing and typography
- Uniform interaction patterns
- Maintainable CSS architecture

### 8.2 Future Enhancement Considerations

**Scalability Planning**:
- Modular CSS organization for easy updates
- Theme switching capability preparation
- Internationalization framework readiness
- Component library potential

**Performance Monitoring**:
- Style rendering performance tracking
- User interaction analytics integration
- Accessibility auditing procedures
- Cross-browser testing protocols

---

## 9. Quality Assurance

### 9.1 Testing Requirements

**Visual Testing**:
- Cross-browser rendering validation
- Responsive design verification
- Color contrast compliance checking
- Typography rendering consistency

**Functional Testing**:
- Form interaction workflows
- State management validation  
- Error handling verification
- Accessibility compliance testing

### 9.2 Code Standards

**CSS Best Practices**:
- Consistent naming conventions
- Efficient selector usage
- Maintainable code organization
- Performance-optimized styles

**Documentation Requirements**:
- Component usage examples
- Style guide maintenance
- Technical implementation notes
- User experience guidelines

---

*This document serves as the comprehensive front-end specification for the Public Procurement Document Generation System, ensuring consistent user experience and maintainable code architecture.*