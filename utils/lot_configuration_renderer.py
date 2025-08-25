"""Renderer for the new lot configuration step - only collects lot names."""
import streamlit as st


def render_lot_configuration():
    """
    Render the lot configuration page that ONLY collects lot names.
    No procurement details are entered here.
    """
    st.header("🗂️ Konfiguracija sklopov")
    
    st.info("""
    **Vnesite imena sklopov**  
    V tem koraku definirate samo imena sklopov. Podrobnosti o naročilu za vsak sklop boste vnašali v naslednjih korakih.
    """)
    
    # Initialize lot_names in session state if not present
    if 'lot_names' not in st.session_state:
        st.session_state.lot_names = ["Sklop 1"]
    
    # Create a container for lot names
    lot_container = st.container()
    
    with lot_container:
        # Display existing lot names with edit/delete functionality
        for i, lot_name in enumerate(st.session_state.lot_names):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                new_name = st.text_input(
                    f"Ime sklopa {i+1}",
                    value=lot_name,
                    key=f"lot_name_input_{i}",
                    help="Vnesite opisno ime sklopa (npr. 'Pisarniški material', 'IT oprema')"
                )
                # Update the lot name in session state
                if new_name != lot_name:
                    st.session_state.lot_names[i] = new_name
            
            with col2:
                # Only show delete button if more than one lot
                if len(st.session_state.lot_names) > 1:
                    if st.button("🗑️", key=f"remove_lot_{i}", 
                                help="Odstrani ta sklop",
                                use_container_width=True):
                        st.session_state.lot_names.pop(i)
                        st.rerun()
    
    # Add new lot button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("➕ Dodaj nov sklop", use_container_width=True):
            next_num = len(st.session_state.lot_names) + 1
            st.session_state.lot_names.append(f"Sklop {next_num}")
            st.rerun()
    
    # Show summary
    st.divider()
    
    if len(st.session_state.lot_names) == 1:
        st.success(f"✅ **Konfiguriran je 1 sklop**")
    else:
        st.success(f"✅ **Konfigurirani so {len(st.session_state.lot_names)} sklopi**")
    
    # Display lot summary
    with st.expander("Pregled sklopov", expanded=True):
        for i, lot_name in enumerate(st.session_state.lot_names):
            st.write(f"{i+1}. **{lot_name}**")
    
    # Update lots in session state with proper structure
    if 'lots' not in st.session_state:
        st.session_state.lots = []
    
    # Sync the lots array with lot_names
    current_lots = st.session_state.lots
    new_lots = []
    
    for i, name in enumerate(st.session_state.lot_names):
        # Preserve existing lot data if it exists
        if i < len(current_lots):
            lot_data = current_lots[i]
            lot_data['name'] = name
            new_lots.append(lot_data)
        else:
            # Create new lot entry
            new_lots.append({'name': name})
    
    st.session_state.lots = new_lots
    
    # Set lot mode
    st.session_state.lot_mode = 'multiple'
    
    return True  # Validation always passes for lot configuration