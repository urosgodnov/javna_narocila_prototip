"""
Admin Document Testing Interface - Story 28.6
Provides testing and validation interface for uploaded documents
Part of Epic: EPIC-FORM-DOCS-001
"""

import streamlit as st
import sqlite3
import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import database

# Configure logging
logger = logging.getLogger(__name__)

# Try to import AI components
try:
    from ui.ai_processor import VectorStoreManager, EmbeddingGenerator
    from services.form_document_processor import trigger_document_processing
    AI_AVAILABLE = True
except ImportError:
    logger.warning("AI components not available for document testing")
    AI_AVAILABLE = False


def render_document_testing_tab():
    """Main entry point - render document testing interface in admin panel"""
    
    st.markdown("### 🧪 Test dokumentov AI integracije")
    
    # Check if AI is available
    if not AI_AVAILABLE:
        st.warning("⚠️ AI komponente niso na voljo. Namestite potrebne knjižnice za testiranje.")
        return
    
    # Three-column selector layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Organization selector
        orgs = get_organizations()
        if not orgs:
            st.warning("Ni organizacij v sistemu")
            return
        
        # Add "All" option for super admin view
        org_options = [{"id": 0, "naziv": "Vse organizacije"}] + orgs
        
        selected_org = st.selectbox(
            "🏢 Organizacija",
            options=org_options,
            format_func=lambda x: x['naziv'],
            key="test_org_select"
        )
    
    with col2:
        # Form selector based on organization
        if selected_org:
            if selected_org['id'] == 0:
                # Show all forms
                forms = get_all_forms()
            else:
                forms = get_forms_for_org(selected_org['naziv'])
            
            if not forms:
                st.info("Ni javnih naročil")
                selected_form = None
            else:
                form_options = [{"id": 0, "naziv": "Vsi obrazci", "status": ""}] + forms
                selected_form = st.selectbox(
                    "📋 Javno naročilo",
                    options=form_options,
                    format_func=lambda x: f"{x['naziv']} {f'({x['status']})' if x['status'] else ''}".strip(),
                    key="test_form_select"
                )
        else:
            selected_form = None
    
    with col3:
        # Document selector based on form
        if selected_form:
            if selected_form['id'] == 0:
                # Show all documents for organization
                if selected_org['id'] == 0:
                    docs = get_all_documents()
                else:
                    docs = get_documents_for_org(selected_org['naziv'])
            else:
                docs = get_form_documents(selected_form['id'])
            
            if not docs:
                st.info("Ni naloženih dokumentov")
                selected_doc = None
            else:
                selected_doc = st.selectbox(
                    "📄 Dokument",
                    options=docs,
                    format_func=lambda x: format_document_name(x),
                    key="test_doc_select"
                )
        else:
            selected_doc = None
    
    # Show document info and testing interface if document selected
    if selected_doc:
        st.markdown("---")
        render_document_info(selected_doc)
        st.markdown("---")
        render_testing_chat(selected_doc, selected_form, selected_org)
    
    # Show statistics if no specific document selected
    elif selected_form or selected_org:
        st.markdown("---")
        render_document_statistics(selected_org, selected_form)


def format_document_name(doc: Dict) -> str:
    """Format document name for display"""
    name = doc['original_name']
    if doc.get('field_name'):
        name += f" [{doc['field_name']}]"
    if doc.get('processing_status'):
        status_emoji = {
            'completed': '✅',
            'processing': '⏳',
            'failed': '❌',
            'pending': '⏸️',
            'skipped': '⏭️'
        }.get(doc['processing_status'], '❓')
        name += f" {status_emoji}"
    return name


