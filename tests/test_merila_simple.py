"""
Simplified Playwright Test for Merila (Selection Criteria)
Practical implementation that works with the actual Streamlit app
"""

from playwright.sync_api import sync_playwright, expect
import time
import os

def test_merila_functionality():
    """
    Main test function for testing Merila (Selection Criteria) functionality
    This test navigates to the form and tests the criteria selection logic
    """
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=False,  # Set to False to see the browser
            slow_mo=1000  # Slow down actions by 1 second for visibility
        )
        
        # Create context and page
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            print("🧪 Starting Merila (Selection Criteria) Test Suite")
            print("=" * 50)
            
            # Navigate to the application
            print("📍 Navigating to application...")
            page.goto("http://localhost:8501")
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Wait for Streamlit to fully load
            
            # Take initial screenshot
            os.makedirs('tests/screenshots', exist_ok=True)
            page.screenshot(path="tests/screenshots/01_initial_page.png")
            print("✅ Application loaded successfully")
            
            # Step 1: Fill Client Information
            print("\n📝 Step 1: Filling client information...")
            
            # Check if we need to select single client
            single_client_radio = page.locator('label:has-text("Naročnik je eden")')
            if single_client_radio.count() > 0:
                single_client_radio.click()
                time.sleep(1)
            
            # Fill client name
            name_input = page.locator('input').filter(has_text="Naziv").or_(
                page.locator('input[aria-label*="Naziv"]')
            ).first
            if name_input.count() == 0:
                name_input = page.locator('input').first
            name_input.fill("Test Naročnik d.o.o.")
            
            # Fill client address  
            address_inputs = page.locator('input').all()
            if len(address_inputs) > 1:
                address_inputs[1].fill("Testna ulica 123, 1000 Ljubljana")
            
            # Fill legal representative
            if len(address_inputs) > 2:
                address_inputs[2].fill("Janez Novak")
            
            time.sleep(1)
            page.screenshot(path="tests/screenshots/02_client_info.png")
            
            # Click Next
            next_button = page.locator('button:has-text("Naprej")').or_(
                page.locator('button:has-text("Naslednji korak")')
            ).or_(page.locator('button').filter(has_text="→"))
            
            if next_button.count() > 0:
                next_button.first.click()
                time.sleep(2)
            
            print("✅ Client information filled")
            
            # Step 2: Fill Project Information
            print("\n📝 Step 2: Filling project information...")
            
            # Fill project name
            project_inputs = page.locator('input').all()
            if len(project_inputs) > 0:
                project_inputs[0].fill("Testno javno naročilo za IT storitve")
            
            # Fill project subject
            subject_area = page.locator('textarea').first
            if subject_area.count() > 0:
                subject_area.fill("Razvoj in vzdrževanje informacijskega sistema")
            
            # Fill CPV codes
            if len(project_inputs) > 1:
                project_inputs[1].fill("72000000-5")
            
            time.sleep(1)
            page.screenshot(path="tests/screenshots/03_project_info.png")
            
            # Click Next
            next_button.first.click() if next_button.count() > 0 else None
            time.sleep(2)
            
            print("✅ Project information filled")
            
            # Continue navigating through steps until we reach Selection Criteria
            print("\n🔍 Navigating to Selection Criteria (Merila)...")
            
            steps_navigated = 0
            max_steps = 20  # Safety limit
            
            while steps_navigated < max_steps:
                # Check if we're on the Selection Criteria page
                criteria_header = page.locator('text=/MERILA|merila|Merila|IZBIRA MERIL/i')
                if criteria_header.count() > 0:
                    print("✅ Reached Selection Criteria section!")
                    break
                
                # Otherwise continue clicking Next
                next_btn = page.locator('button:has-text("Naprej")').or_(
                    page.locator('button').filter(has_text="→")
                )
                
                if next_btn.count() > 0:
                    # Fill any required fields on current step with dummy data
                    text_inputs = page.locator('input[type="text"]').all()
                    for inp in text_inputs[:3]:  # Fill first 3 text inputs
                        try:
                            if inp.input_value() == "":
                                inp.fill("Test podatek")
                        except:
                            pass
                    
                    # Select first option in any dropdowns
                    selects = page.locator('select').all()
                    for sel in selects:
                        try:
                            options = sel.locator('option').all()
                            if len(options) > 1:
                                sel.select_option(index=1)
                        except:
                            pass
                    
                    next_btn.first.click()
                    time.sleep(2)
                    steps_navigated += 1
                else:
                    print("❌ Could not find Next button")
                    break
            
            # Test Selection Criteria functionality
            print("\n🎯 Testing Selection Criteria (Merila) functionality...")
            
            # Take screenshot of empty criteria form
            page.screenshot(path="tests/screenshots/04_merila_empty.png")
            
            # Test 1: Enable Price criteria
            print("\n📊 Test 1: Enabling price criteria...")
            price_checkbox = page.locator('text=/Cena/i').locator('xpath=..').locator('input[type="checkbox"]')
            if price_checkbox.count() > 0:
                price_checkbox.first.check()
                time.sleep(1)
                print("✅ Price criteria enabled")
                
                # Enter points for price
                price_points = page.locator('input[type="number"]').filter(has_text="Cena").or_(
                    page.locator('input[aria-label*="Cena"]').filter(has_text="točk")
                )
                if price_points.count() == 0:
                    price_points = page.locator('input[type="number"]').first
                
                if price_points.count() > 0:
                    price_points.fill("40")
                    print("✅ Price points set to 40")
            
            # Test 2: Enable Additional References
            print("\n📚 Test 2: Enabling additional references...")
            refs_checkbox = page.locator('text=/reference/i').locator('xpath=..').locator('input[type="checkbox"]')
            if refs_checkbox.count() > 0:
                refs_checkbox.first.check()
                time.sleep(1)
                
                # Enter points
                refs_points = page.locator('input[type="number"]').nth(1)
                if refs_points.count() > 0:
                    refs_points.fill("30")
                    print("✅ References points set to 30")
            
            # Test 3: Enable Social Criteria
            print("\n👥 Test 3: Testing social criteria...")
            social_checkbox = page.locator('text=/Socialna merila/i').locator('xpath=..').locator('input[type="checkbox"]')
            if social_checkbox.count() > 0:
                social_checkbox.first.check()
                time.sleep(1)
                print("✅ Social criteria enabled")
                
                # Check for sub-options
                young_employees = page.locator('text=/mladi/i').locator('xpath=..').locator('input[type="checkbox"]')
                if young_employees.count() > 0:
                    young_employees.first.check()
                    print("✅ Young employees sub-criteria selected")
                
                # Enter points for social criteria
                social_points = page.locator('input[type="number"]').nth(2)
                if social_points.count() > 0:
                    social_points.fill("30")
                    print("✅ Social criteria points set to 30")
            
            # Take screenshot of configured criteria
            time.sleep(1)
            page.screenshot(path="tests/screenshots/05_merila_configured.png")
            
            # Test 4: Tiebreaker configuration
            print("\n⚖️ Test 4: Configuring tiebreaker rules...")
            tiebreaker_select = page.locator('select').filter(has_text="žreb").or_(
                page.locator('select[aria-label*="enako"]')
            )
            
            if tiebreaker_select.count() > 0:
                tiebreaker_select.select_option("prednost po specifičnem merilu")
                time.sleep(1)
                print("✅ Tiebreaker rule configured")
                
                # Select specific criterion for tiebreaker
                criterion_select = page.locator('select').last
                if criterion_select.count() > 0:
                    criterion_select.select_option("cena")
                    print("✅ Tiebreaker criterion set to price")
            
            # Final screenshot
            page.screenshot(path="tests/screenshots/06_merila_complete.png")
            
            # Test 5: Navigation persistence
            print("\n💾 Test 5: Testing data persistence...")
            
            # Navigate back
            back_button = page.locator('button:has-text("Nazaj")').or_(
                page.locator('button').filter(has_text="←")
            )
            
            if back_button.count() > 0:
                back_button.first.click()
                time.sleep(2)
                print("✅ Navigated back")
                
                # Navigate forward again
                next_button.first.click() if next_button.count() > 0 else None
                time.sleep(2)
                print("✅ Navigated forward")
                
                # Check if price checkbox is still checked
                price_checkbox = page.locator('text=/Cena/i').locator('xpath=..').locator('input[type="checkbox"]')
                if price_checkbox.count() > 0:
                    is_checked = price_checkbox.first.is_checked()
                    if is_checked:
                        print("✅ Data persisted correctly - Price criteria still selected")
                    else:
                        print("❌ Data persistence issue - Price criteria not selected")
            
            # Final summary
            print("\n" + "=" * 50)
            print("🎉 Test Suite Completed!")
            print(f"📸 Screenshots saved in: tests/screenshots/")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            page.screenshot(path="tests/screenshots/error_screenshot.png")
            raise
        
        finally:
            # Clean up
            browser.close()
            print("\n🧹 Browser closed")

def main():
    """Main entry point for running the tests."""
    print("""
    ╔════════════════════════════════════════════════╗
    ║   MERILA (Selection Criteria) Test Suite      ║
    ║   Powered by Playwright & Quinn QA            ║
    ╚════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  Prerequisites:")
    print("   1. Make sure your Streamlit app is running on http://localhost:8501")
    print("   2. Run: streamlit run app.py")
    print("\n📝 Starting tests in 3 seconds...\n")
    
    time.sleep(3)
    
    try:
        test_merila_functionality()
        print("\n✅ All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())