import sqlite3
import json
from datetime import datetime, timedelta, date
import os

DATABASE_FILE = 'mainDB.db'  # Back to using main database after fixing corruption

def convert_dates_to_strings(obj):
    """Recursively convert date objects to ISO format strings for JSON serialization."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_dates_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_strings(item) for item in obj]
    else:
        return obj

def init_db():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                form_data_json TEXT NOT NULL
            )
        ''')
        
        # Create the main procurements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS javna_narocila (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organizacija TEXT DEFAULT 'demo_organizacija',
                naziv TEXT NOT NULL,
                vrsta TEXT,
                postopek TEXT,
                datum_objave DATE,
                status TEXT DEFAULT 'Osnutek',
                vrednost REAL,
                form_data_json TEXT NOT NULL,
                zadnja_sprememba TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uporabnik TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_organizacija 
            ON javna_narocila(organizacija)
        ''')
        
        # Create CPV codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpv_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for CPV table
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cpv_code 
            ON cpv_codes(code)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cpv_description 
            ON cpv_codes(description)
        ''')
        
        # Create criteria types table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS criteria_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create CPV criteria junction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpv_criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpv_code VARCHAR(20) NOT NULL,
                criteria_type_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cpv_code) REFERENCES cpv_codes(code) ON DELETE CASCADE,
                FOREIGN KEY (criteria_type_id) REFERENCES criteria_types(id) ON DELETE CASCADE,
                UNIQUE(cpv_code, criteria_type_id)
            )
        ''')
        
        # Create indexes for criteria tables
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cpv_criteria_code 
            ON cpv_criteria(cpv_code)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cpv_criteria_type 
            ON cpv_criteria(criteria_type_id)
        ''')
        
        # Execute logs table migration
        create_logs_table()
        
        # Execute form documents table migration
        create_form_documents_tables()
        
        # Execute AI documents table migration
        create_ai_documents_tables()
        
        conn.commit()

def save_draft(form_data):
    """DEPRECATED: Use create_procurement() with status='Delno izpolnjeno' instead."""
    # Simply create a procurement with draft status
    form_data['status'] = 'Delno izpolnjeno'
    return create_procurement(form_data)

def update_draft(draft_id, form_data):
    """DEPRECATED: Use update_procurement() instead."""
    # Simply update the procurement
    return update_procurement(draft_id, form_data)

def get_all_draft_metadata():
    """DEPRECATED: Use get_all_procurements() with status filter instead."""
    # Return procurements with draft status
    procurements = get_all_procurements()
    return [(p['id'], p['zadnja_sprememba']) for p in procurements if p.get('status') == 'Delno izpolnjeno']

def get_recent_drafts(limit=5):
    """Get the most recent draft entries with metadata."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, form_data_json 
            FROM drafts 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            draft_id, timestamp, form_data_json = row
            # Parse JSON to get metadata if available
            try:
                data = json.loads(form_data_json)
                metadata = data.get('_save_metadata', {})
                results.append({
                    'id': draft_id,
                    'created_at': timestamp,
                    'current_step': metadata.get('current_step', 0),
                    'save_type': metadata.get('save_type', 'unknown')
                })
            except:
                results.append({
                    'id': draft_id,
                    'created_at': timestamp,
                    'current_step': 0,
                    'save_type': 'unknown'
                })
        
        return results

def load_draft(draft_id):
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT form_data_json FROM drafts WHERE id = ?', (draft_id,))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

# ============ PROCUREMENT CRUD OPERATIONS ============

def get_procurements_for_customer(customer_name='demo_organizacija'):
    """Fetch all procurements for a specific customer."""
    init_db()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, naziv, vrsta, postopek, datum_objave, status, vrednost, 
               zadnja_sprememba, uporabnik
        FROM javna_narocila 
        WHERE organizacija = ? 
        ORDER BY id DESC
    """, (customer_name,))
    
    columns = [desc[0] for desc in cursor.description]
    procurements = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return procurements

def get_procurement_by_id(procurement_id):
    """Fetch a single procurement by ID."""
    init_db()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM javna_narocila WHERE id = ?
    """, (procurement_id,))
    
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    
    if row:
        procurement = dict(zip(columns, row))
        # Parse the JSON form data
        if procurement.get('form_data_json'):
            procurement['form_data'] = json.loads(procurement['form_data_json'])
        return procurement
    return None

