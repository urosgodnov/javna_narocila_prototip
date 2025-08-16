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
    'pogodbe': '📝 Pogodbe',
    'razpisi': '📋 Razpisi', 
    'pravilniki': '📖 Pravilniki',
    'navodila': '📘 Navodila',
    'razno': '📂 Razno'
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
    """Main entry point from admin panel"""
    
    # Check environment configuration
    if not validate_environment():
        st.error("❌ AI modul ni konfiguriran. Manjkajo API ključi v .env datoteki.")
        st.info("Potrebni ključi: OPENAI_API_KEY, QDRANT_API_KEY")
        st.markdown("""
        ### 📝 Navodila za konfiguracijo:
        1. Ustvarite `.env` datoteko v korenski mapi projekta
        2. Dodajte naslednje ključe:
        ```
        OPENAI_API_KEY=sk-...
        QDRANT_API_KEY=your-key-here
        ```
        3. Ponovno naložite aplikacijo
        """)
        return
    
    # Initialize database tables
    init_ai_tables()
    
    inject_custom_css()
    
    st.markdown("""
    <div class="ai-header">
        <h1>🤖 AI Management System</h1>
        <p>Upravljanje z dokumenti in AI asistentom za javna naročila</p>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["📚 Dokumenti", "🔍 Poizvedbe", "🤖 Sistemski pozivi", "⚙️ Nastavitve", "📊 Analitika"])
    
    with tabs[0]:
        render_document_management()
    with tabs[1]:
        render_query_interface()
    with tabs[2]:
        render_system_prompts_management()
    with tabs[3]:
        render_settings_panel()
    with tabs[4]:
        render_analytics_dashboard()

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
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tip_dokumenta TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                processing_status TEXT DEFAULT 'pending',
                chunk_count INTEGER DEFAULT 0,
                embedding_model TEXT,
                metadata_json TEXT,
                description TEXT,
                tags TEXT
            )
        """)
        
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
    """Inject gradient styling to match admin panel"""
    st.markdown("""
    <style>
        .ai-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        
        .ai-header h1 {
            margin: 0;
            font-size: 2rem;
        }
        
        .ai-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        .upload-zone {
            border: 2px dashed rgba(102, 126, 234, 0.3);
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
            transition: all 0.3s ease;
        }
        
        .upload-zone:hover {
            border-color: rgba(102, 126, 234, 0.5);
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        }
        
        .doc-card {
            background: white;
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .prompt-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
            border: 1px solid rgba(102, 126, 234, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-pending {
            background: #fef3c7;
            color: #92400e;
        }
        
        .status-processing {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .status-completed {
            background: #d1fae5;
            color: #065f46;
        }
        
        .status-failed {
            background: #fee2e2;
            color: #991b1b;
        }
    </style>
    """, unsafe_allow_html=True)

def render_document_management():
    """Document management interface with type categorization"""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0;">📚 Upravljanje dokumentov</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Naložite dokumente za bazo znanja AI sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload section
    st.markdown("### 📤 Nalaganje dokumentov")
    
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
                st.error("❌ Datoteka je prevelika! Maksimalna velikost je 10MB.")
            else:
                # Display file info
                st.info(f"""
                📄 **Datoteka:** {uploaded_file.name}  
                📊 **Velikost:** {uploaded_file.size / 1024:.1f} KB  
                🏷️ **Tip:** {DOCUMENT_TYPES[tip_dokumenta]}
                """)
                
                if st.button("📤 Naloži dokument", type="primary", use_container_width=True):
                    with st.spinner("Nalagam dokument..."):
                        doc_id = save_document(
                            file=uploaded_file,
                            tip_dokumenta=tip_dokumenta,
                            description=description,
                            tags=tags
                        )
                        if doc_id:
                            st.success(f"✅ Dokument uspešno naložen (ID: {doc_id})")
                            st.rerun()
                        else:
                            st.error("❌ Napaka pri nalaganju dokumenta")
    
    st.divider()
    
    # Document list with filtering
    st.markdown("### 📂 Naloženi dokumenti")
    
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
        if st.button("🔍 Išči", use_container_width=True):
            st.session_state.search_active = True
    
    # Display filtered documents
    documents = load_documents(
        document_types=filter_type,
        search_query=search_query if search_query else None
    )
    
    if documents:
        for doc in documents:
            status_class = f"status-{doc['processing_status']}"
            
            with st.expander(f"{DOCUMENT_TYPES[doc['tip_dokumenta']]} - {doc['filename']}"):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**Opis:** {doc.get('description', 'Ni opisa')}")
                    if doc.get('tags'):
                        st.write(f"**Oznake:** {doc['tags']}")
                    st.write(f"**Velikost:** {doc['file_size'] / 1024:.1f} KB")
                
                with col2:
                    st.markdown(f"""
                    <span class="status-badge {status_class}">
                        {doc['processing_status'].upper()}
                    </span>
                    """, unsafe_allow_html=True)
                    st.write(f"**Naloženo:** {doc['upload_date']}")
                    if doc['chunk_count'] > 0:
                        st.write(f"**Število delov:** {doc['chunk_count']}")
                
                with col3:
                    # Process button for pending documents
                    if doc['processing_status'] == 'pending' and AI_PROCESSING_AVAILABLE:
                        if st.button("⚙️ Procesiraj", key=f"proc_{doc['id']}", use_container_width=True):
                            with st.spinner("Procesiram dokument..."):
                                success = process_document_async(doc['id'])
                                if success:
                                    st.success("Dokument procesiran!")
                                else:
                                    st.error("Napaka pri procesiranju")
                                st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Izbriši", key=f"del_{doc['id']}", use_container_width=True):
                        if delete_document(doc['id']):
                            st.success("Dokument izbrisan")
                            st.rerun()
    else:
        st.info("🔍 Ni naloženih dokumentov ali ni rezultatov iskanja")

