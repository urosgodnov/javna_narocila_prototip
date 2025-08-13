import sqlite3
import json
from datetime import datetime

DATABASE_FILE = 'drafts.db'

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