def create_procurement(form_data, customer_name='demo_organizacija'):
    """Create a new procurement record."""
    init_db()
    
    # Debug: Print what we're getting
    import logging
    logging.warning(f"=== DEBUG create_procurement: form_data keys = {list(form_data.keys())}")
    if 'projectInfo' in form_data:
        logging.warning(f"  projectInfo = {form_data['projectInfo']}")
    if 'orderType' in form_data:
        logging.warning(f"  orderType = {form_data['orderType']}")
    
    # Extract key fields from form data
    naziv = form_data.get('projectInfo', {}).get('projectName', 'Neimenovano naročilo')
    vrsta = form_data.get('orderType', {}).get('type', '')
    postopek = form_data.get('submissionProcedure', {}).get('procedure', '')
    
    # Calculate value - sum from lots if present, otherwise from main field
    vrednost = 0
    
    # Check for new lot structure (lot_0, lot_1, etc.)
    lot_mode = form_data.get('lot_mode', '')
    num_lots = form_data.get('num_lots', 0)
    
    if lot_mode == 'multiple' and num_lots > 0:
        # New structure: sum values from lot_X fields
        for i in range(num_lots):
            # Try different possible field names for lot values
            value_fields = [
                f'lot_{i}.orderType.estimatedValue',
                f'lot_{i}.priceInfo.estimatedValue',
                f'lot_{i}_orderType_estimatedValue',  # Old underscore format
                f'lot_{i}_priceInfo_estimatedValue'   # Old underscore format
            ]
            
            for field in value_fields:
                if field in form_data:
                    lot_value = form_data.get(field, 0)
                    try:
                        if isinstance(lot_value, str):
                            lot_value = float(lot_value.replace(',', '.')) if lot_value else 0
                        vrednost += lot_value
                        logging.info(f"Found lot {i} value in {field}: {lot_value}")
                        break  # Use first found value field for this lot
                    except (ValueError, AttributeError):
                        continue
    
    # Old structure fallback
    elif form_data.get('lotsInfo', {}).get('hasLots', False) and 'lots' in form_data:
        # Old structure: Sum up values from all lots in array
        for lot in form_data.get('lots', []):
            if isinstance(lot, dict):
                lot_value = lot.get('estimatedValue', 0)
                try:
                    if isinstance(lot_value, str):
                        lot_value = float(lot_value.replace(',', '.')) if lot_value else 0
                    vrednost += lot_value
                except (ValueError, AttributeError):
                    continue
    
    # If no value from lots, try to get from main field
    if vrednost == 0:
        # Try general mode fields
        if lot_mode == 'general':
            value_fields = [
                'general.orderType.estimatedValue',
                'general.priceInfo.estimatedValue'
            ]
            for field in value_fields:
                if field in form_data:
                    vrednost = form_data.get(field, 0)
                    if isinstance(vrednost, str):
                        try:
                            vrednost = float(vrednost.replace(',', '.')) if vrednost else 0
                        except ValueError:
                            vrednost = 0
                    if vrednost > 0:
                        break
        
        # Fallback to old structure
        if vrednost == 0:
            vrednost = form_data.get('orderType', {}).get('estimatedValue', 0)
            if isinstance(vrednost, str):
                try:
                    vrednost = float(vrednost.replace(',', '.')) if vrednost else 0
                except ValueError:
                    vrednost = 0
    
    # Debug: Show what we extracted
    logging.warning(f"  Extracted: naziv='{naziv}', vrsta='{vrsta}', postopek='{postopek}', vrednost={vrednost}, has_lots={has_lots}")
    
    # Set default date and status
    datum_objave = datetime.now().date().isoformat()
    status = 'Osnutek'
    
    # Convert any date objects to strings before JSON serialization
    form_data_serializable = convert_dates_to_strings(form_data)
    form_data_json = json.dumps(form_data_serializable)
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO javna_narocila 
            (organizacija, naziv, vrsta, postopek, datum_objave, status, vrednost, form_data_json, uporabnik)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, naziv, vrsta, postopek, datum_objave, status, vrednost, form_data_json, 'current_user'))
        conn.commit()
        return cursor.lastrowid

