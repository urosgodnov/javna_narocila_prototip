#!/usr/bin/env python3
"""
Set test CPV code in the database for a procurement.
"""

import sqlite3
import json
import database

def set_test_cpv():
    """Create a test procurement with CPV code 50700000-2."""
    database.init_db()
    
    # Create test form data with CPV code
    form_data = {
        'orderType': {
            'type': 'storitve',
            'cpvCodes': '50700000-2 - Repair and maintenance services of building installations'
        },
        'projectInfo': {
            'projectName': 'Test naročilo za CPV validacijo'
        }
    }
    
    # Save as a draft
    draft_id = database.save_draft(form_data)
    print(f"Created draft with ID: {draft_id}")
    print(f"CPV code set: 50700000-2")
    print("You can now load this draft in the app and test validation on step 13")
    
    return draft_id

if __name__ == "__main__":
    draft_id = set_test_cpv()