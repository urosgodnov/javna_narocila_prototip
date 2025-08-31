# Test Suite Organization

## Important Convention
**ALL test files MUST be created in this `/tests` directory.**

## Overview
This directory contains all test files for the javna_narocila_prototip project. Tests are organized by category and purpose.
- **Total test files**: 132
- **Test utilities**: 6  
- **Categories**: Form tests, Validation, Integration, E2E, Database, UI

## Directory Structure
```
tests/
├── test_*.py            # Main test files (132 files)
├── utils/               # Test utilities and helper scripts
│   ├── manual_test.py
│   ├── run_modern_form_tests.py
│   ├── run_tests.py
│   ├── run_with_logging.py
│   ├── set_test_cpv.py
│   └── transformers_test.py
├── backups/             # Backup files from previous versions
│   ├── test_dynamic_labels.py.bak
│   └── test_procedure_dropdown.py.bak
└── e2e/                 # End-to-end tests
    └── test_modern_form_e2e.py
```

## Naming Conventions
- Test files should start with `test_` prefix (e.g., `test_feature.py`)
- Validation scripts can start with `validate_` prefix
- Test classes should start with `Test` (e.g., `TestFeature`)
- Test functions should start with `test_` (e.g., `def test_something():`)

## Running Tests
```bash
# Run all tests
python3 run_tests.py

# Run specific test
python3 tests/test_specific.py

# With pytest (if installed)
pytest tests/
```

## Creating New Tests
When creating new test files:
1. ALWAYS create them in `/tests` directory
2. Add proper path setup at the top:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
3. Follow the naming conventions above
4. Import modules from the project root perspective

## Test Categories

### Form Renderer Tests (10 files)
- `test_form_*.py` - Tests for form rendering functionality
- `test_unified_forms.py` - Tests for new unified lot architecture
- `test_new_form_renderer_system.py` - System tests for Form Renderer 2.0

### Validation Tests (9 files)
- `test_valid*.py` - Various validation scenarios
- `test_criteria_validation.py` - Criteria-specific validation
- `test_cpv_validation.py` - CPV code validation

### Integration Tests (5 files)
- `test_*integration*.py` - Integration between components
- `test_form_controller_integration.py` - New FormController integration

### End-to-End Tests (4 files)
- `test_*e2e*.py` - Full workflow tests
- `test_comprehensive_procurement_e2e.py` - Complete procurement flow

### Database Tests
- `test_database*.py` - Database operations
- `test_qdrant_*.py` - Qdrant vector database tests

### UI Tests
- `test_dashboard.py` - Dashboard functionality
- `test_admin_panel.py` - Admin panel features
- `test_*_playwright.py` - Browser automation tests

## Recent Updates

### Form Renderer 2.0 Migration (2024-01-30)
- Added `test_new_form_renderer_system.py` - Tests for new unified lot architecture
- Updated integration tests for FormController
- All tests now use the new "everything is a lot" architecture

### Test Organization (2024-01-30)
- Moved test files from root to tests folder
- Created utils/ for test utilities
- Created backups/ for old test versions
- Organized 132 test files by category

## DO NOT
- ❌ Create test files in the project root
- ❌ Create test files in module directories
- ❌ Use inconsistent naming patterns