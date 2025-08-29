#!/usr/bin/env python3
"""
One-time migration script to add password_hash column to organizacija table.
Run this script to update the existing database structure.
"""
import sqlite3
import sys

DATABASE_FILE = 'mainDB.db'

def migrate_database():
    """Add password_hash column to organizacija table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(organizacija)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'password_hash' not in columns:
            print("Adding password_hash column to organizacija table...")
            cursor.execute('ALTER TABLE organizacija ADD COLUMN password_hash TEXT')
            conn.commit()
            print("✅ Migration successful! password_hash column added.")
        else:
            print("✅ Column password_hash already exists. No migration needed.")
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        if "no such table: organizacija" in str(e):
            print("❌ Error: organizacija table doesn't exist.")
            print("Creating organizacija table with password_hash column...")
            try:
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS organizacija (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        naziv TEXT NOT NULL,
                        password_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                conn.close()
                print("✅ Table created successfully!")
                return True
            except Exception as create_error:
                print(f"❌ Failed to create table: {create_error}")
                return False
        else:
            print(f"❌ Database error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting database migration...")
    if migrate_database():
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)