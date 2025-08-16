#!/usr/bin/env python3
"""Test script for logs table migration."""

import sqlite3
import json
from datetime import datetime, timedelta
import database
import config

def test_migration():
    """Test the logs table migration."""
    print("Testing logs table migration...")
    
    # Initialize database
    database.init_db()
    
    # Verify table exists
    assert database.verify_logs_table_exists(), "Logs table was not created"
    print("✓ Logs table created successfully")
    
    # Test table structure
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Check columns exist
        cursor.execute("PRAGMA table_info(application_logs)")
        columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            'id', 'timestamp', 'organization_id', 'organization_name',
            'session_id', 'log_level', 'module', 'function_name',
            'line_number', 'message', 'retention_hours', 'expires_at',
            'additional_context', 'log_type', 'created_at'
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"
        print("✓ All required columns exist")
        
        # Test inserting a log entry
        now = datetime.now()
        expires = database.calculate_expires_at(now, 24)
        
        cursor.execute("""
            INSERT INTO application_logs 
            (log_level, module, function_name, message, retention_hours, expires_at, log_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('INFO', 'test', 'test_migration', 'Test log entry', 24, expires, None))
        
        # Verify insertion
        cursor.execute("SELECT * FROM application_logs WHERE module = 'test'")
        row = cursor.fetchone()
        assert row is not None, "Failed to insert test log"
        print("✓ Successfully inserted test log entry")
        
        # Test log level constraint
        try:
            cursor.execute("""
                INSERT INTO application_logs (log_level, message, retention_hours)
                VALUES ('INVALID', 'Test', 24)
            """)
            assert False, "Should have failed with invalid log level"
        except sqlite3.IntegrityError:
            print("✓ Log level constraint working")
        
        # Test views
        cursor.execute("SELECT * FROM log_statistics")
        stats = cursor.fetchall()
        print(f"✓ log_statistics view working - {len(stats)} rows")
        
        cursor.execute("SELECT * FROM retention_summary")
        summary = cursor.fetchall()
        print(f"✓ retention_summary view working - {len(summary)} rows")
        
        # Test cleanup function
        # Insert expired log
        past = (datetime.now() - timedelta(days=2)).isoformat()
        cursor.execute("""
            INSERT INTO application_logs 
            (log_level, message, retention_hours, expires_at)
            VALUES (?, ?, ?, ?)
        """, ('DEBUG', 'Expired log', 6, past))
        conn.commit()
        
        # Run cleanup
        deleted = database.cleanup_expired_logs()
        print(f"✓ Cleanup function working - deleted {deleted} expired logs")
        
        # Test retention config
        assert 'DEBUG' in config.LOG_RETENTION_HOURS
        assert config.LOG_RETENTION_HOURS['ERROR'] == 168
        assert 'form_submission' in config.SPECIAL_LOG_RETENTION
        print("✓ Retention configuration loaded correctly")
    
    print("\n✅ All tests passed successfully!")
    return True

if __name__ == "__main__":
    test_migration()