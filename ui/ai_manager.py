import streamlit as st
import os
import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import database
from utils.validations import ValidationManager

# Import AI processing capabilities
try:
    from ui.ai_processor import (
        DocumentProcessor, 
        process_document_async,
        FormAIAssistant,
        EmbeddingGenerator,
        VectorStoreManager
    )
    AI_PROCESSING_AVAILABLE = True
except ImportError as e:
    AI_PROCESSING_AVAILABLE = False
    print(f"AI processing not available: {e}")

# Import OpenAI for query processing
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    
# Import plotly for analytics
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly not available for analytics charts")

# Load environment variables
load_dotenv()

# Document type definitions
DOCUMENT_TYPES = {
    'pogodbe': 'Pogodbe',
    'razpisi': 'Razpisi', 
    'pravilniki': 'Pravilniki',
    'navodila': 'Navodila',
    'razno': 'Razno'
}

# Form section mappings for prompts
PROMPT_SECTIONS = {
    'vrsta_narocila': {
        'title': 'Vrsta javnega naročila',
        'fields': ['posebne_zahteve_sofinancerja']
    },
    'pogajanja': {
        'title': 'Pogajanja',
        'fields': ['posebne_zelje_pogajanja']
    },
    'pogoji_sodelovanje': {
        'title': 'Pogoji za sodelovanje',
        'fields': [
            'ustreznost_poklicna_drugo',
            'ekonomski_polozaj_drugo',
            'tehnicna_sposobnost_drugo'
        ]
    },
    'variante_merila': {
        'title': 'Variante merila',
        'fields': ['merila_drugo']
    }
}

def render_ai_manager():
    """Unified AI and Vector Database Management"""
    
    # Apply unified design system
    from ui.admin_module_design import apply_design_system
    apply_design_system()
    
    # Import modern components
    from ui.components.modern_components import (
        modern_card, error_message, info_banner
    )
    
    # Check environment configuration
    if not validate_environment():
        error_message(
            title="AI modul ni konfiguriran",
            message="Manjkajo API ključi v .env datoteki.",
            details="Potrebni ključi: OPENAI_API_KEY, QDRANT_API_KEY (opcijsko)"
        )
        info_banner(
            message="Za konfiguracijo: 1) Ustvarite .env datoteko 2) Dodajte API ključe 3) Ponovno naložite aplikacijo",
            dismissible=False
        )
        return
    
    # Initialize database tables
    init_ai_tables()
    
    # Check vector database status
    vector_db_status = "Aktivna"
    try:
        from services.qdrant_crud_service import QdrantCRUDService
        crud = QdrantCRUDService()
        stats = crud.get_collection_stats()
        vector_info = f"{stats.get('total_vectors', 0)} vektorjev"
    except:
        vector_db_status = "Omejena"
        vector_info = "Samo lokalno shranjevanje"
    
    # Header section
    st.markdown("### AI & Document Management")
    st.caption("Centralizirano upravljanje dokumentov in AI funkcionalnosti")
    
    # Status info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"Vektorska baza: **{vector_db_status}** • {vector_info}")
    
    tabs = st.tabs(["Dokumenti", "AI Iskanje", "Analitika", "Sistemski pozivi", "Nastavitve"])
    
    with tabs[0]:
        render_document_management()
    with tabs[1]:
        render_ai_search_interface()
    with tabs[2]:
        render_analytics_dashboard()
    with tabs[3]:
        render_system_prompts_management()
    with tabs[4]:
        render_settings_panel()