def render_document_info(doc: Dict):
    """Display document metrics and status"""
    
    st.markdown("#### 📊 Informacije o dokumentu")
    
    # Create info cards in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Velikost", f"{doc.get('file_size', 0) / 1024:.1f} KB")
        file_type = doc.get('file_type', 'Unknown').upper().replace('.', '')
        st.metric("📎 Tip", file_type)
    
    with col2:
        status = doc.get('processing_status', 'unknown')
        status_display = {
            'completed': '✅ Dokončano',
            'processing': '⏳ V obdelavi',
            'failed': '❌ Neuspešno',
            'pending': '⏸️ Čaka',
            'skipped': '⏭️ Preskočeno'
        }.get(status, status.title())
        st.metric("🔄 Status", status_display)
        
        chunks = doc.get('chunks_count', 0) or doc.get('chunk_count', 0)
        st.metric("📝 Kosi besedila", chunks)
    
    with col3:
        upload_date = doc.get('upload_date', doc.get('created_at', ''))
        if upload_date:
            if isinstance(upload_date, str):
                date_display = upload_date[:10]
            else:
                date_display = upload_date.strftime("%Y-%m-%d")
        else:
            date_display = "Neznano"
        st.metric("📅 Datum nalaganja", date_display)
        
        shared = get_shared_forms_count(doc['id'])
        st.metric("🔗 Deljeno z obrazci", shared)
    
    with col4:
        # Action buttons based on status
        if status == 'completed':
            st.success("✅ Pripravljen za testiranje")
            
            # Reprocess button
            if st.button("🔄 Ponovno procesiraj", key=f"reprocess_{doc['id']}"):
                if trigger_document_reprocessing(doc['id']):
                    st.success("Dokument dodan v vrsto za procesiranje")
                    st.rerun()
        
        elif status == 'processing':
            st.info("⏳ Dokument se trenutno procesira...")
            
            # Check status button
            if st.button("🔍 Preveri status", key=f"check_{doc['id']}"):
                st.rerun()
        
        elif status in ['failed', 'pending']:
            st.warning(f"⚠️ Status: {status}")
            
            # Process button
            if st.button("▶️ Procesiraj", key=f"process_{doc['id']}"):
                if trigger_document_reprocessing(doc['id']):
                    st.success("Dokument dodan v vrsto za procesiranje")
                    st.rerun()
        
        else:
            st.info(f"ℹ️ Status: {status}")
    
    # Show additional metadata in expander
    with st.expander("🔍 Dodatni podatki"):
        metadata_cols = st.columns(2)
        
        with metadata_cols[0]:
            st.write(f"**ID dokumenta:** {doc['id']}")
            st.write(f"**Hash datoteke:** {doc.get('file_hash', 'N/A')[:16]}...")
            st.write(f"**MIME tip:** {doc.get('mime_type', 'N/A')}")
            st.write(f"**Verzija:** {doc.get('version', 1)}")
        
        with metadata_cols[1]:
            st.write(f"**AI dokument ID:** {doc.get('ai_document_id', 'N/A')}")
            st.write(f"**Embeddings:** {doc.get('embeddings_count', 0)}")
            st.write(f"**Aktivno:** {'Da' if doc.get('is_active', True) else 'Ne'}")
            
            # Show processing error if exists
            if doc.get('processing_error'):
                st.error(f"**Napaka:** {doc['processing_error']}")


