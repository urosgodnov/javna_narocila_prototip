"""
Vector Database Management UI - Story 27.2
Admin interface for managing documents in Qdrant vector database
"""

import streamlit as st
import os
import sys
import tempfile
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services
from services.qdrant_document_processor import QdrantDocumentProcessor, get_processor_status
from services.qdrant_crud_service import QdrantCRUDService
from utils.qdrant_init import check_qdrant_status
import database


def save_uploaded_file(uploaded_file) -> str:
    """
    Save uploaded file to temporary location.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Path to saved file
    """
    # Create temp directory if doesn't exist
    temp_dir = Path(tempfile.gettempdir()) / "qdrant_uploads"
    temp_dir.mkdir(exist_ok=True)
    
    # Save file with unique name
    file_ext = Path(uploaded_file.name).suffix
    temp_path = temp_dir / f"{uuid.uuid4()}{file_ext}"
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return str(temp_path)


def detect_document_type(filename: str) -> str:
    """
    Detect document type from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Document type string
    """
    filename_lower = filename.lower()
    
    if "specification" in filename_lower or "spec" in filename_lower:
        return "specification"
    elif "contract" in filename_lower or "pogodba" in filename_lower:
        return "contract"
    elif "tender" in filename_lower or "razpis" in filename_lower:
        return "tender"
    elif "procurement" in filename_lower or "narocilo" in filename_lower:
        return "procurement"
    elif "report" in filename_lower or "porocilo" in filename_lower:
        return "report"
    else:
        return "general"


def generate_doc_id() -> str:
    """Generate unique document ID."""
    return f"doc_{uuid.uuid4().hex[:12]}"


