"""CPV Criteria management module for database operations."""
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import database
import json
import os


def init_criteria_types():
    """Initialize default criteria types if they don't exist."""
    database.init_db()
    
    default_types = [
        ("Merila - cena", "Izberite kode, kjer cena ne sme biti edino merilo"),
        ("Merila - socialna merila", "Izberite kode, kjer veljajo socialna merila")
    ]
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        for name, description in default_types:
            cursor.execute('''
                INSERT OR IGNORE INTO criteria_types (name, description)
                VALUES (?, ?)
            ''', (name, description))
        
        conn.commit()


def get_criteria_types() -> List[Dict]:
    """Get all criteria types from database."""
    database.init_db()
    init_criteria_types()  # Ensure defaults exist
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, created_at
            FROM criteria_types
            ORDER BY id
        ''')
        
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3]
            }
            for row in rows
        ]


def get_criteria_type_by_name(name: str) -> Optional[Dict]:
    """Get a specific criteria type by name."""
    database.init_db()
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, created_at
            FROM criteria_types
            WHERE name = ?
        ''', (name,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3]
            }
        return None


def get_cpv_for_criteria(criteria_type_id: int) -> List[str]:
    """Get all CPV codes for a specific criteria type."""
    database.init_db()
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cpv_code
            FROM cpv_criteria
            WHERE criteria_type_id = ?
            ORDER BY cpv_code
        ''', (criteria_type_id,))
        
        return [row[0] for row in cursor.fetchall()]


def save_cpv_criteria(criteria_type_id: int, cpv_codes: List[str]) -> Dict:
    """
    Save CPV codes for a criteria type (replaces existing assignments).
    
    Args:
        criteria_type_id: ID of the criteria type
        cpv_codes: List of CPV codes to assign
    
    Returns:
        Dict with operation results
    """
    database.init_db()
    
    result = {
        'success': False,
        'added': 0,
        'removed': 0,
        'error': None
    }
    
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Get current assignments
            cursor.execute('''
                SELECT cpv_code FROM cpv_criteria
                WHERE criteria_type_id = ?
            ''', (criteria_type_id,))
            current_codes = set(row[0] for row in cursor.fetchall())
            
            new_codes = set(cpv_codes)
            
            # Codes to add
            to_add = new_codes - current_codes
            # Codes to remove
            to_remove = current_codes - new_codes
            
            # Remove codes that are no longer selected
            for code in to_remove:
                cursor.execute('''
                    DELETE FROM cpv_criteria
                    WHERE cpv_code = ? AND criteria_type_id = ?
                ''', (code, criteria_type_id))
                result['removed'] += 1
            
            # Add new codes
            now = datetime.now().isoformat()
            for code in to_add:
                # Verify CPV code exists
                cursor.execute('SELECT 1 FROM cpv_codes WHERE code = ?', (code,))
                if cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO cpv_criteria (cpv_code, criteria_type_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    ''', (code, criteria_type_id, now, now))
                    result['added'] += 1
            
            # Commit transaction
            conn.commit()
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
        if conn:
            conn.rollback()
    
    return result


def delete_cpv_criteria(criteria_type_id: int, cpv_code: str) -> bool:
    """
    Delete a specific CPV-criteria relationship.
    
    Args:
        criteria_type_id: ID of the criteria type
        cpv_code: CPV code to remove
    
    Returns:
        True if successful, False otherwise
    """
    database.init_db()
    
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM cpv_criteria
                WHERE cpv_code = ? AND criteria_type_id = ?
            ''', (cpv_code, criteria_type_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False


def get_criteria_for_cpv(cpv_code: str) -> List[Dict]:
    """
    Get all criteria types assigned to a specific CPV code.
    
    Args:
        cpv_code: CPV code to check
    
    Returns:
        List of criteria type dictionaries
    """
    database.init_db()
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ct.id, ct.name, ct.description
            FROM criteria_types ct
            JOIN cpv_criteria cc ON ct.id = cc.criteria_type_id
            WHERE cc.cpv_code = ?
            ORDER BY ct.id
        ''', (cpv_code,))
        
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2]
            }
            for row in rows
        ]


def has_criteria(cpv_code: str) -> bool:
    """
    Check if a CPV code has any criteria assigned.
    
    Args:
        cpv_code: CPV code to check
    
    Returns:
        True if code has criteria, False otherwise
    """
    database.init_db()
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM cpv_criteria
            WHERE cpv_code = ?
        ''', (cpv_code,))
        
        count = cursor.fetchone()[0]
        return count > 0


def migrate_from_json():
    """
    Migrate existing JSON-based criteria settings to database.
    
    Returns:
        Dict with migration results
    """
    result = {
        'success': False,
        'migrated_price': 0,
        'migrated_social': 0,
        'error': None
    }
    
    # Check for JSON file
    json_path = os.path.join('json_files', 'cpv_criteria_settings.json')
    
    if not os.path.exists(json_path):
        result['error'] = 'No JSON file to migrate'
        return result
    
    try:
        # Load JSON settings
        with open(json_path, 'r') as f:
            settings = json.load(f)
        
        # Initialize criteria types
        init_criteria_types()
        
        # Get criteria type IDs
        price_type = get_criteria_type_by_name("Merila - cena")
        social_type = get_criteria_type_by_name("Merila - socialna merila")
        
        if not price_type or not social_type:
            result['error'] = 'Failed to get criteria types'
            return result
        
        # Migrate price criteria
        if 'price_criteria' in settings and settings['price_criteria']:
            save_result = save_cpv_criteria(price_type['id'], settings['price_criteria'])
            result['migrated_price'] = save_result['added']
        
        # Migrate social criteria
        if 'social_criteria' in settings and settings['social_criteria']:
            save_result = save_cpv_criteria(social_type['id'], settings['social_criteria'])
            result['migrated_social'] = save_result['added']
        
        # Rename JSON file to backup
        backup_path = json_path + '.backup'
        os.rename(json_path, backup_path)
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def get_criteria_statistics() -> Dict:
    """
    Get statistics about criteria assignments.
    
    Returns:
        Dict with statistics
    """
    database.init_db()
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Total CPV codes with criteria
        cursor.execute('''
            SELECT COUNT(DISTINCT cpv_code)
            FROM cpv_criteria
        ''')
        total_with_criteria = cursor.fetchone()[0]
        
        # Count per criteria type
        cursor.execute('''
            SELECT ct.name, COUNT(cc.cpv_code) as count
            FROM criteria_types ct
            LEFT JOIN cpv_criteria cc ON ct.id = cc.criteria_type_id
            GROUP BY ct.id, ct.name
            ORDER BY ct.id
        ''')
        
        type_counts = {}
        for row in cursor.fetchall():
            type_counts[row[0]] = row[1]
        
        return {
            'total_cpv_with_criteria': total_with_criteria,
            'by_type': type_counts
        }