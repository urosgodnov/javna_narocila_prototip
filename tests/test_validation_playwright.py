#!/usr/bin/env python3
"""Test validation logic with Playwright."""

import asyncio
import subprocess
import time
import sys
from playwright.async_api import async_playwright

async def test_validation():
    """Test the validation logic in the Streamlit app."""
    
    # Start Streamlit app
    print("Starting Streamlit app...")
    process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", "8503", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to start
    print("Waiting for app to start...")
    time.sleep(10)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("Navigating to app...")
            await page.goto("http://localhost:8503", wait_until="networkidle", timeout=30000)
            
            print("Taking initial screenshot...")
            await page.screenshot(path="test_initial.png")
            
            # Test 1: Check if validation toggle is present
            print("\nTest 1: Checking validation toggle...")
            validation_toggle = await page.query_selector("text=Izklopljena validacija")
            if validation_toggle:
                print("✓ Found validation toggle")
                await page.screenshot(path="test_validation_toggle.png")
            else:
                print("✗ Validation toggle not found")
            
            # Test 2: Navigate to Step 2 and select CPV codes
            print("\nTest 2: Testing CPV code selection...")
            
            # Click next to go to step 2
            next_button = await page.query_selector("button:has-text('Naprej')")
            if next_button:
                await next_button.click()
                await page.wait_for_load_state("networkidle")
                print("✓ Navigated to Step 2")
                
                # Look for CPV input field
                cpv_input = await page.query_selector("input[placeholder*='CPV']")
                if cpv_input:
                    # Enter a CPV code that requires additional criteria
                    await cpv_input.fill("79000000")
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(1000)
                    print("✓ Entered CPV code 79000000")
                    
                    await page.screenshot(path="test_cpv_entered.png")
            
            # Test 3: Navigate to criteria step
            print("\nTest 3: Testing criteria validation...")
            next_button = await page.query_selector("button:has-text('Naprej')")
            if next_button:
                await next_button.click()
                await page.wait_for_load_state("networkidle")
                
                # Check for validation messages
                validation_msg = await page.query_selector("text=zahtevajo dodatna merila")
                if validation_msg:
                    print("✓ Validation message displayed")
                    await page.screenshot(path="test_validation_message.png")
                else:
                    print("✗ No validation message found")
                
                # Try to select only price
                price_checkbox = await page.query_selector("input[type='checkbox']:near(:text('Cena'))")
                if price_checkbox:
                    await price_checkbox.check()
                    await page.wait_for_timeout(500)
                    print("✓ Selected price criterion")
                    
                    # Check if error appears
                    error_msg = await page.query_selector(".stAlert")
                    if error_msg:
                        print("✓ Validation error displayed")
                        await page.screenshot(path="test_validation_error.png")
                
                # Now add another criterion
                tech_checkbox = await page.query_selector("input[type='checkbox']:near(:text('Dodatne tehnične zahteve'))")
                if tech_checkbox:
                    await tech_checkbox.check()
                    await page.wait_for_timeout(500)
                    print("✓ Added additional criterion")
                    
                    # Check if error is gone
                    success_msg = await page.query_selector(".stSuccess")
                    if success_msg:
                        print("✓ Validation passed")
                        await page.screenshot(path="test_validation_success.png")
            
            # Test 4: Test validation control toggles
            print("\nTest 4: Testing validation control...")
            
            # Look for step validation toggle
            step_toggle = await page.query_selector("text=Uveljavi validacijo")
            if step_toggle:
                print("✓ Found step validation toggle")
                await step_toggle.click()
                await page.wait_for_timeout(500)
                await page.screenshot(path="test_step_validation.png")
            
            print("\n=== Test Summary ===")
            print("All validation tests completed!")
            print("Screenshots saved:")
            print("  - test_initial.png")
            print("  - test_validation_toggle.png")
            print("  - test_cpv_entered.png")
            print("  - test_validation_message.png")
            print("  - test_validation_error.png")
            print("  - test_validation_success.png")
            print("  - test_step_validation.png")
            
        except Exception as e:
            print(f"Error during testing: {e}")
            await page.screenshot(path="test_error.png")
        finally:
            await browser.close()
            process.terminate()
            print("\nStreamlit app stopped.")

if __name__ == "__main__":
    asyncio.run(test_validation())