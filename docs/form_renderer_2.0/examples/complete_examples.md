# Form Renderer 2.0 - Complete Examples

## Example 1: Simple Contact Form

### Scenario
Basic contact form with name, email, and message fields. Demonstrates the simplest use case.

```python
import streamlit as st
from ui.controllers.form_controller import FormController

def render_contact_form():
    """Simple contact form with automatic General lot."""
    
    # Define schema
    schema = {
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
                'title': 'Your Name',
                'description': 'Please enter your full name',
                'minLength': 2,
                'maxLength': 100
            },
            'email': {
                'type': 'string',
                'format': 'email',
                'title': 'Email Address',
                'description': 'We\'ll never share your email'
            },
            'subject': {
                'type': 'string',
                'title': 'Subject',
                'enum': ['General Inquiry', 'Support', 'Feedback', 'Other']
            },
            'message': {
                'type': 'string',
                'title': 'Message',
                'description': 'Your message here',
                'minLength': 10,
                'maxLength': 1000
            }
        },
        'required': ['name', 'email', 'message']
    }
    
    # Create and render form
    controller = FormController(schema)
    controller.render_form()
    
    # Handle submission
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button('Submit', type='primary'):
            if controller.validate_form():
                data = controller.get_form_data()
                st.success('✅ Message sent successfully!')
                
                # Display data (for demo)
                with st.expander('Submitted Data'):
                    st.json(data)
                
                # In production, you'd send email here
                # send_email(data['lots.0.email'], data['lots.0.message'])
            else:
                st.error('Please fill in all required fields')
    
    with col2:
        if st.button('Clear'):
            controller.clear_form()
            st.rerun()

# Usage
render_contact_form()
```

**Key Points:**
- Form automatically gets a "General" lot
- All data stored as `lots.0.name`, `lots.0.email`, etc.
- No lot management needed for simple forms

---

## Example 2: Multi-Lot Procurement Form

### Scenario
Procurement form where each lot represents a different item category with specific requirements.

```python
import streamlit as st
from ui.controllers.form_controller import FormController

def render_procurement_form():
    """Complex procurement form with multiple lots."""
    
    # Define schema for lot items
    lot_schema = {
        'type': 'object',
        'properties': {
            'category': {
                'type': 'string',
                'title': 'Item Category',
                'enum': ['IT Equipment', 'Office Supplies', 'Services', 'Construction']
            },
            'description': {
                'type': 'string',
                'title': 'Description',
                'description': 'Detailed description of requirements'
            },
            'quantity': {
                'type': 'number',
                'title': 'Quantity',
                'minimum': 1
            },
            'estimatedValue': {
                'type': 'number',
                'title': 'Estimated Value',
                'format': 'financial',
                'description': 'Budget estimate in EUR'
            },
            'technicalSpecs': {
                'type': 'object',
                'title': 'Technical Specifications',
                'properties': {
                    'mandatory': {
                        'type': 'array',
                        'title': 'Mandatory Requirements',
                        'items': {'type': 'string'}
                    },
                    'optional': {
                        'type': 'array',
                        'title': 'Optional Requirements',
                        'items': {'type': 'string'}
                    }
                }
            },
            'deliveryDate': {
                'type': 'string',
                'format': 'date',
                'title': 'Required Delivery Date'
            }
        },
        'required': ['category', 'description', 'quantity', 'estimatedValue'],
        'allow_multiple_lots': True  # Enable lot management
    }
    
    # Create controller
    controller = FormController(lot_schema)
    
    # Render lot navigation
    st.markdown("### 📦 Procurement Lots")
    controller.lot_manager.render_lot_navigation(
        style='tabs',
        allow_add=True,
        allow_remove=True,
        max_lots=10
    )
    
    st.divider()
    
    # Render current lot form
    controller.render_form()
    
    # Lot operations
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button('📋 Copy to New Lot'):
            current_index = controller.context.lot_index
            new_index = controller.context.add_lot(f'Copy of Lot {current_index + 1}')
            controller.context.copy_lot_data(current_index, new_index)
            st.success(f'Copied to Lot {new_index + 1}')
            st.rerun()
    
    with col2:
        if st.button('💰 Calculate Total'):
            total = 0
            for i in range(controller.context.get_lot_count()):
                controller.context.switch_to_lot(i)
                value = controller.context.get_field_value('estimatedValue')
                if value:
                    total += value
            st.info(f'Total Estimated Value: €{total:,.2f}')
    
    with col3:
        if st.button('✅ Validate All'):
            if controller.validate_form():
                st.success('All lots valid!')
            else:
                st.error('Some lots have validation errors')
                for field, errors in controller.context.validation_errors.items():
                    for error in errors:
                        st.error(f'• {error}')

# Usage
st.title('Procurement Request Form')
render_procurement_form()
```

