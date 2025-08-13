"""CPV data migration module."""
import sqlite3
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
from utils.cpv_manager import get_cpv_codes_for_dropdown, search_cpv_codes

def parse_legacy_cpv_text(text: str) -> List[str]:
    """
    Parse legacy CPV text formats.
    
    Handles formats like:
    - "30192000-1, 45000000-7"
    - "30192000-1 - Office supplies, 45000000-7 - Construction"
    - "Office supplies (30192000-1)"
    
    Args:
        text: Legacy CPV text
    
    Returns:
        List of extracted CPV codes
    """
    if not text:
        return []
    
    codes = []
    
    # Pattern 1: Direct CPV codes (XXXXXXXX-X)
    pattern1 = r'\b(\d{8}-\d)\b'
    matches = re.findall(pattern1, text)
    codes.extend(matches)
    
    # Pattern 2: CPV codes without dash (XXXXXXXXX)
    pattern2 = r'\b(\d{9})\b'
    for match in re.findall(pattern2, text):
        # Add dash format
        codes.append(f"{match[:8]}-{match[8]}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_codes = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)
    
    return unique_codes


def match_cpv_by_description(text: str) -> List[str]:
    """
    Try to match CPV codes by description text.
    
    Args:
        text: Text that might contain CPV descriptions
    
    Returns:
        List of matched CPV codes
    """
    if not text:
        return []
    
    matched_codes = []
    
    # Try to search for matching descriptions
    # Split by common delimiters
    parts = re.split(r'[,;|]', text)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Skip if it's already a CPV code
        if re.match(r'^\d{8}-\d$', part):
            continue
        
        # Search for matching CPV codes by description
        results = search_cpv_codes(part, limit=1)
        if results:
            matched_codes.append(results[0]['code'])
    
    return matched_codes


def migrate_procurement_cpv_data(conn: sqlite3.Connection) -> Dict[str, any]:
    """
    Migrate CPV data for all procurements.
    
    Args:
        conn: SQLite database connection
    
    Returns:
        Migration report dictionary
    """
    report = {
        'start_time': datetime.now().isoformat(),
        'total_processed': 0,
        'successful_migrations': 0,
        'partial_migrations': 0,
        'failed_migrations': 0,
        'codes_found': 0,
        'codes_matched': 0,
        'details': []
    }
    
    cursor = conn.cursor()
    
    try:
        # Add migration columns if they don't exist
        cursor.execute("""
            SELECT COUNT(*) FROM pragma_table_info('javna_narocila') 
            WHERE name='cpv_codes_structured'
        """)
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE javna_narocila 
                ADD COLUMN cpv_codes_structured TEXT
            """)
            cursor.execute("""
                ALTER TABLE javna_narocila 
                ADD COLUMN cpv_codes_legacy TEXT
            """)
            cursor.execute("""
                ALTER TABLE javna_narocila 
                ADD COLUMN cpv_migration_status TEXT
            """)
            cursor.execute("""
                ALTER TABLE javna_narocila 
                ADD COLUMN cpv_migration_timestamp TEXT
            """)
        
        # Get all procurements with CPV data
        cursor.execute("""
            SELECT id, form_data_json 
            FROM javna_narocila 
            WHERE form_data_json IS NOT NULL
        """)
        
        procurements = cursor.fetchall()
        
        for proc_id, form_data_json in procurements:
            report['total_processed'] += 1
            
            try:
                form_data = json.loads(form_data_json) if form_data_json else {}
                
                # Extract CPV text from various possible locations
                cpv_text = ""
                if 'projectInfo' in form_data and 'cpvCodes' in form_data['projectInfo']:
                    cpv_text = form_data['projectInfo']['cpvCodes']
                elif 'cpvCodes' in form_data:
                    cpv_text = form_data['cpvCodes']
                
                if not cpv_text:
                    continue
                
                # Parse CPV codes
                parsed_codes = parse_legacy_cpv_text(cpv_text)
                report['codes_found'] += len(parsed_codes)
                
                # Try to match by description if no codes found
                if not parsed_codes:
                    parsed_codes = match_cpv_by_description(cpv_text)
                    report['codes_matched'] += len(parsed_codes)
                
                # Validate codes against database
                valid_codes = []
                invalid_text = []
                
                cpv_options = get_cpv_codes_for_dropdown()
                valid_code_set = {opt['value'] for opt in cpv_options}
                
                for code in parsed_codes:
                    if code in valid_code_set:
                        valid_codes.append(code)
                    else:
                        invalid_text.append(code)
                
                # Store migration results
                if valid_codes:
                    cursor.execute("""
                        UPDATE javna_narocila 
                        SET cpv_codes_structured = ?,
                            cpv_codes_legacy = ?,
                            cpv_migration_status = ?,
                            cpv_migration_timestamp = ?
                        WHERE id = ?
                    """, (
                        ', '.join(valid_codes),
                        cpv_text if invalid_text else None,
                        'complete' if not invalid_text else 'partial',
                        datetime.now().isoformat(),
                        proc_id
                    ))
                    
                    if invalid_text:
                        report['partial_migrations'] += 1
                    else:
                        report['successful_migrations'] += 1
                else:
                    # No valid codes found, keep original text
                    cursor.execute("""
                        UPDATE javna_narocila 
                        SET cpv_codes_legacy = ?,
                            cpv_migration_status = ?,
                            cpv_migration_timestamp = ?
                        WHERE id = ?
                    """, (
                        cpv_text,
                        'legacy_only',
                        datetime.now().isoformat(),
                        proc_id
                    ))
                    report['failed_migrations'] += 1
                
                report['details'].append({
                    'id': proc_id,
                    'original': cpv_text[:100],
                    'valid_codes': valid_codes,
                    'status': 'complete' if valid_codes and not invalid_text else 
                             'partial' if valid_codes else 'failed'
                })
                
            except Exception as e:
                report['failed_migrations'] += 1
                report['details'].append({
                    'id': proc_id,
                    'error': str(e)
                })
        
        conn.commit()
        report['end_time'] = datetime.now().isoformat()
        report['success'] = True
        
    except Exception as e:
        conn.rollback()
        report['error'] = str(e)
        report['success'] = False
    
    return report


def rollback_cpv_migration(conn: sqlite3.Connection) -> Dict[str, any]:
    """
    Rollback CPV migration by removing structured fields.
    
    Args:
        conn: SQLite database connection
    
    Returns:
        Rollback report
    """
    report = {
        'start_time': datetime.now().isoformat(),
        'success': False,
        'message': ''
    }
    
    cursor = conn.cursor()
    
    try:
        # Clear migration fields
        cursor.execute("""
            UPDATE javna_narocila 
            SET cpv_codes_structured = NULL,
                cpv_migration_status = NULL,
                cpv_migration_timestamp = NULL
            WHERE cpv_migration_status IS NOT NULL
        """)
        
        affected = cursor.rowcount
        conn.commit()
        
        report['success'] = True
        report['message'] = f"Rolled back {affected} records"
        report['end_time'] = datetime.now().isoformat()
        
    except Exception as e:
        conn.rollback()
        report['error'] = str(e)
        report['message'] = f"Rollback failed: {str(e)}"
    
    return report


def display_cpv_codes(cpv_string: str) -> str:
    """
    Enhanced display of CPV codes with descriptions.
    
    Args:
        cpv_string: Comma-separated CPV codes
    
    Returns:
        Formatted display string
    """
    if not cpv_string:
        return ""
    
    codes = [c.strip() for c in cpv_string.split(',')]
    cpv_options = get_cpv_codes_for_dropdown()
    cpv_dict = {opt['value']: opt['display'] for opt in cpv_options}
    
    display_lines = []
    for code in codes:
        if code in cpv_dict:
            display_lines.append(f"• {cpv_dict[code]}")
        else:
            display_lines.append(f"• {code}")
    
    return '\n'.join(display_lines)


def get_migration_status(conn: sqlite3.Connection) -> Dict[str, any]:
    """
    Get current migration status.
    
    Args:
        conn: SQLite database connection
    
    Returns:
        Status report
    """
    cursor = conn.cursor()
    
    try:
        # Check if migration columns exist
        cursor.execute("""
            SELECT COUNT(*) FROM pragma_table_info('javna_narocila') 
            WHERE name='cpv_migration_status'
        """)
        
        if cursor.fetchone()[0] == 0:
            return {
                'migrated': False,
                'message': 'Migration not started'
            }
        
        # Get migration statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cpv_migration_status = 'complete' THEN 1 ELSE 0 END) as complete,
                SUM(CASE WHEN cpv_migration_status = 'partial' THEN 1 ELSE 0 END) as partial,
                SUM(CASE WHEN cpv_migration_status = 'legacy_only' THEN 1 ELSE 0 END) as legacy_only,
                SUM(CASE WHEN cpv_migration_status IS NULL THEN 1 ELSE 0 END) as not_migrated
            FROM javna_narocila
            WHERE form_data_json IS NOT NULL
        """)
        
        stats = cursor.fetchone()
        
        return {
            'migrated': True,
            'total': stats[0],
            'complete': stats[1] or 0,
            'partial': stats[2] or 0,
            'legacy_only': stats[3] or 0,
            'not_migrated': stats[4] or 0
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'migrated': False
        }


def run_migration():
    """
    Run the CPV migration process.
    
    Returns:
        Migration report
    """
    conn = sqlite3.connect('drafts.db')
    
    try:
        # Check current status
        status = get_migration_status(conn)
        
        if status.get('migrated') and status.get('complete', 0) > 0:
            return {
                'success': False,
                'message': 'Migration already completed',
                'status': status
            }
        
        # Run migration
        report = migrate_procurement_cpv_data(conn)
        
        # Save report to file
        with open('cpv_migration_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
        
    finally:
        conn.close()


if __name__ == "__main__":
    # Run migration when executed directly
    report = run_migration()
    
    if report['success']:
        print(f"Migration completed successfully!")
        print(f"Total processed: {report['total_processed']}")
        print(f"Successful: {report['successful_migrations']}")
        print(f"Partial: {report['partial_migrations']}")
        print(f"Failed: {report['failed_migrations']}")
    else:
        print(f"Migration failed: {report.get('message', 'Unknown error')}")