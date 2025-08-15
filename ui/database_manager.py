"""
Database management module for admin panel.
Provides schema visualization and CRUD operations for all tables.
"""

import streamlit as st
import sqlite3
import pandas as pd
from typing import Dict, List, Any
import database
from utils.validations import ValidationManager

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
        render_table_management()
    
    with tab3:
        st.info("🔧 Orodja za bazo podatkov")


def render_schema_visualization():
    """Render database schema information."""
    
    st.markdown("## 📊 Shema podatkovne baze")
    st.markdown("Pregled vseh tabel in njihovih struktur")
    
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


def render_table_management():
    """Render CRUD interface for database tables."""
    st.markdown("## 📝 Upravljanje podatkov")
    
    # Add custom styling for beautiful UI
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
            background-color: #f0f2f6;
            border-radius: 8px;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .dataframe tbody tr:hover {
            background-color: #f5f5f5;
            cursor: pointer;
        }
        .metric-card {
            padding: 15px;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for each table
    tabs = st.tabs([f"📁 {TABLE_NAMES.get(table, table)}" for table in TABLES])
    
    for idx, (tab, table) in enumerate(zip(tabs, TABLES)):
        with tab:
            render_single_table_management(table)


def render_single_table_management(table_name: str):
    """
    Render CRUD interface for a single table.
    
    Args:
        table_name: Name of the table to manage
    """
    # Initialize session state for this table
    if f'{table_name}_page' not in st.session_state:
        st.session_state[f'{table_name}_page'] = 0
    if f'{table_name}_search' not in st.session_state:
        st.session_state[f'{table_name}_search'] = ""
    
    # Get row count
    row_count = get_row_count(table_name)
    
    # Display table header with metrics
    st.markdown(f"""
    <div class="metric-card">
        <h3>📊 {TABLE_NAMES.get(table_name, table_name)}</h3>
        <p style="font-size: 24px; margin: 10px 0;">{row_count} zapisov</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons row
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Iskanje", 
            key=f"{table_name}_search_input",
            placeholder="Vnesi iskalni niz..."
        )
        st.session_state[f'{table_name}_search'] = search_term
    
    with col2:
        if st.button("➕ Dodaj", key=f"{table_name}_add_btn", use_container_width=True):
            st.session_state[f'{table_name}_show_add'] = True
    
    with col3:
        if st.button("🔄 Osveži", key=f"{table_name}_refresh_btn", use_container_width=True):
            st.rerun()
    
    with col4:
        export_csv = st.button("📥 Izvozi CSV", key=f"{table_name}_export_btn", use_container_width=True)
    
    # Show add form if requested
    if st.session_state.get(f'{table_name}_show_add', False):
        render_add_form(table_name)
    
    # Fetch and display data
    page_size = 50
    offset = st.session_state[f'{table_name}_page'] * page_size
    
    df = fetch_table_data(
        table_name, 
        search_term,
        limit=page_size,
        offset=offset
    )
    
    if df is not None and not df.empty:
        # Create a container for the table with actions
        st.markdown("### 📋 Podatki tabele")
        
        # Add action columns to dataframe
        df_display = df.copy()
        
        # Display the dataframe
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Action buttons section
        st.markdown("### ⚙️ Akcije za zapise")
        
        # Create selection for row operations
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Get primary key column
            columns = get_table_schema(table_name)
            pk_col = None
            for col in columns:
                if col['pk']:
                    pk_col = col['name']
                    break
            
            if pk_col and pk_col in df.columns:
                selected_id = st.selectbox(
                    "Izberi zapis (ID)",
                    options=df[pk_col].tolist(),
                    key=f"{table_name}_select_record"
                )
                
                if selected_id is not None:
                    selected_row = df[df[pk_col] == selected_id].iloc[0] if len(df[df[pk_col] == selected_id]) > 0 else None
                    
                    if selected_row is not None:
                        with col2:
                            if st.button("✏️ Uredi", key=f"{table_name}_edit_selected", use_container_width=True):
                                st.session_state[f'{table_name}_edit_record'] = selected_row.to_dict()
                                st.session_state[f'{table_name}_show_edit'] = True
                        
                        with col3:
                            if st.button("🗑️ Izbriši", key=f"{table_name}_delete_selected", use_container_width=True):
                                st.session_state[f'{table_name}_delete_record'] = selected_row.to_dict()
                                st.session_state[f'{table_name}_show_delete'] = True
        
        # Show edit form if requested
        if st.session_state.get(f'{table_name}_show_edit', False):
            render_edit_form(table_name, st.session_state[f'{table_name}_edit_record'])
        
        # Show delete confirmation if requested
        if st.session_state.get(f'{table_name}_show_delete', False):
            render_delete_confirmation(table_name, st.session_state[f'{table_name}_delete_record'])
        
        # Pagination controls
        total_pages = (row_count // page_size) + (1 if row_count % page_size else 0)
        
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            if st.button("⬅️ Prejšnja", key=f"{table_name}_prev", 
                        disabled=st.session_state[f'{table_name}_page'] == 0):
                st.session_state[f'{table_name}_page'] -= 1
                st.rerun()
        
        with col2:
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'>Stran {st.session_state[f'{table_name}_page'] + 1} od {total_pages}</div>",
                unsafe_allow_html=True
            )
        
        with col3:
            if st.button("Naslednja ➡️", key=f"{table_name}_next",
                        disabled=st.session_state[f'{table_name}_page'] >= total_pages - 1):
                st.session_state[f'{table_name}_page'] += 1
                st.rerun()
        
        # Export to CSV if requested
        if export_csv:
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Prenesi CSV",
                data=csv,
                file_name=f"{table_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"{table_name}_download"
            )
    else:
        st.info("Ni podatkov za prikaz")


def fetch_table_data(table_name: str, search_term: str = "", limit: int = 50, offset: int = 0) -> pd.DataFrame:
    """
    Fetch data from a database table with optional search and pagination.
    
    Args:
        table_name: Name of the table
        search_term: Search term to filter results
        limit: Number of records to fetch
        offset: Number of records to skip
        
    Returns:
        DataFrame with table data
    """
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            # Build query
            if search_term:
                # Get columns to search
                columns = get_table_schema(table_name)
                searchable_cols = [col['name'] for col in columns if col['type'] in ['TEXT', 'VARCHAR']]
                
                if searchable_cols:
                    where_clauses = [f"{col} LIKE ?" for col in searchable_cols]
                    where_clause = " OR ".join(where_clauses)
                    query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT ? OFFSET ?"
                    params = [f"%{search_term}%" for _ in searchable_cols] + [limit, offset]
                else:
                    query = f"SELECT * FROM {table_name} LIMIT ? OFFSET ?"
                    params = [limit, offset]
            else:
                query = f"SELECT * FROM {table_name} LIMIT ? OFFSET ?"
                params = [limit, offset]
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
            
    except Exception as e:
        st.error(f"Napaka pri pridobivanju podatkov: {str(e)}")
        return pd.DataFrame()


def get_row_count(table_name: str) -> int:
    """Get the number of rows in a table."""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
    except:
        return 0


def render_add_form(table_name: str):
    """
    Render form for adding a new record.
    
    Args:
        table_name: Name of the table
    """
    st.markdown("### ➕ Dodaj nov zapis")
    
    columns = get_table_schema(table_name)
    
    with st.form(key=f"{table_name}_add_form"):
        values = {}
        
        for col in columns:
            # Skip auto-increment primary keys
            if col['pk'] and col['type'] == 'INTEGER':
                continue
            
            col_name = col['name']
            col_type = col['type']
            
            # Check for foreign keys
            if col_name.endswith('_id') or col_name == 'cpv_code':
                # Implement foreign key dropdown
                ref_table = get_referenced_table(col_name)
                if ref_table:
                    ref_data = get_foreign_key_options(ref_table)
                    if ref_data:
                        # Create selectbox with meaningful display
                        option_display = {row['id']: row['display'] for row in ref_data}
                        selected = st.selectbox(
                            f"{col_name} ({TABLE_NAMES.get(ref_table, ref_table)})",
                            options=list(option_display.keys()),
                            format_func=lambda x: f"{x} - {option_display[x]}",
                            key=f"{table_name}_{col_name}_input"
                        )
                        values[col_name] = selected
                    else:
                        st.warning(f"Tabela {ref_table} je prazna")
                        values[col_name] = st.number_input(
                            f"{col_name} (Foreign Key)",
                            key=f"{table_name}_{col_name}_input"
                        )
                else:
                    values[col_name] = st.number_input(
                        f"{col_name} (Foreign Key)",
                        key=f"{table_name}_{col_name}_input"
                    )
            elif 'DATE' in col_type.upper() or 'TIME' in col_type.upper():
                if 'DATE' in col_type.upper() and 'TIME' not in col_type.upper():
                    values[col_name] = st.date_input(
                        col_name,
                        key=f"{table_name}_{col_name}_input"
                    )
                else:
                    values[col_name] = st.text_input(
                        f"{col_name} (DateTime)",
                        key=f"{table_name}_{col_name}_input",
                        placeholder="YYYY-MM-DD HH:MM:SS"
                    )
            elif col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                values[col_name] = st.number_input(
                    col_name,
                    key=f"{table_name}_{col_name}_input"
                )
            elif col_name.endswith('_json'):
                values[col_name] = st.text_area(
                    f"{col_name} (JSON)",
                    key=f"{table_name}_{col_name}_input",
                    placeholder='{"key": "value"}'
                )
            else:
                values[col_name] = st.text_input(
                    col_name,
                    key=f"{table_name}_{col_name}_input"
                )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Shrani", use_container_width=True):
                if save_record(table_name, values):
                    st.success("✅ Zapis uspešno dodan!")
                    st.session_state[f'{table_name}_show_add'] = False
                    st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Prekliči", use_container_width=True):
                st.session_state[f'{table_name}_show_add'] = False
                st.rerun()


def save_record(table_name: str, values: dict) -> bool:
    """
    Save a new record to the database.
    
    Args:
        table_name: Name of the table
        values: Dictionary of column values
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Filter out empty values
        filtered_values = {k: v for k, v in values.items() if v is not None and v != ""}
        
        if not filtered_values:
            st.error("Ni podatkov za shranjevanje")
            return False
        
        # Validate the record before saving
        validator = ValidationManager()
        is_valid, errors = validator.validate_database_record(table_name, filtered_values, is_update=False)
        
        if not is_valid:
            for error in errors:
                st.error(f"❌ {error}")
            return False
        
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            columns = list(filtered_values.keys())
            placeholders = ["?" for _ in columns]
            
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, list(filtered_values.values()))
            conn.commit()
            
            return True
            
    except Exception as e:
        st.error(f"Napaka pri shranjevanju: {str(e)}")
        return False


def render_edit_form(table_name: str, record: dict):
    """
    Render form for editing an existing record.
    
    Args:
        table_name: Name of the table
        record: Dictionary containing the current record values
    """
    st.markdown("### ✏️ Uredi zapis")
    
    columns = get_table_schema(table_name)
    
    with st.form(key=f"{table_name}_edit_form"):
        values = {}
        primary_key = None
        primary_key_value = None
        
        for col in columns:
            col_name = col['name']
            col_type = col['type']
            current_value = record.get(col_name)
            
            # Store primary key for WHERE clause
            if col['pk']:
                primary_key = col_name
                primary_key_value = current_value
                st.text_input(f"{col_name} (Primary Key)", value=str(current_value), disabled=True)
                continue
            
            # Check for foreign keys
            if col_name.endswith('_id') or col_name == 'cpv_code':
                ref_table = get_referenced_table(col_name)
                if ref_table:
                    ref_data = get_foreign_key_options(ref_table)
                    if ref_data:
                        # Create selectbox with meaningful display
                        option_display = {row['id']: row['display'] for row in ref_data}
                        current_val = int(current_value) if current_value else list(option_display.keys())[0] if option_display else 0
                        selected = st.selectbox(
                            f"{col_name} ({TABLE_NAMES.get(ref_table, ref_table)})",
                            options=list(option_display.keys()),
                            format_func=lambda x: f"{x} - {option_display[x]}",
                            index=list(option_display.keys()).index(current_val) if current_val in option_display else 0,
                            key=f"{table_name}_{col_name}_edit"
                        )
                        values[col_name] = selected
                    else:
                        st.warning(f"Tabela {ref_table} je prazna")
                        values[col_name] = st.number_input(
                            f"{col_name} (Foreign Key)",
                            value=int(current_value) if current_value else 0,
                            key=f"{table_name}_{col_name}_edit"
                        )
                else:
                    values[col_name] = st.number_input(
                        f"{col_name} (Foreign Key)",
                        value=int(current_value) if current_value else 0,
                        key=f"{table_name}_{col_name}_edit"
                    )
            elif 'DATE' in col_type.upper() or 'TIME' in col_type.upper():
                values[col_name] = st.text_input(
                    f"{col_name} ({col_type})",
                    value=str(current_value) if current_value else "",
                    key=f"{table_name}_{col_name}_edit"
                )
            elif col_type in ['INTEGER', 'REAL', 'NUMERIC']:
                values[col_name] = st.number_input(
                    col_name,
                    value=float(current_value) if current_value else 0,
                    key=f"{table_name}_{col_name}_edit"
                )
            elif col_name.endswith('_json'):
                values[col_name] = st.text_area(
                    f"{col_name} (JSON)",
                    value=str(current_value) if current_value else "",
                    key=f"{table_name}_{col_name}_edit"
                )
            else:
                values[col_name] = st.text_input(
                    col_name,
                    value=str(current_value) if current_value else "",
                    key=f"{table_name}_{col_name}_edit"
                )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Shrani spremembe", use_container_width=True):
                if update_record(table_name, values, primary_key, primary_key_value):
                    st.success("✅ Zapis uspešno posodobljen!")
                    st.session_state[f'{table_name}_show_edit'] = False
                    st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Prekliči", use_container_width=True):
                st.session_state[f'{table_name}_show_edit'] = False
                st.rerun()


def update_record(table_name: str, values: dict, primary_key: str, primary_key_value) -> bool:
    """
    Update an existing record in the database.
    
    Args:
        table_name: Name of the table
        values: Dictionary of column values to update
        primary_key: Name of the primary key column
        primary_key_value: Value of the primary key for the record to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Filter out empty values
        filtered_values = {k: v for k, v in values.items() if v is not None and v != ""}
        
        if not filtered_values:
            st.error("Ni podatkov za posodobitev")
            return False
        
        # Validate the record before updating
        validator = ValidationManager()
        is_valid, errors = validator.validate_database_record(table_name, filtered_values, is_update=True, record_id=primary_key_value)
        
        if not is_valid:
            for error in errors:
                st.error(f"❌ {error}")
            return False
        
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            set_clauses = [f"{col} = ?" for col in filtered_values.keys()]
            
            query = f"""
                UPDATE {table_name}
                SET {', '.join(set_clauses)}
                WHERE {primary_key} = ?
            """
            
            params = list(filtered_values.values()) + [primary_key_value]
            cursor.execute(query, params)
            conn.commit()
            
            return True
            
    except Exception as e:
        st.error(f"Napaka pri posodabljanju: {str(e)}")
        return False


def render_delete_confirmation(table_name: str, record: dict):
    """
    Render delete confirmation dialog.
    
    Args:
        table_name: Name of the table
        record: Dictionary containing the record to delete
    """
    st.markdown("### ⚠️ Potrditev brisanja")
    st.warning("Ali ste prepričani, da želite izbrisati ta zapis?")
    
    # Display record details
    st.json(record)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Da, izbriši", key=f"{table_name}_confirm_delete", use_container_width=True):
            # Find primary key
            columns = get_table_schema(table_name)
            primary_key = None
            primary_key_value = None
            
            for col in columns:
                if col['pk']:
                    primary_key = col['name']
                    primary_key_value = record.get(primary_key)
                    break
            
            if primary_key and primary_key_value is not None:
                if delete_record(table_name, primary_key, primary_key_value):
                    st.success("✅ Zapis uspešno izbrisan!")
                    st.session_state[f'{table_name}_show_delete'] = False
                    st.rerun()
            else:
                st.error("Ni mogoče najti primarnega ključa za brisanje")
    
    with col2:
        if st.button("❌ Prekliči", key=f"{table_name}_cancel_delete", use_container_width=True):
            st.session_state[f'{table_name}_show_delete'] = False
            st.rerun()


def delete_record(table_name: str, primary_key: str, primary_key_value) -> bool:
    """
    Delete a record from the database.
    
    Args:
        table_name: Name of the table
        primary_key: Name of the primary key column
        primary_key_value: Value of the primary key for the record to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            query = f"DELETE FROM {table_name} WHERE {primary_key} = ?"
            cursor.execute(query, [primary_key_value])
            conn.commit()
            
            return True
            
    except Exception as e:
        st.error(f"Napaka pri brisanju: {str(e)}")
        return False


def get_referenced_table(column_name: str) -> str:
    """
    Get the referenced table name from a foreign key column name.
    
    Args:
        column_name: Name of the foreign key column
        
    Returns:
        Name of the referenced table or None
    """
    # Map foreign key columns to their referenced tables
    fk_mapping = {
        'organization_id': 'organizacija',
        'criteria_type_id': 'criteria_types',
        'cpv_code': 'cpv_codes',  # Note: cpv_code is a string FK, not _id
    }
    
    return fk_mapping.get(column_name)


def get_foreign_key_options(table_name: str) -> List[Dict[str, Any]]:
    """
    Get options for a foreign key dropdown.
    
    Args:
        table_name: Name of the referenced table
        
    Returns:
        List of dictionaries with 'id' and 'display' keys
    """
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Determine which columns to use for display based on table
            if table_name == 'organizacija':
                query = "SELECT id, naziv FROM organizacija ORDER BY naziv"
                cursor.execute(query)
                results = cursor.fetchall()
                return [{'id': row[0], 'display': row[1]} for row in results]
                
            elif table_name == 'criteria_types':
                query = "SELECT id, name FROM criteria_types ORDER BY name"
                cursor.execute(query)
                results = cursor.fetchall()
                return [{'id': row[0], 'display': row[1]} for row in results]
                
            elif table_name == 'cpv_codes':
                query = "SELECT code, description FROM cpv_codes ORDER BY code"
                cursor.execute(query)
                results = cursor.fetchall()
                return [{'id': row[0], 'display': f"{row[0]} - {row[1][:50]}"} for row in results]
                
            else:
                # Generic fallback - just get id
                query = f"SELECT id FROM {table_name} ORDER BY id"
                cursor.execute(query)
                results = cursor.fetchall()
                return [{'id': row[0], 'display': str(row[0])} for row in results]
                
    except Exception as e:
        st.error(f"Napaka pri pridobivanju opcij: {str(e)}")
        return []