def update_procurement(procurement_id, form_data):
    """Update an existing procurement record."""
    import logging
    
    init_db()
    
    # Debug: Check if clients data exists in form_data
    if 'clientInfo' in form_data:
        if 'clients' in form_data['clientInfo']:
            logging.info(f"[update_procurement] clientInfo.clients: {form_data['clientInfo']['clients']}")
        else:
            logging.info(f"[update_procurement] clientInfo exists but no clients field. Keys: {list(form_data['clientInfo'].keys())}")
    else:
        logging.info("[update_procurement] No clientInfo in form_data")
    
    # Extract key fields from form data
    naziv = form_data.get('projectInfo', {}).get('projectName', 'Neimenovano naročilo')
    vrsta = form_data.get('orderType', {}).get('type', '')
    postopek = form_data.get('submissionProcedure', {}).get('procedure', '')
    
    # Calculate value - same logic as create_procurement
    vrednost = 0
    
    # Check for new lot structure (lot_0, lot_1, etc.)
    lot_mode = form_data.get('lot_mode', '')
    num_lots = form_data.get('num_lots', 0)
    
    # Auto-detect num_lots if not set
    if lot_mode == 'multiple' and num_lots == 0:
        # Count lot_X fields to determine num_lots
        lot_indices = set()
        for key in form_data.keys():
            if key.startswith('lot_') and '.' in key:
                lot_part = key.split('.')[0]
                if '_' in lot_part:
                    idx = lot_part.split('_')[1]
                    if idx.isdigit():
                        lot_indices.add(int(idx))
        num_lots = len(lot_indices)
    
    if lot_mode == 'multiple' and num_lots > 0:
        # New structure: sum values from lot_X fields
        for i in range(num_lots):
            # Try different possible field names for lot values
            value_fields = [
                f'lot_{i}.orderType.estimatedValue',
                f'lot_{i}.priceInfo.estimatedValue',
                f'lot_{i}_orderType_estimatedValue',  # Old underscore format
                f'lot_{i}_priceInfo_estimatedValue'   # Old underscore format
            ]
            
            for field in value_fields:
                if field in form_data:
                    lot_value = form_data.get(field, 0)
                    try:
                        if isinstance(lot_value, str):
                            lot_value = float(lot_value.replace(',', '.')) if lot_value else 0
                        vrednost += lot_value
                        break  # Use first found value field for this lot
                    except (ValueError, AttributeError):
                        continue
    
    # If no value from lots, try to get from main field
    if vrednost == 0:
        # Try general mode fields
        if lot_mode == 'general' or lot_mode == 'none':
            value_fields = [
                'general.orderType.estimatedValue',
                'general.priceInfo.estimatedValue'
            ]
            for field in value_fields:
                if field in form_data:
                    vrednost = form_data.get(field, 0)
                    if isinstance(vrednost, str):
                        try:
                            vrednost = float(vrednost.replace(',', '.')) if vrednost else 0
                        except ValueError:
                            vrednost = 0
                    if vrednost > 0:
                        break
        
        # Fallback to old structure
        if vrednost == 0:
            vrednost = form_data.get('orderType', {}).get('estimatedValue', 0)
            if isinstance(vrednost, str):
                try:
                    vrednost = float(vrednost.replace(',', '.')) if vrednost else 0
                except ValueError:
                    vrednost = 0
    
    # Convert any date objects to strings before JSON serialization
    form_data_serializable = convert_dates_to_strings(form_data)
    form_data_json = json.dumps(form_data_serializable)
    zadnja_sprememba = datetime.now().isoformat()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE javna_narocila 
            SET naziv = ?, vrsta = ?, postopek = ?, vrednost = ?, 
                form_data_json = ?, zadnja_sprememba = ?
            WHERE id = ?
        """, (naziv, vrsta, postopek, vrednost, form_data_json, zadnja_sprememba, procurement_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_procurement(procurement_id):
    """Delete a procurement record."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM javna_narocila WHERE id = ?", (procurement_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============ LOGGING TABLE OPERATIONS ============

def create_logs_table():
    """Create the application_logs table and related objects."""
    migration_file = os.path.join('migrations', '001_create_logs_table.sql')
    
    if not os.path.exists(migration_file):
        # If migration file doesn't exist, create table directly
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Create organizacija table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizacija (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naziv TEXT NOT NULL,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Story 2: Add password_hash column if it doesn't exist (migration)
            cursor.execute("PRAGMA table_info(organizacija)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'password_hash' not in columns:
                cursor.execute('ALTER TABLE organizacija ADD COLUMN password_hash TEXT')
            
            # Create application_logs table with new columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS application_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    organization_id INTEGER,
                    organization_name TEXT,
                    session_id TEXT,
                    log_level TEXT NOT NULL CHECK (log_level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
                    module TEXT,
                    function_name TEXT,
                    line_number INTEGER,
                    message TEXT,
                    retention_hours INTEGER NOT NULL DEFAULT 24,
                    expires_at DATETIME,
                    additional_context TEXT,
                    log_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    log_date DATE,
                    log_time TIME,
                    FOREIGN KEY (organization_id) REFERENCES organizacija(id) ON DELETE CASCADE
                )
            ''')
            
            # Ensure new columns exist if table already exists
            try:
                cursor.execute("PRAGMA table_info(application_logs)")
                existing_cols = [col[1] for col in cursor.fetchall()]
                if 'log_date' not in existing_cols:
                    cursor.execute('ALTER TABLE application_logs ADD COLUMN log_date DATE')
                if 'log_time' not in existing_cols:
                    cursor.execute('ALTER TABLE application_logs ADD COLUMN log_time TIME')
            except Exception as e:
                # If there's any issue with the migration, log it but don't crash
                print(f"Warning: Could not add log_date/log_time columns: {e}")
                # These columns are optional optimizations, so we can continue without them
            
            # Create indexes including new columns
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_expires ON application_logs(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON application_logs(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_org_level ON application_logs(organization_id, log_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON application_logs(log_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_type ON application_logs(log_type) WHERE log_type IS NOT NULL')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_message ON application_logs(message)')
            
            # Only create indexes on log_date/log_time if columns exist
            try:
                cursor.execute("PRAGMA table_info(application_logs)")
                existing_cols = [col[1] for col in cursor.fetchall()]
                if 'log_date' in existing_cols:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_date ON application_logs(log_date DESC)')
                if 'log_date' in existing_cols and 'log_time' in existing_cols:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_date_time ON application_logs(log_date DESC, log_time DESC)')
            except Exception as e:
                # If we can't create indexes, it's not critical
                print(f"Warning: Could not create date/time indexes: {e}")
            
            # Create views
            cursor.execute('''
                CREATE VIEW IF NOT EXISTS log_statistics AS
                SELECT 
                    log_level,
                    COUNT(*) as count,
                    DATE(timestamp) as date,
                    organization_name,
                    AVG(retention_hours) as avg_retention_hours,
                    MIN(timestamp) as oldest_entry,
                    MAX(timestamp) as newest_entry
                FROM application_logs
                GROUP BY log_level, DATE(timestamp), organization_name
            ''')
            
            cursor.execute('''
                CREATE VIEW IF NOT EXISTS retention_summary AS
                SELECT 
                    log_level,
                    retention_hours,
                    COUNT(*) as count,
                    SUM(LENGTH(message) + LENGTH(COALESCE(additional_context, ''))) as total_size
                FROM application_logs
                GROUP BY log_level, retention_hours
                ORDER BY log_level, retention_hours
            ''')
            
            conn.commit()
    else:
        # Execute migration from file
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            # Split by semicolon and execute each statement
            for statement in migration_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            conn.commit()

def verify_logs_table_exists():
    """Verify that the application_logs table exists."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='application_logs'
        """)
        return cursor.fetchone() is not None

def cleanup_expired_logs():
    """Delete expired log entries based on expires_at timestamp."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Delete expired logs
        cursor.execute("""
            DELETE FROM application_logs 
            WHERE expires_at < datetime('now')
        """)
        deleted_count = cursor.rowcount
        
        # Log the cleanup action
        if deleted_count > 0:
            cursor.execute("""
                INSERT INTO application_logs 
                (log_level, module, function_name, message, retention_hours, log_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('INFO', 'database', 'cleanup_expired_logs', 
                  f'Cleaned up {deleted_count} expired log entries', 24, 'system_maintenance'))
        
        conn.commit()
        return deleted_count

def calculate_expires_at(timestamp, retention_hours):
    """Calculate the expiration timestamp based on retention hours."""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    return timestamp + timedelta(hours=retention_hours)

# ============ FORM DOCUMENTS TABLE OPERATIONS ============

def create_form_documents_tables():
    """Create the form_documents tables and related objects."""
    migration_file = os.path.join('migrations', '002_form_documents_tables.sql')
    
    if os.path.exists(migration_file):
        # Execute migration from file
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            # Use executescript for complex SQL with triggers
            try:
                cursor.executescript(migration_sql)
            except sqlite3.OperationalError as e:
                # If error is not about existing objects, raise it
                error_msg = str(e).lower()
                if "already exists" not in error_msg and "duplicate" not in error_msg:
                    # Log the error for debugging
                    print(f"Migration error: {e}")
                    # For now, continue without the new tables
                    pass
            conn.commit()
    else:
        # Create tables directly if migration file doesn't exist
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Create form_documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    form_id INTEGER,
                    form_type TEXT CHECK(form_type IN ('draft', 'submission')),
                    field_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    file_size INTEGER,
                    mime_type TEXT,
                    file_hash TEXT,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processing_status TEXT DEFAULT 'pending',
                    processing_error TEXT,
                    ai_document_id INTEGER,
                    metadata_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ai_document_id) REFERENCES ai_documents(id) ON DELETE SET NULL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_form_documents_form ON form_documents(form_id, form_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_form_documents_status ON form_documents(processing_status)')
            
            conn.commit()

def save_form_document(form_id, form_type, field_name, file_path, original_name, 
                      file_size, mime_type, file_hash=None, metadata=None):
    """Save form document metadata to database with new schema."""
    import hashlib
    
    # Generate hash if not provided
    if not file_hash:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Check if document with same hash already exists
        cursor.execute('SELECT id FROM form_documents WHERE file_hash = ? AND is_active = 1', (file_hash,))
        existing = cursor.fetchone()
        
        if existing:
            doc_id = existing[0]
        else:
            # Insert new document
            cursor.execute('''
                INSERT INTO form_documents 
                (file_hash, original_name, file_path, file_size, 
                 mime_type, file_type, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_hash, original_name, file_path, file_size,
                  mime_type, os.path.splitext(original_name)[1].lower(), 
                  json.dumps(metadata) if metadata else None))
            doc_id = cursor.lastrowid
        
        # Create association
        cursor.execute('''
            INSERT OR IGNORE INTO form_document_associations
            (form_document_id, form_id, form_type, field_name)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, form_id, form_type, field_name))
        
        conn.commit()
        return doc_id

def get_form_documents(form_id, form_type='draft'):
    """Get all documents for a specific form."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, a.field_name, a.association_type
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND a.form_type = ? AND d.is_active = 1
            ORDER BY d.upload_date DESC
        ''', (form_id, form_type))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def update_form_document_status(doc_id, status, error_message=None):
    """Update the processing status of a form document."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE form_documents 
            SET processing_status = ?, processing_error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, error_message, doc_id))
        conn.commit()
        return cursor.rowcount > 0

# ============ AI DOCUMENTS TABLE OPERATIONS ============

def create_ai_documents_tables():
    """Create the ai_documents tables and related objects."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # First check if tables already exist with proper schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_documents'")
        if cursor.fetchone():
            # Table exists, check if it has created_at column
            cursor.execute("PRAGMA table_info(ai_documents)")
            columns = {col[1] for col in cursor.fetchall()}
            
            if 'created_at' in columns:
                # Table exists with correct schema, nothing to do
                return
            else:
                # Table exists but needs column migration
                # Add missing columns if they don't exist
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE ai_documents ADD COLUMN created_at DATETIME")
                    cursor.execute("UPDATE ai_documents SET created_at = upload_date WHERE created_at IS NULL AND upload_date IS NOT NULL")
                
                if 'processed_at' not in columns:
                    cursor.execute("ALTER TABLE ai_documents ADD COLUMN processed_at DATETIME")
                
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE ai_documents ADD COLUMN updated_at DATETIME")
                    cursor.execute("UPDATE ai_documents SET updated_at = COALESCE(created_at, upload_date, CURRENT_TIMESTAMP) WHERE updated_at IS NULL")
                
                conn.commit()
                return
        
        # Table doesn't exist, try to create from migration file
        migration_file = os.path.join('migrations', '003_ai_documents_tables.sql')
        
        if os.path.exists(migration_file):
            # Execute migration from file
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            try:
                cursor.executescript(migration_sql)
            except sqlite3.OperationalError as e:
                # If error is not about existing objects, raise it
                error_msg = str(e).lower()
                if "already exists" not in error_msg and "duplicate" not in error_msg:
                    print(f"AI migration warning: {e}")
                    pass
            conn.commit()
        else:
            # Create tables directly if migration file doesn't exist
            # Create ai_documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    tip_dokumenta TEXT DEFAULT 'general',
                    tags TEXT,
                    description TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    embedding_count INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create ai_document_chunks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    vector_id TEXT,
                    embedding_generated BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES ai_documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, chunk_index)
                )
            ''')
            
            conn.commit()

# ============ ORGANIZATION MANAGEMENT (Story 2) ============

def get_all_organizations():
    """Get all organizations from the database."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Try to get with password_hash first, fallback to without
        try:
            cursor.execute('SELECT id, naziv, password_hash FROM organizacija ORDER BY naziv')
            columns = ['id', 'name', 'password_hash']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "password_hash" in str(e):
                # Column doesn't exist, try without it and add None for password_hash
                cursor.execute('SELECT id, naziv FROM organizacija ORDER BY naziv')
                result = []
                for row in cursor.fetchall():
                    result.append({'id': row[0], 'name': row[1], 'password_hash': None})
                return result
            else:
                raise

def get_organization_by_name(name):
    """Get organization by name."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Try to get with password_hash first, fallback to without
        try:
            cursor.execute('SELECT id, naziv, password_hash FROM organizacija WHERE naziv = ?', (name,))
            row = cursor.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'password_hash': row[2]}
            return None
        except sqlite3.OperationalError as e:
            if "password_hash" in str(e):
                # Column doesn't exist, try without it
                cursor.execute('SELECT id, naziv FROM organizacija WHERE naziv = ?', (name,))
                row = cursor.fetchone()
                if row:
                    return {'id': row[0], 'name': row[1], 'password_hash': None}
                return None
            else:
                raise

def create_organization(name, password_hash=None):
    """Create a new organization."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Try to insert with password_hash first, fallback to without
        try:
            cursor.execute(
                'INSERT INTO organizacija (naziv, password_hash) VALUES (?, ?)',
                (name, password_hash)
            )
        except sqlite3.OperationalError as e:
            if "password_hash" in str(e):
                # Column doesn't exist, insert without it
                cursor.execute(
                    'INSERT INTO organizacija (naziv) VALUES (?)',
                    (name,)
                )
            else:
                raise
        
        conn.commit()
        return cursor.lastrowid

def update_organization(org_id, name=None, password_hash=None):
    """Update an organization."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        try:
            if name and password_hash is not None:
                cursor.execute(
                    'UPDATE organizacija SET naziv = ?, password_hash = ? WHERE id = ?',
                    (name, password_hash, org_id)
                )
            elif name:
                cursor.execute(
                    'UPDATE organizacija SET naziv = ? WHERE id = ?',
                    (name, org_id)
                )
            elif password_hash is not None:
                cursor.execute(
                    'UPDATE organizacija SET password_hash = ? WHERE id = ?',
                    (password_hash, org_id)
                )
        except sqlite3.OperationalError as e:
            if "password_hash" in str(e) and password_hash is not None:
                # Column doesn't exist, try to add it first
                try:
                    cursor.execute('ALTER TABLE organizacija ADD COLUMN password_hash TEXT')
                    conn.commit()
                    # Retry the update
                    if name and password_hash is not None:
                        cursor.execute(
                            'UPDATE organizacija SET naziv = ?, password_hash = ? WHERE id = ?',
                            (name, password_hash, org_id)
                        )
                    elif password_hash is not None:
                        cursor.execute(
                            'UPDATE organizacija SET password_hash = ? WHERE id = ?',
                            (password_hash, org_id)
                        )
                except:
                    # If we can't add the column, just update the name
                    if name:
                        cursor.execute(
                            'UPDATE organizacija SET naziv = ? WHERE id = ?',
                            (name, org_id)
                        )
            elif name:
                # Just update the name if that's all we have
                cursor.execute(
                    'UPDATE organizacija SET naziv = ? WHERE id = ?',
                    (name, org_id)
                )
            else:
                raise
        
        conn.commit()
        return cursor.rowcount > 0

def delete_organization(org_id):
    """Delete an organization."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM organizacija WHERE id = ?', (org_id,))
        conn.commit()
        return cursor.rowcount > 0

def update_procurement_status(procurement_id, new_status):
    """Update the status of a procurement (Story 2)."""
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE javna_narocila SET status = ?, zadnja_sprememba = datetime("now") WHERE id = ?',
            (new_status, procurement_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def ensure_demo_organization_exists():
    """Ensure demo_organizacija exists in the database."""
    try:
        org = get_organization_by_name('demo_organizacija')
        if not org:
            create_organization('demo_organizacija', None)  # No password for demo
    except sqlite3.OperationalError as e:
        # If there's an error with the organizacija table, try to handle it gracefully
        if "no such table" in str(e):
            # Table doesn't exist, create it
            init_db()
            create_organization('demo_organizacija', None)
        else:
            # For other errors, just ensure we can continue
            pass
