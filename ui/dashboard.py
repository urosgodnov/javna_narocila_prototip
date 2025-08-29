"""
Dashboard view for managing public procurements
Provides table view with CRUD operations
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time
import database
from utils.schema_utils import get_form_data_from_session, clear_form_data
from utils.loading_state import set_loading_state, LOADING_MESSAGES

def update_status_callback(procurement_id, new_status):
    """Callback function to update procurement status."""
    if database.update_procurement_status(procurement_id, new_status):
        st.success(f"✅ Status uspešno spremenjen na: {new_status}")

def calculate_procurement_value(proc):
    """
    Calculate total procurement value.
    If procurement has lots, sum up all lot values.
    Otherwise, use the main value field.
    """
    # Check if procurement has form_data with lots
    if proc.get('form_data') and isinstance(proc['form_data'], dict):
        form_data = proc['form_data']
        
        # Check for new lot structure first (lot_0, lot_1, etc.)
        lot_mode = form_data.get('lot_mode', '')
        num_lots = form_data.get('num_lots', 0)
        
        # Auto-detect num_lots if not set
        if lot_mode == 'multiple' and num_lots == 0:
            # Count lot_X fields to determine num_lots
            lot_indices = set()
            for key in form_data.keys():
                if key.startswith('lot_') and '.' in key:
                    lot_part = key.split('.')[0]
                    if '_' in lot_part:
                        idx = lot_part.split('_')[1]
                        if idx.isdigit():
                            lot_indices.add(int(idx))
            num_lots = len(lot_indices)
        
        if lot_mode == 'multiple' and num_lots > 0:
            # New structure: sum values from lot_X fields
            total_value = 0
            for i in range(num_lots):
                # Try different possible field names for lot values
                value_fields = [
                    f'lot_{i}.orderType.estimatedValue',
                    f'lot_{i}.priceInfo.estimatedValue',
                    f'lot_{i}_orderType_estimatedValue',  # Old underscore format
                    f'lot_{i}_priceInfo_estimatedValue'   # Old underscore format
                ]
                
                for field in value_fields:
                    if field in form_data:
                        lot_value = form_data.get(field, 0)
                        try:
                            if isinstance(lot_value, str):
                                lot_value = float(lot_value.replace(',', '.')) if lot_value else 0
                            total_value += lot_value
                            break  # Use first found value field for this lot
                        except (ValueError, AttributeError):
                            continue
            
            return total_value if total_value > 0 else proc.get('vrednost', 0)
        
        # Old structure fallback - check if this procurement has lots
        has_lots = form_data.get('lotsInfo', {}).get('hasLots', False)
        
        if has_lots and 'lots' in form_data:
            # Sum up values from all lots
            total_value = 0
            lots = form_data.get('lots', [])
            
            for lot in lots:
                if isinstance(lot, dict):
                    lot_value = lot.get('estimatedValue', 0)
                    try:
                        # Convert to float if it's a string
                        if isinstance(lot_value, str):
                            lot_value = float(lot_value.replace(',', '.')) if lot_value else 0
                        total_value += lot_value
                    except (ValueError, AttributeError):
                        continue
            
            return total_value if total_value > 0 else proc.get('vrednost', 0)
    
    # Fall back to the main value field
    return proc.get('vrednost', 0)

def render_dashboard():
    """Render the procurement dashboard with table view."""
    
    # Professional dashboard styling with subtle colors
    st.markdown("""
    <style>
    /* Professional color palette */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #64748b;
        --success-color: #16a34a;
        --warning-color: #ea580c;
        --danger-color: #dc2626;
        --dark-text: #1e293b;
        --light-bg: #f8fafc;
        --border-color: #e2e8f0;
    }
    
    /* Clean modern buttons - matching input form gray for secondary buttons */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #6c757d, #5a6268) !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #5a6268, #495057) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(108,117,125,0.3) !important;
    }
    
    /* Primary button - light green for Novo naročilo */
    .stButton > button[kind="primary"] {
        background-color: #86efac !important;
        color: #14532d !important;
        border: 1px solid #86efac !important;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #65d989 !important;
        border-color: #65d989 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Logout button - red/danger style */
    button[key="logout_button"] {
        background-color: #ef4444 !important;
        color: white !important;
        border: 1px solid #ef4444 !important;
    }
    
    button[key="logout_button"]:hover {
        background-color: #dc2626 !important;
        border-color: #dc2626 !important;
        transform: translateY(-1px);
    }
    
    /* Stats cards */
    [data-testid="metric-container"] {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    }
    
    /* Metric values */
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 2rem !important;
        font-weight: 700;
        color: #2C3E50;
    }
    
    [data-testid="metric-container"] label {
        font-size: 0.9rem;
        color: #7F8C8D;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Table enhancements */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    
    .dataframe tbody tr {
        transition: all 0.2s ease;
    }
    
    .dataframe tbody tr:hover {
        background-color: #F0F3FF !important;
        transform: scale(1.01);
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-active {
        background: linear-gradient(135deg, #48C774, #3EC46D);
        color: white;
    }
    
    .status-draft {
        background: linear-gradient(135deg, #FFB443, #FF9A00);
        color: white;
    }
    
    .status-completed {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    /* Action buttons row */
    .action-buttons {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    /* Search input */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #E1E8ED;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    /* Animations */
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
        }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    </style>
    
    <script>
    // Dynamic button styling based on text content - similar to input form
    function styleButtons() {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            const text = button.innerText.toLowerCase();
            
            // Apply styles based on button text
            if (text.includes('odjava') || text.includes('logout')) {
                button.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #c82333, #a71d2a)';
                    this.style.boxShadow = '0 4px 8px rgba(220,53,69,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('osveži') || text.includes('refresh')) {
                button.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #0056b3, #004494)';
                    this.style.boxShadow = '0 4px 8px rgba(0,123,255,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('uvoz') || text.includes('import')) {
                button.style.background = 'linear-gradient(135deg, #17a2b8, #20c997)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #138496, #17a085)';
                    this.style.boxShadow = '0 4px 8px rgba(23,162,184,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #17a2b8, #20c997)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('nastavitve') || text.includes('settings')) {
                button.style.background = 'linear-gradient(135deg, #6c757d, #5a6268)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #5a6268, #495057)';
                    this.style.boxShadow = '0 4px 8px rgba(108,117,125,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #6c757d, #5a6268)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('uredi') || text.includes('edit')) {
                button.style.background = 'linear-gradient(135deg, #fbbf24, #f59e0b)';
                button.style.border = 'none';
                button.style.color = '#1e293b';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #f59e0b, #ea580c)';
                    this.style.boxShadow = '0 4px 8px rgba(245,158,11,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #fbbf24, #f59e0b)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('kopiraj') || text.includes('copy')) {
                button.style.background = 'linear-gradient(135deg, #8b5cf6, #7c3aed)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #7c3aed, #6d28d9)';
                    this.style.boxShadow = '0 4px 8px rgba(139,92,246,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #8b5cf6, #7c3aed)';
                    this.style.boxShadow = '';
                };
            } else if (text.includes('izbriši') || text.includes('delete')) {
                button.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                button.style.border = 'none';
                button.style.color = 'white';
                button.onmouseover = function() {
                    this.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)';
                    this.style.boxShadow = '0 4px 8px rgba(239,68,68,0.3)';
                };
                button.onmouseout = function() {
                    this.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                    this.style.boxShadow = '';
                };
            }
        });
    }
    
    // Run periodically and observe DOM changes
    setInterval(styleButtons, 100);
    const observer = new MutationObserver(styleButtons);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)
    
    # Clean professional header with narrower logout button
    col_header, col_spacer, col_logout = st.columns([5, 2, 0.8])
    
    with col_header:
        st.markdown("""
        <h1 style='
            color: #1e293b;
            font-size: 2rem;
            font-weight: 600;
            margin: 0;
            padding: 0;
        '>Javna Naročila</h1>
        """, unsafe_allow_html=True)
        
        current_org = st.session_state.get('organization', 'demo_organizacija')
        st.markdown(f"""
        <p style='
            color: #64748b;
            font-size: 1rem;
            margin-top: 0.25rem;
        '>Organizacija: <strong style='color: #334155;'>{current_org}</strong></p>
        """, unsafe_allow_html=True)
    
    # Empty spacer column for better layout
    with col_spacer:
        pass
    
    with col_logout:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Odjava", use_container_width=True, key="logout_button"):
            # Clear authentication
            for key in ['authenticated', 'organization']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Action buttons row - all buttons at same level
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Novo naročilo", use_container_width=True, key="new_procurement", type="primary"):
            with st.spinner('Pripravljam nov obrazec...'):
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = False
                st.session_state.edit_record_id = None
                st.session_state.current_step = 0  # Reset to first step
                clear_form_data()  # Clear any existing form data
                st.rerun()
    
    with col2:
        if st.button("Osveži", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("Uvoz", use_container_width=True):
            st.session_state.show_import_dialog = True
    
    with col4:
        if st.button("Nastavitve", use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()
    
    # Fetch procurements
    procurements = database.get_procurements_for_customer('demo_organizacija')
    
    if procurements:
        # Modern stats section with enhanced cards
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Calculate metrics
        total_count = len(procurements)
        active_count = len([p for p in procurements if p['status'] == 'Aktivno'])
        draft_count = len([p for p in procurements if p['status'] == 'Osnutek'])
        total_value = sum([calculate_procurement_value(p) for p in procurements])
        
        # Display metrics with enhanced styling
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="VSA NAROČILA",
                value=total_count,
                delta=None
            )
        
        with col2:
            st.metric(
                label="AKTIVNA",
                value=active_count,
                delta=f"{(active_count/total_count*100):.0f}%" if total_count > 0 else "0%"
            )
        
        with col3:
            st.metric(
                label="OSNUTKI", 
                value=draft_count,
                delta=f"{(draft_count/total_count*100):.0f}%" if total_count > 0 else "0%"
            )
        
        with col4:
            st.metric(
                label="SKUPNA VREDNOST",
                value=f"{total_value:,.0f} €",
                delta=None
            )
        
        # Elegant separator
        st.markdown("""
        <div style='
            height: 2px; 
            background: linear-gradient(90deg, transparent, #e0e0e0 20%, #e0e0e0 80%, transparent);
            margin: 2rem 0;
        '></div>
        """, unsafe_allow_html=True)
        
        # Display procurements in an enhanced table
        display_procurements_table(procurements)
        
    else:
        # Empty state
        st.info("Ni najdenih javnih naročil.")
        st.markdown("""
        ### Začnite z ustvarjanjem prvega javnega naročila
        
        Kliknite na gumb **'+ Novo naročilo'** zgoraj, da začnete z vnosom.
        
        Po ustvarjanju bo naročilo prikazano v tej tabeli, kjer ga boste lahko:
        - Urejali
        - Kopirali
        - Brisali
        - Spremljali status
        """)
    
    # Import Dialog (works even with empty database)
    if st.session_state.get('show_import_dialog', False):
        with st.expander("Uvoz podatkov", expanded=True):
            uploaded_file = st.file_uploader("Izberite JSON datoteko za uvoz", type=['json'])
            if uploaded_file:
                try:
                    import json
                    import sqlite3
                    data = json.load(uploaded_file)
                    
                    # Direct database insert
                    conn = sqlite3.connect('mainDB.db')
                    cursor = conn.cursor()
                    
                    # Extract basic fields from nested structure
                    naziv = data.get('projectInfo', {}).get('projectName', data.get('naziv', 'Uvoženo naročilo'))
                    vrsta = data.get('orderType', {}).get('type', data.get('vrsta', ''))
                    postopek = data.get('submissionProcedure', {}).get('procedure', data.get('postopek', ''))
                    vrednost = data.get('orderType', {}).get('estimatedValue', data.get('vrednost', 0))
                    status = data.get('status', 'Osnutek')
                    
                    # Get form_data
                    if 'form_data' in data and isinstance(data['form_data'], str):
                        form_data_json = data['form_data']
                    elif 'form_data' in data:
                        form_data_json = json.dumps(data['form_data'])
                    else:
                        form_data_json = json.dumps(data)
                    
                    # Direct insert
                    cursor.execute('''
                        INSERT INTO javna_narocila (
                            organizacija, naziv, vrsta, postopek, 
                            datum_objave, status, vrednost, form_data_json,
                            zadnja_sprememba, uporabnik
                        ) VALUES (?, ?, ?, ?, date('now'), ?, ?, ?, datetime('now'), ?)
                    ''', ('demo_organizacija', naziv, vrsta, postopek, 
                          status, vrednost, form_data_json, 'import'))
                    
                    new_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                    
                    # Clear session state
                    if 'show_import_dialog' in st.session_state:
                        del st.session_state['show_import_dialog']
                    st.session_state.current_page = 'dashboard'
                    st.session_state['JUST_IMPORTED'] = True
                    
                    st.success(f"Uspešno uvoženo kot naročilo #{new_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Napaka pri uvozu: {str(e)}")
            
            if st.button("Zapri"):
                del st.session_state['show_import_dialog']
                st.rerun()

def display_procurements_table(procurements):
    """Display procurements in an interactive table with actions."""
    
    # Convert to DataFrame for better display
    df_data = []
    for proc in procurements:
        # Calculate value (sum of lots if applicable)
        value = calculate_procurement_value(proc)
        
        # Check if this has lots for display purposes
        has_lots = False
        if proc.get('form_data') and isinstance(proc['form_data'], dict):
            has_lots = proc['form_data'].get('lotsInfo', {}).get('hasLots', False)
        
        # Add indicator if value is from lots
        value_display = f"{value:,.2f}"
        if has_lots:
            num_lots = len(proc['form_data'].get('lots', [])) if proc.get('form_data') else 0
            if num_lots > 0:
                value_display = f"{value:,.2f} ({num_lots} sklopov)"
        
        df_data.append({
            'ID': proc['id'],
            'Naziv': proc['naziv'] or 'Neimenovano',
            'Vrsta': proc['vrsta'] or '-',
            'Postopek': proc['postopek'] or '-',
            'Datum': proc['datum_objave'] or '-',
            'Status': proc['status'],
            'Vrednost (€)': value_display,
            'Posodobljeno': proc['zadnja_sprememba'][:10] if proc['zadnja_sprememba'] else '-'
        })
    
    df = pd.DataFrame(df_data)
    
    # Display the dataframe with clean header
    st.markdown("""
    <h3 style='
        color: #1e293b;
        font-weight: 500;
        margin-bottom: 1rem;
        border-left: 3px solid #e2e8f0;
        padding-left: 10px;
    '>Seznam javnih naročil</h3>
    """, unsafe_allow_html=True)
    
    # Add search/filter
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_term = st.text_input("Iskanje", placeholder="Vnesite iskalni niz...")
    with col2:
        status_filter = st.selectbox("Status", ["Vsi", "Osnutek", "Aktivno", "Zaključeno"])
    
    # Apply filters
    if search_term:
        mask = df['Naziv'].str.contains(search_term, case=False, na=False) | \
               df['Postopek'].str.contains(search_term, case=False, na=False)
        df = df[mask]
    
    if status_filter != "Vsi":
        df = df[df['Status'] == status_filter]
    
    # Display the filtered dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(
                "ID",
                width="small",
            ),
            "Naziv": st.column_config.TextColumn(
                "Naziv naročila",
                width="large",
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                width="small",
                options=["Osnutek", "Aktivno", "Zaključeno"],
            ),
            "Vrednost (€)": st.column_config.TextColumn(
                "Vrednost",
                width="small",
            ),
        }
    )
    
    # Action buttons section with clean styling
    st.markdown("""
    <h3 style='
        color: #1e293b;
        font-weight: 500;
        margin: 2rem 0 1rem 0;
        border-left: 3px solid #e2e8f0;
        padding-left: 10px;
    '>Akcije</h3>
    """, unsafe_allow_html=True)
    
    
    # Create a selectbox for choosing which procurement to act on
    if len(procurements) > 0:
        procurement_options = {f"{p['id']} - {p['naziv'] or 'Neimenovano'}": p['id'] for p in procurements}
        selected_proc_label = st.selectbox(
            "Izberite naročilo za urejanje:",
            options=list(procurement_options.keys())
        )
        selected_id = procurement_options[selected_proc_label]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Uredi", use_container_width=True):
                import logging
                logging.info(f"=== EDIT BUTTON CLICKED for ID {selected_id} ===")
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = True
                st.session_state.edit_record_id = selected_id
                st.session_state.current_step = 0
                # Clear the flag to force data reload
                if 'edit_data_loaded' in st.session_state:
                    del st.session_state.edit_data_loaded
                st.rerun()
        
        with col2:
            if st.button("Kopiraj", use_container_width=True):
                # Story 1: Direct copy without opening form
                # Load full procurement data
                original_data = database.get_procurement_by_id(selected_id)
                if original_data and original_data.get('form_data'):
                    # Get the form data
                    form_data_copy = original_data['form_data'].copy()
                    
                    # Modify the name to append "(kopija)"
                    if 'projectInfo' in form_data_copy and 'projectName' in form_data_copy['projectInfo']:
                        original_name = form_data_copy['projectInfo']['projectName']
                        form_data_copy['projectInfo']['projectName'] = f"{original_name} (kopija)"
                    else:
                        # Fallback if structure is different
                        form_data_copy['projectInfo'] = form_data_copy.get('projectInfo', {})
                        form_data_copy['projectInfo']['projectName'] = f"{original_data.get('naziv', 'Neimenovano')} (kopija)"
                    
                    # Create new procurement
                    new_id = database.create_procurement(form_data_copy)
                    if new_id:
                        st.success(f"Naročilo uspešno kopirano! Novo naročilo ID: {new_id}")
                        st.rerun()
                    else:
                        st.error("Napaka pri kopiranju naročila")
                else:
                    st.error("Ni mogoče naložiti podatkov naročila")
        
        with col3:
            # Handle delete with confirmation
            if f"confirm_delete_{selected_id}" not in st.session_state:
                if st.button("Izbriši", use_container_width=True):
                    st.session_state[f"confirm_delete_{selected_id}"] = True
                    st.rerun()
            else:
                st.warning("Ali ste prepričani?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Da, izbriši", use_container_width=True):
                        with st.spinner(LOADING_MESSAGES['delete']):
                            if database.delete_procurement(selected_id):
                                st.success("Naročilo uspešno izbrisano")
                                if f"confirm_delete_{selected_id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{selected_id}"]
                                st.rerun()
                with col_no:
                    if st.button("Prekliči", use_container_width=True):
                        del st.session_state[f"confirm_delete_{selected_id}"]
                        st.rerun()
        
        with col4:
            if st.button("Izvoz/Uvoz", use_container_width=True):
                st.session_state.show_export_import = True
                st.session_state.export_selected_id = selected_id
        
        # Second row with symmetric buttons - TODO(human): Implement status change logic
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        col1_2, col2_2, col3_2, col4_2 = st.columns(4)
        
        with col1_2:
            # TODO(human): Implement status change functionality
            # This button should cycle through statuses: Osnutek -> Aktivno -> Zaključeno -> Osnutek
            # Current status should be shown on the button label
            selected_proc = next((p for p in procurements if p['id'] == selected_id), None)
            if selected_proc:
                current_status = selected_proc.get('status', 'Osnutek')
                # Determine next status in cycle
                status_cycle = {
                    'Osnutek': 'Aktivno',
                    'Aktivno': 'Zaključeno', 
                    'Zaključeno': 'Osnutek'
                }
                next_status = status_cycle.get(current_status, 'Osnutek')
                
                if st.button(f"Status: {current_status} → {next_status}", 
                           use_container_width=True, 
                           key=f"status_change_{selected_id}"):
                    if database.update_procurement_status(selected_id, next_status):
                        st.success(f"Status uspešno spremenjen na {next_status}")
                        st.rerun()
        
        with col2_2:
            # Story 25.2: DUMMY AI Generation button
            if st.button("Generiraj z AI", use_container_width=True, key=f"ai_gen_{selected_id}"):
                st.info("Funkcija generiranja z AI bo kmalu na voljo")
        
        with col3_2:
            # Story 25.3: DUMMY Form Preparation button  
            if st.button("Pripravi obrazce", use_container_width=True, key=f"prep_forms_{selected_id}"):
                st.info("Funkcija priprave obrazcev bo kmalu na voljo")
        
        with col4_2:
            # Empty column for symmetry
            st.empty()
        
        # Export/Import Dialog (moved after buttons)
        if st.session_state.get('show_export_import', False):
            with st.expander("Izvoz/Uvoz podatkov", expanded=True):
                operation = st.radio("Izberite operacijo:", ["Izvoz", "Uvoz"])
                
                if operation == "Izvoz":
                    procurement = database.get_procurement_by_id(st.session_state.export_selected_id)
                    if procurement:
                        import json
                        export_data = json.dumps(procurement, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="Prenesi JSON",
                            data=export_data,
                            file_name=f"narocilo_{st.session_state.export_selected_id}.json",
                            mime="application/json"
                        )
                
                elif operation == "Uvoz":
                    uploaded_file = st.file_uploader("Izberite JSON datoteko", type=['json'])
                    if uploaded_file:
                        try:
                            import json
                            import sqlite3
                            data = json.load(uploaded_file)
                            
                            
                            # Direct database insert
                            conn = sqlite3.connect('mainDB.db')
                            cursor = conn.cursor()
                            
                            # Extract basic fields from nested structure
                            # Try to extract from nested structure first, fallback to top-level
                            naziv = data.get('projectInfo', {}).get('projectName', data.get('naziv', 'Uvoženo naročilo'))
                            vrsta = data.get('orderType', {}).get('type', data.get('vrsta', ''))
                            postopek = data.get('submissionProcedure', {}).get('procedure', data.get('postopek', ''))
                            vrednost = data.get('orderType', {}).get('estimatedValue', data.get('vrednost', 0))
                            status = data.get('status', 'Osnutek')
                            
                            
                            # Get form_data 
                            if 'form_data' in data and isinstance(data['form_data'], str):
                                form_data_json = data['form_data']
                            elif 'form_data' in data:
                                form_data_json = json.dumps(data['form_data'])
                            else:
                                form_data_json = json.dumps(data)
                            
                            # Direct insert
                            cursor.execute('''
                                INSERT INTO javna_narocila (
                                    organizacija, naziv, vrsta, postopek, 
                                    datum_objave, status, vrednost, form_data_json,
                                    zadnja_sprememba, uporabnik
                                ) VALUES (?, ?, ?, ?, date('now'), ?, ?, ?, datetime('now'), ?)
                            ''', ('demo_organizacija', naziv, vrsta, postopek, 
                                  status, vrednost, form_data_json, 'import'))
                            
                            new_id = cursor.lastrowid
                            conn.commit()
                            
                            # Verify it was actually inserted
                            cursor.execute('SELECT id, naziv FROM javna_narocila WHERE id = ?', (new_id,))
                            verification = cursor.fetchone()
                            conn.close()
                            
                            
                            # Clear session state
                            for key in ['edit_mode', 'edit_record_id', 'edit_data_loaded', 
                                       'show_export_import', 'current_step']:
                                if key in st.session_state:
                                    if key in ['edit_mode']:
                                        st.session_state[key] = False
                                    elif key in ['edit_record_id']:
                                        st.session_state[key] = None
                                    else:
                                        del st.session_state[key]
                            
                            # Ensure dashboard view after import
                            st.session_state.current_page = 'dashboard'
                            st.session_state['JUST_IMPORTED'] = True  # Flag for app.py to handle redirect
                            
                            st.success(f"Uspešno uvoženo kot naročilo #{new_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Napaka pri uvozu: {str(e)}")
                
                if st.button("Zapri"):
                    del st.session_state['show_export_import']
                    st.rerun()
    else:
        # No procurements
        st.warning("Ni naročil v bazi. Ustvarite novo naročilo z gumbom '+ Novo naročilo' zgoraj.")