def validate_environment() -> bool:
    """Check if required API keys are present"""
    required_keys = ['OPENAI_API_KEY', 'QDRANT_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        return False
    return True

def init_ai_tables():
    """Initialize AI-related database tables"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_documents'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create new table with both upload_date and created_at for compatibility
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    tip_dokumenta TEXT,
                    document_type TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processing_status TEXT DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    chunks_count INTEGER DEFAULT 0,
                    embedding_model TEXT,
                    metadata_json TEXT,
                    description TEXT,
                    tags TEXT,
                    document_id TEXT,
                    original_filename TEXT,
                    organization TEXT,
                    file_format TEXT,
                    vectors_count INTEGER,
                    extraction_method TEXT,
                    processed_at DATETIME,
                    updated_at DATETIME,
                    status TEXT
                )
            """)
        else:
            # Add missing columns to existing table for compatibility
            cursor.execute("PRAGMA table_info(ai_documents)")
            existing_columns = {col[1] for col in cursor.fetchall()}
            
            # List of columns that might be missing
            columns_to_add = [
                ("upload_date", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                ("document_id", "TEXT"),
                ("original_filename", "TEXT"),
                ("document_type", "TEXT"),
                ("organization", "TEXT"),
                ("file_format", "TEXT"),
                ("file_size", "INTEGER"),
                ("file_type", "TEXT"),
                ("chunks_count", "INTEGER DEFAULT 0"),
                ("chunk_count", "INTEGER DEFAULT 0"),
                ("vectors_count", "INTEGER DEFAULT 0"),
                ("extraction_method", "TEXT"),
                ("processed_at", "DATETIME"),
                ("updated_at", "DATETIME"),
                ("status", "TEXT"),
                ("tip_dokumenta", "TEXT"),
                ("description", "TEXT"),
                ("tags", "TEXT"),
                ("metadata_json", "TEXT"),
                ("embedding_model", "TEXT")
            ]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE ai_documents ADD COLUMN {col_name} {col_def}")
                    except sqlite3.OperationalError:
                        pass  # Column might already exist
        
        # Document chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_size INTEGER,
                vector_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES ai_documents(id) ON DELETE CASCADE
            )
        """)
        
        # System prompts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_system_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_key TEXT UNIQUE NOT NULL,
                form_section TEXT NOT NULL,
                field_name TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                version INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # Prompt usage log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_prompt_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                form_section TEXT,
                user_input TEXT,
                ai_response TEXT,
                response_time_ms INTEGER,
                tokens_used INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_system_prompts(id)
            )
        """)
        
        # Query log table for analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                sources_json TEXT,
                response_time_seconds REAL,
                confidence_score REAL,
                tokens_used INTEGER,
                user_feedback TEXT,
                is_bookmarked BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Query sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_query_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                document_id INTEGER NOT NULL,
                document_name TEXT,
                chunk_indices TEXT,
                relevance_score REAL,
                FOREIGN KEY (query_id) REFERENCES ai_query_log(id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES ai_documents(id)
            )
        """)
        
        conn.commit()

def inject_custom_css():
    """Inject modern minimal styling to match admin panel"""
    st.markdown("""
    <style>
        .ai-header {
            background: var(--bg-secondary, #FAFAFA);
            padding: 24px;
            border-radius: var(--radius-lg, 8px);
            border: 1px solid var(--border, #E5E5E5);
            margin-bottom: 24px;
        }
        
        .ai-header h1 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary, #000000);
            letter-spacing: -0.02em;
        }
        
        .ai-header p {
            margin: 8px 0 0 0;
            color: var(--text-secondary, #666666);
            font-size: 14px;
        }
        
        .upload-zone {
            border: 2px dashed var(--border, #E5E5E5);
            border-radius: var(--radius-lg, 8px);
            padding: 32px;
            text-align: center;
            background: var(--bg-secondary, #FAFAFA);
            transition: all var(--transition-fast, 150ms ease);
        }
        
        .upload-zone:hover {
            border-color: var(--border-hover, #CCCCCC);
            background: var(--bg-tertiary, #F5F5F5);
        }
        
        .doc-card {
            background: var(--bg-primary, #FFFFFF);
            border: 1px solid var(--border, #E5E5E5);
            padding: 16px;
            border-radius: var(--radius-md, 6px);
            margin-bottom: 12px;
            transition: border-color var(--transition-fast, 150ms ease);
        }
        
        .doc-card:hover {
            border-color: var(--border-hover, #CCCCCC);
        }
        
        .prompt-card {
            background: var(--bg-secondary, #FAFAFA);
            border: 1px solid var(--border, #E5E5E5);
            padding: 20px;
            border-radius: var(--radius-md, 6px);
            margin-bottom: 12px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: var(--radius-sm, 4px);
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        
        .status-pending {
            background: rgba(245, 158, 11, 0.1);
            color: #f59e0b;
        }
        
        .status-processing {
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
        }
        
        .status-completed {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
        }
        
        .status-failed {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }
    </style>
    """, unsafe_allow_html=True)

def render_document_management():
    """Document management interface with type categorization"""
    from ui.components.modern_components import modern_card, modern_button, status_badge
    
    modern_card(
        title="Upravljanje dokumentov",
        content='<p style="color: var(--text-secondary);">Naložite dokumente za bazo znanja AI sistema</p>',
        key="doc_mgmt_header"
    )
    
    # Upload section
    st.markdown("### Nalaganje dokumentov")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Document type selection (required)
        tip_dokumenta = st.selectbox(
            "Tip dokumenta *",
            options=list(DOCUMENT_TYPES.keys()),
            format_func=lambda x: DOCUMENT_TYPES[x],
            key="doc_type_select",
            help="Izberite kategorijo dokumenta za boljšo organizacijo"
        )
        
        # Optional description
        description = st.text_area(
            "Opis dokumenta",
            placeholder="Kratka opisna vsebina dokumenta...",
            key="doc_description",
            height=100
        )
        
        # Optional tags
        tags = st.text_input(
            "Oznake (ločene z vejico)",
            placeholder="npr. 2024, gradnje, EU sredstva",
            key="doc_tags"
        )
    
    with col2:
        # File uploader
        uploaded_file = st.file_uploader(
            "Izberite dokument",
            type=['pdf', 'docx', 'txt', 'md'],
            key="doc_uploader",
            help="Maksimalna velikost: 10MB"
        )
        
        if uploaded_file:
            # Check file size
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                st.error(" Datoteka je prevelika! Maksimalna velikost je 10MB.")
            else:
                # Display file info
                st.info(f"""
                 **Datoteka:** {uploaded_file.name}  
                 **Velikost:** {uploaded_file.size / 1024:.1f} KB  
                 **Tip:** {DOCUMENT_TYPES[tip_dokumenta]}
                """)
                
                if st.button(" Naloži dokument", type="primary", use_container_width=True):
                    with st.spinner("Nalagam dokument..."):
                        doc_id = save_document(
                            file=uploaded_file,
                            tip_dokumenta=tip_dokumenta,
                            description=description,
                            tags=tags
                        )
                        if doc_id:
                            st.success(f" Dokument uspešno naložen (ID: {doc_id})")
                            st.rerun()
                        else:
                            st.error(" Napaka pri nalaganju dokumenta")
    
    st.divider()
    
    # Document list with filtering
    st.markdown("###  Naloženi dokumenti")
    
    # Filter controls
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        filter_type = st.multiselect(
            "Filtriraj po tipu",
            options=list(DOCUMENT_TYPES.keys()),
            format_func=lambda x: DOCUMENT_TYPES[x],
            default=list(DOCUMENT_TYPES.keys()),
            key="filter_doc_type"
        )
    
    with filter_col2:
        search_query = st.text_input(
            "Išči v dokumentih",
            placeholder="Vnesi iskalni niz...",
            key="search_docs"
        )
    
    with filter_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(" Išči", use_container_width=True):
            st.session_state.search_active = True
    
    # Display filtered documents
    documents = load_documents(
        document_types=filter_type,
        search_query=search_query if search_query else None
    )
    
    if documents:
        for doc in documents:
            status_class = f"status-{doc.get('processing_status', 'pending')}"
            
            with st.expander(f"{DOCUMENT_TYPES.get(doc.get('tip_dokumenta', 'general'), 'Splošno')} - {doc['filename']}"):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**Opis:** {doc.get('description', 'Ni opisa')}")
                    if doc.get('tags'):
                        st.write(f"**Oznake:** {doc['tags']}")
                    st.write(f"**Velikost:** {doc.get('file_size', 0) / 1024:.1f} KB")
                    if doc.get('chunks_count') or doc.get('chunk_count'):
                        st.write(f"**Število delov:** {doc.get('chunks_count') or doc.get('chunk_count', 0)}")
                    if doc.get('vectors_count'):
                        st.write(f"**Vektorji:** {doc.get('vectors_count', 0)}")
                
                with col2:
                    status = doc.get('processing_status', 'pending')
                    st.markdown(f"""
                    <span class="status-badge status-{status}">
                        {status.upper()}
                    </span>
                    """, unsafe_allow_html=True)
                    upload_date = doc.get('upload_date') or doc.get('created_at', 'Neznano')
                    st.write(f"**Naloženo:** {upload_date}")
                
                with col3:
                    # Reprocess button for completed documents
                    if status == 'completed':
                        if st.button(" Ponovno procesiraj", key=f"reproc_{doc['id']}", use_container_width=True):
                            with st.spinner("Ponovno procesiram..."):
                                success = reprocess_document(doc['id'], doc.get('file_path'))
                                if success:
                                    st.success("Dokument ponovno procesiran!")
                                    st.rerun()
                    
                    # Process button for pending/failed documents
                    elif status in ['pending', 'failed']:
                        if st.button(" Procesiraj", key=f"proc_{doc['id']}", use_container_width=True):
                            with st.spinner("Procesiram dokument..."):
                                success = reprocess_document(doc['id'], doc.get('file_path'))
                                if success:
                                    st.success("Dokument procesiran!")
                                    st.rerun()
                    
                    # Delete button
                    if st.button(" Izbriši", key=f"del_{doc['id']}", use_container_width=True):
                        if delete_document_with_vectors(doc['id'], doc.get('document_id')):
                            st.success("Dokument in vektorji izbrisani")
                            st.rerun()
    else:
        st.info(" Ni naloženih dokumentov ali ni rezultatov iskanja")

def render_system_prompts_management():
    """Manage system prompts for form AI assistance"""
    
    st.markdown("""
    <div style="background: var(--bg-secondary, #FAFAFA); 
                padding: 20px; border-radius: var(--radius-lg, 8px); 
                border: 1px solid var(--border, #E5E5E5); margin-bottom: 24px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600; color: var(--text-primary, #000000);">Sistemski pozivi</h2>
        <p style="margin: 8px 0 0 0; color: var(--text-secondary, #666666); font-size: 14px;">Upravljanje s pozivi za AI asistenta v obrazcih</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create/Edit prompt section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("###  Dodaj/Uredi poziv")
        
        # Select form section
        selected_section = st.selectbox(
            "Izberi sekcijo",
            options=list(PROMPT_SECTIONS.keys()),
            format_func=lambda x: PROMPT_SECTIONS[x]['title'],
            key="prompt_section"
        )
        
        # Select field within section
        selected_field = st.selectbox(
            "Izberi polje",
            options=PROMPT_SECTIONS[selected_section]['fields'],
            key="prompt_field"
        )
        
        # Generate prompt key
        prompt_key = f"{selected_section}_{selected_field}"
        
        # Check if prompt exists
        existing_prompt = get_prompt(prompt_key)
        
        if existing_prompt:
            st.info(f" Urejate obstoječi poziv (v{existing_prompt['version']})")
    
    with col2:
        st.markdown("###  Vsebina poziva")
        
        # Prompt description
        prompt_description = st.text_input(
            "Opis poziva",
            value=existing_prompt['description'] if existing_prompt else "",
            placeholder="Kratek opis namena poziva",
            key="prompt_desc"
        )
        
        # Prompt text
        default_prompt = existing_prompt['prompt_text'] if existing_prompt else get_default_prompt(selected_section, selected_field)
        prompt_text = st.text_area(
            "Sistemski poziv",
            value=default_prompt,
            height=200,
            key="prompt_text",
            help="Ta poziv bo uporabljen za generiranje AI predlogov"
        )
        
        # Active status
        is_active = st.checkbox(
            "Poziv je aktiven",
            value=existing_prompt['is_active'] if existing_prompt else True,
            key="prompt_active"
        )
        
        # Save button
        if st.button(" Shrani poziv", type="primary", use_container_width=True):
            if save_prompt(prompt_key, selected_section, selected_field, prompt_text, prompt_description, is_active):
                st.success(" Poziv uspešno shranjen")
                st.rerun()
            else:
                st.error(" Napaka pri shranjevanju poziva")
    
    st.divider()
    
    # List existing prompts
    st.markdown("###  Obstoječi pozivi")
    
    prompts = load_all_prompts()
    
    if prompts:
        for prompt in prompts:
            status_text = " Aktiven" if prompt['is_active'] else " Neaktiven"
            
            with st.expander(f"{PROMPT_SECTIONS[prompt['form_section']]['title']} - {prompt['field_name']} {status_text}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Opis:** {prompt.get('description', 'Ni opisa')}")
                    st.write(f"**Verzija:** {prompt['version']}")
                    st.write(f"**Uporab:** {prompt['usage_count']}")
                    st.write(f"**Ustvarjeno:** {prompt['created_at']}")
                    st.write(f"**Posodobljeno:** {prompt['updated_at']}")
                    st.code(prompt['prompt_text'], language="text")
                
                with col2:
                    if st.button(" Izbriši", key=f"del_prompt_{prompt['id']}", use_container_width=True):
                        if delete_prompt(prompt['id']):
                            st.success("Poziv izbrisan")
                            st.rerun()
    else:
        st.info(" Ni shranjenih pozivov")

def render_ai_search_interface():
    """Unified AI search interface for documents"""
    
    st.markdown("""
    <div style="background: var(--bg-secondary, #FAFAFA); 
                padding: 20px; border-radius: var(--radius-lg, 8px);
                border: 1px solid var(--border, #E5E5E5); margin-bottom: 24px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600; color: var(--text-primary, #000000);">AI Iskanje po dokumentih</h2>
        <p style="margin: 8px 0 0 0; color: var(--text-secondary, #666666); font-size: 14px;">Semantično iskanje po vseh naloženih dokumentih</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Preset scenarios
    st.markdown("###  Hitri scenariji")
    st.markdown("Izberite enega od pogostih scenarijev iskanja:")
    
    col1, col2, col3 = st.columns(3)
    
    # Check if we should trigger a preset search
    trigger_search = False
    preset_query = None
    
    with col1:
        if st.button(" **Povzetek dokumenta**\n\nCeloten pregled", use_container_width=True, key="preset_summary", 
                     help="Dobi povzetek celotnega dokumenta z glavnimi točkami"):
            preset_query = "Povzemi trenutni dokument - kaj so glavni pogoji, roki, zahteve in merila?"
            trigger_search = True
    
    with col2:
        if st.button(" **Zahteve ponudnika**\n\nPogoji sodelovanja", use_container_width=True, key="preset_requirements",
                     help="Preglej vse zahteve, reference in pogoje za ponudnike"):
            preset_query = "Kakšne so zahteve za ponudnike? Katere reference, certifikati in pogoji so potrebni?"
            trigger_search = True
    
    with col3:
        if st.button(" **Roki in vrednosti**\n\nKljučni datumi", use_container_width=True, key="preset_deadlines",
                     help="Najdi vse pomembne roke in finančne vrednosti"):
            preset_query = "Kateri so pomembni roki (oddaja, veljavnost, izvedba)? Kakšna je ocenjena vrednost?"
            trigger_search = True
    
    st.divider()
    
    # Use preset query if a scenario was selected
    if preset_query:
        search_query = preset_query
    else:
        search_query = st.text_area(
            "Vnesite iskalni pojem ali vprašanje",
            placeholder="npr. 'Kakšni so roki za oddajo ponudb?' ali 'pogoji za sodelovanje' ali 'reference za gradnje'",
            height=100,
            key="ai_unified_search"
        )
    
    # Search filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        doc_type_filter = st.selectbox(
            "Filter po tipu dokumenta",
            ["Vsi"] + list(DOCUMENT_TYPES.values()),
            key="search_doc_type_filter"
        )
    
    with col2:
        result_limit = st.slider(
            "Število rezultatov",
            min_value=5, max_value=50, value=10,
            key="search_result_limit"
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button(" Išči", type="primary", use_container_width=True)
    
    # Trigger search if preset was selected or search button clicked
    if (trigger_search and preset_query) or (search_btn and search_query):
        perform_ai_search(preset_query if trigger_search else search_query, doc_type_filter, result_limit)
    
    # Recent searches
    st.divider()
    col_title, col_clear = st.columns([3, 1])
    with col_title:
        st.markdown("###  Nedavna iskanja")
    with col_clear:
        if st.button(" Počisti vse", key="clear_all_queries", help="Izbriši vso zgodovino iskanj"):
            if delete_all_queries():
                st.rerun()
    
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT query_text, MAX(created_at) as last_used, MAX(id) as query_id
                FROM ai_query_log
                WHERE query_text IS NOT NULL
                GROUP BY query_text
                ORDER BY last_used DESC
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            if recent:
                for query, timestamp, query_id in recent:
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.text(query[:80] + '...' if len(query) > 80 else query)
                    with col2:
                        if st.button("Ponovi", key=f"repeat_{query_id}", use_container_width=True):
                            perform_ai_search(query, "Vsi", 10)
                    with col3:
                        if st.button("", key=f"delete_{query_id}", help="Izbriši to iskanje"):
                            if delete_single_query(query_text=query):
                                st.rerun()
            else:
                st.info("Ni nedavnih iskanj")
    except Exception as e:
        st.info("Zgodovina iskanj ni na voljo")

def perform_ai_search(query: str, doc_type_filter: str, limit: int):
    """Perform AI-powered semantic search"""
    try:
        from services.qdrant_crud_service import QdrantCRUDService
        
        with st.spinner("Iščem v dokumentih..."):
            crud_service = QdrantCRUDService()
            
            # Prepare filters
            filters = {}
            if doc_type_filter != "Vsi":
                # Find key for value
                for key, value in DOCUMENT_TYPES.items():
                    if value == doc_type_filter:
                        filters["document_type"] = key
                        break
            
            # Search
            results, total = crud_service.search_documents(
                query=query,
                filters=filters,
                limit=limit
            )
            
            # Check if this is a summary request
            from services.ai_response_service import AIResponseService
            ai_service = AIResponseService()
            
            is_summary_request = any(keyword in query.lower() for keyword in [
                "povzemi", "povzetek", "opiši", "kaj vsebuje", "kaj je v",
                "trenutni dokument", "ta dokument", "celoten dokument"
            ])
            
            # Log query with proper error handling
            try:
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO ai_query_log 
                        (query_text, response_text, confidence_score, response_time_seconds)
                        VALUES (?, ?, ?, ?)
                    """, (query, f"Found {total} results", 0.8, 1.0))
                    conn.commit()
            except Exception as e:
                st.warning(f"Opozorilo: Poizvedba ni bila shranjena v zgodovino. Napaka: {str(e)}")
                print(f"Error saving query to database: {e}")
            
            if results:
                # Always generate AI response (except for raw search)
                st.info(" Generiram odgovor...")
                
                # Generate AI response
                ai_response = ai_service.generate_response(
                    query=query,
                    chunks=results[:10],  # Use top 10 chunks for context
                    context_mode="document",
                    language="sl"
                )
                
                # Display AI response based on request type
                if is_summary_request:
                    # For summaries - full width, no chunks shown by default
                    st.markdown("###  Povzetek dokumenta")
                    st.markdown(f"""
                    <div style="background: var(--bg-secondary, #FAFAFA); 
                                padding: 20px; border-radius: var(--radius-md, 6px); 
                                border: 1px solid var(--border, #E5E5E5); margin: 20px 0;">
                        <div style="color: var(--text-primary, #000000);">{ai_response}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Source chunks in expander for summaries
                    with st.expander(" Viri (kosi dokumenta)", expanded=False):
                        for i, result in enumerate(results[:5], 1):
                            st.markdown(f"**{i}. {result.get('original_filename', 'Neznano')}** (del {result.get('chunk_index', '?')})")
                            st.text(result.get('chunk_text', '')[:200] + "...")
                    
                    st.success(f" Povzetek ustvarjen iz {min(10, len(results))} delov dokumenta")
                else:
                    # For Q&A - show answer AND relevant chunks
                    st.markdown("###  Odgovor AI")
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.05); 
                                padding: 20px; border-radius: var(--radius-md, 6px); 
                                border: 1px solid rgba(16, 185, 129, 0.2); margin: 20px 0;">
                        <div style="color: var(--text-primary, #000000);">{ai_response}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.success(f" Odgovor ustvarjen iz {min(10, len(results))} najdenih delov")
                    
                    # Show relevant chunks where answer was found
                    st.markdown("###  Relevantni deli dokumenta")
                    st.info("Tukaj so deli dokumenta, kjer je bil najden odgovor:")
                    
                    # Display top 5 most relevant chunks with evidence
                    for i, result in enumerate(results[:5], 1):
                        score = result.get('score', 0)
                        
                        # Determine relevance indicator
                        if score > 0.8:
                            relevance = " Visoka"
                            color = "green"
                        elif score > 0.6:
                            relevance = " Srednja"  
                            color = "yellow"
                        else:
                            relevance = " Nizka"
                            color = "red"
                        
                        with st.expander(f" Del {result.get('chunk_index', '?')}: {result.get('original_filename', 'Neznano')} - {relevance} ({score:.2f})", expanded=(i==1)):
                            # Show chunk metadata
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.caption(f"**Dokument:** {result.get('original_filename', 'Neznano')}")
                            with col2:
                                st.caption(f"**Del:** {result.get('chunk_index', '?')} od {result.get('total_chunks', '?')}")
                            with col3:
                                st.caption(f"**Relevanca:** {score:.0%}")
                            
                            # Show the actual text content
                            st.markdown("**Vsebina:**")
                            content = result.get('chunk_text', result.get('text', 'Ni vsebine'))
                            
                            # Highlight search terms in the content
                            highlighted = content
                            for term in query.split():
                                if len(term) > 2:
                                    highlighted = highlighted.replace(
                                        term.lower(), 
                                        f"<mark style='background: yellow; padding: 2px;'>{term.lower()}</mark>"
                                    )
                            
                            st.markdown(
                                f"<div style='padding: 12px; background: var(--bg-secondary, #FAFAFA); border: 1px solid var(--border, #E5E5E5); border-radius: var(--radius-md, 6px); font-size: 14px;'>{highlighted}</div>",
                                unsafe_allow_html=True
                            )
            else:
                st.warning("😕 Ni najdenih rezultatov za to poizvedbo")
                
    except ImportError:
        st.error(" AI iskanje ni na voljo - manjkajo potrebne knjižnice")
        st.info("Namestite: pip install qdrant-client openai")
    except Exception as e:
        st.error(f" Napaka pri iskanju: {str(e)}")

def render_query_interface():
    """Render the query interface with chat UI"""
    
    st.markdown("""
    <div class="ai-header">
        <h2> Iskanje po bazi znanja</h2>
        <p>Postavite vprašanje v naravnem jeziku</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'recent_queries' not in st.session_state:
        st.session_state.recent_queries = []
    
    # Query input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Vaše vprašanje:",
            placeholder="npr. Kakšni so roki za oddajo ponudb pri odprtem postopku?",
            key="query_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button(" Iskanje", key="search_btn", use_container_width=True)
    
    # Recent queries (suggestions)
    if st.session_state.recent_queries:
        st.markdown("**Nedavna iskanja:**")
        for i, recent in enumerate(st.session_state.recent_queries[-3:]):
            if st.button(f"↻ {recent}", key=f"recent_{i}"):
                st.session_state.query_input = recent
                st.rerun()
    
    # Process query
    if search_button and query:
        if not AI_PROCESSING_AVAILABLE:
            st.error("AI procesiranje ni na voljo. Preverite konfiguracijo.")
        else:
            with st.spinner("Iščem odgovor..."):
                try:
                    engine = QueryEngine()
                    result = engine.process_query(query)
                    
                    # Store in session
                    st.session_state.query_history.append(result)
                    
                    if query not in st.session_state.recent_queries:
                        st.session_state.recent_queries.append(query)
                        # Keep only last 10 recent queries
                        if len(st.session_state.recent_queries) > 10:
                            st.session_state.recent_queries.pop(0)
                            
                except Exception as e:
                    st.error(f"Napaka pri procesiranju poizvedbe: {str(e)}")
    
    # Display results
    if st.session_state.query_history:
        latest_result = st.session_state.query_history[-1]
        
        # Response card
        st.markdown("""
        <div style="
            background: white;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
        """, unsafe_allow_html=True)
        
        st.markdown(f"###  Odgovor")
        st.write(latest_result['response'])
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Čas odziva", f"{latest_result['response_time']:.2f}s")
        with col2:
            st.metric("Zanesljivost", f"{latest_result['confidence']:.0%}")
        with col3:
            st.metric("Viri", len(latest_result['sources']))
        
        # Sources
        if latest_result['sources']:
            with st.expander(" Viri"):
                for doc_id, source in latest_result['sources'].items():
                    st.write(f"**{source['name']}**")
                    st.write(f"*Tip:* {DOCUMENT_TYPES.get(source.get('tip_dokumenta', 'unknown'), 'Neznano')}")
                    st.write(f"*Relevantnost:* {source['confidence']:.0%}")
                    st.write(f"*Uporabljeni deli:* {', '.join(map(str, source['chunks']))}")
                    st.divider()
        
        # Actions with feedback
        col1, col2, col3, col4 = st.columns(4)
        
        query_id = latest_result.get('query_id')
        
        with col1:
            if st.button(" Kopiraj", key="copy_response"):
                # In a real implementation, this would copy to clipboard
                st.toast("Odgovor kopiran!", icon="")
        
        with col2:
            if st.button(" Všeč mi je", key="like_response"):
                if query_id:
                    update_query_feedback(query_id, 'positive')
                    st.success("Hvala za povratno informacijo!")
        
        with col3:
            if st.button("👎 Ni uporabno", key="dislike_response"):
                if query_id:
                    update_query_feedback(query_id, 'negative')
                    st.info("Hvala, bomo izboljšali!")
        
        with col4:
            if st.button(" Shrani", key="bookmark_response"):
                if query_id:
                    bookmark_query(query_id)
                    st.success("Odgovor shranjen!")
        
        # TODO(human): Add export button here
        # Use st.download_button to export latest_result as JSON
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Optional: Query history in main panel (collapsible)
    if st.session_state.query_history:
        st.markdown("---")
        with st.expander("📜 Zgodovina poizvedb", expanded=False):
            # Add clear all button at the top of the expander
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(" Počisti vse", key="clear_history_expander"):
                    if delete_all_queries():
                        st.rerun()
            
            # Create a clean table view of query history with delete buttons
            for idx, item in enumerate(reversed(st.session_state.query_history[-10:])):
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    query_text = item['query'][:80] + '...' if len(item['query']) > 80 else item['query']
                    st.markdown(f"**{query_text}**")
                    st.caption(f"⏱ {item['timestamp'].strftime('%H:%M:%S')} | "
                             f"💯 {item['confidence']:.0%} | "
                             f" {item['response_time']:.2f}s")
                
                with col2:
                    if st.button("Ponovi", key=f"repeat_hist_{idx}"):
                        perform_ai_search(item['query'], "Vsi", 10)
                
                with col3:
                    if st.button("", key=f"delete_hist_{idx}"):
                        if delete_single_query(query_text=item['query']):
                            st.rerun()
                
                st.divider()
            
            # Export button
            if st.session_state.query_history:
                history_data = []
                for item in reversed(st.session_state.query_history[-10:]):
                    history_data.append({
                        'Poizvedba': item['query'],
                        'Čas': item['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'Zanesljivost': f"{item['confidence']:.0%}",
                        'Odziv': f"{item['response_time']:.2f}s"
                    })
                
                if history_data:
                    df = pd.DataFrame(history_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label=" Izvozi zgodovino",
                        data=csv,
                        file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="export_query_history"
                    )


def update_query_feedback(query_id: int, feedback: str):
    """Update query feedback in database"""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_query_log 
                SET user_feedback = ?
                WHERE id = ?
            """, (feedback, query_id))
            conn.commit()
    except Exception as e:
        st.error(f"Napaka pri shranjevanju povratne informacije: {str(e)}")


def bookmark_query(query_id: int):
    """Bookmark a query response"""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_query_log 
                SET is_bookmarked = 1
                WHERE id = ?
            """, (query_id,))
            conn.commit()
    except Exception as e:
        st.error(f"Napaka pri shranjevanju: {str(e)}")


def export_query_result_to_json(query_result: Dict) -> str:
    """Export query result to JSON format"""
    export_data = {
        'query': query_result['query'],
        'response': query_result['response'],
        'sources': query_result['sources'],
        'confidence': query_result['confidence'],
        'response_time': query_result['response_time'],
        'timestamp': query_result['timestamp'].isoformat() if query_result.get('timestamp') else None
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)


def delete_single_query(query_text: str) -> bool:
    """Delete a single query from the database and session state"""
    try:
        # Delete from database
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM ai_query_log 
                WHERE query_text = ?
            """, (query_text,))
            conn.commit()
        
        # Remove from session state if present
        if 'query_history' in st.session_state:
            st.session_state.query_history = [
                q for q in st.session_state.query_history 
                if q.get('query') != query_text
            ]
        
        if 'recent_queries' in st.session_state:
            st.session_state.recent_queries = [
                q for q in st.session_state.recent_queries 
                if q != query_text
            ]
        
        return True
    except Exception as e:
        st.error(f"Napaka pri brisanju poizvedbe: {str(e)}")
        return False


def delete_all_queries() -> bool:
    """Delete all queries from the database and clear session state"""
    try:
        # Show confirmation dialog
        if 'confirm_delete_all' not in st.session_state:
            st.session_state.confirm_delete_all = False
        
        if not st.session_state.confirm_delete_all:
            st.warning("Ali ste prepričani, da želite izbrisati vso zgodovino iskanj?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(" Da, izbriši vse", key="confirm_yes"):
                    st.session_state.confirm_delete_all = True
                    st.rerun()
            with col2:
                if st.button(" Prekliči", key="confirm_no"):
                    return False
            return False
        
        # Delete from database
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_query_log")
            conn.commit()
        
        # Clear session state
        if 'query_history' in st.session_state:
            st.session_state.query_history = []
        if 'recent_queries' in st.session_state:
            st.session_state.recent_queries = []
        
        # Reset confirmation flag
        st.session_state.confirm_delete_all = False
        
        st.success("Vsa zgodovina iskanj je bila izbrisana!")
        return True
        
    except Exception as e:
        st.error(f"Napaka pri brisanju zgodovine: {str(e)}")
        return False


def generate_analytics_report(start_date, end_date) -> str:
    """Generate analytics report for export"""
    analytics = load_analytics_data(start_date, end_date)
    
    report = f"""
# AI System Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

## Overview
- Total Queries: {analytics['total_queries']}
- Queries Today: {analytics['queries_today']}
- Average Response Time: {analytics['avg_response_time']:.2f}s
- Total Documents: {analytics['total_documents']}
- New Documents (last 7 days): {analytics['new_documents']}
- Total Tokens Used: {analytics['total_tokens']:,}
- Estimated Cost: ${analytics['estimated_cost']:.2f}

## Top Queries
{analytics['top_queries'].to_string() if not analytics['top_queries'].empty else 'No query data available'}

## System Performance
- Response Time Trend: {analytics['response_time_trend']:.1%}
- Average Confidence Score: {analytics['top_queries']['Povp. zanesljivost'].mean() if not analytics['top_queries'].empty else 'N/A'}

## Notes
- Token cost estimation based on GPT-4 pricing ($0.01 per 1K tokens)
- Success rate based on user feedback when available
"""
    return report

def render_settings_panel():
    """Settings panel for configuration"""
    st.markdown("""
    <div style="background: var(--bg-secondary, #FAFAFA); 
                padding: 20px; border-radius: var(--radius-lg, 8px);
                border: 1px solid var(--border, #E5E5E5); margin-bottom: 24px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600; color: var(--text-primary, #000000);">Nastavitve</h2>
        <p style="margin: 8px 0 0 0; color: var(--text-secondary, #666666); font-size: 14px;">Konfiguracija AI sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status
    st.markdown("###  Status povezav")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        openai_status = " Povezan" if os.getenv('OPENAI_API_KEY') else " Ni povezan"
        st.metric("OpenAI API", openai_status)
    
    with col2:
        qdrant_status = " Povezan" if os.getenv('QDRANT_API_KEY') else " Ni povezan"
        st.metric("Qdrant API", qdrant_status)
    
    with col3:
        processing_status = " Aktivno" if AI_PROCESSING_AVAILABLE else " Neaktivno"
        st.metric("AI Procesiranje", processing_status)
    
    st.divider()
    
    # Processing settings
    st.markdown("###  Nastavitve procesiranja")
    
    # Model selection
    st.markdown("####  OpenAI Model")
    
    # Available OpenAI models with descriptions
    OPENAI_MODELS = {
        "gpt-5-nano": "GPT-5 Nano (prihodnji ultra-mini model)",
        "gpt-4.1-mini": "GPT-4.1 Mini (najnovejši mini model)",
        "gpt-4o-mini": "GPT-4o Mini (najhitrejši, najcenejši)",
        "gpt-4o-mini-2024-07-18": "GPT-4o Mini Juli 2024",
        "o1-mini": "O1 Mini (napredno sklepanje)",
        "o1-preview": "O1 Preview (kompleksno sklepanje)",
        "gpt-4o": "GPT-4o (hiter, multimodalni)",
        "gpt-4o-2024-08-06": "GPT-4o Avgust 2024",
        "gpt-4o-2024-05-13": "GPT-4o Maj 2024",
        "gpt-4-turbo": "GPT-4 Turbo (najnovejši)",
        "gpt-4-turbo-preview": "GPT-4 Turbo Preview",
        "gpt-4-turbo-2024-04-09": "GPT-4 Turbo April 2024",
        "gpt-4": "GPT-4 (zelo natančen)",
        "gpt-4-32k": "GPT-4 32K (dolg kontekst)",
        "gpt-4-0125-preview": "GPT-4 Turbo Januar 2024",
        "gpt-4-1106-preview": "GPT-4 Turbo November 2023",
        "gpt-3.5-turbo": "GPT-3.5 Turbo (cenovno ugoden)",
        "gpt-3.5-turbo-16k": "GPT-3.5 Turbo 16K (dolg kontekst)",
        "gpt-3.5-turbo-0125": "GPT-3.5 Turbo Januar 2024",
        "gpt-3.5-turbo-1106": "GPT-3.5 Turbo November 2023"
    }
    
    current_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Model selector
    selected_model = st.selectbox(
        "Izberi AI model",
        options=list(OPENAI_MODELS.keys()),
        index=list(OPENAI_MODELS.keys()).index(current_model) if current_model in OPENAI_MODELS else 0,
        format_func=lambda x: f"{x} - {OPENAI_MODELS[x]}",
        help="Različni modeli imajo različne zmogljivosti in cene"
    )
    
    # Save model selection to session state
    if 'selected_openai_model' not in st.session_state:
        st.session_state.selected_openai_model = selected_model
    else:
        st.session_state.selected_openai_model = selected_model
    
    # Show model info
    model_info = {
        "gpt-5-nano": {"context": "256K", "cost": "$", "speed": "Ultra hitra", "quality": "Odlična"},
        "gpt-4.1-mini": {"context": "128K", "cost": "$", "speed": "Zelo hitra", "quality": "Zelo dobra"},
        "gpt-4o-mini": {"context": "128K", "cost": "$", "speed": "Zelo hitra", "quality": "Dobra"},
        "gpt-4o-mini-2024-07-18": {"context": "128K", "cost": "$", "speed": "Zelo hitra", "quality": "Dobra"},
        "o1-mini": {"context": "128K", "cost": "$$", "speed": "Srednja", "quality": "Odlična*"},
        "o1-preview": {"context": "128K", "cost": "$$$$$", "speed": "Počasna", "quality": "Vrhunska*"},
        "gpt-4o": {"context": "128K", "cost": "$$$", "speed": "Hitra", "quality": "Odlična"},
        "gpt-4o-2024-08-06": {"context": "128K", "cost": "$$$", "speed": "Hitra", "quality": "Odlična"},
        "gpt-4o-2024-05-13": {"context": "128K", "cost": "$$$", "speed": "Hitra", "quality": "Odlična"},
        "gpt-4-turbo": {"context": "128K", "cost": "$$$$", "speed": "Srednja", "quality": "Odlična"},
        "gpt-4-turbo-preview": {"context": "128K", "cost": "$$$$", "speed": "Srednja", "quality": "Odlična"},
        "gpt-4-turbo-2024-04-09": {"context": "128K", "cost": "$$$$", "speed": "Srednja", "quality": "Odlična"},
        "gpt-4": {"context": "8K", "cost": "$$$$", "speed": "Počasna", "quality": "Odlična"},
        "gpt-4-32k": {"context": "32K", "cost": "$$$$$", "speed": "Počasna", "quality": "Odlična"},
        "gpt-4-0125-preview": {"context": "128K", "cost": "$$$$", "speed": "Srednja", "quality": "Odlična"},
        "gpt-4-1106-preview": {"context": "128K", "cost": "$$$$", "speed": "Srednja", "quality": "Odlična"},
        "gpt-3.5-turbo": {"context": "16K", "cost": "$$", "speed": "Hitra", "quality": "Dobra"},
        "gpt-3.5-turbo-16k": {"context": "16K", "cost": "$$", "speed": "Hitra", "quality": "Dobra"},
        "gpt-3.5-turbo-0125": {"context": "16K", "cost": "$$", "speed": "Hitra", "quality": "Dobra"},
        "gpt-3.5-turbo-1106": {"context": "16K", "cost": "$$", "speed": "Hitra", "quality": "Dobra"}
    }
    
    if selected_model in model_info:
        info = model_info[selected_model]
        col1_info, col2_info, col3_info, col4_info = st.columns(4)
        with col1_info:
            st.metric("Kontekst", info["context"])
        with col2_info:
            st.metric("Cena", info["cost"])
        with col3_info:
            st.metric("Hitrost", info["speed"])
        with col4_info:
            st.metric("Kvaliteta", info["quality"])
    
    st.divider()
    
    # Other settings
    st.markdown("####  Parametri procesiranja")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.number_input(
            "Velikost dela dokumenta (znakov)",
            min_value=100,
            max_value=5000,
            value=int(os.getenv('CHUNK_SIZE', 1000)),
            step=100,
            help="Število znakov v posameznem delu dokumenta"
        )
        
        chunk_overlap = st.number_input(
            "Prekrivanje delov (znakov)",
            min_value=0,
            max_value=500,
            value=int(os.getenv('CHUNK_OVERLAP', 200)),
            step=50,
            help="Število znakov, ki se prekrivajo med deli"
        )
    
    with col2:
        max_tokens = st.number_input(
            "Maksimalno število tokenov",
            min_value=100,
            max_value=4000,
            value=int(os.getenv('AI_MAX_TOKENS', 1000)),
            step=100,
            help="Maksimalno število tokenov za AI odgovor"
        )
        
        temperature = st.slider(
            "Temperatura (kreativnost)",
            min_value=0.0,
            max_value=1.0,
            value=float(os.getenv('AI_TEMPERATURE', 0.7)),
            step=0.1,
            help="Višja vrednost = bolj kreativni odgovori"
        )
    
    # Save settings button
    if st.button(" Shrani nastavitve", type="primary"):
        # Update environment variables (in memory)
        os.environ['OPENAI_MODEL'] = selected_model
        os.environ['CHUNK_SIZE'] = str(chunk_size)
        os.environ['CHUNK_OVERLAP'] = str(chunk_overlap)
        os.environ['AI_MAX_TOKENS'] = str(max_tokens)
        os.environ['AI_TEMPERATURE'] = str(temperature)
        
        # Also update .env file for persistence
        try:
            env_path = '.env'
            env_content = []
            
            # Read existing .env
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.readlines()
            
            # Update or add settings
            settings = {
                'OPENAI_MODEL': selected_model,
                'CHUNK_SIZE': str(chunk_size),
                'CHUNK_OVERLAP': str(chunk_overlap),
                'AI_MAX_TOKENS': str(max_tokens),
                'AI_TEMPERATURE': str(temperature)
            }
            
            # Update existing lines or prepare new ones
            updated = {key: False for key in settings}
            new_content = []
            
            for line in env_content:
                updated_line = False
                for key, value in settings.items():
                    if line.startswith(f'{key}='):
                        new_content.append(f'{key}={value}\n')
                        updated[key] = True
                        updated_line = True
                        break
                
                if not updated_line:
                    new_content.append(line)
            
            # Add any missing settings
            for key, value in settings.items():
                if not updated[key]:
                    new_content.append(f'{key}={value}\n')
            
            # Write back to .env
            with open(env_path, 'w') as f:
                f.writelines(new_content)
            
            st.success(f" Nastavitve shranjene! Model: {selected_model}")
            
        except Exception as e:
            st.error(f" Napaka pri shranjevanju: {str(e)}")
            st.info(" Nastavitve so shranjene v pomnilniku in se bodo uporabile do ponovnega zagona")
    
    st.info(" Nastavitve se bodo uporabile pri naslednjem procesiranju")

def render_analytics_dashboard():
    """Render analytics dashboard with charts and metrics"""
    
    st.markdown("""
    <div class="ai-header">
        <h2> Analitika AI sistema</h2>
        <p>Pregled uporabe in učinkovitosti</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Od datuma", 
            datetime.now() - timedelta(days=30),
            key="analytics_start_date"
        )
    with col2:
        end_date = st.date_input(
            "Do datuma", 
            datetime.now(),
            key="analytics_end_date"
        )
    
    # Load analytics data
    analytics = load_analytics_data(start_date, end_date)
    
    # Overview metrics
    st.markdown("###  Pregled")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Skupaj poizvedb",
            analytics['total_queries'],
            f"+{analytics['queries_today']} danes"
        )
    
    with col2:
        st.metric(
            "Povp. čas odziva",
            f"{analytics['avg_response_time']:.2f}s",
            f"{analytics['response_time_trend']:.1%}"
        )
    
    with col3:
        st.metric(
            "Dokumentov",
            analytics['total_documents'],
            f"+{analytics['new_documents']} novo"
        )
    
    with col4:
        st.metric(
            "Poraba tokenov",
            f"{analytics['total_tokens']:,}",
            f"~${analytics['estimated_cost']:.2f}"
        )
    
    # TODO(human): Add export analytics report button here
    # Use st.download_button with generate_analytics_report function
    
    # Charts tabs
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly ni nameščen. Grafi niso na voljo.")
        return
        
    tab1, tab2, tab3 = st.tabs([" Poizvedbe", " Prompti", " Učinkovitost"])
    
    with tab1:
        # Query volume over time
        if not analytics['daily_queries'].empty:
            fig = px.line(
                analytics['daily_queries'],
                x='date',
                y='count',
                title='Poizvedbe po dnevih',
                labels={'count': 'Število poizvedb', 'date': 'Datum'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top queries
        st.markdown("#### 🔝 Najpogostejše poizvedbe")
        if not analytics['top_queries'].empty:
            st.dataframe(
                analytics['top_queries'],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Ni podatkov o poizvedbah")
        
        # Bookmarked queries
        st.markdown("####  Shranjene poizvedbe")
        if not analytics['bookmarked_queries'].empty:
            for _, query in analytics['bookmarked_queries'].iterrows():
                with st.expander(f" {query['query_text'][:80]}..."):
                    st.write(f"**Odgovor:** {query['response_text']}")
                    st.write(f"**Zanesljivost:** {query['confidence_score']:.0%}")
                    st.write(f"**Datum:** {query['created_at']}")
        else:
            st.info("Ni shranjenih poizvedb")
    
    with tab2:
        # Prompt usage by form section
        if not analytics['prompt_usage'].empty:
            fig = px.pie(
                analytics['prompt_usage'],
                values='count',
                names='form_section',
                title='Uporaba promptov po sekcijah',
                color_discrete_sequence=px.colors.sequential.Purples
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Prompt performance
        st.markdown("####  Učinkovitost promptov")
        if not analytics['prompt_performance'].empty:
            st.dataframe(
                analytics['prompt_performance'],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Ni podatkov o promptih")
    
    with tab3:
        # Response time distribution
        if not analytics['response_times'].empty:
            fig = px.histogram(
                analytics['response_times'],
                x='response_time',
                nbins=20,
                title='Porazdelitev časov odziva',
                labels={'response_time': 'Čas odziva (s)', 'count': 'Število'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Success rate over time (based on feedback)
        if not analytics['daily_success'].empty:
            fig = px.area(
                analytics['daily_success'],
                x='date',
                y='success_rate',
                title='Uspešnost odgovorov (na podlagi povratnih informacij)',
                labels={'success_rate': 'Uspešnost (%)', 'date': 'Datum'}
            )
            fig.update_yaxes(range=[0, 100])
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Token usage over time
        if not analytics['daily_tokens'].empty:
            fig = px.bar(
                analytics['daily_tokens'],
                x='date',
                y='tokens',
                title='Poraba tokenov po dnevih',
                labels={'tokens': 'Število tokenov', 'date': 'Datum'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)


def load_analytics_data(start_date, end_date):
    """Load analytics data from database"""
    
    analytics = {
        'total_queries': 0,
        'queries_today': 0,
        'avg_response_time': 0.0,
        'response_time_trend': 0.0,
        'total_documents': 0,
        'new_documents': 0,
        'total_tokens': 0,
        'estimated_cost': 0.0,
        'daily_queries': pd.DataFrame(),
        'top_queries': pd.DataFrame(),
        'bookmarked_queries': pd.DataFrame(),
        'prompt_usage': pd.DataFrame(),
        'prompt_performance': pd.DataFrame(),
        'response_times': pd.DataFrame(),
        'daily_success': pd.DataFrame(),
        'daily_tokens': pd.DataFrame()
    }
    
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            # Convert dates to string format for SQLite
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # Total queries
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM ai_query_log 
                WHERE created_at BETWEEN ? AND ?
            """, (start_str, end_str))
            analytics['total_queries'] = cursor.fetchone()[0] or 0
            
            # Queries today
            cursor.execute("""
                SELECT COUNT(*) FROM ai_query_log 
                WHERE DATE(created_at) = DATE(?)
            """, (today_str,))
            analytics['queries_today'] = cursor.fetchone()[0] or 0
            
            # Average response time
            cursor.execute("""
                SELECT AVG(response_time_seconds) FROM ai_query_log 
                WHERE created_at BETWEEN ? AND ?
            """, (start_str, end_str))
            result = cursor.fetchone()[0]
            analytics['avg_response_time'] = result if result else 0.0
            
            # Response time trend (compare to previous period)
            prev_start = (start_date - (end_date - start_date)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT AVG(response_time_seconds) FROM ai_query_log 
                WHERE created_at BETWEEN ? AND ?
            """, (prev_start, start_str))
            prev_avg = cursor.fetchone()[0]
            if prev_avg and analytics['avg_response_time']:
                analytics['response_time_trend'] = (
                    (analytics['avg_response_time'] - prev_avg) / prev_avg
                )
            
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM ai_documents")
            analytics['total_documents'] = cursor.fetchone()[0] or 0
            
            # New documents (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM ai_documents 
                WHERE DATE(upload_date) >= DATE('now', '-7 days')
            """)
            analytics['new_documents'] = cursor.fetchone()[0] or 0
            
            # Total tokens
            cursor.execute("""
                SELECT SUM(tokens_used) FROM ai_query_log 
                WHERE created_at BETWEEN ? AND ?
            """, (start_str, end_str))
            result = cursor.fetchone()[0]
            analytics['total_tokens'] = result if result else 0
            
            # Estimated cost (rough estimate: $0.01 per 1K tokens for GPT-4)
            analytics['estimated_cost'] = analytics['total_tokens'] * 0.00001
            
            # Daily queries
            daily_queries_df = pd.read_sql_query("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM ai_query_log
                WHERE created_at BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn, params=(start_str, end_str))
            
            if not daily_queries_df.empty:
                daily_queries_df['date'] = pd.to_datetime(daily_queries_df['date'])
                analytics['daily_queries'] = daily_queries_df
            
            # Top queries (by similarity)
            top_queries_df = pd.read_sql_query("""
                SELECT 
                    query_text as 'Poizvedba',
                    COUNT(*) as 'Število',
                    AVG(response_time_seconds) as 'Povp. čas (s)',
                    AVG(confidence_score) as 'Povp. zanesljivost'
                FROM ai_query_log
                WHERE created_at BETWEEN ? AND ?
                GROUP BY query_text
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """, conn, params=(start_str, end_str))
            
            if not top_queries_df.empty:
                top_queries_df['Povp. čas (s)'] = top_queries_df['Povp. čas (s)'].round(2)
                top_queries_df['Povp. zanesljivost'] = (
                    top_queries_df['Povp. zanesljivost'] * 100
                ).round(0).astype(str) + '%'
                analytics['top_queries'] = top_queries_df
            
            # Bookmarked queries
            bookmarked_df = pd.read_sql_query("""
                SELECT query_text, response_text, confidence_score, created_at
                FROM ai_query_log
                WHERE is_bookmarked = 1 AND created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
                LIMIT 10
            """, conn, params=(start_str, end_str))
            analytics['bookmarked_queries'] = bookmarked_df
            
            # Prompt usage
            prompt_usage_df = pd.read_sql_query("""
                SELECT form_section, COUNT(*) as count
                FROM ai_prompt_usage_log
                WHERE created_at BETWEEN ? AND ?
                GROUP BY form_section
            """, conn, params=(start_str, end_str))
            analytics['prompt_usage'] = prompt_usage_df
            
            # Prompt performance
            prompt_perf_df = pd.read_sql_query("""
                SELECT 
                    p.field_name as 'Prompt',
                    p.usage_count as 'Uporab',
                    AVG(l.tokens_used) as 'Povp. tokeni',
                    p.form_section as 'Sekcija'
                FROM ai_system_prompts p
                LEFT JOIN ai_prompt_usage_log l ON p.id = l.prompt_id
                WHERE l.created_at BETWEEN ? AND ?
                GROUP BY p.id
                ORDER BY p.usage_count DESC
                LIMIT 10
            """, conn, params=(start_str, end_str))
            
            if not prompt_perf_df.empty:
                prompt_perf_df['Povp. tokeni'] = prompt_perf_df['Povp. tokeni'].round(0)
                analytics['prompt_performance'] = prompt_perf_df
            
            # Response times distribution
            response_times_df = pd.read_sql_query("""
                SELECT response_time_seconds as response_time
                FROM ai_query_log
                WHERE created_at BETWEEN ? AND ?
            """, conn, params=(start_str, end_str))
            analytics['response_times'] = response_times_df
            
            # Daily success rate (based on feedback)
            daily_success_df = pd.read_sql_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(CASE WHEN user_feedback = 'positive' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(CASE WHEN user_feedback IS NOT NULL THEN 1 END), 0) as success_rate
                FROM ai_query_log
                WHERE created_at BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn, params=(start_str, end_str))
            
            if not daily_success_df.empty:
                daily_success_df['date'] = pd.to_datetime(daily_success_df['date'])
                # Fill NaN with 85% default
                daily_success_df['success_rate'] = daily_success_df['success_rate'].fillna(85)
                analytics['daily_success'] = daily_success_df
            
            # Daily token usage
            daily_tokens_df = pd.read_sql_query("""
                SELECT 
                    DATE(created_at) as date,
                    SUM(tokens_used) as tokens
                FROM ai_query_log
                WHERE created_at BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn, params=(start_str, end_str))
            
            if not daily_tokens_df.empty:
                daily_tokens_df['date'] = pd.to_datetime(daily_tokens_df['date'])
                analytics['daily_tokens'] = daily_tokens_df
            
    except Exception as e:
        st.error(f"Napaka pri nalaganju analitike: {str(e)}")
    
    return analytics

# Helper functions

def save_document(file, tip_dokumenta: str, description: str = None, tags: str = None) -> Optional[int]:
    """Save document with categorization and vector processing"""
    try:
        # Generate unique IDs
        file_id = str(uuid.uuid4())
        document_id = f"doc_{file_id[:8]}"
        file_extension = Path(file.name).suffix
        
        # Create directory structure
        doc_dir = Path(f"data/documents/{tip_dokumenta}")
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = doc_dir / f"{file_id}{file_extension}"
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        
        # Save metadata to database with both schemas
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_documents 
                (filename, file_path, tip_dokumenta, document_type, file_type, file_size, 
                 description, tags, document_id, original_filename, file_format,
                 upload_date, created_at, processing_status, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'pending', 'pending')
            """, (
                file.name,
                str(file_path),
                tip_dokumenta,
                tip_dokumenta,  # Use tip_dokumenta as document_type
                file_extension,
                file.size,
                description,
                tags,
                document_id,
                file.name,
                file_extension.lower().replace('.', '')
            ))
            conn.commit()
            doc_db_id = cursor.lastrowid
            
        # Process document for vector database if enabled
        if st.session_state.get('enable_vector_processing', True):
            try:
                from services.qdrant_document_processor import QdrantDocumentProcessor
                
                with st.spinner(f"Processing document for AI search..."):
                    processor = QdrantDocumentProcessor()
                    
                    # Prepare metadata without organization (for all organizations)
                    metadata = {
                        "document_id": document_id,
                        "document_type": tip_dokumenta,
                        "file_format": file_extension.lower().replace('.', ''),
                        "description": description or "",
                        "tags": tags or "",
                        "original_filename": file.name
                    }
                    
                    # Process document
                    result = processor.process_document(
                        str(file_path),
                        metadata,
                        progress_callback=None  # Could add progress tracking here
                    )
                    
                    if result.get("status") == "success":
                        # Update processing status
                        with sqlite3.connect(database.DATABASE_FILE) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE ai_documents 
                                SET processing_status = 'completed',
                                    status = 'completed',
                                    processed_at = CURRENT_TIMESTAMP,
                                    chunks_count = ?,
                                    chunk_count = ?,
                                    vectors_count = ?,
                                    extraction_method = ?
                                WHERE id = ?
                            """, (
                                result.get("chunks_created", 0),
                                result.get("chunks_created", 0),
                                result.get("vectors_created", 0),
                                result.get("extraction_method", "unknown"),
                                doc_db_id
                            ))
                            conn.commit()
                        
                        st.success(f" Document processed: {result.get('chunks_created', 0)} chunks, {result.get('vectors_created', 0)} vectors created")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        if 'image' in error_msg.lower() or 'ocr' in error_msg.lower():
                            st.warning(" Document saved but appears to be scanned/image PDF. OCR processing not available yet.")
                            st.info(" The document is stored and can be manually reviewed.")
                        else:
                            st.warning(f" Document saved but vector processing incomplete: {error_msg}")
                        
            except ImportError:
                st.info(" Vector processing not available - document saved for regular use")
            except Exception as e:
                error_str = str(e)
                if 'pdf' in error_str.lower() and 'image' in error_str.lower():
                    st.warning(" Document saved. This appears to be a scanned PDF that requires OCR.")
                    st.info(" The document is stored for manual review. Text extraction from images will be added in future updates.")
                else:
                    st.warning(f" Document saved but vector processing failed: {error_str}")
                    
                # Update status to indicate processing failed but document is saved
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE ai_documents 
                        SET processing_status = 'partial',
                            status = 'partial'
                        WHERE id = ?
                    """, (doc_db_id,))
                    conn.commit()
        
        return doc_db_id
    except Exception as e:
        st.error(f"Napaka pri shranjevanju: {str(e)}")
        return None

def load_documents(document_types: List[str] = None, search_query: str = None) -> List[Dict]:
    """Load documents with optional filtering"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM ai_documents WHERE 1=1"
        params = []
        
        if document_types:
            placeholders = ','.join(['?' for _ in document_types])
            query += f" AND tip_dokumenta IN ({placeholders})"
            params.extend(document_types)
        
        if search_query:
            query += " AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Try both column names for compatibility
        # upload_date is from original AI Manager, created_at is from Vector Database
        query += " ORDER BY COALESCE(upload_date, created_at, datetime('now')) DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def reprocess_document(doc_id: int, file_path: str = None) -> bool:
    """Reprocess document for vector database"""
    try:
        # Get document info if file_path not provided
        if not file_path:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path, tip_dokumenta, description, tags FROM ai_documents WHERE id = ?", (doc_id,))
                result = cursor.fetchone()
                if not result:
                    return False
                file_path, tip_dokumenta, description, tags = result
        else:
            # Get metadata from database
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT tip_dokumenta, description, tags, document_id FROM ai_documents WHERE id = ?", (doc_id,))
                result = cursor.fetchone()
                if result:
                    tip_dokumenta, description, tags, document_id = result
                else:
                    tip_dokumenta = 'general'
                    description = ''
                    tags = ''
                    document_id = f"doc_{str(uuid.uuid4())[:8]}"
        
        # Process with Qdrant
        from services.qdrant_document_processor import QdrantDocumentProcessor
        processor = QdrantDocumentProcessor()
        
        metadata = {
            "document_id": document_id,
            "document_type": tip_dokumenta,
            "description": description or "",
            "tags": tags or ""
        }
        
        result = processor.process_document(file_path, metadata)
        
        if result.get("status") == "success":
            # Update database
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE ai_documents 
                    SET processing_status = 'completed',
                        status = 'completed',
                        processed_at = CURRENT_TIMESTAMP,
                        chunks_count = ?,
                        chunk_count = ?,
                        vectors_count = ?
                    WHERE id = ?
                """, (
                    result.get("chunks_created", 0),
                    result.get("chunks_created", 0),
                    result.get("vectors_created", 0),
                    doc_id
                ))
                conn.commit()
            return True
    except Exception as e:
        st.error(f"Napaka pri ponovnem procesiranju: {str(e)}")
        return False
    return False

def delete_document_with_vectors(doc_id: int, document_id: str = None) -> bool:
    """Delete document and its vectors from both database and Qdrant"""
    try:
        # Get document info
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, document_id FROM ai_documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            if not result:
                return False
            file_path, doc_document_id = result
            
            # Use provided document_id or the one from database
            if not document_id:
                document_id = doc_document_id
        
        # Delete from Qdrant if document_id exists
        if document_id:
            try:
                from services.qdrant_crud_service import QdrantCRUDService
                crud_service = QdrantCRUDService()
                crud_service.delete_document(document_id)
            except Exception as e:
                st.warning(f"Vektorji morda niso bili izbrisani: {str(e)}")
        
        # Delete file
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
        
        # Delete from database
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_documents WHERE id = ?", (doc_id,))
            # Also try to delete from chunks table if exists
            cursor.execute("DELETE FROM ai_document_chunks WHERE document_id = ?", (document_id,)) if document_id else None
            conn.commit()
        
        return True
    except Exception as e:
        st.error(f"Napaka pri brisanju: {str(e)}")
        return False

def delete_document(doc_id: int) -> bool:
    """Delete document and its file"""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Get file path
            cursor.execute("SELECT file_path FROM ai_documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                
                # Delete file if exists
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Delete from database
                cursor.execute("DELETE FROM ai_documents WHERE id = ?", (doc_id,))
                conn.commit()
                return True
        return False
    except Exception as e:
        st.error(f"Napaka pri brisanju: {str(e)}")
        return False

def get_prompt(prompt_key: str) -> Optional[Dict]:
    """Get a prompt by key"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_system_prompts 
            WHERE prompt_key = ?
        """, (prompt_key,))
        result = cursor.fetchone()
        return dict(result) if result else None

def save_prompt(prompt_key: str, form_section: str, field_name: str, 
                prompt_text: str, description: str, is_active: bool) -> bool:
    """Save or update a prompt"""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Check if exists
            existing = get_prompt(prompt_key)
            
            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE ai_system_prompts 
                    SET prompt_text = ?, description = ?, is_active = ?, 
                        version = version + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE prompt_key = ?
                """, (prompt_text, description, is_active, prompt_key))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO ai_system_prompts 
                    (prompt_key, form_section, field_name, prompt_text, description, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (prompt_key, form_section, field_name, prompt_text, description, is_active))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Napaka pri shranjevanju poziva: {str(e)}")
        return False

def load_all_prompts() -> List[Dict]:
    """Load all prompts"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_system_prompts 
            ORDER BY form_section, field_name
        """)
        return [dict(row) for row in cursor.fetchall()]

def delete_prompt(prompt_id: int) -> bool:
    """Delete a prompt"""
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_system_prompts WHERE id = ?", (prompt_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Napaka pri brisanju: {str(e)}")
        return False

def get_default_prompt(section: str, field: str) -> str:
    """Get default prompt for a field"""
    default_prompts = {
        'vrsta_narocila_posebne_zahteve_sofinancerja': """
Ti si AI asistent za javna naročila. Na podlagi konteksta dokumentov in podatkov obrazca 
generiraj ustrezne posebne zahteve sofinancerja. Zahteve morajo biti:
- Specifične in merljive
- Skladne z zakonodajo o javnih naročilih
- Relevantne za vrsto naročila
- Napisane v slovenščini
Odgovori samo s konkretnimi zahtevami, brez dodatnih pojasnil.
""",
        'pogajanja_posebne_zelje_pogajanja': """
Ti si AI asistent za javna naročila. Generiraj predloge za posebne želje v zvezi s pogajanji.
Predlogi morajo biti:
- Realistični in izvedljivi
- V skladu s postopkom pogajanj
- Usmerjeni v optimizacijo ponudb
- Napisani v slovenščini
Odgovori samo s konkretnimi predlogi.
""",
        'pogoji_sodelovanje_ustreznost_poklicna_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za poklicno ustreznost.
Pogoji morajo biti:
- Relevantni za predmet naročila
- Sorazmerni in nediskriminatorni
- Preverljivi z dokazili
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
        'pogoji_sodelovanje_ekonomski_polozaj_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za ekonomski in finančni položaj.
Pogoji morajo biti:
- Sorazmerni z vrednostjo naročila
- Objektivno preverljivi
- V skladu z ZJN-3
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
        'pogoji_sodelovanje_tehnicna_sposobnost_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za tehnično in strokovno sposobnost.
Pogoji morajo biti:
- Povezani s predmetom naročila
- Objektivno merljivi
- Razumni in dosegljivi
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
        'variante_merila_merila_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatna merila za ocenjevanje ponudb.
Merila morajo biti:
- Povezana s predmetom naročila
- Objektivna in merljiva
- Z jasno metodologijo točkovanja
- Napisana v slovenščini
Odgovori samo s konkretnimi merili in načinom točkovanja.
"""
    }
    
    prompt_key = f"{section}_{field}"
    return default_prompts.get(prompt_key, "Generiraj ustrezen predlog za to polje na podlagi konteksta.")


# Query Engine Implementation
class QueryEngine:
    """RAG implementation for knowledge base queries"""
    
    def __init__(self):
        if AI_PROCESSING_AVAILABLE:
            self.embedding_gen = EmbeddingGenerator()
            self.vector_store = VectorStoreManager()
        else:
            self.embedding_gen = None
            self.vector_store = None
            
        if openai:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                self.openai_client = None
        else:
            self.openai_client = None
    
    def process_query(self, query: str, top_k: int = 5) -> Dict:
        """Process user query through RAG pipeline"""
        
        start_time = datetime.now()
        
        try:
            # 1. Generate query embedding
            if not self.embedding_gen:
                raise ValueError("Embedding generator not available")
                
            query_embedding = self.embedding_gen.generate_single_embedding(query)
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # 2. Search similar chunks in Qdrant
            search_results = self.vector_store.search(
                query_vector=query_embedding,
                top_k=top_k
            )
            
            # 3. Assemble context
            context_chunks = []
            sources = {}
            
            for hit in search_results:
                chunk_text = hit.payload.get('text', '')
                doc_id = hit.payload.get('document_id', 0)
                confidence = hit.score
                
                context_chunks.append(chunk_text)
                
                # Get document name
                if doc_id not in sources:
                    sources[doc_id] = {
                        'name': hit.payload.get('filename', 'Unknown'),
                        'confidence': confidence,
                        'chunks': [],
                        'tip_dokumenta': hit.payload.get('tip_dokumenta', 'unknown')
                    }
                sources[doc_id]['chunks'].append(hit.payload.get('chunk_index', 0))
            
            # 4. Generate response
            response = self.generate_response(query, context_chunks)
            
            # 5. Calculate metrics
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Calculate confidence score
            avg_confidence = sum(s['confidence'] for s in sources.values()) / len(sources) if sources else 0
            
            # 6. Log query
            query_id = self.log_query(query, response, sources, response_time, avg_confidence)
            
            return {
                'query': query,
                'response': response,
                'sources': sources,
                'response_time': response_time,
                'timestamp': datetime.now(),
                'confidence': avg_confidence,
                'query_id': query_id
            }
            
        except Exception as e:
            # Return error response
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                'query': query,
                'response': f"Napaka pri iskanju: {str(e)}",
                'sources': {},
                'response_time': response_time,
                'timestamp': datetime.now(),
                'confidence': 0,
                'query_id': None
            }
    
    def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using OpenAI"""
        
        if not self.openai_client:
            return "OpenAI API ni na voljo. Preverite konfiguracijo."
        
        if not context_chunks:
            return "Ni najdenih relevantnih dokumentov za vaše vprašanje."
        
        context = "\n\n".join(context_chunks)
        
        messages = [
            {"role": "system", "content": """
Si AI asistent za javna naročila. Odgovori na vprašanje na podlagi podanega konteksta.
Če informacije ni v kontekstu, to jasno povej.
Odgovori v slovenščini.
Bodi konkreten in jedrnat.
"""},
            {"role": "user", "content": f"""
Kontekst:
{context}

Vprašanje: {query}
"""}
        ]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                messages=messages,
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=int(os.getenv('AI_MAX_TOKENS', 1000))
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Napaka pri generiranju odgovora: {str(e)}"
    
    def log_query(self, query: str, response: str, sources: Dict, 
                  response_time: float, confidence: float) -> Optional[int]:
        """Log query to database for analytics"""
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                
                # Estimate tokens (rough approximation)
                tokens_used = (len(query) + len(response)) // 4
                
                # Insert query log
                cursor.execute("""
                    INSERT INTO ai_query_log 
                    (query_text, response_text, sources_json, response_time_seconds, 
                     confidence_score, tokens_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    query,
                    response,
                    json.dumps(sources, ensure_ascii=False),
                    response_time,
                    confidence,
                    tokens_used
                ))
                
                query_id = cursor.lastrowid
                
                # Insert source references
                for doc_id, source_info in sources.items():
                    cursor.execute("""
                        INSERT INTO ai_query_sources 
                        (query_id, document_id, document_name, chunk_indices, relevance_score)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        query_id,
                        doc_id,
                        source_info['name'],
                        json.dumps(source_info['chunks']),
                        source_info['confidence']
                    ))
                
                conn.commit()
                return query_id
                
        except Exception as e:
            st.error(f"Napaka pri beleženju poizvedbe: {str(e)}")
            return None
    
    def get_document_name(self, doc_id: int) -> str:
        """Get document name by ID"""
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT filename FROM ai_documents WHERE id = ?", (doc_id,))
                result = cursor.fetchone()
                return result[0] if result else "Unknown"
        except:
            return "Unknown"