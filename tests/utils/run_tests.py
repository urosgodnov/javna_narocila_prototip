#!/usr/bin/env python3
"""Simple test runner for all test files in the tests directory."""

import os
import sys
import glob
import subprocess
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check for common success indicators
        if result.returncode == 0:
            if "FAIL" not in result.stdout and "ERROR" not in result.stdout:
                print(f"✅ {test_file} - PASSED")
                return True
        
        print(f"❌ {test_file} - FAILED")
        return False
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ {test_file} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {test_file} - ERROR: {e}")
        return False

def main():
    """Run all test files in the tests directory."""
    print("🧪 Running all tests in tests/ directory...")
    print("="*60)
    
    # Find all test files (we're now in the tests directory)
    test_files = glob.glob("test_*.py")
    test_files.extend(glob.glob("validate_*.py"))
    test_files.sort()
    
    if not test_files:
        print("No test files found in tests/ directory")
        return 1
    
    print(f"Found {len(test_files)} test files")
    
    # Run each test
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test_file(test_file):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())