**Key Points:**
- Multiple lots for different procurement categories
- Lot navigation with tabs
- Cross-lot calculations (total value)
- Per-lot validation

---

## Example 3: Dynamic Form with Conditional Fields

### Scenario
Form where fields appear/disappear based on user selections.

```python
import streamlit as st
from ui.controllers.form_controller import FormController

def render_dynamic_form():
    """Form with conditional field rendering."""
    
    schema = {
        'type': 'object',
        'properties': {
            'projectType': {
                'type': 'string',
                'title': 'Project Type',
                'enum': ['Software', 'Hardware', 'Consulting', 'Mixed'],
                'description': 'Select the type of project'
            },
            
            # Software-specific fields
            'programmingLanguage': {
                'type': 'string',
                'title': 'Programming Language',
                'enum': ['Python', 'JavaScript', 'Java', 'C#', 'Other'],
                'render_if': {'field': 'projectType', 'value': 'Software'}
            },
            'framework': {
                'type': 'string',
                'title': 'Framework',
                'render_if': {'field': 'projectType', 'value': 'Software'}
            },
            
            # Hardware-specific fields
            'deviceType': {
                'type': 'string',
                'title': 'Device Type',
                'enum': ['Server', 'Network', 'Storage', 'Endpoint'],
                'render_if': {'field': 'projectType', 'value': 'Hardware'}
            },
            'quantity': {
                'type': 'number',
                'title': 'Quantity',
                'minimum': 1,
                'render_if': {'field': 'projectType', 'value': 'Hardware'}
            },
            
            # Consulting-specific fields
            'consultingArea': {
                'type': 'string',
                'title': 'Consulting Area',
                'enum': ['Strategy', 'Implementation', 'Training', 'Audit'],
                'render_if': {'field': 'projectType', 'value': 'Consulting'}
            },
            'duration': {
                'type': 'number',
                'title': 'Duration (days)',
                'minimum': 1,
                'render_if': {'field': 'projectType', 'value': 'Consulting'}
            },
            
            # Common fields
            'budget': {
                'type': 'number',
                'format': 'financial',
                'title': 'Budget',
                'description': 'Project budget in EUR'
            },
            'startDate': {
                'type': 'string',
                'format': 'date',
                'title': 'Start Date'
            },
            'requiresApproval': {
                'type': 'boolean',
                'title': 'Requires Management Approval'
            },
            
            # Conditional on requiresApproval
            'approverEmail': {
                'type': 'string',
                'format': 'email',
                'title': 'Approver Email',
                'render_if': {'field': 'requiresApproval', 'value': True}
            },
            'justification': {
                'type': 'string',
                'title': 'Justification',
                'description': 'Why is approval needed?',
                'render_if': {'field': 'requiresApproval', 'value': True}
            }
        },
        'required': ['projectType', 'budget', 'startDate']
    }
    
    st.title('Dynamic Project Request Form')
    
    # Create controller
    controller = FormController(schema)
    
    # Render form (conditional fields handled automatically)
    controller.render_form()
    
    # Show current state
    with st.sidebar:
        st.markdown("### Current Form State")
        project_type = controller.context.get_field_value('projectType')
        if project_type:
            st.info(f"Project Type: {project_type}")
            
            # Show which fields are visible
            st.markdown("**Visible Fields:**")
            if project_type == 'Software':
                st.text("• Programming Language")
                st.text("• Framework")
            elif project_type == 'Hardware':
                st.text("• Device Type")
                st.text("• Quantity")
            elif project_type == 'Consulting':
                st.text("• Consulting Area")
                st.text("• Duration")
        
        requires_approval = controller.context.get_field_value('requiresApproval')
        if requires_approval:
            st.warning("Approval fields shown")
    
    # Submit
    if st.button('Submit Project Request'):
        if controller.validate_form():
            data = controller.get_form_data()
            st.success('Project request submitted!')
            
            # Show only populated fields
            st.markdown("### Submitted Data")
            for key, value in data.items():
                if key.startswith('lots.0.') and value:
                    field_name = key.replace('lots.0.', '')
                    st.write(f"**{field_name}:** {value}")

# Usage
render_dynamic_form()
```

