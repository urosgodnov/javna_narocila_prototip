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

def render_form(schema):
    st.header(schema.get("title", "Obrazec"))
    form_data = {}
    for prop_name, prop_details in schema.get("properties", {}).items():
        label = prop_details.get("title", prop_name)
        
        # Get current value from session_state if available, otherwise use default
        current_value = st.session_state.get(prop_name, "")
        if prop_details.get("type") == "number":
            current_value = st.session_state.get(prop_name, 0.0)
        elif prop_details.get("format") == "date":
            current_value = st.session_state.get(prop_name, date.today())
        elif prop_details.get("type") == "array":
            current_value = st.session_state.get(prop_name, [])

        if prop_details.get("type") == "array" and "enum" in prop_details:
            # Multi-select dropdown
            form_data[prop_name] = st.multiselect(label, options=prop_details["enum"], default=current_value, key=prop_name)
        elif prop_details.get("type") == "string" and "enum" in prop_details:
            # Single-select dropdown
            form_data[prop_name] = st.selectbox(label, options=prop_details["enum"], index=prop_details["enum"].index(current_value) if current_value in prop_details["enum"] else 0, key=prop_name)
        elif prop_details.get("type") == "string":
            if prop_details.get("format") == "textarea":
                form_data[prop_name] = st.text_area(label, value=current_value, key=prop_name)
            elif prop_details.get("format") == "date":
                form_data[prop_name] = st.date_input(label, value=current_value, key=prop_name)
            elif prop_details.get("format") == "file":
                form_data[prop_name] = st.file_uploader(label, key=prop_name)
            else:
                form_data[prop_name] = st.text_input(label, value=current_value, key=prop_name)
        elif prop_details.get("type") == "number":
            form_data[prop_name] = st.number_input(label, value=current_value, key=prop_name)
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
            with st.form(key='procurement_form'):
                form_values = render_form(st.session_state['schema'])
                submit_button = st.form_submit_button(label='Pošlji')

                if submit_button:
                    st.write("Obrazec poslan s podatki:")
                    st.json(form_values)

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
                        for key, value in loaded_data.items():
                            st.session_state[key] = value
                        st.success("Osnutek uspešno naložen!") # Localized
                        st.experimental_rerun() # Rerun to update form fields
                    else:
                        st.error("Napaka pri nalaganju osnutka.") # Localized
            else:
                st.info("Ni shranjenih osnutkov.") # Localized
            
            save_draft_button = st.button("Shrani osnutek") # Localized
            if save_draft_button:
                draft_id = database.save_draft(form_values)
                st.success(f"Osnutek shranjen z ID: {draft_id}") # Localized
                st.experimental_rerun() # Rerun to update draft list

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
                    st.experimental_rerun()
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