"""Administration panel UI components."""
import streamlit as st
import os
from datetime import datetime
import template_service
from config import ADMIN_PASSWORD


def render_admin_header():
    """Render the admin header with status and logout option."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("🔧 Administracija predlog")
    with col2:
        if st.button("🚪 Odjava", type="secondary"):
            st.session_state["logged_in"] = False
            st.rerun()


def render_login_form():
    """Render the admin login form with improved styling."""
    # Add some vertical spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center the login form with improved styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Create a styled container for the login form
        with st.container():
            st.markdown("""
            <div style="
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: #f8f9fa;
                margin: 20px 0;
            ">
            """, unsafe_allow_html=True)
            
            st.markdown("### 🔐 Prijava v administracijo")
            password = st.text_input("Geslo", type="password", placeholder="Vnesite admin geslo")
            
            if st.button("Prijava", type="primary", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("Uspešna prijava!")
                    st.rerun()
                else:
                    st.error("Napačno geslo.")
            
            st.markdown("</div>", unsafe_allow_html=True)


def get_template_metadata(template_name, template_dir='templates'):
    """Get metadata for a template file."""
    file_path = os.path.join(template_dir, template_name)
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        }
    return None


def render_template_management_tab():
    """Render the template management tab content."""
    with st.container():
        st.markdown("### 📄 Upravljanje predlog Word")
        
        # Upload section
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Naloži novo predlogo (.docx)", 
                type=["docx"],
                help="Izberite Word datoteko (.docx) za upload"
            )
        with col2:
            if uploaded_file:
                overwrite_existing = st.checkbox("Prepiši obstoječo predlogo")
        
        if uploaded_file:
            with st.spinner("Nalagam predlogo..."):
                success, message = template_service.save_template(uploaded_file, overwrite=overwrite_existing)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        st.markdown("---")
        
        # Templates list section
        st.markdown("### 📋 Seznam obstoječih predlog")
        templates = template_service.list_templates()
        
        if templates:
            # Header for the table
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            with col1:
                st.markdown("**Ime datoteke**")
            with col2:
                st.markdown("**Velikost**")
            with col3:
                st.markdown("**Zadnja sprememba**")
            with col4:
                st.markdown("**Tip**")
            
            st.markdown("---")
            
            for template in templates:
                metadata = get_template_metadata(template)
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                    with col1:
                        st.markdown(f"📄 **{template}**")
                    with col2:
                        if metadata:
                            size_kb = metadata['size'] / 1024
                            st.markdown(f"{size_kb:.1f} KB")
                    with col3:
                        if metadata:
                            st.markdown(f"{metadata['modified']}")
                    with col4:
                        st.markdown("Word")
        else:
            st.info("📭 Ni najdenih predlog. Naložite prvo predlogo zgoraj.")


def render_draft_management_tab():
    """Render the draft management tab content."""
    with st.container():
        st.markdown("### 💾 Upravljanje osnutkov")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🗑️ Počisti osnutke")
            st.markdown("Izbriše vse shranjene osnutke iz baze podatkov.")
            
            # Initialize confirmation state
            if "confirm_clear_drafts" not in st.session_state:
                st.session_state.confirm_clear_drafts = False
            
            if not st.session_state.confirm_clear_drafts:
                if st.button("Počisti vse osnutke", type="secondary", use_container_width=True):
                    st.session_state.confirm_clear_drafts = True
                    st.rerun()
            else:
                st.warning("⚠️ Ste prepričani, da želite izbrisati vse osnutke? Ta akcija je nepovratna.")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("🗑️ Da, izbriši", type="primary", use_container_width=True):
                        with st.spinner("Brišem osnutke..."):
                            success, message = template_service.clear_drafts()
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        st.session_state.confirm_clear_drafts = False
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Prekliči", type="secondary", use_container_width=True):
                        st.session_state.confirm_clear_drafts = False
                        st.rerun()
        
        with col2:
            st.markdown("#### 💼 Varnostno kopiranje")
            st.markdown("Ustvari varnostno kopijo vseh osnutkov.")
            if st.button("Varnostno kopiraj osnutke", type="primary", use_container_width=True):
                with st.spinner("Ustvarjam varnostno kopijo..."):
                    success, message = template_service.backup_drafts()
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")


def render_database_management_tab():
    """Render the database management tab content."""
    with st.container():
        st.markdown("### 🗄️ Upravljanje zbirk ChromaDB")
        
        st.info("🚧 Funkcionalnost upravljanja zbirk ChromaDB še ni implementirana.")
        
        # Placeholder for future ChromaDB management features
        st.markdown("""
        **Načrtovane funkcionalnosti:**
        - 📊 Pregled obstoječih zbirk
        - ➕ Dodajanje novih zbirk
        - 🗑️ Brisanje zbirk
        - 🔄 Sinhronizacija podatkov
        """)


def render_admin_panel():
    """Render the complete admin panel with modern interface."""
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        render_login_form()
    else:
        render_admin_header()
        
        # Tabbed interface for different admin sections
        tab1, tab2, tab3 = st.tabs(["📄 Predloge", "💾 Osnutki", "🗄️ Baza podatkov"])
        
        with tab1:
            render_template_management_tab()
        
        with tab2:
            render_draft_management_tab()
        
        with tab3:
            render_database_management_tab()