**Key Points:**
- Fields conditionally rendered based on selections
- `render_if` conditions in schema
- Automatic handling by SectionRenderer
- Sidebar shows active fields

---

## Example 4: Nested Data Structure Form

### Scenario
Complex form with deeply nested objects and arrays.

```python
import streamlit as st
from ui.controllers.form_controller import FormController

def render_company_form():
    """Complex company registration form with nested structures."""
    
    schema = {
        'type': 'object',
        'properties': {
            'company': {
                'type': 'object',
                'title': 'Company Information',
                'use_container': True,
                'properties': {
                    'name': {'type': 'string', 'title': 'Company Name'},
                    'registration': {'type': 'string', 'title': 'Registration Number'},
                    'headquarters': {
                        'type': 'object',
                        'title': 'Headquarters',
                        'properties': {
                            'street': {'type': 'string', 'title': 'Street'},
                            'city': {'type': 'string', 'title': 'City'},
                            'country': {'type': 'string', 'title': 'Country'},
                            'postalCode': {'type': 'string', 'title': 'Postal Code'}
                        }
                    }
                }
            },
            'departments': {
                'type': 'array',
                'title': 'Departments',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'title': 'Department Name'},
                        'manager': {'type': 'string', 'title': 'Manager'},
                        'employees': {
                            'type': 'array',
                            'title': 'Employees',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'firstName': {'type': 'string', 'title': 'First Name'},
                                    'lastName': {'type': 'string', 'title': 'Last Name'},
                                    'position': {'type': 'string', 'title': 'Position'},
                                    'email': {'type': 'string', 'format': 'email', 'title': 'Email'}
                                }
                            }
                        }
                    }
                }
            },
            'financials': {
                'type': 'object',
                'title': 'Financial Information',
                'use_expander': True,
                'properties': {
                    'revenue': {'type': 'number', 'format': 'financial', 'title': 'Annual Revenue'},
                    'employees': {'type': 'number', 'title': 'Total Employees'},
                    'founded': {'type': 'number', 'title': 'Year Founded'}
                }
            }
        }
    }
    
    st.title('Company Registration Form')
    
    # Create controller
    controller = FormController(schema)
    
    # Render nested form
    controller.render_form()
    
    # Operations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button('📊 Show Structure'):
            data = controller.get_form_data()
            st.json(data)
    
    with col2:
        if st.button('👥 Count Employees'):
            total = 0
            departments = controller.context.get_field_value('departments')
            if departments:
                for dept in departments:
                    if 'employees' in dept:
                        total += len(dept['employees'])
            st.info(f'Total Employees in Departments: {total}')
    
    with col3:
        if st.button('✅ Validate'):
            if controller.validate_form():
                st.success('Form is valid!')

# Usage
render_company_form()
```

**Key Points:**
- Deeply nested objects (company → headquarters → address)
- Arrays of objects (departments)
- Arrays within arrays (departments → employees)
- Visual containers and expanders

---

## Example 5: Form with Custom Validation

### Scenario
Form with custom validation rules beyond basic schema validation.

