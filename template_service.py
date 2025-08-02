import os
import shutil
from datetime import datetime
import json
import sqlite3 # Import sqlite3 here for direct use

# TEMPLATE_DIR is now passed as an argument to functions that need it

def list_templates(template_dir='templates'):
    """Lists available .docx templates."""
    templates = []
    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith('.docx'):
                templates.append(filename)
    return templates

def save_template(uploaded_file, overwrite=False, template_dir='templates'):
    """Saves a new .docx template or overwrites an existing one."""
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    file_path = os.path.join(template_dir, uploaded_file.name)
    
    if os.path.exists(file_path) and not overwrite:
        return False, f"Datoteka '{uploaded_file.name}' že obstaja. Uporabite možnost preglasitve, če jo želite posodobiti."
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return True, f"Datoteka '{uploaded_file.name}' uspešno shranjena."

def clear_drafts():
    """Clears all drafts from the SQLite database."""
    try:
        # Import database here to avoid circular dependency if database.py imports template_service
        import database 
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM drafts')
            conn.commit()
        return True, "Vsi osnutki so bili uspešno izbrisani."
    except Exception as e:
        return False, f"Napaka pri brisanju osnutkov: {e}"

def backup_drafts():
    """Backs up the SQLite database file."""
    import database
    if not os.path.exists(database.DATABASE_FILE):
        return False, "Ni baze podatkov za varnostno kopiranje."
    
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'drafts_backup_{timestamp}.db')
    
    try:
        shutil.copyfile(database.DATABASE_FILE, backup_file)
        return True, f"Varnostna kopija uspešno ustvarjena: {backup_file}"
    except Exception as e:
        return False, f"Napaka pri ustvarjanju varnostne kopije: {e}"

def manage_chromadb_collections(action, collection_name=None):
    """Placeholder for ChromaDB collection management."""
    if action == "list":
        return [], "Seznam zbirk ChromaDB (ni implementirano)."
    elif action == "create":
        return False, "Ustvarjanje zbirke ChromaDB (ni implementirano)."
    elif action == "delete":
        return False, "Brisanje zbirke ChromaDB (ni implementirano)."
    return False, "Neznano dejanje ChromaDB."