def render_testing_chat(doc: Dict, form: Optional[Dict], org: Dict):
    """Render chat interface for document testing"""
    
    st.markdown("#### 💬 Testni pogovor z dokumentom")
    
    # Context mode selector
    context_mode = st.radio(
        "🔍 Kontekst iskanja:",
        ["Samo ta dokument", "Vsi dokumenti obrazca", "Vsi dokumenti organizacije", "Celotna baza znanja"],
        horizontal=True,
        key="test_context_mode"
    )
    
    # Initialize chat history in session state
    if 'doc_test_messages' not in st.session_state:
        st.session_state.doc_test_messages = []
    
    # Add example queries
    with st.expander("💡 Primeri vprašanj"):
        st.write("""
        - Kakšne so tehnične zahteve v tem dokumentu?
        - Povzemi glavne pogoje sodelovanja
        - Kateri certifikati so zahtevani?
        - Kakšna je ocenjena vrednost projekta?
        - Kateri so roki za oddajo ponudb?
        """)
    
    # Display chat history
    for msg in st.session_state.doc_test_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show chunks used for AI responses
            if msg["role"] == "assistant" and "chunks" in msg:
                if msg['chunks']:
                    with st.expander(f"📚 Uporabljeni deli dokumenta ({len(msg['chunks'])})"):
                        for i, chunk in enumerate(msg['chunks'], 1):
                            st.markdown(f"**{i}. Del (Relevanca: {chunk['score']:.1%})**")
                            
                            # Show metadata
                            if 'metadata' in chunk:
                                meta = chunk['metadata']
                                if meta.get('original_name'):
                                    st.caption(f"Dokument: {meta['original_name']}")
                                if meta.get('chunk_index') is not None:
                                    st.caption(f"Indeks: {meta['chunk_index']}")
                            
                            # Show text excerpt
                            text = chunk['text'][:300]
                            if len(chunk['text']) > 300:
                                text += "..."
                            st.text(text)
                            
                            if i < len(msg['chunks']):
                                st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("Vprašajte karkoli o dokumentu..."):
        # Check if document is processed
        if doc.get('processing_status') != 'completed':
            st.error("⚠️ Dokument še ni procesiran. Prosimo počakajte ali ga ročno procesirajte.")
            return
        
        # Add user message to history
        st.session_state.doc_test_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Generate response
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Iščem v dokumentu..."):
                response, chunks = search_document(
                    prompt, 
                    doc, 
                    context_mode, 
                    org['id'] if org else None,
                    form['id'] if form and form['id'] != 0 else None
                )
                st.markdown(response)
        
        # Add assistant message to history
        st.session_state.doc_test_messages.append({
            "role": "assistant",
            "content": response,
            "chunks": chunks
        })
        
        st.rerun()
    
    # Chat controls
    if st.session_state.doc_test_messages:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export conversation
            if st.button("📥 Izvozi pogovor", key="export_test"):
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "document": {
                        "id": doc['id'],
                        "name": doc['original_name'],
                        "status": doc.get('processing_status')
                    },
                    "organization": org['naziv'] if org else "N/A",
                    "form": form['naziv'] if form else "N/A",
                    "context_mode": context_mode,
                    "messages": st.session_state.doc_test_messages
                }
                
                st.download_button(
                    label="💾 Prenesi JSON",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"doc_test_{doc['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            # Clear conversation
            if st.button("🗑️ Počisti pogovor", key="clear_test"):
                st.session_state.doc_test_messages = []
                st.rerun()
        
        with col3:
            # Show message count
            st.metric("💬 Sporočila", len(st.session_state.doc_test_messages))


def search_document(query: str, doc: Dict, context_mode: str, 
                    org_id: Optional[int], form_id: Optional[int]) -> Tuple[str, List[Dict]]:
    """Search document content using vector store"""
    
    try:
        vector_store = VectorStoreManager()
        embedding_gen = EmbeddingGenerator()
        
        # Generate query embedding
        query_embedding = embedding_gen.generate_single_embedding(query)
        
        if not query_embedding:
            return "❌ Napaka pri generiranju poizvedbe.", []
        
        # Build filter based on context mode
        filter_dict = {}
        
        if context_mode == "Samo ta dokument":
            # Filter by AI document ID
            ai_doc_id = doc.get('ai_document_id')
            if ai_doc_id:
                filter_dict = {"document_id": ai_doc_id}
            else:
                return "⚠️ Dokument nima povezanega AI dokumenta.", []
        
        elif context_mode == "Vsi dokumenti obrazca":
            if form_id:
                filter_dict = {"form_id": form_id}
            else:
                return "⚠️ Obrazec ni izbran.", []
        
        elif context_mode == "Vsi dokumenti organizacije":
            if org_id and org_id != 0:
                filter_dict = {"organization_id": org_id}
        
        # For "Celotna baza znanja" - no filter
        
        # Search vector store
        if vector_store and vector_store.client:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build Qdrant filter
            qdrant_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Perform search
            results = vector_store.client.search(
                collection_name=vector_store.collection_name,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=5,
                with_payload=True
            )
        else:
            return "⚠️ Vector store ni na voljo.", []
        
        if not results:
            return "🔍 Ni najdenih relevantnih delov dokumenta za to vprašanje.", []
        
        # Format response
        response_parts = [f"Na podlagi iskanja v kontekstu '{context_mode}':\n"]
        
        # Add summary from top chunks
        for i, result in enumerate(results[:3], 1):
            payload = result.payload or {}
            text = payload.get('text', '')
            if text:
                # Clean and truncate text
                text_preview = text.strip()[:200]
                if len(text) > 200:
                    text_preview += "..."
                response_parts.append(f"\n**{i}.** {text_preview}")
        
        response = "\n".join(response_parts)
        
        # Format chunks for display
        chunks = []
        for result in results:
            payload = result.payload or {}
            chunks.append({
                'score': result.score,
                'text': payload.get('text', ''),
                'metadata': {
                    'original_name': payload.get('original_name', payload.get('filename', 'Unknown')),
                    'chunk_index': payload.get('chunk_index'),
                    'document_id': payload.get('document_id'),
                    'form_id': payload.get('form_id')
                }
            })
        
        return response, chunks
        
    except Exception as e:
        logger.error(f"Error searching document: {e}")
        return f"❌ Napaka pri iskanju: {str(e)}", []


def render_document_statistics(org: Optional[Dict], form: Optional[Dict]):
    """Render statistics for documents"""
    
    st.markdown("#### 📊 Statistika dokumentov")
    
    # Get statistics based on selection
    if form and form['id'] != 0:
        stats = get_form_document_stats(form['id'])
        st.write(f"Statistika za obrazec: **{form['naziv']}**")
    elif org and org['id'] != 0:
        stats = get_org_document_stats(org['naziv'])
        st.write(f"Statistika za organizacijo: **{org['naziv']}**")
    else:
        stats = get_all_document_stats()
        st.write("Statistika za **vse dokumente**")
    
    # Display statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Skupaj dokumentov", stats['total'])
        st.metric("✅ Procesirani", stats['completed'])
    
    with col2:
        st.metric("⏳ V obdelavi", stats['processing'])
        st.metric("❌ Neuspešni", stats['failed'])
    
    with col3:
        st.metric("📝 Skupaj kosov", stats['total_chunks'])
        st.metric("🔗 Povprečno kosov/dok", f"{stats['avg_chunks']:.1f}")
    
    with col4:
        st.metric("💾 Skupna velikost", f"{stats['total_size_mb']:.1f} MB")
        st.metric("🔁 Deduplikacija", f"{stats['dedup_ratio']:.1%}")
    
    # Show document type distribution
    if stats['by_type']:
        st.markdown("##### 📊 Porazdelitev po tipih")
        type_df = pd.DataFrame(
            stats['by_type'].items(),
            columns=['Tip', 'Število']
        )
        st.bar_chart(type_df.set_index('Tip'))
    
    # Show processing status chart
    if stats['by_status']:
        st.markdown("##### 🔄 Status procesiranja")
        status_df = pd.DataFrame(
            stats['by_status'].items(),
            columns=['Status', 'Število']
        )
        st.bar_chart(status_df.set_index('Status'))


# Database query functions

def get_organizations() -> List[Dict]:
    """Get all organizations from database"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # First try the organizacija table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='organizacija'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, naziv 
                FROM organizacija 
                ORDER BY naziv
            """)
        else:
            # Fallback to getting unique organizations from javna_narocila
            cursor.execute("""
                SELECT DISTINCT organizacija as naziv, 
                       ROW_NUMBER() OVER (ORDER BY organizacija) as id
                FROM javna_narocila 
                WHERE organizacija IS NOT NULL
                ORDER BY organizacija
            """)
        
        columns = ['id', 'naziv']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_all_forms() -> List[Dict]:
    """Get all forms from database"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, naziv, status 
            FROM javna_narocila 
            ORDER BY id DESC
        """)
        columns = ['id', 'naziv', 'status']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_forms_for_org(org_name: str) -> List[Dict]:
    """Get forms for specific organization"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, naziv, status 
            FROM javna_narocila 
            WHERE organizacija = ?
            ORDER BY id DESC
        """, (org_name,))
        columns = ['id', 'naziv', 'status']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_all_documents() -> List[Dict]:
    """Get all documents from database"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT d.*, a.field_name
            FROM form_documents d
            LEFT JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE d.is_active = 1
            ORDER BY d.upload_date DESC
            LIMIT 100
        """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_documents_for_org(org_name: str) -> List[Dict]:
    """Get documents for specific organization"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT d.*, a.field_name
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            JOIN javna_narocila j ON a.form_id = j.id
            WHERE j.organizacija = ? AND d.is_active = 1
            ORDER BY d.upload_date DESC
        """, (org_name,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_form_documents(form_id: int) -> List[Dict]:
    """Get documents for specific form"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, a.field_name
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND d.is_active = 1
            ORDER BY d.upload_date DESC
        """, (form_id,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_shared_forms_count(doc_id: int) -> int:
    """Get count of forms sharing this document"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT form_id) 
            FROM form_document_associations 
            WHERE form_document_id = ?
        """, (doc_id,))
        return cursor.fetchone()[0]


def trigger_document_reprocessing(doc_id: int) -> bool:
    """Trigger AI reprocessing for document"""
    try:
        # Update status to queue for reprocessing
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE form_documents 
                SET processing_status = 'pending',
                    processing_error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (doc_id,))
            conn.commit()
        
        # Trigger processing if available
        if AI_AVAILABLE:
            trigger_document_processing(doc_id)
        
        return True
    except Exception as e:
        logger.error(f"Error triggering reprocessing: {e}")
        return False


