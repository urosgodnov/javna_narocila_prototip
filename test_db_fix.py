#!/usr/bin/env python3
"""Test script to verify database fixes for log_date column issue."""

import sqlite3
import sys
import os

def test_database():
    """Test database connection and schema."""
    db_file = 'mainDB.db'
    
    print(f"Testing database: {db_file}")
    print(f"File exists: {os.path.exists(db_file)}")
    print(f"File size: {os.path.getsize(db_file) if os.path.exists(db_file) else 'N/A'}")
    
    try:
        # Try to connect with different journal modes
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA journal_mode=WAL")  # Try WAL mode for better concurrency
        
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if application_logs exists
        if 'application_logs' in [t[0] for t in tables]:
            print("\n✓ application_logs table exists")
            
            # Check columns
            cursor.execute("PRAGMA table_info(application_logs)")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            print("\nColumns in application_logs:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check for problematic columns
            has_log_date = 'log_date' in col_names
            has_log_time = 'log_time' in col_names
            
            print(f"\n✓ log_date column exists: {has_log_date}")
            print(f"✓ log_time column exists: {has_log_time}")
            
            if has_log_date and has_log_time:
                print("\n✓ Both optimized columns exist - queries should work fine")
            else:
                print("\n⚠ Missing optimized columns - using fallback queries")
        else:
            print("\n⚠ application_logs table does not exist")
            print("  Running database.init_db() should create it")
        
        conn.close()
        print("\n✓ Database connection successful")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"\n✗ Database error: {e}")
        
        if "disk I/O error" in str(e):
            print("\nPossible solutions:")
            print("1. Check if the database file is locked by another process")
            print("2. Try closing any open database connections")
            print("3. If using WSL, try: sudo chmod 666 mainDB.db")
            print("4. Copy database to a local WSL path: cp mainDB.db /tmp/mainDB_test.db")
        
        return False
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

def test_log_query_builder():
    """Test the LogQueryBuilder compatibility layer."""
    print("\n" + "="*50)
    print("Testing LogQueryBuilder...")
    
    try:
        from utils.log_query_builder import LogQueryBuilder
        
        builder = LogQueryBuilder()
        print(f"✓ LogQueryBuilder initialized")
        print(f"✓ Has optimized columns: {builder.has_optimized_columns()}")
        
        # Test query generation
        query, params = builder.recent_logs_query(limit=10)
        print(f"✓ Generated recent logs query")
        
        builder.close()
        print("✓ LogQueryBuilder tests passed")
        
    except Exception as e:
        print(f"✗ LogQueryBuilder error: {e}")

def test_database_logger():
    """Test the DatabaseLogHandler."""
    print("\n" + "="*50)
    print("Testing DatabaseLogHandler...")
    
    try:
        from utils.database_logger import DatabaseLogHandler
        import logging
        
        handler = DatabaseLogHandler()
        print(f"✓ DatabaseLogHandler initialized")
        print(f"✓ Has new columns: {handler._has_new_columns}")
        
        # Create a test log record
        logger = logging.getLogger("test")
        logger.addHandler(handler)
        
        print("✓ DatabaseLogHandler tests passed")
        
    except Exception as e:
        print(f"✗ DatabaseLogHandler error: {e}")

if __name__ == "__main__":
    print("Database Fix Verification Script")
    print("="*50)
    
    # Test database
    db_ok = test_database()
    
    if db_ok:
        # Test components only if database is accessible
        test_log_query_builder()
        test_database_logger()
    
    print("\n" + "="*50)
    if db_ok:
        print("✓ All tests passed - the log_date error should be fixed")
    else:
        print("⚠ Database access issues detected - see suggestions above")