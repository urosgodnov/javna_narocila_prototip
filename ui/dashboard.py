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
        
        # Check if this procurement has lots
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
    
    # Header with organization and logout
    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.title("📋 Javna Naročila - Pregled")
        current_org = st.session_state.get('organization', 'demo_organizacija')
        st.markdown(f"**Organizacija:** {current_org}")
    
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        if st.button("🚪 Odjava", use_container_width=True):
            # Clear authentication
            for key in ['authenticated', 'organization']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        if st.button("➕ Novo javno naročilo", type="primary", use_container_width=True):
            with st.spinner('Pripravljam nov obrazec...'):
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = False
                st.session_state.edit_record_id = None
                st.session_state.current_step = 0  # Reset to first step
                clear_form_data()  # Clear any existing form data
                st.rerun()
    
    with col2:
        if st.button("🔄 Osveži", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📋 Uvoz", use_container_width=True):
            st.session_state.show_import_dialog = True
    
    with col4:
        if st.button("⚙️ Nastavitve", use_container_width=True):
            st.session_state.current_page = 'admin'
            st.rerun()
    
    # Fetch procurements
    procurements = database.get_procurements_for_customer('demo_organizacija')
    
    if procurements:
        # Add some statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vsa naročila", len(procurements))
        with col2:
            active_count = len([p for p in procurements if p['status'] == 'Aktivno'])
            st.metric("Aktivna", active_count)
        with col3:
            draft_count = len([p for p in procurements if p['status'] == 'Osnutek'])
            st.metric("Osnutki", draft_count)
        with col4:
            total_value = sum([calculate_procurement_value(p) for p in procurements])
            st.metric("Skupna vrednost", f"{total_value:,.2f} €")
        
        st.markdown("---")
        
        # Display procurements in an enhanced table
        display_procurements_table(procurements)
        
    else:
        # Empty state
        st.info("📭 Ni najdenih javnih naročil.")
        st.markdown("""
        ### Začnite z ustvarjanjem prvega javnega naročila
        
        Kliknite na gumb **'➕ Novo javno naročilo'** zgoraj, da začnete z vnosom.
        
        Po ustvarjanju bo naročilo prikazano v tej tabeli, kjer ga boste lahko:
        - 📝 Urejali
        - 📋 Kopirali
        - 🗑️ Brisali
        - 📊 Spremljali status
        """)
    
    # Import Dialog (works even with empty database)
    if st.session_state.get('show_import_dialog', False):
        with st.expander("📋 Uvoz podatkov", expanded=True):
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
                    
                    st.success(f"✅ Uspešno uvoženo kot naročilo #{new_id}")
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
    
    # Display the dataframe
    st.subheader("📊 Seznam javnih naročil")
    
    # Add search/filter
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_term = st.text_input("🔍 Iskanje", placeholder="Vnesite iskalni niz...")
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
    
    # Action buttons for each row
    st.subheader("🔧 Akcije")
    
    
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
            if st.button("✏️ Uredi", use_container_width=True):
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
            if st.button("📋 Kopiraj", use_container_width=True):
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
                        st.success(f"✅ Naročilo uspešno kopirano! Novo naročilo ID: {new_id}")
                        st.rerun()
                    else:
                        st.error("❌ Napaka pri kopiranju naročila")
                else:
                    st.error("❌ Ni mogoče naložiti podatkov naročila")
        
        with col3:
            # Handle delete with confirmation
            if f"confirm_delete_{selected_id}" not in st.session_state:
                if st.button("🗑️ Izbriši", use_container_width=True, type="secondary"):
                    st.session_state[f"confirm_delete_{selected_id}"] = True
                    st.rerun()
            else:
                st.warning("Ali ste prepričani?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Da, izbriši", type="primary", use_container_width=True):
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
            if st.button("📋 Izvoz/Uvoz", use_container_width=True):
                st.session_state.show_export_import = True
                st.session_state.export_selected_id = selected_id
        
        # Second row of buttons
        col_ai, col_forms, col_status = st.columns(3)
        
        with col_ai:
            # Story 25.2: DUMMY AI Generation button
            if st.button("🤖 Generiraj vsebino z AI", use_container_width=True, key=f"ai_gen_{selected_id}"):
                st.info("ℹ️ Funkcija generiranja z AI bo kmalu na voljo")
        
        with col_forms:
            # Story 25.3: DUMMY Form Preparation button
            if st.button("📄 Pripravi obrazce", use_container_width=True, key=f"prep_forms_{selected_id}"):
                st.info("ℹ️ Funkcija priprave obrazcev bo kmalu na voljo")
        
        with col_status:
            # Status change with button confirmation
            try:
                selected_proc = next(p for p in procurements if p['id'] == selected_id)
                current_status = selected_proc.get('status', 'Osnutek')
                
                st.markdown(f"**Trenutni status:** {current_status}")
                
                # Show buttons for status change
                st.markdown("Spremeni na:")
                col_s1, col_s2, col_s3 = st.columns(3)
                
                with col_s1:
                    if current_status != "Osnutek":
                        if st.button("📝 Osnutek", key=f"set_osnutek_{selected_id}", use_container_width=True):
                            if database.update_procurement_status(selected_id, "Osnutek"):
                                st.success("Status spremenjen!")
                                st.rerun()
                
                with col_s2:
                    if current_status != "Aktivno":
                        if st.button("▶️ Aktivno", key=f"set_aktivno_{selected_id}", use_container_width=True):
                            if database.update_procurement_status(selected_id, "Aktivno"):
                                st.success("Status spremenjen!")
                                st.rerun()
                
                with col_s3:
                    if current_status != "Zaključeno":
                        if st.button("✅ Zaključeno", key=f"set_zakljuceno_{selected_id}", use_container_width=True):
                            if database.update_procurement_status(selected_id, "Zaključeno"):
                                st.success("Status spremenjen!")
                                st.rerun()
                                
            except Exception as e:
                st.error(f"Napaka pri statusu: {str(e)}")
        
        # Export/Import Dialog (moved after buttons)
        if st.session_state.get('show_export_import', False):
            with st.expander("📋 Izvoz/Uvoz podatkov", expanded=True):
                operation = st.radio("Izberite operacijo:", ["Izvoz", "Uvoz"])
                
                if operation == "Izvoz":
                    procurement = database.get_procurement_by_id(st.session_state.export_selected_id)
                    if procurement:
                        import json
                        export_data = json.dumps(procurement, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="💾 Prenesi JSON",
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
                            
                            st.success(f"✅ Uspešno uvoženo kot naročilo #{new_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Napaka pri uvozu: {str(e)}")
                
                if st.button("Zapri"):
                    del st.session_state['show_export_import']
                    st.rerun()
    else:
        # No procurements
        st.warning("⚠️ Ni naročil v bazi. Ustvarite novo naročilo z gumbom '➕ Novo javno naročilo' zgoraj.")

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
        
        # Check if we have lots configuration
        has_lots = flattened_data.get('lotsInfo.hasLots', False)
        
        # Set lot mode based on has_lots
        if not has_lots:
            st.session_state.lot_mode = 'none'
        else:
            lots = flattened_data.get('lots', [])
            if len(lots) > 1:
                st.session_state.lot_mode = 'multiple'
            elif len(lots) == 1:
                st.session_state.lot_mode = 'single'
            else:
                st.session_state.lot_mode = 'none'
        
        logging.info(f"Has lots: {has_lots}, lot_mode: {st.session_state.lot_mode}")
        logging.info(f"Loading {len(flattened_data)} keys into session state")
        logging.info(f"Sample keys: {list(flattened_data.keys())[:5]}")
        
        for key, value in flattened_data.items():
            # Skip special keys that shouldn't have prefix
            special_keys = ['lots', 'lot_names', 'lot_mode', 'current_lot_index', 
                          'lotsInfo.hasLots', 'current_step', 'completed_steps']
            
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