def store_document_metadata(doc_info: Dict[str, Any]) -> bool:
    """
    Store document metadata in SQLite database.
    
    Args:
        doc_info: Document information dictionary
        
    Returns:
        True if successful
    """
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT UNIQUE NOT NULL,
                    original_filename TEXT NOT NULL,
                    document_type TEXT,
                    organization TEXT,
                    file_format TEXT,
                    file_size INTEGER,
                    chunks_count INTEGER,
                    vectors_count INTEGER,
                    extraction_method TEXT,
                    embedding_model TEXT,
                    processing_status TEXT,
                    processing_time REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or update document record
            cursor.execute("""
                INSERT OR REPLACE INTO ai_documents (
                    document_id, original_filename, document_type, organization,
                    file_format, file_size, chunks_count, vectors_count,
                    extraction_method, embedding_model, processing_status,
                    processing_time, error_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                doc_info.get("document_id"),
                doc_info.get("original_filename"),
                doc_info.get("document_type"),
                doc_info.get("organization"),
                doc_info.get("file_format"),
                doc_info.get("file_size"),
                doc_info.get("chunks_count"),
                doc_info.get("vectors_count"),
                doc_info.get("extraction_method"),
                doc_info.get("embedding_model"),
                doc_info.get("processing_status"),
                doc_info.get("processing_time"),
                doc_info.get("error_message")
            ))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Failed to store document metadata: {e}")
        return False


def get_vector_documents() -> list:
    """
    Get list of documents from database.
    
    Returns:
        List of document records
    """
    try:
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_documents'
            """)
            
            if not cursor.fetchone():
                return []
            
            # Get all documents
            cursor.execute("""
                SELECT 
                    document_id, original_filename, document_type, organization,
                    file_format, file_size, chunks_count, vectors_count,
                    processing_status, processing_time, created_at
                FROM ai_documents
                ORDER BY created_at DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
    except Exception as e:
        st.error(f"Failed to fetch documents: {e}")
        return []


def delete_document_from_db(document_id: str) -> bool:
    """
    Delete document from database and Qdrant.
    
    Args:
        document_id: Document ID to delete
        
    Returns:
        True if successful
    """
    try:
        # Delete from Qdrant
        processor = QdrantDocumentProcessor()
        processor.delete_document(document_id)
        
        # Delete from database
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_documents WHERE document_id = ?", (document_id,))
            conn.commit()
        
        return True
        
    except Exception as e:
        st.error(f"Failed to delete document: {e}")
        return False


def render_vector_database_tab():
    """Render the Vector Database management interface for admin panel."""
    
    st.markdown("### 🔍 Vector Database Management")
    
    # Create tabs for different operations
    tabs = st.tabs(["📊 Dashboard", "🔎 Search", "📤 Upload", "📚 Manage", "📈 Analytics"])
    
    with tabs[0]:  # Dashboard
        render_dashboard_section()
    
    with tabs[1]:  # Search
        render_search_section()
    
    with tabs[2]:  # Upload
        render_upload_section()
    
    with tabs[3]:  # Manage
        render_management_section()
    
    with tabs[4]:  # Analytics
        render_analytics_section()


def render_dashboard_section():
    """Render the main dashboard with system status."""
    # Check system status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Manage documents for semantic search using Qdrant vector database")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # System Status Section  
    with st.expander("📊 System Status", expanded=True):
        # Check Qdrant status
        qdrant_status = check_qdrant_status()
        processor_status = get_processor_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Qdrant Database**")
            if qdrant_status["connected"]:
                st.success(f"✅ Connected to {qdrant_status['collection_name']}")
                if qdrant_status["collection_exists"]:
                    st.metric("Vectors in collection", qdrant_status.get("vector_count", 0))
            else:
                st.error("❌ Not connected")
                st.caption(qdrant_status.get("error", "Check configuration"))
        
        with col2:
            st.markdown("**Document Processing**")
            for component, available in processor_status.items():
                if component not in ["pdf_support", "docx_support"]:  # Group file support
                    icon = "✅" if available else "❌"
                    st.write(f"{icon} {component.replace('_', ' ').title()}")
        
        with col3:
            st.markdown("**File Format Support**")
            st.write(f"{'✅' if processor_status.get('pdf_support') else '❌'} PDF")
            st.write(f"{'✅' if processor_status.get('docx_support') else '❌'} DOCX")
            st.write("✅ HTML")
            st.write("✅ TXT")
    

def render_search_section():
    """Render the semantic search interface."""
    st.markdown("### 🔎 Semantic Search")
    
    # Search input
    search_query = st.text_input(
        "Search Query",
        placeholder="Enter your search query...",
        help="Search across all documents using natural language"
    )
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        doc_type_filter = st.selectbox(
            "Document Type",
            ["All", "procurement", "contract", "specification", "tender", "report", "general"]
        )
    
    with col2:
        # Get unique organizations
        documents = get_vector_documents()
        orgs = list(set(doc.get("organization", "") for doc in documents if doc.get("organization")))
        org_filter = st.selectbox(
            "Organization",
            ["All"] + sorted(orgs)
        )
    
    with col3:
        limit = st.number_input(
            "Results Limit",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort By",
            ["Relevance", "Date (Newest)", "Date (Oldest)"]
        )
    
    # Search button
    if search_query and st.button("🔍 Search", type="primary", use_container_width=True):
        with st.spinner("Searching..."):
            crud_service = QdrantCRUDService()
            
            # Build filters
            filters = {}
            if doc_type_filter != "All":
                filters["document_type"] = doc_type_filter
            if org_filter != "All":
                filters["organization"] = org_filter
            
            # Perform search
            results, total_count = crud_service.search_documents(
                query=search_query,
                filters=filters,
                limit=limit
            )
            
            # Display results
            if results:
                st.success(f"Found {total_count} relevant documents (showing top {min(limit, len(results))})")
                
                for i, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    color = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                    
                    with st.expander(
                        f"{color} **{result.get('original_filename', 'Unknown')}** "
                        f"(Score: {score:.3f})"
                    ):
                        # Document info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Type:** {result.get('document_type', 'Unknown')}")
                            st.write(f"**Organization:** {result.get('organization', 'Unknown')}")
                        with col2:
                            st.write(f"**Chunk:** {result.get('chunk_index', 0) + 1}/{result.get('total_chunks', 1)}")
                            st.write(f"**Format:** {result.get('file_format', 'Unknown')}")
                        with col3:
                            st.write(f"**Created:** {result.get('created_at', 'Unknown')[:10] if result.get('created_at') else 'Unknown'}")
                            st.write(f"**Doc ID:** {result.get('document_id', 'Unknown')[:8]}...")
                        
                        # Chunk text preview
                        st.markdown("**Content Preview:**")
                        chunk_text = result.get('chunk_text', 'No preview available')
                        
                        # Highlight search terms
                        for term in search_query.split():
                            if len(term) > 2:  # Only highlight meaningful terms
                                chunk_text = chunk_text.replace(
                                    term.lower(), 
                                    f"**{term.lower()}**"
                                )
                                chunk_text = chunk_text.replace(
                                    term.capitalize(), 
                                    f"**{term.capitalize()}**"
                                )
                        
                        st.markdown(chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text)
            else:
                st.info("No documents found matching your search criteria.")
    
    elif not search_query:
        st.info("Enter a search query to find relevant documents.")


def render_upload_section():
    """Render the document upload section."""
    st.markdown("### 📤 Upload Documents")
    
    # Check system readiness
    qdrant_status = check_qdrant_status()
    processor_status = get_processor_status()
    
    if not qdrant_status["connected"]:
        st.warning("⚠️ Qdrant is not connected. Please check configuration in .env file.")
        return
    
    if not processor_status["openai"]:
        st.warning("⚠️ OpenAI API is not configured. Please set OPENAI_API_KEY in .env file.")
        return
    
    # File upload
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a document to process",
            type=['pdf', 'html', 'htm', 'doc', 'docx', 'txt'],
            help="Supported formats: PDF, HTML, DOC, DOCX, TXT"
        )
    
    with col2:
        # Organization selection
        organization = st.text_input(
            "Organization",
            value=st.session_state.get("organization", "demo_organizacija"),
            help="Organization name for the document"
        )
    
    if uploaded_file:
        # Document preview
        st.markdown("#### 📄 Document Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        
        with col2:
            doc_type = st.selectbox(
                "Document Type",
                ["auto-detect", "procurement", "contract", "specification", 
                 "tender", "report", "general"],
                help="Select document type or use auto-detection"
            )
            if doc_type == "auto-detect":
                doc_type = detect_document_type(uploaded_file.name)
                st.caption(f"Detected: {doc_type}")
        
        with col3:
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                chunk_size = st.number_input(
                    "Chunk Size",
                    min_value=100,
                    max_value=2000,
                    value=int(os.getenv("CHUNK_SIZE", "1000")),
                    step=100,
                    help="Size of text chunks in characters"
                )
                chunk_overlap = st.number_input(
                    "Chunk Overlap",
                    min_value=0,
                    max_value=500,
                    value=int(os.getenv("CHUNK_OVERLAP", "200")),
                    step=50,
                    help="Overlap between chunks in characters"
                )
        
        # Process button
        if st.button("🚀 Process Document", type="primary", use_container_width=True):
            try:
                # Initialize progress container
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(message: str, progress: float):
                        status_text.text(message)
                        progress_bar.progress(progress)
                    
                    # Save uploaded file
                    update_progress("Saving uploaded file...", 0.05)
                    temp_path = save_uploaded_file(uploaded_file)
                    
                    # Prepare metadata
                    doc_id = generate_doc_id()
                    metadata = {
                        "document_id": doc_id,
                        "original_filename": uploaded_file.name,
                        "document_type": doc_type,
                        "organization": organization,
                        "file_format": Path(uploaded_file.name).suffix.lower()[1:],
                        "file_size": uploaded_file.size,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Process document
                    processor = QdrantDocumentProcessor()
                    
                    # Override chunk settings if changed
                    if chunk_size != int(os.getenv("CHUNK_SIZE", "1000")):
                        os.environ["CHUNK_SIZE"] = str(chunk_size)
                    if chunk_overlap != int(os.getenv("CHUNK_OVERLAP", "200")):
                        os.environ["CHUNK_OVERLAP"] = str(chunk_overlap)
                    
                    result = processor.process_document(
                        temp_path,
                        metadata,
                        progress_callback=update_progress
                    )
                    
                    # Store metadata in database
                    doc_info = {
                        **metadata,
                        "chunks_count": result["chunks_processed"],
                        "vectors_count": result["vectors_stored"],
                        "extraction_method": result["extraction_metadata"].get("extraction_method"),
                        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                        "processing_status": result["status"],
                        "processing_time": result["processing_time"],
                        "error_message": result.get("error")
                    }
                    
                    store_document_metadata(doc_info)
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    # Show result
                    if result["status"] == "success":
                        st.success(f"""
                        ✅ Document processed successfully!
                        - **Document ID:** {doc_id}
                        - **Chunks created:** {result['chunks_processed']}
                        - **Vectors stored:** {result['vectors_stored']}
                        - **Processing time:** {result['processing_time']:.1f}s
                        """)
                    else:
                        st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Failed to process document: {str(e)}")
    
    st.markdown("---")
    
    # Existing Documents Section
    st.markdown("### 📚 Existing Documents")
    
    documents = get_vector_documents()
    
    if documents:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", len(documents))
        with col2:
            total_chunks = sum(doc.get("chunks_count", 0) for doc in documents)
            st.metric("Total Chunks", total_chunks)
        with col3:
            total_vectors = sum(doc.get("vectors_count", 0) for doc in documents)
            st.metric("Total Vectors", total_vectors)
        with col4:
            success_rate = sum(1 for doc in documents if doc.get("processing_status") == "success") / len(documents) * 100
            st.metric("Success Rate", f"{success_rate:.0f}%")
        
        # Document table
        df = pd.DataFrame(documents)
        
        # Format columns
        display_columns = [
            "document_id", "original_filename", "document_type", 
            "organization", "chunks_count", "vectors_count", 
            "processing_status", "created_at"
        ]
        
        # Filter to available columns
        display_columns = [col for col in display_columns if col in df.columns]
        
        # Format dates
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        
        # Display with selection
        selected_indices = st.data_editor(
            df[display_columns],
            hide_index=True,
            use_container_width=True,
            disabled=display_columns,
            column_config={
                "document_id": st.column_config.TextColumn("ID", width="small"),
                "original_filename": st.column_config.TextColumn("Filename"),
                "document_type": st.column_config.TextColumn("Type", width="small"),
                "organization": st.column_config.TextColumn("Organization"),
                "chunks_count": st.column_config.NumberColumn("Chunks", width="small"),
                "vectors_count": st.column_config.NumberColumn("Vectors", width="small"),
                "processing_status": st.column_config.TextColumn("Status", width="small"),
                "created_at": st.column_config.TextColumn("Created At")
            }
        )
        
        # Document actions
        st.markdown("#### 🔧 Document Actions")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            doc_to_delete = st.selectbox(
                "Select document to delete",
                options=[""] + [f"{doc['document_id']} - {doc['original_filename']}" 
                               for doc in documents],
                help="Select a document to remove from vector database"
            )
        
        with col2:
            if st.button("🗑️ Delete Selected", type="secondary", disabled=not doc_to_delete):
                if doc_to_delete:
                    doc_id = doc_to_delete.split(" - ")[0]
                    if delete_document_from_db(doc_id):
                        st.success(f"✅ Document {doc_id} deleted successfully")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete document")
        
        with col3:
            if st.button("🧹 Clear All Documents", type="secondary"):
                if st.checkbox("⚠️ Confirm deletion of ALL documents"):
                    processor = QdrantDocumentProcessor()
                    for doc in documents:
                        processor.delete_document(doc["document_id"])
                    
                    with sqlite3.connect(database.DATABASE_FILE) as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM ai_documents")
                        conn.commit()
                    
                    st.success("✅ All documents cleared")
                    st.rerun()
    else:
        st.info("📭 No documents in vector database. Upload documents above to get started.")


def render_management_section():
    """Render the document management section with CRUD operations."""
    st.markdown("### 📚 Document Management")
    
    documents = get_vector_documents()
    
    if documents:
        # Add selection column
        for doc in documents:
            doc["Select"] = False
        
        # Create editable dataframe
        edited_df = st.data_editor(
            pd.DataFrame(documents),
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select documents for batch operations",
                    default=False,
                ),
                "document_id": st.column_config.TextColumn("ID", width="small"),
                "original_filename": st.column_config.TextColumn("Filename"),
                "document_type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["procurement", "contract", "specification", "tender", "report", "general"],
                    width="small"
                ),
                "organization": st.column_config.TextColumn("Organization"),
                "chunks_count": st.column_config.NumberColumn("Chunks", width="small"),
                "vectors_count": st.column_config.NumberColumn("Vectors", width="small"),
                "processing_status": st.column_config.TextColumn("Status", width="small"),
                "created_at": st.column_config.TextColumn("Created")
            },
            disabled=["document_id", "original_filename", "chunks_count", "vectors_count", "processing_status", "created_at"],
            hide_index=True,
            use_container_width=True
        )
        
        # Get selected documents
        selected_docs = edited_df[edited_df["Select"] == True]
        
        if len(selected_docs) > 0:
            st.info(f"Selected {len(selected_docs)} document(s) for batch operations")
            
            # Batch operations
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                    if st.checkbox(f"Confirm deletion of {len(selected_docs)} documents?"):
                        crud_service = QdrantCRUDService()
                        doc_ids = selected_docs["document_id"].tolist()
                        
                        with st.spinner("Deleting documents..."):
                            results = crud_service.batch_delete(doc_ids)
                            successful = sum(1 for v in results.values() if v)
                            
                        if successful > 0:
                            st.success(f"✅ Deleted {successful}/{len(doc_ids)} documents")
                            st.rerun()
                        else:
                            st.error("Failed to delete documents")
            
            with col2:
                if st.button("📥 Export Metadata", use_container_width=True):
                    crud_service = QdrantCRUDService()
                    doc_ids = selected_docs["document_id"].tolist()
                    
                    metadata = crud_service.export_metadata(doc_ids)
                    if metadata:
                        # Convert to CSV
                        import csv
                        from io import StringIO
                        
                        output = StringIO()
                        if metadata:
                            writer = csv.DictWriter(output, fieldnames=metadata[0].keys())
                            writer.writeheader()
                            writer.writerows(metadata)
                            
                            st.download_button(
                                label="💾 Download CSV",
                                data=output.getvalue(),
                                file_name=f"document_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
            
            with col3:
                if st.button("🔄 Re-process", use_container_width=True):
                    st.info("Re-processing feature coming soon")
            
            with col4:
                if st.button("🏷️ Update Tags", use_container_width=True):
                    st.info("Tag management coming soon")
        
        # Check for metadata changes
        for index, row in edited_df.iterrows():
            original_doc = documents[index]
            if row["document_type"] != original_doc["document_type"] or \
               row["organization"] != original_doc["organization"]:
                # Update metadata
                crud_service = QdrantCRUDService()
                updates = {
                    "document_type": row["document_type"],
                    "organization": row["organization"]
                }
                if crud_service.update_document_metadata(row["document_id"], updates):
                    st.success(f"✅ Updated metadata for {row['original_filename']}")
                    st.rerun()
    else:
        st.info("📭 No documents to manage. Upload documents first.")


def render_analytics_section():
    """Render the analytics dashboard."""
    st.markdown("### 📈 Analytics Dashboard")
    
    crud_service = QdrantCRUDService()
    stats = crud_service.get_collection_stats()
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Documents",
            stats["total_documents"],
            help="Number of documents in the database"
        )
    
    with col2:
        st.metric(
            "Total Chunks",
            stats["total_chunks"],
            help="Total text chunks across all documents"
        )
    
    with col3:
        st.metric(
            "Total Vectors",
            stats["total_vectors"],
            help="Number of vectors stored in Qdrant"
        )
    
    with col4:
        st.metric(
            "Storage Used",
            f"{stats['storage_mb']:.1f} MB",
            help="Estimated storage usage"
        )
    
    st.markdown("---")
    
    # Distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Document Types")
        if stats["document_types"]:
            # Count documents by type
            documents = get_vector_documents()
            type_counts = {}
            for doc in documents:
                doc_type = doc.get("document_type", "unknown")
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Display as bar chart (simple text representation)
            for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(documents)) * 100
                bar = "█" * int(percentage / 2)
                st.text(f"{doc_type:15} {bar} {count} ({percentage:.1f}%)")
        else:
            st.info("No documents yet")
    
    with col2:
        st.markdown("#### 🏢 Organizations")
        if stats["organizations"]:
            # Count documents by organization
            documents = get_vector_documents()
            org_counts = {}
            for doc in documents:
                org = doc.get("organization", "unknown")
                org_counts[org] = org_counts.get(org, 0) + 1
            
            # Display as list
            for org, count in sorted(org_counts.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{org}**: {count} documents")
        else:
            st.info("No organizations yet")
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("#### 📅 Recent Activity")
    if stats["latest_document"]:
        st.info(
            f"Latest document: **{stats['latest_document']['filename']}** "
            f"(uploaded {stats['latest_document']['created_at'][:10]})"
        )
    
    # Processing statistics
    documents = get_vector_documents()
    if documents:
        successful = sum(1 for doc in documents if doc.get("processing_status") == "success")
        failed = sum(1 for doc in documents if doc.get("processing_status") == "failed")
        pending = sum(1 for doc in documents if doc.get("processing_status") == "pending")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Successful", successful)
        with col2:
            st.metric("❌ Failed", failed)
        with col3:
            st.metric("⏳ Pending", pending)
    
    # System health
    st.markdown("---")
    st.markdown("#### 🔧 System Health")
    
    qdrant_status = check_qdrant_status()
    processor_status = get_processor_status()
    
    health_items = [
        ("Qdrant Connection", qdrant_status["connected"]),
        ("Collection Exists", qdrant_status["collection_exists"]),
        ("OpenAI API", processor_status["openai"]),
        ("Docling Support", processor_status["docling"]),
        ("LangChain Support", processor_status["langchain"]),
        ("PDF Support", processor_status["pdf_support"]),
        ("DOCX Support", processor_status["docx_support"])
    ]
    
    for item, status in health_items:
        icon = "✅" if status else "❌"
        st.write(f"{icon} {item}: {'Operational' if status else 'Not Available'}")
    
    st.markdown("---")
    
    # Search Test Section
    st.markdown("### 🔎 Test Semantic Search")
    
    if documents and total_vectors > 0:
        search_query = st.text_input(
            "Enter search query",
            placeholder="e.g., technical specifications for procurement",
            help="Test semantic search across your documents"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            search_limit = st.number_input(
                "Results limit",
                min_value=1,
                max_value=20,
                value=5
            )
        
        with col2:
            filter_org = st.selectbox(
                "Filter by organization",
                options=["All"] + list(set(doc.get("organization", "") for doc in documents if doc.get("organization")))
            )
        
        if search_query and st.button("🔍 Search", type="primary"):
            processor = QdrantDocumentProcessor()
            
            # Prepare filters
            filters = {}
            if filter_org != "All":
                filters["organization"] = filter_org
            
            # Perform search
            with st.spinner("Searching..."):
                results = processor.search_similar(search_query, limit=search_limit, filter_conditions=filters)
            
            if results:
                st.success(f"Found {len(results)} relevant results:")
                
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i} - Score: {result['score']:.3f}"):
                        st.write(f"**Document:** {result.get('original_filename', 'Unknown')}")
                        st.write(f"**Organization:** {result.get('organization', 'Unknown')}")
                        st.write(f"**Type:** {result.get('document_type', 'Unknown')}")
                        st.write(f"**Chunk {result.get('chunk_index', 0) + 1}:**")
                        st.text(result.get('chunk_text', 'No preview available'))
            else:
                st.info("No results found. Try a different query.")
    else:
        st.info("Upload and process documents first to test semantic search.")


# Module can be imported and used in admin_panel.py
if __name__ == "__main__":
    # Standalone testing
    st.set_page_config(page_title="Vector Database Manager", layout="wide")
    st.title("🔍 Vector Database Manager")
    render_vector_database_tab()