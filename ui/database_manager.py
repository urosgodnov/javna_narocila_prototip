"""
Database management module for admin panel.
Provides schema visualization and CRUD operations for all tables.
"""

import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from typing import Dict, List, Any
import database

# Constants
TABLES = [
    'drafts', 
    'javna_narocila', 
    'cpv_codes', 
    'criteria_types', 
    'cpv_criteria', 
    'organizacija', 
    'application_logs'
]

TABLE_NAMES = {
    'drafts': 'Osnutki',
    'javna_narocila': 'Javna naročila',
    'cpv_codes': 'CPV kode',
    'criteria_types': 'Tipi meril',
    'cpv_criteria': 'CPV merila',
    'organizacija': 'Organizacije',
    'application_logs': 'Dnevniški zapisi'
}

def render_database_manager():
    """Main function called from admin_panel.py"""
    st.markdown("### 🗄️ Upravljanje podatkovne baze")
    
    # Create main tabs
    tab1, tab2, tab3 = st.tabs(["📊 Shema baze", "📝 Podatki", "🔧 Orodja"])
    
    with tab1:
        render_schema_visualization()
    
    with tab2:
        st.info("📝 CRUD vmesnik za tabele bo implementiran v Story 2")
    
    with tab3:
        st.info("🔧 Orodja za bazo podatkov")


def render_schema_visualization():
    """Render database ERD diagram."""
    
    st.markdown("## 📊 Shema podatkovne baze")
    st.markdown("Entity Relationship Diagram (ERD) vseh tabel in njihovih povezav")
    
    # Use ONLY HTML component with hardcoded diagram
    mermaid_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    </head>
    <body>
        <div class="mermaid">
erDiagram
DRAFTS {
    int id PK
    string timestamp
    string form_data_json
}
JAVNA_NAROCILA {
    int id PK
    string organizacija
    string naziv
    string vrsta
    string postopek
    Date datum_objave
    string status
    Double vrednost
    string form_data_json
    DateTime zadnja_sprememba
    string uporabnik
    DateTime created_at
}
CPV_CODES {
    int id PK
    string code
    string description
    DateTime created_at
    DateTime updated_at
}
CRITERIA_TYPES {
    int id PK
    string name
    string description
    DateTime created_at
}
CPV_CRITERIA {
    int id PK
    string cpv_code FK
    int criteria_type_id FK
    DateTime created_at
    DateTime updated_at
}
ORGANIZACIJA {
    int id PK
    string naziv
    DateTime created_at
}
APPLICATION_LOGS {
    int id PK
    DateTime timestamp
    int organization_id FK
    string organization_name
    string session_id
    string log_level
    string module
    string function_name
    int line_number
    string message
    int retention_hours
    DateTime expires_at
    string additional_context
    string log_type
    DateTime created_at
}
CPV_CRITERIA }o--|| CPV_CODES : has
CPV_CRITERIA }o--|| CRITERIA_TYPES : has
APPLICATION_LOGS }o--|| ORGANIZACIJA : has
        </div>
        <script>
            mermaid.initialize({ 
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            });
        </script>
    </body>
    </html>
    """
    
    components.html(mermaid_html, height=800, scrolling=True)
    
    # Table details section
    st.markdown("### 📋 Podrobnosti tabel")
    
    # Create expanders for each table
    for table in TABLES:
        with st.expander(f"📁 {TABLE_NAMES.get(table, table)} ({table})"):
            render_table_details(table)


def render_table_details(table_name: str):
    """
    Render detailed information about a table.
    
    Args:
        table_name: Name of the table
    """
    # Get schema
    columns = get_table_schema(table_name)
    
    # Get row count
    row_count = 0
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
    except:
        row_count = 0
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Število stolpcev", len(columns))
    
    with col2:
        st.metric("Število zapisov", row_count)
    
    with col3:
        st.metric("Tuji ključi", 0)
    
    # Display columns
    st.markdown("#### Stolpci")
    
    # Create DataFrame for columns
    if columns:
        df_columns = pd.DataFrame(columns)
        df_columns['Ključ'] = df_columns['pk'].apply(lambda x: '🔑 PK' if x else '')
        df_columns['Obvezno'] = df_columns['notnull'].apply(lambda x: '✓' if x else '')
        
        # Reorder and rename columns
        df_display = df_columns[['name', 'type', 'Ključ', 'Obvezno', 'default']]
        df_display.columns = ['Ime stolpca', 'Tip', 'Ključ', 'Obvezno', 'Privzeta vrednost']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Get schema information for a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of column information dictionaries
    """
    columns = []
    
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Get table info using PRAGMA
            cursor.execute(f"PRAGMA table_info({table_name})")
            
            for row in cursor.fetchall():
                columns.append({
                    'cid': row[0],
                    'name': row[1],
                    'type': row[2],
                    'notnull': row[3],
                    'default': row[4],
                    'pk': row[5]
                })
    
    except Exception as e:
        st.error(f"Napaka pri pridobivanju sheme: {str(e)}")
    
    return columns