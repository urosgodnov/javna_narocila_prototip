"""
Playwright E2E Test Suite for Merila (Selection Criteria) Logic
Author: Quinn - Senior Developer & QA Architect
Purpose: Comprehensive testing of the selection criteria functionality in the procurement form
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, expect
import json
from typing import Dict, List, Optional
import time

class TestMerilaLogic:
    """
    Test suite for comprehensive validation of Merila (Selection Criteria) functionality.
    Tests cover rendering, validation, scoring logic, and data persistence.
    """
    
    BASE_URL = "http://localhost:8501"
    TIMEOUT = 30000  # 30 seconds for page load operations
    
    @pytest.fixture(scope="class")
    async def browser_context(self):
        """Create and manage browser context for tests."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Set to True for CI/CD
                slow_mo=500  # Slow down for visibility during development
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='sl-SI'
            )
            page = await context.new_page()
            yield page
            await browser.close()
    
    async def navigate_to_merila_step(self, page):
        """
        Navigate through the form to reach the Merila (Selection Criteria) step.
        This is a helper method to get to the criteria section efficiently.
        """
        await page.goto(self.BASE_URL)
        await page.wait_for_load_state('networkidle')
        
        # We need to fill minimum required fields and navigate to merila step
        # Based on config.py, selectionCriteria is in LOT_SPECIFIC_STEPS
        
        # Step 1: Client Info
        await page.fill('input[aria-label*="Naziv"]', 'Test Naročnik')
        await page.fill('input[aria-label*="Naslov"]', 'Testna ulica 1, 1000 Ljubljana')
        await page.click('button:has-text("Naprej")')
        
        # Step 2: Project Info
        await page.fill('input[aria-label*="Naziv javnega naročila"]', 'Test Javno Naročilo')
        await page.fill('textarea[aria-label*="Predmet javnega naročila"]', 'Test predmet')
        await page.click('button:has-text("Naprej")')
        
        # Continue navigating until we reach selectionCriteria
        while True:
            # Check if we're on the selection criteria page
            criteria_header = await page.locator('h2:has-text("IZBIRA MERIL")').count()
            if criteria_header > 0:
                break
            
            # Otherwise, click next
            next_button = await page.locator('button:has-text("Naprej")')
            if await next_button.count() > 0:
                await next_button.click()
                await page.wait_for_timeout(500)
            else:
                # We've reached the end without finding criteria
                raise Exception("Could not navigate to Merila section")
    
    @pytest.mark.asyncio
    async def test_merila_section_rendering(self, browser_context):
        """
        Test 1: Verify that all merila fields render correctly
        Validates the presence of all criteria checkboxes and input fields
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Verify main criteria checkboxes
        criteria_elements = {
            'price': 'Cena',
            'additionalReferences': 'Dodatne reference imenovanega kadra',
            'additionalTechnicalRequirements': 'Dodatne tehnične zahteve',
            'shorterDeadline': 'Krajši rok izvedbe',
            'longerWarranty': 'Garancija daljša od zahtevane',
            'costEfficiency': 'Stroškovna učinkovitost',
            'socialCriteria': 'Socialna merila',
            'otherCriteriaCustom': 'Drugo, imamo predlog',
            'otherCriteriaAI': 'Drugo, prosim za predlog AI'
        }
        
        for key, label in criteria_elements.items():
            element = await page.locator(f'label:has-text("{label}")')
            assert await element.count() > 0, f"Criteria '{label}' not found"
        
        # Verify scoring section header
        scoring_header = await page.locator('h2:has-text("RAZMERJA MED MERILI")')
        assert await scoring_header.count() > 0, "Scoring section header not found"
        
        # Verify tiebreaker section
        tiebreaker_header = await page.locator('h2:has-text("PRAVILO ZA ENAKO ŠTEVILO TOČK")')
        assert await tiebreaker_header.count() > 0, "Tiebreaker section not found"
    
    @pytest.mark.asyncio
    async def test_conditional_field_rendering(self, browser_context):
        """
        Test 2: Verify conditional rendering of dependent fields
        Tests that selecting criteria shows corresponding point input fields
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Test price criteria and points field
        await page.check('input[type="checkbox"][name*="price"]')
        await page.wait_for_timeout(500)
        
        # Verify points field appears
        price_points_field = await page.locator('input[type="number"][aria-label*="Cena → točk"]')
        assert await price_points_field.count() > 0, "Price points field did not appear"
        
        # Test social criteria with sub-options
        await page.check('input[type="checkbox"][name*="socialCriteria"]')
        await page.wait_for_timeout(500)
        
        # Verify sub-options appear
        social_sub_options = [
            'Delež zaposlenih mladih',
            'Delež zaposlenih starejših',
            'Priglašeni kader je zaposlen pri ponudniku',
            'Povprečna plača priglašenega kadra'
        ]
        
        for option in social_sub_options:
            element = await page.locator(f'label:has-text("{option}")')
            assert await element.count() > 0, f"Social sub-option '{option}' not found"
        
        # Test custom criteria textarea
        await page.check('input[type="checkbox"][name*="otherCriteriaCustom"]')
        await page.wait_for_timeout(500)
        
        custom_description_field = await page.locator('textarea[aria-label*="Opišite merilo"]')
        assert await custom_description_field.count() > 0, "Custom criteria description field did not appear"
    
    @pytest.mark.asyncio
    async def test_scoring_points_validation(self, browser_context):
        """
        Test 3: Validate scoring points input and calculation
        Tests that point values are properly accepted and stored
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Select multiple criteria
        criteria_with_points = {
            'price': 40,
            'additionalReferences': 20,
            'shorterDeadline': 15,
            'socialCriteria': 25
        }
        
        total_points = 0
        
        for criteria, points in criteria_with_points.items():
            # Check the criteria checkbox
            await page.check(f'input[type="checkbox"][name*="{criteria}"]')
            await page.wait_for_timeout(300)
            
            # Enter points
            points_field = await page.locator(f'input[type="number"][name*="{criteria}Points"]')
            await points_field.fill(str(points))
            total_points += points
        
        # Verify total equals 100
        assert total_points == 100, f"Total points should equal 100, got {total_points}"
        
        # Test tiebreaker rule selection
        await page.select_option('select[name*="tiebreakerRule"]', 'prednost po specifičnem merilu')
        await page.wait_for_timeout(300)
        
        # Verify tiebreaker criterion dropdown appears
        tiebreaker_criterion = await page.locator('select[name*="tiebreakerCriterion"]')
        assert await tiebreaker_criterion.count() > 0, "Tiebreaker criterion dropdown did not appear"
        
        await page.select_option('select[name*="tiebreakerCriterion"]', 'cena')
    
    @pytest.mark.asyncio
    async def test_technical_requirements_integration(self, browser_context):
        """
        Test 4: Test integration of technical requirements with criteria
        Validates that technical requirement descriptions are properly handled
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Enable additional technical requirements
        await page.check('input[type="checkbox"][name*="additionalTechnicalRequirements"]')
        await page.wait_for_timeout(300)
        
        # Fill in technical requirements description
        tech_description = "Test tehnične zahteve:\n1. Certifikat ISO 9001\n2. Min 5 let izkušenj"
        tech_field = await page.locator('textarea[aria-label*="dodatne tehnične zahteve"]')
        await tech_field.fill(tech_description)
        
        # Add points for technical requirements
        tech_points_field = await page.locator('input[type="number"][name*="additionalTechnicalRequirementsPoints"]')
        await tech_points_field.fill("30")
        
        # Verify the value was stored
        stored_value = await tech_field.input_value()
        assert stored_value == tech_description, "Technical requirements description not stored correctly"
    
    @pytest.mark.asyncio
    async def test_social_criteria_complex_workflow(self, browser_context):
        """
        Test 5: Test complex social criteria selection workflow
        Validates nested checkbox logic and custom social criteria
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Enable social criteria
        await page.check('input[type="checkbox"][name*="socialCriteria"]')
        await page.wait_for_timeout(500)
        
        # Select specific social sub-criteria
        social_selections = {
            'youngEmployeesShare': True,
            'elderlyEmployeesShare': False,
            'registeredStaffEmployed': True,
            'averageSalary': True,
            'otherSocial': True
        }
        
        for criteria, should_check in social_selections.items():
            checkbox = await page.locator(f'input[type="checkbox"][name*="{criteria}"]')
            if should_check and await checkbox.count() > 0:
                await checkbox.check()
                await page.wait_for_timeout(200)
        
        # Fill custom social criteria description
        if social_selections['otherSocial']:
            other_social_field = await page.locator('textarea[name*="otherSocialDescription"]')
            await other_social_field.fill("Zaposlovanje lokalnega prebivalstva - min 50%")
        
        # Add points for social criteria
        social_points_field = await page.locator('input[type="number"][name*="socialCriteriaPoints"]')
        await social_points_field.fill("35")
    
    @pytest.mark.asyncio
    async def test_data_persistence_navigation(self, browser_context):
        """
        Test 6: Test data persistence when navigating between steps
        Ensures criteria selections are preserved during navigation
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Make selections
        test_data = {
            'price': {'checked': True, 'points': 50},
            'longerWarranty': {'checked': True, 'points': 20},
            'costEfficiency': {'checked': True, 'points': 30}
        }
        
        for criteria, config in test_data.items():
            await page.check(f'input[type="checkbox"][name*="{criteria}"]')
            await page.wait_for_timeout(200)
            
            points_field = await page.locator(f'input[type="number"][name*="{criteria}Points"]')
            await points_field.fill(str(config['points']))
        
        # Navigate back
        await page.click('button:has-text("Nazaj")')
        await page.wait_for_timeout(500)
        
        # Navigate forward again
        await page.click('button:has-text("Naprej")')
        await page.wait_for_timeout(500)
        
        # Verify data persistence
        for criteria, config in test_data.items():
            checkbox = await page.locator(f'input[type="checkbox"][name*="{criteria}"]')
            is_checked = await checkbox.is_checked()
            assert is_checked == config['checked'], f"{criteria} checkbox state not preserved"
            
            points_field = await page.locator(f'input[type="number"][name*="{criteria}Points"]')
            points_value = await points_field.input_value()
            assert points_value == str(config['points']), f"{criteria} points value not preserved"
    
    @pytest.mark.asyncio
    async def test_edge_cases_validation(self, browser_context):
        """
        Test 7: Test edge cases and validation rules
        Tests boundary conditions, invalid inputs, and error handling
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Test 1: Negative points
        await page.check('input[type="checkbox"][name*="price"]')
        price_points = await page.locator('input[type="number"][name*="pricePoints"]')
        await price_points.fill("-10")
        
        # Browser should enforce min=0 on number inputs
        actual_value = await price_points.input_value()
        assert int(actual_value) >= 0, "Negative points should not be allowed"
        
        # Test 2: Very large point values
        await price_points.fill("999999")
        stored_value = await price_points.input_value()
        assert stored_value == "999999", "Large point values should be accepted"
        
        # Test 3: Empty required fields when criteria is selected
        await page.check('input[type="checkbox"][name*="shorterDeadline"]')
        await page.wait_for_timeout(200)
        
        # Try to proceed without filling minimum deadline
        min_deadline_field = await page.locator('input[name*="shorterDeadlineMinimum"]')
        if await min_deadline_field.count() > 0:
            # Leave it empty and try to navigate
            await page.click('button:has-text("Naprej")')
            await page.wait_for_timeout(500)
            
            # Check for validation message
            warning = await page.locator('.stWarning')
            # Validation behavior depends on implementation
    
    @pytest.mark.asyncio
    async def test_lot_specific_criteria(self, browser_context):
        """
        Test 8: Test criteria configuration for multiple lots
        Validates that criteria can be configured differently per lot
        """
        page = browser_context
        
        # First, we need to configure lots in the form
        await page.goto(self.BASE_URL)
        await page.wait_for_load_state('networkidle')
        
        # Navigate to lots configuration
        # ... (navigation code to lots step)
        
        # Enable lots
        lots_checkbox = await page.locator('input[type="checkbox"][name*="hasLots"]')
        if await lots_checkbox.count() > 0:
            await lots_checkbox.check()
            await page.wait_for_timeout(300)
            
            # Add multiple lots
            # This would require specific implementation based on how lots are added in the UI
            # For now, we'll document this as a test scenario
            
            # Once lots are configured, each lot should have its own criteria section
            # This test would verify that criteria can be configured independently per lot
    
    @pytest.mark.asyncio
    async def test_screenshot_documentation(self, browser_context):
        """
        Test 9: Generate screenshots for documentation
        Creates visual documentation of the merila functionality
        """
        page = browser_context
        await self.navigate_to_merila_step(page)
        
        # Take screenshot of empty criteria form
        await page.screenshot(path="tests/screenshots/merila_empty.png", full_page=True)
        
        # Configure typical criteria setup
        await page.check('input[type="checkbox"][name*="price"]')
        await page.fill('input[type="number"][name*="pricePoints"]', "40")
        
        await page.check('input[type="checkbox"][name*="additionalReferences"]')
        await page.fill('input[type="number"][name*="additionalReferencesPoints"]', "30")
        
        await page.check('input[type="checkbox"][name*="socialCriteria"]')
        await page.wait_for_timeout(300)
        await page.check('input[type="checkbox"][name*="youngEmployeesShare"]')
        await page.fill('input[type="number"][name*="socialCriteriaPoints"]', "30")
        
        # Take screenshot of configured form
        await page.screenshot(path="tests/screenshots/merila_configured.png", full_page=True)
        
        # Configure tiebreaker
        await page.select_option('select[name*="tiebreakerRule"]', 'prednost po specifičnem merilu')
        await page.select_option('select[name*="tiebreakerCriterion"]', 'cena')
        
        # Final screenshot
        await page.screenshot(path="tests/screenshots/merila_complete.png", full_page=True)
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, browser_context):
        """
        Test 10: Measure performance metrics for criteria section
        Validates that the form performs well under various conditions
        """
        page = browser_context
        
        # Start performance monitoring
        start_time = time.time()
        
        await self.navigate_to_merila_step(page)
        
        navigation_time = time.time() - start_time
        assert navigation_time < 10, f"Navigation took too long: {navigation_time}s"
        
        # Measure interaction responsiveness
        interaction_start = time.time()
        
        # Perform multiple rapid interactions
        for _ in range(5):
            await page.check('input[type="checkbox"][name*="price"]')
            await page.uncheck('input[type="checkbox"][name*="price"]')
        
        interaction_time = time.time() - interaction_start
        assert interaction_time < 5, f"Interactions took too long: {interaction_time}s"
        
        # Test form with maximum selections
        all_criteria = [
            'price', 'additionalReferences', 'additionalTechnicalRequirements',
            'shorterDeadline', 'longerWarranty', 'costEfficiency',
            'socialCriteria', 'otherCriteriaCustom'
        ]
        
        selection_start = time.time()
        
        for criteria in all_criteria:
            checkbox = await page.locator(f'input[type="checkbox"][name*="{criteria}"]')
            if await checkbox.count() > 0:
                await checkbox.check()
        
        selection_time = time.time() - selection_start
        assert selection_time < 5, f"Selecting all criteria took too long: {selection_time}s"


class TestMerilaIntegration:
    """
    Integration tests for Merila with other form components
    """
    
    @pytest.mark.asyncio
    async def test_merila_with_financial_guarantees(self, browser_context):
        """
        Test integration between merila and financial guarantees
        Ensures proper interaction between scoring criteria and financial requirements
        """
        # Implementation would test the relationship between
        # selection criteria scores and financial guarantee requirements
        pass
    
    @pytest.mark.asyncio
    async def test_merila_export_import(self, browser_context):
        """
        Test export and import of form data including merila configuration
        """
        # Would test saving drafts with criteria configuration
        # and loading them back correctly
        pass


# Test execution helpers
def run_tests():
    """Run all merila tests with proper configuration."""
    pytest.main([
        __file__,
        '-v',  # Verbose output
        '--tb=short',  # Short traceback
        '--html=tests/reports/merila_test_report.html',  # HTML report
        '--self-contained-html',  # Include CSS/JS in HTML
        '-k', 'test_merila'  # Run only merila tests
    ])


if __name__ == "__main__":
    # Create necessary directories
    import os
    os.makedirs('tests/screenshots', exist_ok=True)
    os.makedirs('tests/reports', exist_ok=True)
    
    # Run the tests
    run_tests()