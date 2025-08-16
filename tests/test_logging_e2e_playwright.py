#!/usr/bin/env python3
"""End-to-end test of logging system using Playwright with actual Streamlit app."""

import os
import sys
import sqlite3
import time
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


def test_logging_with_streamlit():
    """Test logging system with actual Streamlit app using Playwright."""
    print("\n" + "="*60)
    print("E2E LOGGING TEST WITH PLAYWRIGHT")
    print("="*60)
    
    # Start Streamlit app in background
    print("\n[1] Starting Streamlit app...")
    process = subprocess.Popen(
        ['streamlit', 'run', 'app.py', '--server.headless', 'true'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to start
    time.sleep(5)
    
    try:
        # Use Playwright to interact with the app
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            print("[2] Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("[3] Navigating to app...")
            page.goto("http://localhost:8501")
            
            # Wait for app to load
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            print("[4] Taking screenshot...")
            page.screenshot(path="tests/test_reports/logging_test_screenshot.png")
            
            # Check if any logs were created during startup
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                
                # Get recent logs
                cursor.execute("""
                    SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                    FROM application_logs
                    WHERE timestamp > datetime('now', '-1 minute')
                """)
                
                count, min_time, max_time = cursor.fetchone()
                
                if count and count > 0:
                    print(f"  ✓ {count} logs recorded during app startup")
                    print(f"    Time range: {min_time} to {max_time}")
                    
                    # Check log levels
                    cursor.execute("""
                        SELECT log_level, COUNT(*) 
                        FROM application_logs
                        WHERE timestamp > datetime('now', '-1 minute')
                        GROUP BY log_level
                    """)
                    
                    print("  Log levels:")
                    for level, cnt in cursor.fetchall():
                        print(f"    - {level}: {cnt}")
                else:
                    print("  ⚠ No logs recorded during startup")
            
            # Try to navigate to admin panel
            print("\n[5] Testing admin panel navigation...")
            
            # Look for admin link or button
            if page.locator("text=Admin").count() > 0:
                page.click("text=Admin")
                time.sleep(2)
                
                # Check for new logs
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM application_logs
                        WHERE timestamp > datetime('now', '-10 seconds')
                        AND message LIKE '%admin%'
                    """)
                    admin_logs = cursor.fetchone()[0]
                    
                    if admin_logs > 0:
                        print(f"  ✓ {admin_logs} admin-related logs recorded")
                    else:
                        print("  ⚠ No admin logs recorded")
            else:
                print("  ⚠ Admin panel not accessible")
            
            browser.close()
    
    finally:
        # Stop Streamlit app
        print("\n[6] Stopping Streamlit app...")
        process.terminate()
        process.wait()
    
    print("\n" + "="*60)
    print("E2E test completed")
    print("="*60)


if __name__ == "__main__":
    try:
        test_logging_with_streamlit()
    except ImportError:
        print("⚠ Playwright not installed. Install with: pip install playwright")
        print("  Then run: playwright install chromium")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)