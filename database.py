import sqlite3
import json
from datetime import datetime, timedelta
import os

DATABASE_FILE = 'mainDB.db'

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
        
        conn.commit()

def save_draft(form_data):
    init_db()
    timestamp = datetime.now().isoformat()
    form_data_json = json.dumps(form_data)
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO drafts (timestamp, form_data_json) VALUES (?, ?)', (timestamp, form_data_json))
        conn.commit()
    return cursor.lastrowid

def get_all_draft_metadata():
    init_db()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp FROM drafts ORDER BY timestamp DESC')
        return cursor.fetchall()

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
    
    # Extract key fields from form data
    naziv = form_data.get('projectInfo', {}).get('projectName', 'Neimenovano naročilo')
    vrsta = form_data.get('orderType', {}).get('type', '')
    postopek = form_data.get('submissionProcedure', {}).get('procedure', '')
    vrednost = form_data.get('orderType', {}).get('estimatedValue', 0)
    
    # Set default date and status
    datum_objave = datetime.now().date().isoformat()
    status = 'Osnutek'
    
    form_data_json = json.dumps(form_data)
    
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
    init_db()
    
    # Extract key fields from form data
    naziv = form_data.get('projectInfo', {}).get('projectName', 'Neimenovano naročilo')
    vrsta = form_data.get('orderType', {}).get('type', '')
    postopek = form_data.get('submissionProcedure', {}).get('procedure', '')
    vrednost = form_data.get('orderType', {}).get('estimatedValue', 0)
    
    form_data_json = json.dumps(form_data)
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

def update_procurement_status(procurement_id, new_status):
    """Update the status of a procurement."""
    init_db()
    zadnja_sprememba = datetime.now().isoformat()
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE javna_narocila 
            SET status = ?, zadnja_sprememba = ?
            WHERE id = ?
        """, (new_status, zadnja_sprememba, procurement_id))
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create application_logs table
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
                    FOREIGN KEY (organization_id) REFERENCES organizacija(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_expires ON application_logs(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON application_logs(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_org_level ON application_logs(organization_id, log_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON application_logs(log_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_type ON application_logs(log_type) WHERE log_type IS NOT NULL')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_message ON application_logs(message)')
            
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
