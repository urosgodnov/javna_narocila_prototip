#!/usr/bin/env python3
"""Comprehensive test of the logging system using Playwright."""

import os
import sys
import sqlite3
import time
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import config
from utils.database_logger import DatabaseLogHandler


def test_logging_infrastructure():
    """Test the complete logging infrastructure."""
    print("\n" + "="*60)
    print("LOGGING SYSTEM QA REVIEW")
    print("="*60)
    
    results = {
        'database_structure': {'passed': 0, 'failed': 0, 'issues': []},
        'log_handler': {'passed': 0, 'failed': 0, 'issues': []},
        'retention_policy': {'passed': 0, 'failed': 0, 'issues': []},
        'performance': {'passed': 0, 'failed': 0, 'issues': []},
        'integration': {'passed': 0, 'failed': 0, 'issues': []}
    }
    
    # ========== TEST 1: Database Structure ==========
    print("\n[1] Testing Database Structure...")
    
    # Check table exists
    database.init_db()
    if database.verify_logs_table_exists():
        results['database_structure']['passed'] += 1
        print("  ✓ application_logs table exists")
    else:
        results['database_structure']['failed'] += 1
        results['database_structure']['issues'].append("Table does not exist")
        print("  ✗ application_logs table missing")
    
    # Verify columns
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(application_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = {
            'id': 'INTEGER',
            'timestamp': 'DATETIME',
            'organization_id': 'INTEGER',
            'organization_name': 'TEXT',
            'session_id': 'TEXT',
            'log_level': 'TEXT',
            'module': 'TEXT',
            'function_name': 'TEXT',
            'line_number': 'INTEGER',
            'message': 'TEXT',
            'retention_hours': 'INTEGER',
            'expires_at': 'DATETIME',
            'additional_context': 'TEXT',
            'log_type': 'TEXT'
        }
        
        for col_name, expected_type in required_columns.items():
            if col_name in columns:
                results['database_structure']['passed'] += 1
                print(f"  ✓ Column {col_name} exists")
            else:
                results['database_structure']['failed'] += 1
                results['database_structure']['issues'].append(f"Missing column: {col_name}")
                print(f"  ✗ Column {col_name} missing")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='application_logs'")
        indexes = {row[0] for row in cursor.fetchall()}
        
        required_indexes = [
            'idx_logs_expires',
            'idx_logs_timestamp', 
            'idx_logs_org_level',
            'idx_logs_level',
            'idx_logs_type'
        ]
        
        for idx_name in required_indexes:
            if idx_name in indexes:
                results['database_structure']['passed'] += 1
                print(f"  ✓ Index {idx_name} exists")
            else:
                results['database_structure']['failed'] += 1
                results['database_structure']['issues'].append(f"Missing index: {idx_name}")
                print(f"  ✗ Index {idx_name} missing")
        
        # Check views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = {row[0] for row in cursor.fetchall()}
        
        if 'log_statistics' in views:
            results['database_structure']['passed'] += 1
            print("  ✓ View log_statistics exists")
        else:
            results['database_structure']['failed'] += 1
            results['database_structure']['issues'].append("Missing view: log_statistics")
            print("  ✗ View log_statistics missing")
        
        if 'retention_summary' in views:
            results['database_structure']['passed'] += 1
            print("  ✓ View retention_summary exists")
        else:
            results['database_structure']['failed'] += 1
            results['database_structure']['issues'].append("Missing view: retention_summary")
            print("  ✗ View retention_summary missing")
    
    # ========== TEST 2: DatabaseLogHandler ==========
    print("\n[2] Testing DatabaseLogHandler...")
    
    import logging
    from utils.database_logger import configure_database_logging
    
    # Configure logger
    test_logger = configure_database_logging('qa_test', logging.DEBUG)
    
    # Test different log levels
    test_messages = {
        'DEBUG': ('Debug test message', 6),
        'INFO': ('Info test message', 24),
        'WARNING': ('Warning test message', 72),
        'ERROR': ('Error test message', 168),
        'CRITICAL': ('Critical test message', 720)
    }
    
    for level, (message, expected_hours) in test_messages.items():
        getattr(test_logger, level.lower())(message)
    
    # Verify logs were stored
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        for level, (message, expected_hours) in test_messages.items():
            cursor.execute("""
                SELECT retention_hours, expires_at, timestamp
                FROM application_logs 
                WHERE log_level = ? AND message LIKE ?
                ORDER BY id DESC LIMIT 1
            """, (level, f"%{message}%"))
            
            row = cursor.fetchone()
            if row:
                retention, expires_str, timestamp_str = row
                
                # Check retention hours
                if retention == expected_hours:
                    results['log_handler']['passed'] += 1
                    print(f"  ✓ {level} retention: {retention} hours")
                else:
                    results['log_handler']['failed'] += 1
                    results['log_handler']['issues'].append(
                        f"{level} wrong retention: {retention} != {expected_hours}"
                    )
                    print(f"  ✗ {level} wrong retention: {retention} != {expected_hours}")
                
                # Verify expires_at calculation
                timestamp = datetime.fromisoformat(timestamp_str)
                expires = datetime.fromisoformat(expires_str)
                expected_expires = timestamp + timedelta(hours=retention)
                
                diff = abs((expires - expected_expires).total_seconds())
                if diff < 60:  # Allow 1 minute tolerance
                    results['log_handler']['passed'] += 1
                    print(f"  ✓ {level} expires_at correct")
                else:
                    results['log_handler']['failed'] += 1
                    results['log_handler']['issues'].append(
                        f"{level} expires_at wrong by {diff} seconds"
                    )
                    print(f"  ✗ {level} expires_at wrong")
            else:
                results['log_handler']['failed'] += 1
                results['log_handler']['issues'].append(f"{level} log not found")
                print(f"  ✗ {level} log not found")
    
    # ========== TEST 3: Retention Policy ==========
    print("\n[3] Testing Retention Policy...")
    
    # Check config values
    if hasattr(config, 'LOG_RETENTION_HOURS'):
        results['retention_policy']['passed'] += 1
        print("  ✓ LOG_RETENTION_HOURS configured")
        
        expected_retention = {
            'CRITICAL': 720,
            'ERROR': 168,
            'WARNING': 72,
            'INFO': 24,
            'DEBUG': 6
        }
        
        for level, hours in expected_retention.items():
            if config.LOG_RETENTION_HOURS.get(level) == hours:
                results['retention_policy']['passed'] += 1
                print(f"  ✓ {level}: {hours} hours")
            else:
                results['retention_policy']['failed'] += 1
                actual = config.LOG_RETENTION_HOURS.get(level, 'not set')
                results['retention_policy']['issues'].append(
                    f"{level} retention: {actual} != {hours}"
                )
                print(f"  ✗ {level}: {actual} != {hours}")
    else:
        results['retention_policy']['failed'] += 1
        results['retention_policy']['issues'].append("LOG_RETENTION_HOURS not configured")
        print("  ✗ LOG_RETENTION_HOURS not configured")
    
    # Test special log types
    if hasattr(config, 'SPECIAL_LOG_RETENTION'):
        results['retention_policy']['passed'] += 1
        print("  ✓ SPECIAL_LOG_RETENTION configured")
        
        # Test special log type
        test_logger.info("Form submission test", extra={'log_type': 'form_submission'})
        
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT retention_hours 
                FROM application_logs 
                WHERE log_type = 'form_submission'
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row and row[0] == 720:
                results['retention_policy']['passed'] += 1
                print("  ✓ Special log type retention working")
            else:
                results['retention_policy']['failed'] += 1
                results['retention_policy']['issues'].append("Special log type retention not working")
                print("  ✗ Special log type retention not working")
    else:
        results['retention_policy']['failed'] += 1
        results['retention_policy']['issues'].append("SPECIAL_LOG_RETENTION not configured")
        print("  ✗ SPECIAL_LOG_RETENTION not configured")
    
    # Test cleanup function
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Insert expired log
        past = (datetime.now() - timedelta(days=2)).isoformat()
        cursor.execute("""
            INSERT INTO application_logs 
            (log_level, message, retention_hours, expires_at)
            VALUES (?, ?, ?, ?)
        """, ('DEBUG', 'Expired test log', 6, past))
        expired_id = cursor.lastrowid
        conn.commit()
        
        # Run cleanup
        deleted = database.cleanup_expired_logs()
        
        # Verify deletion
        cursor.execute("SELECT id FROM application_logs WHERE id = ?", (expired_id,))
        if cursor.fetchone() is None:
            results['retention_policy']['passed'] += 1
            print(f"  ✓ Cleanup function deleted {deleted} expired logs")
        else:
            results['retention_policy']['failed'] += 1
            results['retention_policy']['issues'].append("Cleanup function not working")
            print("  ✗ Cleanup function not working")
    
    # ========== TEST 4: Performance ==========
    print("\n[4] Testing Performance...")
    
    start = time.time()
    for i in range(100):
        test_logger.info(f"Performance test {i}")
    elapsed = time.time() - start
    per_log = (elapsed / 100) * 1000  # ms
    
    if per_log < 10:  # Should be under 10ms per log
        results['performance']['passed'] += 1
        print(f"  ✓ Performance: {per_log:.2f}ms per log (target < 10ms)")
    else:
        results['performance']['failed'] += 1
        results['performance']['issues'].append(f"Slow: {per_log:.2f}ms per log")
        print(f"  ✗ Performance: {per_log:.2f}ms per log (target < 10ms)")
    
    # ========== TEST 5: Integration ==========
    print("\n[5] Testing Integration with App...")
    
    # Check if logging is configured in app.py
    with open('app.py', 'r') as f:
        app_content = f.read()
        
        if 'from utils.database_logger import configure_database_logging' in app_content:
            results['integration']['passed'] += 1
            print("  ✓ DatabaseLogger imported in app.py")
        else:
            results['integration']['failed'] += 1
            results['integration']['issues'].append("DatabaseLogger not imported")
            print("  ✗ DatabaseLogger not imported in app.py")
        
        if 'configure_database_logging' in app_content:
            results['integration']['passed'] += 1
            print("  ✓ Logging configured in app.py")
        else:
            results['integration']['failed'] += 1
            results['integration']['issues'].append("Logging not configured")
            print("  ✗ Logging not configured in app.py")
    
    # Check fallback logging
    handler = DatabaseLogHandler(fallback_file='logs/test_qa_fallback.log')
    if os.path.exists('logs/test_qa_fallback.log'):
        os.remove('logs/test_qa_fallback.log')
    
    # ========== SUMMARY ==========
    print("\n" + "="*60)
    print("QA REVIEW SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for category, stats in results.items():
        passed = stats['passed']
        failed = stats['failed']
        total_passed += passed
        total_failed += failed
        
        status = "✓ PASS" if failed == 0 else "✗ FAIL"
        print(f"\n{category.replace('_', ' ').title()}: {status}")
        print(f"  Passed: {passed}, Failed: {failed}")
        
        if stats['issues']:
            print("  Issues:")
            for issue in stats['issues']:
                print(f"    - {issue}")
    
    print("\n" + "="*60)
    print(f"OVERALL: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("✅ ALL TESTS PASSED - Logging system is production ready!")
    else:
        print("❌ TESTS FAILED - Issues need to be addressed")
    
    print("="*60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = test_logging_infrastructure()
    sys.exit(0 if success else 1)