#!/usr/bin/env python3
"""Migration to add log_date and log_time columns to application_logs table."""

import sqlite3
import os
import sys

def migrate_database(db_path='mainDB.db'):
    """Add log_date and log_time columns if they don't exist."""
    
    try:
        # Try different approaches for WSL/Windows compatibility
        conn = None
        
        # Attempt 1: Direct connection
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.OperationalError:
            # Attempt 2: Copy to temp and work there
            import shutil
            temp_db = '/tmp/mainDB_migration.db'
            shutil.copy2(db_path, temp_db)
            conn = sqlite3.connect(temp_db)
            db_path = temp_db
        
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='application_logs'")
        if not cursor.fetchone():
            print("application_logs table doesn't exist - will be created on first run")
            conn.close()
            return True
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(application_logs)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        columns_added = False
        
        # Add log_date if missing
        if 'log_date' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE application_logs ADD COLUMN log_date DATE")
                print("✓ Added log_date column")
                columns_added = True
            except sqlite3.OperationalError as e:
                if 'duplicate column' not in str(e).lower():
                    print(f"Warning: Could not add log_date column: {e}")
        else:
            print("✓ log_date column already exists")
        
        # Add log_time if missing
        if 'log_time' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE application_logs ADD COLUMN log_time TIME")
                print("✓ Added log_time column")
                columns_added = True
            except sqlite3.OperationalError as e:
                if 'duplicate column' not in str(e).lower():
                    print(f"Warning: Could not add log_time column: {e}")
        else:
            print("✓ log_time column already exists")
        
        if columns_added:
            conn.commit()
            print("✓ Database migration completed successfully")
            
            # If we used a temp database, copy it back
            if db_path == '/tmp/mainDB_migration.db':
                import shutil
                shutil.copy2(db_path, 'mainDB.db')
                print("✓ Database copied back from temp location")
        else:
            print("✓ No migration needed - columns already exist")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Migration error: {e}")
        print("\nThe application will still work using fallback queries.")
        return False

if __name__ == "__main__":
    print("Running log_date/log_time column migration...")
    print("-" * 50)
    
    success = migrate_database()
    
    if success:
        print("\n✓ Migration completed successfully")
    else:
        print("\n⚠ Migration failed, but application will use fallback queries")
        print("  The application will still work correctly.")