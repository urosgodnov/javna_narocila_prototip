#!/usr/bin/env python3
"""Test that the Streamlit app starts without errors."""

import sys
import os
import time
import subprocess
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_app_startup():
    """Test that the app can start without errors."""
    print("Testing app startup...")
    
    # Start the app in a subprocess
    process = None
    try:
        # Start streamlit app
        process = subprocess.Popen(
            ["streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8502"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process terminated
            stdout, stderr = process.communicate()
            print(f"❌ App failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        
        print("✓ App started successfully")
        
        # Test is successful if app started
        return True
        
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return False
        
    finally:
        # Clean up - terminate the process
        if process and process.poll() is None:
            print("Stopping app...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def test_imports_in_app():
    """Test that app.py can be imported without errors."""
    print("\nTesting app imports...")
    
    try:
        # This will fail if there are syntax errors or missing imports
        import app
        print("✓ app.py imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import app.py: {e}")
        return False


def main():
    """Run startup tests."""
    print("=" * 50)
    print("App Startup Tests")
    print("=" * 50)
    
    # First test imports
    if not test_imports_in_app():
        print("\n❌ Import test failed")
        sys.exit(1)
    
    # Then test actual startup
    if not test_app_startup():
        print("\n❌ Startup test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All startup tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()