def load_procurement_to_form(procurement_id):
    """Load procurement data into form session state."""
    import logging
    logging.info(f"=== FUNCTION START: Loading procurement {procurement_id} to form ===")
    
    from utils.data_migration import migrate_form_data
    
    procurement = database.get_procurement_by_id(procurement_id)
    logging.info(f"Procurement retrieved: {procurement is not None}")
    
    if procurement and procurement.get('form_data'):
        form_data = procurement['form_data']
        logging.info(f"Form data keys: {list(form_data.keys()) if isinstance(form_data, dict) else 'NOT A DICT'}")
        
        # Apply Epic 3.0 data migrations
        form_data = migrate_form_data(form_data)
        logging.info(f"After migration, form data keys: {list(form_data.keys()) if isinstance(form_data, dict) else 'NOT A DICT'}")
        
        # Clear existing form data first
        clear_form_data()
        
        # Set the current draft ID for this session
        st.session_state.current_draft_id = procurement_id
        
        # Load all form data into session state
        def flatten_dict(d, parent_key='', sep='.'):
            """Flatten nested dictionary into dot-notation keys, preserving lists."""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    # Preserve lists as-is (don't flatten them)
                    # This is important for arrays like customers, cofinancers, etc.
                    items.append((new_key, v))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        # Flatten and load into session state
        flattened_data = flatten_dict(form_data)
        
        # Check if we have lots configuration
        has_lots = flattened_data.get('lotsInfo.hasLots', False) or form_data.get('lot_mode') == 'multiple'
        
        # Check for lot-specific fields to handle new lot structure
        lot_mode = form_data.get('lot_mode', '')
        num_lots = form_data.get('num_lots', 0)
        
        # Set lot mode based on has_lots or lot_mode
        if lot_mode == 'multiple':
            st.session_state.lot_mode = 'multiple'
            st.session_state.num_lots = num_lots
        elif not has_lots:
            st.session_state.lot_mode = 'none'
        else:
            lots = flattened_data.get('lots', [])
            if len(lots) > 1:
                st.session_state.lot_mode = 'multiple'
            elif len(lots) == 1:
                st.session_state.lot_mode = 'single'
            else:
                st.session_state.lot_mode = 'none'
        
        logging.info(f"Has lots: {has_lots}, lot_mode: {st.session_state.get('lot_mode')}, num_lots: {num_lots}")
        logging.info(f"Loading {len(flattened_data)} keys into session state")
        logging.info(f"Sample keys: {list(flattened_data.keys())[:10]}")
        
        # Debug: Check for customer/client data
        customer_keys = [k for k in flattened_data.keys() if 'customer' in k.lower() or 'client' in k.lower()]
        logging.info(f"Customer/Client-related keys found: {customer_keys}")
        for ck in customer_keys:
            logging.info(f"  {ck} = {flattened_data[ck]}")
        
        # Specifically check clientInfo.clients (will be handled in main loop below)
        if 'clientInfo.clients' in flattened_data:
            logging.info(f"[load_procurement_to_form] Found clientInfo.clients with {len(flattened_data['clientInfo.clients'])} items")
        
        for key, value in flattened_data.items():
            # Skip special keys that shouldn't have prefix
            special_keys = ['lots', 'lot_names', 'lot_mode', 'current_lot_index', 
                          'lotsInfo.hasLots', 'current_step', 'completed_steps']
            
            # Special handling for clientInfo.clients - always preserve it as-is
            if key == 'clientInfo.clients':
                st.session_state[key] = value
                logging.info(f"[load_procurement_to_form] Preserved {key} = {value}")
                # Also set with general prefix if needed
                if not has_lots:
                    st.session_state[f'general.{key}'] = value
                    
                # CRITICAL FIX: Also set individual fields for each client
                if isinstance(value, list):
                    for i, client in enumerate(value):
                        if isinstance(client, dict):
                            for field_name, field_value in client.items():
                                individual_key = f'clientInfo.clients.{i}.{field_name}'
                                st.session_state[individual_key] = field_value
                                logging.info(f"[load_procurement_to_form] Set individual field {individual_key} = {field_value}")
                continue
            
            if not has_lots and not key.startswith('lot_') and key not in special_keys and not key.startswith('_'):
                # In general mode, add "general." prefix for non-special keys
                general_key = f'general.{key}'
                st.session_state[general_key] = value
                logging.debug(f"Set {general_key} = {value[:50] if isinstance(value, str) else value}")
                # Also set without prefix for backward compatibility
                st.session_state[key] = value
            else:
                # For lots mode or special keys, use as is
                st.session_state[key] = value
                logging.debug(f"Set {key} = {value[:50] if isinstance(value, str) else value}")
        
        # Store that we loaded data for tracking changes
        st.session_state._last_loaded_data = flattened_data.copy()
        
        # Debug: Check what we loaded
        logging.info("=== Data loaded to session state ===")
        logging.info(f"Total keys in session state: {len(st.session_state.keys())}")
        
        test_keys = ['general.clientInfo.name', 'clientInfo.name', 'general.projectInfo.projectName', 'projectInfo.projectName']
        for tk in test_keys:
            if tk in st.session_state:
                logging.info(f"  {tk} = {st.session_state[tk][:50] if isinstance(st.session_state[tk], str) else st.session_state[tk]}")
            else:
                logging.info(f"  {tk} = NOT FOUND")
        
        logging.info("=== END load_procurement_to_form ===")