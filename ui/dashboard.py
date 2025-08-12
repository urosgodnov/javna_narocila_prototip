"""
Dashboard view for managing public procurements
Provides table view with CRUD operations
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import database
from utils.schema_utils import get_form_data_from_session, clear_form_data

def render_dashboard():
    """Render the procurement dashboard with table view."""
    # Import and use modern dashboard if available
    try:
        from ui.modern_dashboard_simple import render_modern_dashboard
        render_modern_dashboard()
        return
    except Exception as e:
        st.error(f"Error loading modern dashboard: {e}")
        pass
    
    st.title("📋 Javna Naročila - Pregled")
    st.markdown(f"**Organizacija:** demo_organizacija")
    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
    with col1:
        if st.button("➕ Novo javno naročilo", type="primary", use_container_width=True):
            st.session_state.current_page = 'form'
            st.session_state.edit_mode = False
            st.session_state.edit_record_id = None
            st.session_state.current_step = 0  # Reset to first step
            clear_form_data()  # Clear any existing form data
            st.rerun()
    
    with col2:
        if st.button("🔄 Osveži", use_container_width=True):
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
            total_value = sum([p['vrednost'] or 0 for p in procurements])
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

def display_procurements_table(procurements):
    """Display procurements in an interactive table with actions."""
    
    # Convert to DataFrame for better display
    df_data = []
    for proc in procurements:
        df_data.append({
            'ID': proc['id'],
            'Naziv': proc['naziv'] or 'Neimenovano',
            'Vrsta': proc['vrsta'] or '-',
            'Postopek': proc['postopek'] or '-',
            'Datum': proc['datum_objave'] or '-',
            'Status': proc['status'],
            'Vrednost (€)': f"{proc['vrednost'] or 0:,.2f}",
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
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = True
                st.session_state.edit_record_id = selected_id
                st.session_state.current_step = 0
                load_procurement_to_form(selected_id)
                st.rerun()
        
        with col2:
            if st.button("📋 Kopiraj", use_container_width=True):
                # Load the procurement but create as new
                st.session_state.current_page = 'form'
                st.session_state.edit_mode = False
                st.session_state.edit_record_id = None
                st.session_state.current_step = 0
                load_procurement_to_form(selected_id)
                st.success("Naročilo kopirano. Urejate novo kopijo.")
                st.rerun()
        
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
            # Status change dropdown
            selected_proc = next(p for p in procurements if p['id'] == selected_id)
            current_status = selected_proc['status']
            new_status = st.selectbox(
                "Spremeni status:",
                options=["Osnutek", "Aktivno", "Zaključeno"],
                index=["Osnutek", "Aktivno", "Zaključeno"].index(current_status),
                key=f"status_{selected_id}"
            )
            if new_status != current_status:
                if database.update_procurement_status(selected_id, new_status):
                    st.success(f"Status spremenjen na: {new_status}")
                    st.rerun()

def load_procurement_to_form(procurement_id):
    """Load procurement data into form session state."""
    procurement = database.get_procurement_by_id(procurement_id)
    
    if procurement and procurement.get('form_data'):
        form_data = procurement['form_data']
        
        # Clear existing form data first
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