def get_form_document_stats(form_id: int) -> Dict:
    """Get statistics for form documents"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN d.processing_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN d.processing_status = 'processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN d.processing_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(d.chunks_count) as total_chunks,
                AVG(d.chunks_count) as avg_chunks,
                SUM(d.file_size) / 1024.0 / 1024.0 as total_size_mb
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND d.is_active = 1
        """, (form_id,))
        
        stats = dict(zip(
            ['total', 'completed', 'processing', 'failed', 'total_chunks', 'avg_chunks', 'total_size_mb'],
            cursor.fetchone()
        ))
        
        # Fix None values
        for key in stats:
            if stats[key] is None:
                stats[key] = 0
        
        # Get distribution by type
        cursor.execute("""
            SELECT d.file_type, COUNT(*) 
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND d.is_active = 1
            GROUP BY d.file_type
        """, (form_id,))
        
        stats['by_type'] = dict(cursor.fetchall())
        
        # Get distribution by status
        cursor.execute("""
            SELECT d.processing_status, COUNT(*) 
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND d.is_active = 1
            GROUP BY d.processing_status
        """, (form_id,))
        
        stats['by_status'] = dict(cursor.fetchall())
        
        # Calculate deduplication ratio
        cursor.execute("""
            SELECT COUNT(DISTINCT d.file_hash) as unique_files
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            WHERE a.form_id = ? AND d.is_active = 1
        """, (form_id,))
        
        unique_files = cursor.fetchone()[0]
        stats['dedup_ratio'] = 1 - (unique_files / stats['total']) if stats['total'] > 0 else 0
        
        return stats