```python
import streamlit as st
from ui.controllers.form_controller import FormController
import re

def render_registration_form():
    """User registration with custom validation."""
    
    schema = {
        'type': 'object',
        'properties': {
            'username': {
                'type': 'string',
                'title': 'Username',
                'description': 'Alphanumeric, 3-20 characters',
                'minLength': 3,
                'maxLength': 20
            },
            'email': {
                'type': 'string',
                'format': 'email',
                'title': 'Email Address'
            },
            'password': {
                'type': 'string',
                'title': 'Password',
                'description': 'At least 8 characters, 1 uppercase, 1 number',
                'minLength': 8
            },
            'confirmPassword': {
                'type': 'string',
                'title': 'Confirm Password'
            },
            'age': {
                'type': 'number',
                'title': 'Age',
                'minimum': 18,
                'maximum': 120
            },
            'acceptTerms': {
                'type': 'boolean',
                'title': 'I accept the terms and conditions'
            }
        },
        'required': ['username', 'email', 'password', 'confirmPassword', 'age', 'acceptTerms']
    }
    
    st.title('User Registration')
    
    # Create controller
    controller = FormController(schema)
    
    # Custom validation function
    def custom_validate():
        """Perform custom validation beyond schema."""
        errors = []
        
        # Get values
        username = controller.context.get_field_value('username')
        password = controller.context.get_field_value('password')
        confirm = controller.context.get_field_value('confirmPassword')
        accept = controller.context.get_field_value('acceptTerms')
        
        # Username validation
        if username and not re.match(r'^[a-zA-Z0-9]+$', username):
            errors.append('Username must be alphanumeric only')
        
        # Password strength
        if password:
            if not re.search(r'[A-Z]', password):
                errors.append('Password must contain at least one uppercase letter')
            if not re.search(r'\d', password):
                errors.append('Password must contain at least one number')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append('Password must contain at least one special character')
        
        # Password match
        if password and confirm and password != confirm:
            errors.append('Passwords do not match')
        
        # Terms acceptance
        if not accept:
            errors.append('You must accept the terms and conditions')
        
        return errors
    
    # Render form
    controller.render_form()
    
    # Real-time validation feedback
    if controller.context.get_field_value('password'):
        password = controller.context.get_field_value('password')
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if len(password) >= 8:
                st.success('✅ 8+ chars')
            else:
                st.error('❌ 8+ chars')
        
        with col2:
            if re.search(r'[A-Z]', password):
                st.success('✅ Uppercase')
            else:
                st.error('❌ Uppercase')
        
        with col3:
            if re.search(r'\d', password):
                st.success('✅ Number')
            else:
                st.error('❌ Number')
        
        with col4:
            if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                st.success('✅ Special')
            else:
                st.error('❌ Special')
    
    # Submit with custom validation
    if st.button('Register', type='primary'):
        # Schema validation
        if controller.validate_form():
            # Custom validation
            custom_errors = custom_validate()
            
            if not custom_errors:
                st.success('✅ Registration successful!')
                data = controller.get_form_data()
                
                # In production, save to database
                # save_user(data)
                
                st.balloons()
            else:
                st.error('Please fix the following issues:')
                for error in custom_errors:
                    st.error(f'• {error}')
        else:
            st.error('Please fill in all required fields correctly')

# Usage
render_registration_form()
```

**Key Points:**
- Schema validation for basic rules
- Custom validation for business logic
- Real-time password strength feedback
- Comprehensive error messaging

---

## Best Practices from Examples

### 1. Always Use FormController
```python
controller = FormController(schema)  # Creates lot structure automatically
```

### 2. Let the System Handle Lots
```python
# Don't do this:
if has_lots:  # ❌ Never check

# Do this:
controller.render_form()  # ✅ Works for all cases
```

### 3. Access Data Consistently
```python
# Always lot-scoped:
value = controller.context.get_field_value('field')  # ✅
```

### 4. Use Built-in Validation
```python
if controller.validate_form():  # Validates all lots
    data = controller.get_form_data()
```

### 5. Leverage Visual Elements
```python
schema = {
    'use_container': True,  # Visual grouping
    'use_expander': True,   # Collapsible sections
}
```

## Conclusion

These examples demonstrate that Form Renderer 2.0 handles everything from simple contact forms to complex nested structures with the same clean API. The unified lot architecture ensures consistency while providing all the power needed for complex scenarios.