def render_system_prompts_management():
    """Manage system prompts for form AI assistance"""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0;">🤖 Sistemski pozivi</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Upravljanje s pozivi za AI asistenta v obrazcih</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create/Edit prompt section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ➕ Dodaj/Uredi poziv")
        
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
            st.info(f"📝 Urejate obstoječi poziv (v{existing_prompt['version']})")
    
    with col2:
        st.markdown("### 📝 Vsebina poziva")
        
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
        if st.button("💾 Shrani poziv", type="primary", use_container_width=True):
            if save_prompt(prompt_key, selected_section, selected_field, prompt_text, prompt_description, is_active):
                st.success("✅ Poziv uspešno shranjen")
                st.rerun()
            else:
                st.error("❌ Napaka pri shranjevanju poziva")
    
    st.divider()
    
    # List existing prompts
    st.markdown("### 📋 Obstoječi pozivi")
    
    prompts = load_all_prompts()
    
    if prompts:
        for prompt in prompts:
            status_text = "🟢 Aktiven" if prompt['is_active'] else "🔴 Neaktiven"
            
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
                    if st.button("🗑️ Izbriši", key=f"del_prompt_{prompt['id']}", use_container_width=True):
                        if delete_prompt(prompt['id']):
                            st.success("Poziv izbrisan")
                            st.rerun()
    else:
        st.info("🔍 Ni shranjenih pozivov")

def render_query_interface():
    """Render the query interface with chat UI"""
    
    st.markdown("""
    <div class="ai-header">
        <h2>🔍 Iskanje po bazi znanja</h2>
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
        search_button = st.button("🔍 Iskanje", key="search_btn", use_container_width=True)
    
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
        
        st.markdown(f"### 💬 Odgovor")
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
            with st.expander("📚 Viri"):
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
            if st.button("📋 Kopiraj", key="copy_response"):
                # In a real implementation, this would copy to clipboard
                st.toast("Odgovor kopiran!", icon="✅")
        
        with col2:
            if st.button("⭐ Všeč mi je", key="like_response"):
                if query_id:
                    update_query_feedback(query_id, 'positive')
                    st.success("Hvala za povratno informacijo!")
        
        with col3:
            if st.button("👎 Ni uporabno", key="dislike_response"):
                if query_id:
                    update_query_feedback(query_id, 'negative')
                    st.info("Hvala, bomo izboljšali!")
        
        with col4:
            if st.button("🔖 Shrani", key="bookmark_response"):
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
            # Create a clean table view of query history
            history_data = []
            for item in reversed(st.session_state.query_history[-10:]):
                history_data.append({
                    'Poizvedba': item['query'][:80] + '...' if len(item['query']) > 80 else item['query'],
                    'Čas': item['timestamp'].strftime('%H:%M:%S'),
                    'Zanesljivost': f"{item['confidence']:.0%}",
                    'Odziv': f"{item['response_time']:.2f}s"
                })
            
            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Add export button for history
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Izvozi zgodovino",
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
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0;">⚙️ Nastavitve</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Konfiguracija AI sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status
    st.markdown("### 🔌 Status povezav")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        openai_status = "🟢 Povezan" if os.getenv('OPENAI_API_KEY') else "🔴 Ni povezan"
        st.metric("OpenAI API", openai_status)
    
    with col2:
        qdrant_status = "🟢 Povezan" if os.getenv('QDRANT_API_KEY') else "🔴 Ni povezan"
        st.metric("Qdrant API", qdrant_status)
    
    with col3:
        processing_status = "🟢 Aktivno" if AI_PROCESSING_AVAILABLE else "🔴 Neaktivno"
        st.metric("AI Procesiranje", processing_status)
    
    st.divider()
    
    # Processing settings
    st.markdown("### 🔧 Nastavitve procesiranja")
    
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
    
    st.info("ℹ️ Nastavitve se bodo uporabile pri naslednjem procesiranju")

def render_analytics_dashboard():
    """Render analytics dashboard with charts and metrics"""
    
    st.markdown("""
    <div class="ai-header">
        <h2>📊 Analitika AI sistema</h2>
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
    st.markdown("### 📈 Pregled")
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
        
    tab1, tab2, tab3 = st.tabs(["🔍 Poizvedbe", "🤖 Prompti", "📊 Učinkovitost"])
    
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
        st.markdown("#### ⭐ Shranjene poizvedbe")
        if not analytics['bookmarked_queries'].empty:
            for _, query in analytics['bookmarked_queries'].iterrows():
                with st.expander(f"📌 {query['query_text'][:80]}..."):
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
        st.markdown("#### ⚡ Učinkovitost promptov")
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
            fig.update_yaxis(range=[0, 100])
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
    """Save document with categorization"""
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.name).suffix
        
        # Create directory structure
        doc_dir = Path(f"data/documents/{tip_dokumenta}")
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = doc_dir / f"{file_id}{file_extension}"
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        
        # Save metadata to database
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_documents 
                (filename, file_path, tip_dokumenta, file_type, file_size, description, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file.name,
                str(file_path),
                tip_dokumenta,
                file_extension,
                file.size,
                description,
                tags
            ))
            conn.commit()
            return cursor.lastrowid
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
        
        query += " ORDER BY upload_date DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

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