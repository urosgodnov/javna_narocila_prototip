"""
E2E Test Configuration for Modern Form Renderer
Using Playwright MCP for browser automation
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base configuration
BASE_DIR = Path(__file__).parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "tests" / "e2e" / "test_data"
SCREENSHOTS_DIR = BASE_DIR / "tests" / "e2e" / "screenshots"
REPORTS_DIR = BASE_DIR / "tests" / "e2e" / "reports"

# Create directories if they don't exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Application configuration
APP_CONFIG = {
    "base_url": "http://localhost:8501",
    "app_title": "Javna Naročila - Modern Form",
    "startup_timeout": 30000,
    "default_timeout": 10000,
    "slow_mo": 100  # Milliseconds between actions for debugging
}

# Test user profiles
TEST_USERS = {
    "standard": {
        "organization": "Test Organization d.o.o.",
        "email": "test@example.com",
        "phone": "+386 1 234 5678",
        "address": "Testna ulica 123, 1000 Ljubljana"
    },
    "government": {
        "organization": "Ministrstvo za testiranje",
        "email": "gov.test@gov.si",
        "phone": "+386 1 478 7000",
        "address": "Gregorčičeva 20, 1000 Ljubljana"
    },
    "international": {
        "organization": "International Test Corp",
        "email": "intl@test.eu",
        "phone": "+49 30 12345678",
        "address": "Teststraße 456, 10115 Berlin"
    }
}

# Form test data scenarios
FORM_SCENARIOS = {
    "simple_goods": {
        "name": "Simple Goods Purchase",
        "orderType": "blago",
        "estimatedValue": 50000,
        "cpvCodes": ["30192000-1"],
        "deliveryDate": "2024-12-31",
        "paymentTerms": "30 dni",
        "description": "Nakup pisarniške opreme"
    },
    "complex_services": {
        "name": "Complex IT Services",
        "orderType": "storitve",
        "estimatedValue": 150000,
        "cpvCodes": ["72000000-5", "72400000-4"],
        "duration": "24 mesecev",
        "lots": 3,
        "criteria": ["cena", "kvaliteta", "rok_izvedbe"],
        "description": "IT storitve vzdrževanja in podpore"
    },
    "construction": {
        "name": "Construction Project",
        "orderType": "gradnje",
        "estimatedValue": 2500000,
        "cpvCodes": ["45000000-7"],
        "executionPeriod": "18 mesecev",
        "guarantee": "10 let",
        "description": "Gradnja upravne stavbe"
    }
}

# Validation test cases
VALIDATION_TESTS = {
    "required_fields": {
        "test_empty_submission": True,
        "test_partial_data": True,
        "expected_errors": [
            "Naziv organizacije je obvezen",
            "Vrsta naročila je obvezna",
            "Ocenjena vrednost je obvezna"
        ]
    },
    "field_formats": {
        "email": ["invalid.email", "test@", "@test.com", "valid@email.com"],
        "phone": ["123", "++386", "+386 1 234 5678"],
        "value": [-100, 0, 1000000000, "abc", 50000]
    },
    "date_validation": {
        "past_dates": False,
        "weekend_dates": True,
        "min_future_days": 14
    }
}

# Browser viewport configurations for responsive testing
VIEWPORTS = {
    "mobile": {"width": 375, "height": 667, "name": "iPhone SE"},
    "tablet": {"width": 768, "height": 1024, "name": "iPad"},
    "laptop": {"width": 1366, "height": 768, "name": "Laptop"},
    "desktop": {"width": 1920, "height": 1080, "name": "Full HD"},
    "4k": {"width": 3840, "height": 2160, "name": "4K Display"}
}

# Performance benchmarks
PERFORMANCE_BENCHMARKS = {
    "page_load": 3000,  # ms
    "form_step_transition": 500,  # ms
    "validation_feedback": 200,  # ms
    "search_autocomplete": 300,  # ms
    "file_upload": 5000  # ms
}

# Accessibility test configuration
ACCESSIBILITY_CONFIG = {
    "test_keyboard_navigation": True,
    "test_screen_reader": True,
    "test_color_contrast": True,
    "wcag_level": "AA",
    "axe_core_rules": [
        "color-contrast",
        "label",
        "aria-valid-attr",
        "button-name",
        "image-alt"
    ]
}

# Test report configuration
REPORT_CONFIG = {
    "format": "html",
    "include_screenshots": True,
    "include_videos": False,
    "include_traces": True,
    "metrics": [
        "test_duration",
        "pass_rate",
        "error_types",
        "performance_metrics"
    ]
}

def get_test_config() -> Dict[str, Any]:
    """Get complete test configuration."""
    return {
        "app": APP_CONFIG,
        "users": TEST_USERS,
        "scenarios": FORM_SCENARIOS,
        "validation": VALIDATION_TESTS,
        "viewports": VIEWPORTS,
        "performance": PERFORMANCE_BENCHMARKS,
        "accessibility": ACCESSIBILITY_CONFIG,
        "report": REPORT_CONFIG
    }

def get_scenario_by_name(name: str) -> Dict[str, Any]:
    """Get specific test scenario by name."""
    return FORM_SCENARIOS.get(name, FORM_SCENARIOS["simple_goods"])

def get_user_by_type(user_type: str) -> Dict[str, Any]:
    """Get test user by type."""
    return TEST_USERS.get(user_type, TEST_USERS["standard"])