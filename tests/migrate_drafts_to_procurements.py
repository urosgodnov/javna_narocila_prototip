#!/usr/bin/env python3
"""
Migration script to convert drafts to procurements.
This script migrates all existing drafts to the procurements table
with status 'Delno izpolnjeno'.
"""

import sqlite3
import json
from datetime import datetime

DATABASE_FILE = 'mainDB.db'

def migrate_drafts():
    """Migrate all drafts to procurements table."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check if drafts table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='drafts'
    """)
    
    if not cursor.fetchone():
        print("No drafts table found - nothing to migrate")
        return
    
    # Get all drafts
    cursor.execute("SELECT id, timestamp, form_data_json FROM drafts")
    drafts = cursor.fetchall()
    
    if not drafts:
        print("No drafts found to migrate")
        return
    
    print(f"Found {len(drafts)} drafts to migrate")
    
    migrated = 0
    for draft_id, timestamp, form_data_json in drafts:
        try:
            # Parse form data
            form_data = json.loads(form_data_json)
            
            # Extract key fields
            naziv = form_data.get('projectInfo', {}).get('projectName', f'Osnutek {draft_id}')
            vrsta = form_data.get('orderType', {}).get('type', '')
            postopek = form_data.get('submissionProcedure', {}).get('procedure', '')
            vrednost = form_data.get('orderType', {}).get('estimatedValue', 0)
            
            # Check if this draft already exists as procurement
            cursor.execute("""
                SELECT id FROM javna_narocila 
                WHERE form_data_json = ? 
                LIMIT 1
            """, (form_data_json,))
            
            if cursor.fetchone():
                print(f"  Draft {draft_id} already exists as procurement - skipping")
                continue
            
            # Insert as procurement with "Delno izpolnjeno" status
            cursor.execute("""
                INSERT INTO javna_narocila (
                    organizacija, naziv, vrsta, postopek, 
                    datum_objave, status, vrednost, form_data_json,
                    zadnja_sprememba, uporabnik
                ) VALUES (?, ?, ?, ?, date('now'), ?, ?, ?, ?, ?)
            """, ('demo_organizacija', naziv, vrsta, postopek, 
                  'Delno izpolnjeno', vrednost, form_data_json, 
                  timestamp, 'migration'))
            
            migrated += 1
            print(f"  Migrated draft {draft_id} -> procurement {cursor.lastrowid}")
            
        except Exception as e:
            print(f"  Error migrating draft {draft_id}: {e}")
    
    conn.commit()
    print(f"\nSuccessfully migrated {migrated} drafts to procurements")
    
    # Optionally rename drafts table to keep backup
    if migrated > 0:
        cursor.execute("ALTER TABLE drafts RENAME TO drafts_backup")
        print("Drafts table renamed to drafts_backup for safety")
    
    conn.close()

if __name__ == "__main__":
    print("Starting draft to procurement migration...")
    migrate_drafts()
    print("Migration complete!")