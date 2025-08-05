import streamlit as st
import json
from datetime import date
import database
import template_service
import sqlite3 # Import sqlite3 for clear_drafts in template_service
import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123") # Default for demonstration

def load_json_schema(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)





def update_session_state(key, value):
    """Update session state for form field changes."""
    st.session_state[key] = value

def render_form_section(schema_properties, parent_key=""):
    """Render form fields based on JSON schema properties."""
    for prop_name, prop_details in schema_properties.items():
        full_key = f"{parent_key}.{prop_name}" if parent_key else prop_name
        label = prop_details.get("title", prop_name)
        
        # Get current value from session_state with appropriate defaults
        current_value = _get_default_value(full_key, prop_details)

        # Render appropriate form element based on property type
        if prop_details.get("type") == "object":
            st.subheader(label)
            render_form_section(prop_details.get("properties", {}), parent_key=full_key)
        elif prop_details.get("type") == "array" and "enum" in prop_details:
            st.multiselect(label, options=prop_details["enum"], default=current_value, key=full_key)
        elif prop_details.get("type") == "string" and "enum" in prop_details:
            index = prop_details["enum"].index(current_value) if current_value in prop_details["enum"] else 0
            st.selectbox(label, options=prop_details["enum"], index=index, key=full_key)
        elif prop_details.get("type") == "string":
            _render_string_field(label, full_key, current_value, prop_details)
        elif prop_details.get("type") == "number":
            st.number_input(label, value=current_value, key=full_key)

def _get_default_value(full_key, prop_details):
    """Get appropriate default value for form field."""
    if prop_details.get("type") == "number":
        return st.session_state.get(full_key, 0.0)
    elif prop_details.get("format") == "date":
        return st.session_state.get(full_key, date.today())
    elif prop_details.get("type") == "array":
        return st.session_state.get(full_key, [])
    else:
        return st.session_state.get(full_key, "")

def _render_string_field(label, full_key, current_value, prop_details):
    """Render string-type form fields based on format."""
    if prop_details.get("format") == "textarea":
        st.text_area(label, value=current_value, key=full_key)
    elif prop_details.get("format") == "date":
        st.date_input(label, value=current_value, key=full_key)
    elif prop_details.get("format") == "file":
        st.file_uploader(label, key=full_key)
    else:
        st.text_input(label, value=current_value, key=full_key)

def get_form_data_from_session():
    """
    Reconstructs the nested form data dictionary from Streamlit's flat session_state.
    """
    form_data = {}
    schema_properties = st.session_state.get('schema', {}).get('properties', {})
    if not schema_properties:
        return {}

    for key, value in st.session_state.items():
        top_level_key = key.split('.')[0]
        if top_level_key in schema_properties:
            parts = key.split('.')
            d = form_data
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value
    return form_data

def main():
    st.set_page_config(layout="wide")
    st.title("Generator dokumentacije za javna naročila")

    schema_file = "SEZNAM_POTREBNIH_PODATKOV.json"
    if st.session_state.get('schema') is None:
        try:
            st.session_state['schema'] = load_json_schema(schema_file)
        except FileNotFoundError:
            st.error(f"Datoteka sheme '{schema_file}' ni najdena. Prepričajte se, da je v pravilnem imeniku.")
            st.stop()

    # Define form steps (4 steps)
    form_steps = [
        ["clientData", "projectName", "submissionProcedure"], # Step 1: Basic project info
        ["orderType"], # Step 2: Order type and details
        ["exclusionReasons", "participationConditions"], # Step 3: Requirements and conditions
        ["financialGuarantees", "selectionCriteria", "socialCriteria", "otherCriteria", "contractType"]  # Step 4: Criteria and contract
    ]

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    # Sidebar navigation
    st.sidebar.header("Navigacija")
    page_selection = st.sidebar.radio("Pojdi na", ["Obrazec za vnos", "Administracija predlog"]) # Localized

    if page_selection == "Obrazec za vnos": # Localized
        # Initialize database and get drafts
        database.init_db()
        draft_metadata = database.get_all_draft_metadata()
        draft_options = {f"{ts} (ID: {id})": id for id, ts in draft_metadata}

        col1, col2 = st.columns([3, 1])

        with col1:
            st.header(st.session_state['schema'].get("title", "Obrazec"))
            
            current_step_properties = {k: st.session_state['schema']["properties"][k] for k in form_steps[st.session_state.current_step]}
            render_form_section(current_step_properties)

            # Edge-aligned navigation buttons
            col_nav_left, col_nav_center, col_nav_right = st.columns([1, 3, 1])

            with col_nav_left:
                if st.session_state.current_step > 0:
                    if st.button("Nazaj", type="secondary"):
                        st.session_state.current_step -= 1
                        st.rerun()

            with col_nav_right:
                if st.session_state.current_step < len(form_steps) - 1:
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
            st.header("Osnutki") # Localized
            if draft_options:
                selected_draft_label = st.selectbox("Naloži osnutek", options=list(draft_options.keys()), key="load_draft_selectbox") # Localized
                load_draft_button = st.button("Naloži izbrani osnutek") # Localized
                if load_draft_button:
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
                        st.success("Osnutek uspešno naložen!") # Localized
                        st.rerun() # Rerun to update form fields
                    else:
                        st.error("Napaka pri nalaganju osnutka.") # Localized
            else:
                st.info("Ni shranjenih osnutkov.") # Localized
            
            save_draft_button = st.button("Shrani osnutek") # Localized
            if save_draft_button:
                form_values = get_form_data_from_session()
                draft_id = database.save_draft(form_values)
                st.success(f"Osnutek shranjen z ID: {draft_id}") # Localized
                st.rerun() # Rerun to update draft list

    elif page_selection == "Administracija predlog": # Localized
        st.header("Administracija predlog") # Localized

        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False

        if not st.session_state["logged_in"]:
            password = st.text_input("Geslo", type="password") # Localized
            if st.button("Prijava"): # Localized
                if password == ADMIN_PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("Uspešna prijava!") # Localized
                    st.rerun()
                else:
                    st.error("Napačno geslo.") # Localized
        
        if st.session_state["logged_in"]:
            st.subheader("Upravljanje predlog Word") # Localized
            uploaded_file = st.file_uploader("Naloži novo predlogo (.docx)", type=["docx"]) # Localized
            if uploaded_file:
                overwrite_existing = st.checkbox("Prepiši obstoječo predlogo, če obstaja") # Localized
                success, message = template_service.save_template(uploaded_file, overwrite=overwrite_existing)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            st.subheader("Seznam obstoječih predlog") # Localized
            templates = template_service.list_templates()
            if templates:
                for t in templates:
                    st.write(f"- {t}")
            else:
                st.info("Ni najdenih predlog.") # Localized

            st.subheader("Upravljanje osnutkov") # Localized
            if st.button("Počisti vse osnutke"): # Localized
                success, message = template_service.clear_drafts()
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            if st.button("Varnostno kopiraj osnutke"): # Localized
                success, message = template_service.backup_drafts()
                if success:
                    st.success(message)
                else:
                    st.error(message)

            st.subheader("Upravljanje zbirk ChromaDB") # Localized
            st.info("Funkcionalnost upravljanja zbirk ChromaDB še ni implementirana.") # Localized

if __name__ == "__main__":
    main()