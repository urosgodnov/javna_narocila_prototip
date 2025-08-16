# Tests Directory

## Important Convention
**ALL test files MUST be created in this `/tests` directory.**

## Naming Conventions
- Test files should start with `test_` prefix (e.g., `test_feature.py`)
- Validation scripts can start with `validate_` prefix
- Test classes should start with `Test` (e.g., `TestFeature`)
- Test functions should start with `test_` (e.g., `def test_something():`)

## Directory Structure
```
tests/
├── __init__.py           # Makes tests a Python package
├── test_*.py            # Unit and integration tests
├── validate_*.py        # Validation scripts
├── e2e/                 # End-to-end tests
└── test_reports/        # Test output reports
```

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

## DO NOT
- ❌ Create test files in the project root
- ❌ Create test files in module directories
- ❌ Use inconsistent naming patterns