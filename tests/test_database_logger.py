#!/usr/bin/env python3
"""Test script for DatabaseLogHandler."""

import logging
import sqlite3
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Add utils to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import config
from utils.database_logger import DatabaseLogHandler, configure_database_logging


def test_database_logger():
    """Test the DatabaseLogHandler implementation."""
    print("Testing DatabaseLogHandler...")
    
    # Initialize database
    database.init_db()
    
    # Configure logging with database handler
    logger = configure_database_logging('test_logger', logging.DEBUG)
    
    print("✓ Logger configured with DatabaseLogHandler")
    
    # Test 1: Basic logging at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # Verify logs were inserted
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM application_logs WHERE module = 'test_database_logger'")
        count = cursor.fetchone()[0]
        assert count >= 5, f"Expected at least 5 logs, got {count}"
        print(f"✓ Basic logging working - {count} logs inserted")
        
        # Test 2: Verify retention hours
        cursor.execute("""
            SELECT log_level, retention_hours 
            FROM application_logs 
            WHERE module = 'test_database_logger'
            ORDER BY id DESC LIMIT 5
        """)
        for row in cursor.fetchall():
            level, hours = row
            expected = config.LOG_RETENTION_HOURS.get(level, 24)
            assert hours == expected, f"Wrong retention for {level}: {hours} != {expected}"
        print("✓ Retention hours correctly set by log level")
        
        # Test 3: Special log type retention
        logger.info("Form submission", extra={'log_type': 'form_submission'})
        
        cursor.execute("""
            SELECT retention_hours 
            FROM application_logs 
            WHERE log_type = 'form_submission'
            ORDER BY id DESC LIMIT 1
        """)
        special_retention = cursor.fetchone()[0]
        assert special_retention == 720, f"Expected 720 hours for form_submission, got {special_retention}"
        print("✓ Special log type retention working")
        
        # Test 4: Verify expires_at calculation
        cursor.execute("""
            SELECT timestamp, retention_hours, expires_at 
            FROM application_logs 
            WHERE module = 'test_database_logger'
            ORDER BY id DESC LIMIT 1
        """)
        timestamp_str, retention, expires_str = cursor.fetchone()
        timestamp = datetime.fromisoformat(timestamp_str)
        expires = datetime.fromisoformat(expires_str)
        expected_expires = timestamp + timedelta(hours=retention)
        
        # Allow 1 minute difference for processing time
        diff = abs((expires - expected_expires).total_seconds())
        assert diff < 60, f"Expires_at calculation off by {diff} seconds"
        print("✓ Expires_at timestamp correctly calculated")
        
    # Test 5: Exception logging
    try:
        raise ValueError("Test exception")
    except ValueError:
        logger.exception("Exception occurred")
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT additional_context 
            FROM application_logs 
            WHERE message LIKE '%Exception occurred%'
            ORDER BY id DESC LIMIT 1
        """)
        context_json = cursor.fetchone()[0]
        assert context_json is not None, "Exception context not stored"
        context = json.loads(context_json)
        assert 'exception' in context, "Exception details not in context"
        print("✓ Exception logging with context working")
    
    # Test 6: Performance test
    start = time.time()
    for i in range(100):
        logger.info(f"Performance test {i}")
    elapsed = time.time() - start
    per_log = (elapsed / 100) * 1000  # Convert to ms
    
    print(f"✓ Performance test: {per_log:.2f}ms per log entry")
    assert per_log < 10, f"Performance too slow: {per_log:.2f}ms per log"
    
    # Test 7: Simulate Streamlit session state
    try:
        import streamlit as st
        st.session_state['organization_id'] = 42
        st.session_state['organization_name'] = 'Test Org'
        st.session_state['session_id'] = 'test-session-123'
        
        logger.info("Message with org context")
        
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT organization_id, organization_name, session_id
                FROM application_logs 
                WHERE message = 'Message with org context'
                ORDER BY id DESC LIMIT 1
            """)
            org_id, org_name, session_id = cursor.fetchone()
            assert org_id == 42, f"Organization ID not captured: {org_id}"
            assert org_name == 'Test Org', f"Organization name not captured: {org_name}"
            assert session_id == 'test-session-123', f"Session ID not captured: {session_id}"
            print("✓ Streamlit session context captured")
    except ImportError:
        print("⚠ Streamlit not installed - skipping session context test")
    
    print("\n✅ All DatabaseLogHandler tests passed!")
    return True


def test_fallback_logging():
    """Test fallback to file logging when database fails."""
    print("\nTesting fallback logging...")
    
    # Create handler with invalid database
    handler = DatabaseLogHandler(
        db_connection=None,
        fallback_file='logs/test_fallback.log'
    )
    
    # Create logger with our handler
    logger = logging.getLogger('fallback_test')
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Temporarily break the database
    original_file = database.DATABASE_FILE
    database.DATABASE_FILE = '/invalid/path/to/database.db'
    
    # Try to log (should fallback to file)
    logger.error("This should go to fallback file")
    
    # Restore database file
    database.DATABASE_FILE = original_file
    
    # Check fallback file exists and contains our message
    assert os.path.exists('logs/test_fallback.log'), "Fallback file not created"
    
    with open('logs/test_fallback.log', 'r') as f:
        content = f.read()
        assert "This should go to fallback file" in content, "Message not in fallback file"
    
    print("✓ Fallback to file logging working")
    
    # Cleanup
    os.remove('logs/test_fallback.log')
    
    return True


if __name__ == "__main__":
    test_database_logger()
    test_fallback_logging()
    print("\n🎉 All tests completed successfully!")