def get_org_document_stats(org_name: str) -> Dict:
    """Get statistics for organization documents"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Similar to get_form_document_stats but filtered by organization
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT d.id) as total,
                SUM(CASE WHEN d.processing_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN d.processing_status = 'processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN d.processing_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(d.chunks_count) as total_chunks,
                AVG(d.chunks_count) as avg_chunks,
                SUM(d.file_size) / 1024.0 / 1024.0 as total_size_mb
            FROM form_documents d
            JOIN form_document_associations a ON d.id = a.form_document_id
            JOIN javna_narocila j ON a.form_id = j.id
            WHERE j.organizacija = ? AND d.is_active = 1
        """, (org_name,))
        
        stats = dict(zip(
            ['total', 'completed', 'processing', 'failed', 'total_chunks', 'avg_chunks', 'total_size_mb'],
            cursor.fetchone()
        ))
        
        # Fix None values
        for key in stats:
            if stats[key] is None:
                stats[key] = 0
        
        # Get type and status distributions
        stats['by_type'] = {}
        stats['by_status'] = {}
        stats['dedup_ratio'] = 0
        
        return stats


def get_all_document_stats() -> Dict:
    """Get statistics for all documents"""
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN processing_status = 'processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(chunks_count) as total_chunks,
                AVG(chunks_count) as avg_chunks,
                SUM(file_size) / 1024.0 / 1024.0 as total_size_mb
            FROM form_documents
            WHERE is_active = 1
        """)
        
        stats = dict(zip(
            ['total', 'completed', 'processing', 'failed', 'total_chunks', 'avg_chunks', 'total_size_mb'],
            cursor.fetchone()
        ))
        
        # Fix None values
        for key in stats:
            if stats[key] is None:
                stats[key] = 0
        
        # Get distributions
        cursor.execute("""
            SELECT file_type, COUNT(*) 
            FROM form_documents
            WHERE is_active = 1
            GROUP BY file_type
        """)
        stats['by_type'] = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT processing_status, COUNT(*) 
            FROM form_documents
            WHERE is_active = 1
            GROUP BY processing_status
        """)
        stats['by_status'] = dict(cursor.fetchall())
        
        # Calculate deduplication ratio
        cursor.execute("""
            SELECT COUNT(DISTINCT file_hash) as unique_files
            FROM form_documents
            WHERE is_active = 1
        """)
        unique_files = cursor.fetchone()[0]
        stats['dedup_ratio'] = 1 - (unique_files / stats['total']) if stats['total'] > 0 else 0
        
        return stats