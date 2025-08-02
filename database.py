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
