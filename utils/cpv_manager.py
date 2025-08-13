"""CPV codes database management module."""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from database import DATABASE_FILE, init_db


def get_all_cpv_codes(search_term: str = "", page: int = 1, per_page: int = 50) -> Tuple[List[Dict], int]:
    """
    Get all CPV codes with optional search and pagination.
    
    Args:
        search_term: Search term for code or description
        page: Page number (1-based)
        per_page: Items per page
    
    Returns:
        Tuple of (list of CPV codes, total count)
    """
    init_db()
    offset = (page - 1) * per_page
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        if search_term:
            # Search in both code and description
            cursor.execute("""
                SELECT COUNT(*) FROM cpv_codes
                WHERE code LIKE ? OR description LIKE ?
            """, (f'%{search_term}%', f'%{search_term}%'))
            total_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT id, code, description, created_at, updated_at
                FROM cpv_codes
                WHERE code LIKE ? OR description LIKE ?
                ORDER BY code
                LIMIT ? OFFSET ?
            """, (f'%{search_term}%', f'%{search_term}%', per_page, offset))
        else:
            cursor.execute("SELECT COUNT(*) FROM cpv_codes")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT id, code, description, created_at, updated_at
                FROM cpv_codes
                ORDER BY code
                LIMIT ? OFFSET ?
            """, (per_page, offset))
        
        columns = [desc[0] for desc in cursor.description]
        cpv_codes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
    return cpv_codes, total_count


def get_cpv_by_id(cpv_id: int) -> Optional[Dict]:
    """Get a single CPV code by ID."""
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, code, description, created_at, updated_at
            FROM cpv_codes
            WHERE id = ?
        """, (cpv_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    return None


def get_cpv_by_code(code: str) -> Optional[Dict]:
    """Get a single CPV code by code."""
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, code, description, created_at, updated_at
            FROM cpv_codes
            WHERE code = ?
        """, (code,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    
    return None


def create_cpv_code(code: str, description: str) -> Optional[int]:
    """
    Create a new CPV code.
    
    Returns:
        ID of created record or None if duplicate
    """
    init_db()
    
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cpv_codes (code, description)
                VALUES (?, ?)
            """, (code, description))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Duplicate code
        return None


def update_cpv_code(cpv_id: int, code: str, description: str) -> bool:
    """
    Update an existing CPV code.
    
    Returns:
        True if updated, False if failed (e.g., duplicate code)
    """
    init_db()
    
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cpv_codes
                SET code = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, description, cpv_id))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        # Duplicate code
        return False


def delete_cpv_code(cpv_id: int) -> bool:
    """Delete a CPV code."""
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cpv_codes WHERE id = ?", (cpv_id,))
        conn.commit()
        return cursor.rowcount > 0


def bulk_insert_cpv_codes(cpv_list: List[Tuple[str, str]]) -> Dict[str, int]:
    """
    Bulk insert CPV codes.
    
    Args:
        cpv_list: List of tuples (code, description)
    
    Returns:
        Dictionary with counts: {'imported': n, 'skipped': m, 'failed': k}
    """
    init_db()
    results = {'imported': 0, 'skipped': 0, 'failed': 0}
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        for code, description in cpv_list:
            try:
                cursor.execute("""
                    INSERT INTO cpv_codes (code, description)
                    VALUES (?, ?)
                """, (code, description))
                results['imported'] += 1
            except sqlite3.IntegrityError:
                # Check if it's a duplicate
                cursor.execute("SELECT id FROM cpv_codes WHERE code = ?", (code,))
                if cursor.fetchone():
                    results['skipped'] += 1
                else:
                    results['failed'] += 1
            except Exception:
                results['failed'] += 1
        
        conn.commit()
    
    return results


def get_cpv_codes_for_dropdown() -> List[Dict[str, str]]:
    """
    Get all CPV codes formatted for dropdown display.
    
    Returns:
        List of dicts with 'value' (code) and 'display' (code - description)
    """
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, description
            FROM cpv_codes
            ORDER BY code
        """)
        
        return [
            {
                'value': code,
                'display': f"{code} - {description}"
            }
            for code, description in cursor.fetchall()
        ]


def search_cpv_codes(search_term: str, limit: int = 20) -> List[Dict]:
    """
    Search CPV codes for autocomplete.
    
    Args:
        search_term: Term to search in code or description
        limit: Maximum number of results
    
    Returns:
        List of matching CPV codes
    """
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, description
            FROM cpv_codes
            WHERE code LIKE ? OR description LIKE ?
            ORDER BY 
                CASE 
                    WHEN code LIKE ? THEN 1
                    WHEN code LIKE ? THEN 2
                    ELSE 3
                END,
                code
            LIMIT ?
        """, (f'%{search_term}%', f'%{search_term}%', 
              f'{search_term}%', f'%{search_term}%', limit))
        
        return [
            {
                'code': code,
                'description': description,
                'display': f"{code} - {description}"
            }
            for code, description in cursor.fetchall()
        ]


def get_cpv_count() -> int:
    """Get total count of CPV codes in database."""
    init_db()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cpv_codes")
        return cursor.fetchone()[0]