"""Modern dashboard UI without external dependencies."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import database

def render_modern_dashboard():
    """Render a beautiful modern dashboard without plotly."""
    
    # Initialize lot-related session state if not present
    if "lot_mode" not in st.session_state:
        st.session_state.lot_mode = "none"  # Changed to match config
    if "current_lot_index" not in st.session_state:
        st.session_state.current_lot_index = None
    
    # Custom CSS for modern styling
    st.markdown("""
    <style>
    /* Modern color scheme */
    :root {
        --primary-blue: #1E40AF;
        --secondary-blue: #3B82F6;
        --light-blue: #DBEAFE;
        --gray-700: #374151;
        --gray-500: #6B7280;
        --gray-100: #F3F4F6;
        --success-green: #10B981;
        --warning-amber: #F59E0B;
        --danger-red: #EF4444;
    }
    
    /* Main container styling */
    .stApp {
        background: linear-gradient(180deg, #F9FAFB 0%, #FFFFFF 100%);
    }
    
    /* Stats card styling */
    .stats-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(229, 231, 235, 0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .stats-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
    }
    
    .stats-card:hover {
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        transform: translateY(-4px);
    }
    
    .stats-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        font-size: 28px;
        position: relative;
    }
    
    .stats-icon::after {
        content: '';
        position: absolute;
        inset: -2px;
        border-radius: 12px;
        background: inherit;
        opacity: 0.2;
        filter: blur(8px);
    }
    
    .stats-title {
        color: #6B7280;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stats-value {
        color: #111827;
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 12px;
        line-height: 1;
    }
    
    .stats-change {
        display: inline-flex;
        align-items: center;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        gap: 4px;
    }
    
    .stats-change.positive {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        color: #065F46;
    }
    
    .stats-change.negative {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        color: #991B1B;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        padding: 40px;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 24px 24px;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        right: -100px;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        border-radius: 50%;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 36px;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin-top: 8px;
        font-size: 18px;
        position: relative;
        z-index: 1;
    }
    
    /* Action button styling */
    .action-button {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border: none;
        padding: 14px 28px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Section cards */
    .section-card {
        background: white;
        padding: 28px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(229, 231, 235, 0.5);
        margin-bottom: 24px;
    }
    
    .section-title {
        margin: 0 0 24px 0;
        color: #111827;
        font-size: 20px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* Table styling */
    .dataframe {
        border: none !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe thead tr th {
        background: linear-gradient(180deg, #F9FAFB 0%, #F3F4F6 100%) !important;
        color: #374151 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 11px !important;
        letter-spacing: 0.05em !important;
        padding: 14px 12px !important;
        border-bottom: 2px solid #E5E7EB !important;
    }
    
    .dataframe tbody tr td {
        padding: 14px 12px !important;
        color: #111827 !important;
        font-size: 14px !important;
        border-bottom: 1px solid #F3F4F6 !important;
    }
    
    .dataframe tbody tr:hover {
        background: #F9FAFB !important;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-active {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        color: #065F46;
    }
    
    .status-draft {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
    }
    
    .status-completed {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
        color: #1E3A8A;
    }
    
    /* Quick action cards */
    .quick-action-card {
        background: white;
        border: 2px solid;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .quick-action-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: currentColor;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .quick-action-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }
    
    .quick-action-card:hover::before {
        opacity: 0.1;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }
    
    .metric-label {
        font-size: 14px;
        color: #6B7280;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Sistem za Javna Naročila</h1>
        <p>Pregled aktivnosti in upravljanje dokumentacije</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get data from database
    procurements = database.get_procurements_for_customer('demo_organizacija')
    
    # Calculate statistics
    total_count = len(procurements) if procurements else 0
    active_count = len([p for p in procurements if p['status'] == 'Aktivno']) if procurements else 0
    draft_count = len([p for p in procurements if p['status'] == 'Osnutek']) if procurements else 0
    completed_count = len([p for p in procurements if p['status'] == 'Zaključeno']) if procurements else 0
    
    # Stats Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_stat_card(
            icon="📋",
            title="Aktivni razpisi",
            value=str(active_count),
            change="+12%",
            change_type="positive",
            color="#3B82F6"
        )
    
    with col2:
        render_stat_card(
            icon="📝",
            title="Osnutki",
            value=str(draft_count),
            change="+3",
            change_type="positive",
            color="#F59E0B"
        )
    
    with col3:
        render_stat_card(
            icon="✅",
            title="Dokončani",
            value=str(completed_count),
            change="+23%",
            change_type="positive",
            color="#10B981"
        )
    
    with col4:
        render_stat_card(
            icon="📊",
            title="Vsi dokumenti",
            value=str(total_count),
            change="+5",
            change_type="positive",
            color="#8B5CF6"
        )
    
    # Quick Actions Section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-card">
        <h3 class="section-title">
            ⚡ Hitre akcije
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Nov razpis", use_container_width=True, type="primary"):
            st.session_state.current_page = 'form'
            st.session_state.edit_mode = False
            st.session_state.edit_record_id = None
            st.session_state.current_step = 0
            from utils.schema_utils import clear_form_data
            clear_form_data()
            st.rerun()
    
    with col2:
        if st.button("📊 Izvozi poročilo", use_container_width=True):
            st.info("Funkcija izvoza bo kmalu na voljo")
    
    with col3:
        if st.button("⚙️ Nastavitve", use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()
    
    # Recent Documents Table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-card">
        <h3 class="section-title">
            📄 Nedavni dokumenti
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if procurements:
        render_documents_table(procurements)
    else:
        st.info("📭 Ni najdenih javnih naročil. Kliknite 'Nov razpis' za začetek.")
    
    # Summary metrics
    if procurements:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="section-card">
            <h3 class="section-title">
                📈 Povzetek
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_value = sum([p['vrednost'] or 0 for p in procurements])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_value:,.0f} €</div>
                <div class="metric-label">Skupna vrednost</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_value = total_value / len(procurements) if procurements else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_value:,.0f} €</div>
                <div class="metric-label">Povprečna vrednost</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            this_month = len([p for p in procurements if p.get('datum_objave', '').startswith(datetime.now().strftime('%Y-%m'))])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{this_month}</div>
                <div class="metric-label">Ta mesec</div>
            </div>
            """, unsafe_allow_html=True)

def render_stat_card(icon: str, title: str, value: str, change: str, change_type: str, color: str):
    """Render a beautiful stats card."""
    change_class = "positive" if change_type == "positive" else "negative"
    arrow = "↑" if change_type == "positive" else "↓"
    
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-icon" style="background: {color}20;">
            <span>{icon}</span>
        </div>
        <div class="stats-title">{title}</div>
        <div class="stats-value">{value}</div>
        <div class="stats-change {change_class}">
            <span>{arrow} {change}</span>
            <span style="margin-left: 8px; color: #6B7280; font-weight: 400;">ta mesec</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_documents_table(procurements):
    """Render the documents table with enhanced styling."""
    # Prepare data for display
    df_data = []
    for proc in procurements[:10]:  # Show last 10
        status_badge = get_status_badge(proc['status'])
        df_data.append({
            'ID': f"#{proc['id']:04d}",
            'Naziv': proc['naziv'] or 'Neimenovano',
            'Status': status_badge,
            'Vrednost': f"{proc['vrednost'] or 0:,.0f} €",
            'Datum': proc['datum_objave'] or proc['zadnja_sprememba'][:10] if proc['zadnja_sprememba'] else '-'
        })
    
    df = pd.DataFrame(df_data)
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Iskanje", placeholder="Vnesite iskalni niz...")
    with col2:
        status_filter = st.selectbox("Filter", ["Vsi", "Aktivno", "Osnutek", "Zaključeno"])
    
    # Apply filters if needed
    if search:
        mask = df['Naziv'].str.contains(search, case=False, na=False)
        df = df[mask]
    
    if status_filter != "Vsi":
        # Filter based on status (this is simplified, you'd need to match the badge HTML)
        pass
    
    # Display the table
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Edit actions
    if len(procurements) > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        selected_id = st.selectbox(
            "Izberite dokument za urejanje:",
            options=[p['id'] for p in procurements],
            format_func=lambda x: f"#{x:04d} - {next(p['naziv'] or 'Neimenovano' for p in procurements if p['id'] == x)}"
        )
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("✏️ Uredi", use_container_width=True):
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = True
                st.session_state.edit_record_id = selected_id
                st.session_state.current_step = 0
                load_procurement_to_form(selected_id)
                st.rerun()
        
        with col2:
            if st.button("📋 Kopiraj", use_container_width=True):
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = False
                st.session_state.edit_record_id = None
                st.session_state.current_step = 0
                load_procurement_to_form(selected_id)
                st.rerun()
        
        with col3:
            if st.button("🗑️ Izbriši", use_container_width=True):
                if database.delete_procurement(selected_id):
                    st.success("Dokument izbrisan")
                    st.rerun()
        
        with col4:
            # Story 25.2: DUMMY AI Generation button
            if st.button("🤖 Generiraj vsebino z AI", use_container_width=True, key=f"ai_gen_{selected_id}"):
                st.info("ℹ️ Funkcija generiranja z AI bo kmalu na voljo")
        
        with col5:
            # Story 25.3: DUMMY Form Preparation button
            if st.button("📄 Pripravi obrazce", use_container_width=True, key=f"prep_forms_{selected_id}"):
                st.info("ℹ️ Funkcija priprave obrazcev bo kmalu na voljo")

def get_status_badge(status):
    """Generate HTML for status badge."""
    if status == 'Aktivno':
        return '<span class="status-badge status-active">Aktivno</span>'
    elif status == 'Osnutek':
        return '<span class="status-badge status-draft">Osnutek</span>'
    elif status == 'Zaključeno':
        return '<span class="status-badge status-completed">Zaključeno</span>'
    else:
        return f'<span class="status-badge">{status}</span>'

def load_procurement_to_form(procurement_id):
    """Load procurement data into form session state."""
    from utils.data_migration import migrate_form_data
    
    procurement = database.get_procurement_by_id(procurement_id)
    
    if procurement and procurement.get('form_data'):
        form_data = procurement['form_data']
        
        # Apply Epic 3.0 data migrations  
        form_data = migrate_form_data(form_data)
        
        # Clear existing form data first
        from utils.schema_utils import clear_form_data
        clear_form_data()
        
        # Load all form data into session state
        def flatten_dict(d, parent_key='', sep='.'):
            """Flatten nested dictionary into dot-notation keys."""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        # Flatten and load into session state
        flattened_data = flatten_dict(form_data)
        for key, value in flattened_data.items():
            st.session_state[key] = value
        
        # Store that we loaded data for tracking changes
        st.session_state._last_loaded_data = flattened_data.copy()