"""Enhanced renderer for lotsInfo that includes lot configuration inline."""
import streamlit as st


def render_lots_info(field_renderer, properties, parent_key=""):
    """
    Render the lotsInfo section with integrated lot configuration.
    When hasLots is checked, show lot configuration immediately.
    """
    # Render the hasLots checkbox using standard field renderer
    has_lots_key = f"{parent_key}.hasLots" if parent_key else "hasLots"
    
    # Render the checkbox
    if 'hasLots' in properties:
        field_renderer.render_field('hasLots', properties['hasLots'], parent_key)
    
    # Check if lots are enabled
    has_lots = st.session_state.get(f"{parent_key}.hasLots" if parent_key else "lotsInfo.hasLots", False)
    
    if has_lots:
        # Show lot configuration immediately
        st.markdown("---")
        st.subheader("🗂️ Konfiguracija sklopov")
        
        st.info("""
        **Vnesite imena sklopov**  
        Definirajte imena sklopov. Podrobnosti za vsak sklop boste vnašali v naslednjih korakih.
        """)
        
        # Initialize lot_names if not present
        if 'lot_names' not in st.session_state:
            st.session_state.lot_names = ["Sklop 1"]
        
        # Display existing lot names with edit/delete functionality
        for i, lot_name in enumerate(st.session_state.lot_names):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                new_name = st.text_input(
                    f"Ime sklopa {i+1} *",
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
        st.markdown("---")
        
        num_lots = len(st.session_state.lot_names)
        if num_lots == 1:
            st.success(f"✅ **Konfiguriran je 1 sklop**")
        elif num_lots == 2:
            st.success(f"✅ **Konfigurirana sta 2 sklopa**")
        elif num_lots in [3, 4]:
            st.success(f"✅ **Konfigurirani so {num_lots} sklopi**")
        else:
            st.success(f"✅ **Konfiguriranih je {num_lots} sklopov**")
        
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
            if i < len(current_lots) and isinstance(current_lots[i], dict):
                lot_data = current_lots[i]
                lot_data['name'] = name
                new_lots.append(lot_data)
            else:
                # Create new lot entry
                new_lots.append({'name': name})
        
        st.session_state.lots = new_lots
        
        # Set lot mode based on number of lots
        if len(st.session_state.lot_names) > 1:
            st.session_state.lot_mode = 'multiple'
        elif len(st.session_state.lot_names) == 1:
            st.session_state.lot_mode = 'single'
        else:
            st.session_state.lot_mode = 'none'
    else:
        # No lots - clear lot configuration
        if 'lot_names' in st.session_state:
            del st.session_state.lot_names
        if 'lots' in st.session_state:
            del st.session_state.lots
        st.session_state.lot_mode = 'none'