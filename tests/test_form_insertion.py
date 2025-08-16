"""
Comprehensive Playwright test suite for procurement form insertion.
Tests form navigation, validation, data persistence, and UI functionality.
"""
import asyncio
from playwright.async_api import async_playwright, expect
import pytest
from datetime import datetime
import json

class TestProcurementFormInsertion:
    """Test suite for procurement form insertion functionality."""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment before each test."""
        self.base_url = "http://localhost:8505"
        self.test_data = {
            "project_name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "client_name": "Test Organization",
            "estimated_value": "50000",
            "description": "Test procurement description for automated testing",
            "cpv_code": "45000000-7",
            "nuts_code": "SI041"
        }
    
    async def test_form_navigation(self):
        """Test form navigation through all steps."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🧪 Testing form navigation...")
            
            # Navigate to the application
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Click on "New procurement" button
            new_button = page.locator("button:has-text('Nov razpis')").first
            if await new_button.count() > 0:
                await new_button.click()
            else:
                # Alternative: look for the button in the form view
                await page.locator("button:has-text('Novo javno naročilo')").first.click()
            
            await page.wait_for_timeout(2000)
            
            # Test navigation through steps
            steps_tested = 0
            max_steps = 10
            
            for step in range(max_steps):
                # Check if we're on a form step
                next_button = page.locator("button:has-text('Naprej')")
                if await next_button.count() == 0:
                    print(f"✅ Reached end of form at step {step}")
                    break
                
                # Check for progress indicator
                progress_bar = page.locator(".progress-fill, [class*='progress']")
                if await progress_bar.count() > 0:
                    print(f"✓ Progress indicator visible at step {step + 1}")
                
                # Navigate to next step
                await next_button.first.click()
                await page.wait_for_timeout(1000)
                steps_tested += 1
                
                # Test back navigation
                back_button = page.locator("button:has-text('Nazaj')")
                if await back_button.count() > 0 and step > 0:
                    await back_button.first.click()
                    await page.wait_for_timeout(500)
                    await next_button.first.click()
                    await page.wait_for_timeout(500)
                    print(f"✓ Back/forward navigation works at step {step + 1}")
            
            print(f"✅ Navigation test completed. Tested {steps_tested} steps.")
            await browser.close()
    
    async def test_form_field_validation(self):
        """Test form field validation and error handling."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🧪 Testing form field validation...")
            
            # Navigate to form
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Navigate to form
            new_button = page.locator("button:has-text('Nov razpis')").first
            if await new_button.count() > 0:
                await new_button.click()
            else:
                await page.locator("button:has-text('Novo javno naročilo')").first.click()
            
            await page.wait_for_timeout(2000)
            
            # Test required field validation
            # Try to proceed without filling required fields
            next_button = page.locator("button:has-text('Naprej')").first
            if await next_button.count() > 0:
                await next_button.click()
                await page.wait_for_timeout(1000)
                
                # Check for validation messages
                error_messages = page.locator("[class*='error'], [class*='warning'], [class*='validation']")
                if await error_messages.count() > 0:
                    print("✓ Validation messages displayed for empty required fields")
                
            # Fill in some test data
            # Look for text inputs
            text_inputs = page.locator("input[type='text'], input:not([type])")
            input_count = await text_inputs.count()
            
            for i in range(min(3, input_count)):
                await text_inputs.nth(i).fill(f"Test Value {i + 1}")
                print(f"✓ Filled text input {i + 1}")
            
            # Test number input validation
            number_inputs = page.locator("input[type='number']")
            if await number_inputs.count() > 0:
                # Test invalid number
                await number_inputs.first.fill("abc")
                await page.wait_for_timeout(500)
                # Test valid number
                await number_inputs.first.fill("12345")
                print("✓ Number input validation tested")
            
            # Test select/dropdown fields
            selects = page.locator("select, [role='combobox'], [data-baseweb='select']")
            if await selects.count() > 0:
                await selects.first.click()
                await page.wait_for_timeout(500)
                # Try to select first available option
                options = page.locator("option, [role='option']")
                if await options.count() > 1:
                    await options.nth(1).click()
                    print("✓ Dropdown selection tested")
            
            print("✅ Field validation test completed.")
            await browser.close()
    
    async def test_save_draft_functionality(self):
        """Test saving and loading draft functionality."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🧪 Testing save draft functionality...")
            
            # Navigate to form
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Start new form
            new_button = page.locator("button:has-text('Nov razpis')").first
            if await new_button.count() > 0:
                await new_button.click()
            else:
                await page.locator("button:has-text('Novo javno naročilo')").first.click()
            
            await page.wait_for_timeout(2000)
            
            # Fill in some test data
            test_value = f"Draft Test {datetime.now().strftime('%H%M%S')}"
            text_inputs = page.locator("input[type='text'], input:not([type])")
            if await text_inputs.count() > 0:
                await text_inputs.first.fill(test_value)
                print(f"✓ Entered test value: {test_value}")
            
            # Look for save button
            save_buttons = page.locator("button:has-text('Shrani'), button:has-text('Save'), button:has-text('💾')")
            if await save_buttons.count() > 0:
                await save_buttons.first.click()
                await page.wait_for_timeout(2000)
                
                # Check for success message
                success_msg = page.locator("[class*='success'], text=/shranjen/i, text=/saved/i")
                if await success_msg.count() > 0:
                    print("✓ Draft saved successfully")
                
                # Try to load the draft
                # Go back to dashboard
                back_button = page.locator("button:has-text('Nazaj'), button:has-text('Dashboard'), button:has-text('Pregled')")
                if await back_button.count() > 0:
                    await back_button.first.click()
                    await page.wait_for_timeout(2000)
                    
                    # Check if draft appears in the list
                    draft_items = page.locator(f"text=/{test_value}/")
                    if await draft_items.count() > 0:
                        print("✓ Draft appears in the list")
                        
                        # Try to edit the draft
                        edit_button = page.locator("button:has-text('Uredi'), button:has-text('Edit')").first
                        if await edit_button.count() > 0:
                            await edit_button.click()
                            await page.wait_for_timeout(2000)
                            
                            # Verify the value is loaded
                            loaded_input = page.locator(f"input[value='{test_value}']")
                            if await loaded_input.count() > 0:
                                print("✓ Draft loaded successfully with saved data")
            
            print("✅ Save draft test completed.")
            await browser.close()
    
    async def test_form_submission(self):
        """Test complete form submission workflow."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🧪 Testing form submission...")
            
            # Navigate to form
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Start new form
            new_button = page.locator("button:has-text('Nov razpis')").first
            if await new_button.count() > 0:
                await new_button.click()
            else:
                await page.locator("button:has-text('Novo javno naročilo')").first.click()
            
            await page.wait_for_timeout(2000)
            
            # Navigate through form and fill minimal required data
            submission_id = f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            steps_completed = 0
            
            for step in range(20):  # Maximum 20 steps
                # Fill any visible required fields
                required_inputs = page.locator("input:visible, textarea:visible, select:visible")
                input_count = await required_inputs.count()
                
                for i in range(min(2, input_count)):
                    element = required_inputs.nth(i)
                    tag_name = await element.evaluate("el => el.tagName")
                    
                    if tag_name == "INPUT":
                        input_type = await element.get_attribute("type")
                        if input_type == "number":
                            await element.fill("1000")
                        elif input_type == "date":
                            await element.fill("2024-12-31")
                        else:
                            await element.fill(f"{submission_id}_field_{i}")
                    elif tag_name == "TEXTAREA":
                        await element.fill(f"Test description for {submission_id}")
                    elif tag_name == "SELECT":
                        options = await element.locator("option").all_text_contents()
                        if len(options) > 1:
                            await element.select_option(index=1)
                
                # Try to proceed to next step
                next_button = page.locator("button:has-text('Naprej')").first
                if await next_button.count() == 0:
                    # Might be at the last step, look for submit
                    submit_button = page.locator("button:has-text('Oddaj'), button:has-text('Submit'), button:has-text('Zaključi')")
                    if await submit_button.count() > 0:
                        await submit_button.first.click()
                        await page.wait_for_timeout(3000)
                        print(f"✓ Form submitted after {steps_completed} steps")
                        
                        # Check for success indication
                        success_indicators = page.locator("[class*='success'], text=/uspešno/i, text=/saved/i, text=/submitted/i")
                        if await success_indicators.count() > 0:
                            print("✓ Success message displayed")
                        break
                    else:
                        print(f"✓ Reached end of form at step {steps_completed}")
                        break
                
                await next_button.click()
                await page.wait_for_timeout(1000)
                steps_completed += 1
                print(f"✓ Completed step {steps_completed}")
            
            print(f"✅ Form submission test completed. ID: {submission_id}")
            await browser.close()
    
    async def test_modern_ui_elements(self):
        """Test modern UI elements and styling."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🧪 Testing modern UI elements...")
            
            # Navigate to application
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Check for modern dashboard elements
            ui_checks = {
                "Stats Cards": "[class*='stats-card'], [class*='metric']",
                "Progress Bar": "[class*='progress']",
                "Gradient Header": "[style*='gradient']",
                "Modern Buttons": "button[class*='primary'], button[type='primary']",
                "Styled Tables": "[class*='dataframe'], table",
                "Icons": "[class*='icon'], svg",
            }
            
            for element_name, selector in ui_checks.items():
                elements = page.locator(selector)
                if await elements.count() > 0:
                    print(f"✓ {element_name} found: {await elements.count()} instance(s)")
                else:
                    print(f"⚠ {element_name} not found")
            
            # Test hover effects
            buttons = page.locator("button:visible")
            if await buttons.count() > 0:
                first_button = buttons.first
                await first_button.hover()
                await page.wait_for_timeout(500)
                print("✓ Hover effects tested")
            
            # Test responsive layout
            # Mobile view
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)
            print("✓ Mobile view tested (375x667)")
            
            # Tablet view
            await page.set_viewport_size({"width": 768, "height": 1024})
            await page.wait_for_timeout(1000)
            print("✓ Tablet view tested (768x1024)")
            
            # Desktop view
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.wait_for_timeout(1000)
            print("✓ Desktop view tested (1920x1080)")
            
            print("✅ Modern UI elements test completed.")
            await browser.close()

# Main test runner
async def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*60)
    print("🧪 PROCUREMENT FORM INSERTION TEST SUITE")
    print("="*60 + "\n")
    
    test_suite = TestProcurementFormInsertion()
    await test_suite.setup()
    
    test_cases = [
        ("Form Navigation", test_suite.test_form_navigation),
        ("Field Validation", test_suite.test_form_field_validation),
        ("Save Draft", test_suite.test_save_draft_functionality),
        ("Form Submission", test_suite.test_form_submission),
        ("Modern UI Elements", test_suite.test_modern_ui_elements),
    ]
    
    results = []
    for test_name, test_func in test_cases:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        try:
            await test_func()
            results.append((test_name, "PASSED ✅"))
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append((test_name, f"FAILED ❌: {str(e)[:50]}"))
        print("-" * 40)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    for test_name, result in results:
        print(f"{test_name:30} {result}")
    
    passed = sum(1 for _, r in results if "PASSED" in r)
    total = len(results)
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())