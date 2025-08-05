"""Main Streamlit application for public procurement document generation."""
import streamlit as st
import database
from config import FORM_STEPS, SCHEMA_FILE
from utils.schema_utils import load_json_schema, get_form_data_from_session
from ui.form_renderer import render_form_section
from ui.admin_panel import render_admin_panel


def main():
    """Main application entry point."""
    st.set_page_config(layout="wide")
    st.title("Generator dokumentacije za javna naročila")

    # Load schema
    if st.session_state.get('schema') is None:
        try:
            st.session_state['schema'] = load_json_schema(SCHEMA_FILE)
        except FileNotFoundError:
            st.error(f"Datoteka sheme '{SCHEMA_FILE}' ni najdena. Prepričajte se, da je v pravilnem imeniku.")
            st.stop()

    # Initialize current step
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    # Sidebar navigation
    st.sidebar.header("Navigacija")
    page_selection = st.sidebar.radio("Pojdi na", ["Obrazec za vnos", "Administracija predlog"])

    if page_selection == "Obrazec za vnos":
        render_main_form()
    elif page_selection == "Administracija predlog":
        render_admin_panel()


def render_main_form():
    """Render the main multi-step form interface."""
    # Initialize database and get drafts
    database.init_db()
    draft_metadata = database.get_all_draft_metadata()
    draft_options = {f"{ts} (ID: {id})": id for id, ts in draft_metadata}

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header(st.session_state['schema'].get("title", "Obrazec"))
        
        # Render current step form fields
        current_step_properties = {
            k: st.session_state['schema']["properties"][k] 
            for k in FORM_STEPS[st.session_state.current_step]
        }
        render_form_section(current_step_properties)

        # Edge-aligned navigation buttons
        col_nav_left, col_nav_center, col_nav_right = st.columns([1, 3, 1])

        with col_nav_left:
            if st.session_state.current_step > 0:
                if st.button("Nazaj", type="secondary"):
                    st.session_state.current_step -= 1
                    st.rerun()

        with col_nav_right:
            if st.session_state.current_step < len(FORM_STEPS) - 1:
                if st.button("Naprej", type="primary"):
                    st.session_state.current_step += 1
                    st.rerun()
            else:
                if st.button("Pripravi dokumente", type="primary"):
                    final_form_data = get_form_data_from_session()
                    st.write("Obrazec poslan s podatki:")
                    st.json(final_form_data)
                    st.success("Dokumenti uspešno pripravljeni!")

    with col2:
        render_drafts_sidebar(draft_options)


def render_drafts_sidebar(draft_options):
    """Render the drafts management sidebar."""
    st.header("Osnutki")
    
    if draft_options:
        selected_draft_label = st.selectbox(
            "Naloži osnutek", 
            options=list(draft_options.keys()), 
            key="load_draft_selectbox"
        )
        
        if st.button("Naloži izbrani osnutek"):
            selected_draft_id = draft_options[selected_draft_label]
            loaded_data = database.load_draft(selected_draft_id)
            if loaded_data:
                # Populate form fields with loaded data
                def populate_session_state(data, parent_key=""):
                    for key, value in data.items():
                        full_key = f"{parent_key}.{key}" if parent_key else key
                        if isinstance(value, dict):
                            populate_session_state(value, full_key)
                        else:
                            st.session_state[full_key] = value
                            
                populate_session_state(loaded_data)
                st.success("Osnutek uspešno naložen!")
                st.rerun()
            else:
                st.error("Napaka pri nalaganju osnutka.")
    else:
        st.info("Ni shranjenih osnutkov.")
    
    if st.button("Shrani osnutek"):
        form_values = get_form_data_from_session()
        draft_id = database.save_draft(form_values)
        st.success(f"Osnutek shranjen z ID: {draft_id}")
        st.rerun()


if __name__ == "__main__":
    main()