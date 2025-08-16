"""Administration panel UI components."""
import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
import template_service
from config import ADMIN_PASSWORD
import json
import uuid
import pandas as pd
from typing import List
import sqlite3
import database
import csv
from io import StringIO
from utils.cpv_manager import (
    get_all_cpv_codes, get_cpv_by_id, create_cpv_code, 
    update_cpv_code, delete_cpv_code, get_cpv_count
)

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
            <div style=\"
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background-color: #f8f9fa;
                margin: 20px 0;
            \">
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
        
        st.markdown("--- ")
        
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
            
            st.markdown("--- ")
            
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
    from ui.database_manager import render_database_manager
    render_database_manager()

def render_organization_management_tab():
    """Render the organization management tab content."""
    
    # Get the absolute path for organizations.json
    dir_path = os.path.dirname(os.path.realpath(__file__))
    org_file_path = os.path.join(dir_path, '..', 'json_files', 'organizations.json')

    # Create the file if it doesn't exist
    if not os.path.exists(org_file_path):
        with open(org_file_path, 'w') as f:
            json.dump([], f)

    # Load organizations and perform migration if necessary
    with open(org_file_path, 'r') as f:
        organizations = json.load(f)

    migrated = False
    new_organizations = []
    demo_org_id = None

    # Migration logic
    for org in organizations:
        if isinstance(org, str):
            # Old format, migrate it
            org_id = str(uuid.uuid4())
            if org == "demo_organizacije":
                demo_org_id = org_id
            new_organizations.append({"id": org_id, "name": org})
            migrated = True
        else:
            # Already new format
            if org["name"] == "demo_organizacije":
                demo_org_id = org["id"]
            new_organizations.append(org)
    
    # Ensure demo_organizacije exists and get its ID
    if not any(org["name"] == "demo_organizacije" for org in new_organizations):
        demo_org_id = str(uuid.uuid4())
        new_organizations.append({"id": demo_org_id, "name": "demo_organizacije"})
        migrated = True

    if migrated:
        with open(org_file_path, 'w') as f:
            json.dump(new_organizations, f, indent=4)
        st.success("Organizacije uspešno migrirane na nov format.")
        st.rerun()

    st.session_state["demo_organizacije_id"] = demo_org_id

    with st.container():
        st.markdown("### 🏢 Upravljanje organizacij")

        # Add new organization form
        with st.form(key='add_organization_form'):
            new_org_name = st.text_input("Naziv nove organizacije")
            submitted = st.form_submit_button("Dodaj organizacijo")
            if submitted and new_org_name:
                # Check if organization already exists by name
                if any(org["name"] == new_org_name for org in new_organizations):
                    st.warning(f"Organizacija '{new_org_name}' že obstaja.")
                else:
                    new_org_id = str(uuid.uuid4())
                    new_organizations.append({"id": new_org_id, "name": new_org_name})
                    with open(org_file_path, "w") as f_write:
                        json.dump(new_organizations, f_write, indent=4)
                    st.success(f"Organizacija '{new_org_name}' dodana.")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Seznam obstoječih organizacij")
        if new_organizations:
            for i, org in enumerate(new_organizations):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"- **{org["name"]}** (ID: `{org["id"]}`)")
                with col2:
                    if st.button(f"🗑️ Izbriši", key=f"delete_org_{org["id"]}"):
                        new_organizations.pop(i)
                        with open(org_file_path, "w") as f_write:
                            json.dump(new_organizations, f_write, indent=4)
                        st.rerun()
        else:
            st.info("Ni najdenih organizacij.")


def render_cpv_management_tab():
    """Render the CPV codes management tab content."""
    with st.container():
        st.markdown("### 🔢 Upravljanje CPV kod")
        
        # Statistics
        total_cpv = get_cpv_count()
        st.info(f"📊 Skupno CPV kod v bazi: **{total_cpv}**")
        
        # Add new CPV code
        st.markdown("#### ➕ Dodaj novo CPV kodo")
        with st.form(key='add_cpv_form'):
            col1, col2 = st.columns([1, 3])
            with col1:
                new_code = st.text_input("CPV koda", placeholder="npr. 30192000-1")
            with col2:
                new_desc = st.text_input("Opis", placeholder="npr. Pisarniški material")
            
            submitted = st.form_submit_button("Dodaj CPV kodo")
            if submitted and new_code and new_desc:
                cpv_id = create_cpv_code(new_code, new_desc)
                if cpv_id:
                    st.success(f"✅ CPV koda {new_code} uspešno dodana")
                    st.rerun()
                else:
                    st.error(f"❌ CPV koda {new_code} že obstaja")
        
        st.markdown("---")
        
        # Search and list CPV codes
        st.markdown("#### 🔍 Iskanje in upravljanje CPV kod")
        
        # Search
        search_term = st.text_input("🔍 Išči po kodi ali opisu", key="cpv_search")
        
        # Pagination
        if 'cpv_page' not in st.session_state:
            st.session_state.cpv_page = 1
        
        # Get CPV codes
        cpv_codes, total_count = get_all_cpv_codes(
            search_term=search_term,
            page=st.session_state.cpv_page,
            per_page=50
        )
        
        if cpv_codes:
            # Pagination controls
            total_pages = (total_count + 49) // 50
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("⬅️ Prejšnja", disabled=st.session_state.cpv_page <= 1):
                    st.session_state.cpv_page -= 1
                    st.rerun()
            
            with col2:
                st.markdown(f"Stran {st.session_state.cpv_page} od {total_pages}")
            
            with col3:
                if st.button("Naslednja ➡️", disabled=st.session_state.cpv_page >= total_pages):
                    st.session_state.cpv_page += 1
                    st.rerun()
            
            # Display CPV codes
            for cpv in cpv_codes:
                with st.expander(f"{cpv['code']} - {cpv['description'][:50]}..."):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Edit form
                        with st.form(key=f"edit_cpv_{cpv['id']}"):
                            edited_code = st.text_input("Koda", value=cpv['code'])
                            edited_desc = st.text_area("Opis", value=cpv['description'], height=100)
                            
                            col_save, col_delete = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Shrani spremembe"):
                                    if update_cpv_code(cpv['id'], edited_code, edited_desc):
                                        st.success("✅ Uspešno posodobljeno")
                                        st.rerun()
                                    else:
                                        st.error("❌ Napaka pri posodabljanju")
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Izbriši", type="secondary"):
                                    if delete_cpv_code(cpv['id']):
                                        st.success("✅ Uspešno izbrisano")
                                        st.rerun()
                                    else:
                                        st.error("❌ Napaka pri brisanju")
                    
                    with col2:
                        st.markdown(f"**ID:** {cpv['id']}")
                        st.markdown(f"**Ustvarjeno:** {cpv['created_at'][:10]}")
                        if cpv['updated_at']:
                            st.markdown(f"**Posodobljeno:** {cpv['updated_at'][:10]}")
        else:
            if search_term:
                st.info(f"Ni najdenih CPV kod za iskalni niz '{search_term}'")
            else:
                st.info("Ni CPV kod v bazi. Uvozite jih zgoraj.")


def expand_cpv_range(start_code: str, end_code: str) -> List[str]:
    """
    Expand a CPV code range into individual codes.
    
    Args:
        start_code: Starting CPV code (e.g., "71000000-8")
        end_code: Ending CPV code (e.g., "72000000-5")
    
    Returns:
        List of CPV codes in the range
    """
    codes = []
    
    # Extract the numeric part before the dash
    start_base = int(start_code.split('-')[0])
    end_base = int(end_code.split('-')[0])
    
    # Generate codes in range
    for code_num in range(start_base, end_base + 1, 10000):
        # Calculate check digit (simplified - normally follows specific algorithm)
        check_digit = code_num % 10
        if check_digit == 0:
            check_digit = 1
        codes.append(f"{code_num:08d}-{check_digit}")
    
    return codes


def load_criteria_settings():
    """Load saved criteria settings from database (kept for compatibility during migration)."""
    from utils import criteria_manager
    
    # Get criteria types
    types = criteria_manager.get_criteria_types()
    
    settings = {
        "price_criteria": [],
        "social_criteria": []
    }
    
    for criteria_type in types:
        cpv_codes = criteria_manager.get_cpv_for_criteria(criteria_type['id'])
        if criteria_type['name'] == "Merila - cena":
            settings["price_criteria"] = cpv_codes
        elif criteria_type['name'] == "Merila - socialna merila":
            settings["social_criteria"] = cpv_codes
    
    return settings


def save_criteria_settings(settings: dict):
    """Save criteria settings to database (kept for compatibility during migration)."""
    from utils import criteria_manager
    
    # Get criteria types
    price_type = criteria_manager.get_criteria_type_by_name("Merila - cena")
    social_type = criteria_manager.get_criteria_type_by_name("Merila - socialna merila")
    
    # Save price criteria
    if price_type:
        criteria_manager.save_cpv_criteria(price_type['id'], settings.get('price_criteria', []))
    
    # Save social criteria
    if social_type:
        criteria_manager.save_cpv_criteria(social_type['id'], settings.get('social_criteria', []))


def get_default_price_criteria_codes() -> List[str]:
    """Get the default CPV codes for price criteria."""
    codes = []
    
    # Range 71000000-8 to 72000000-5
    codes.extend(expand_cpv_range("71000000-8", "72000000-5"))
    
    # Additional specific code
    codes.append("79530000-8")
    
    # Additional specific codes list
    additional_codes = [
        "66122000-1", "66170000-2", "66171000-9", "66519310-7", "66523000-2",
        "71210000-3", "71241000-9", "71310000-4", "71311000-1", "71311200-3",
        "71311210-6", "71311300-4", "71312000-8", "71313000-5", "71313100-6",
        "71313200-7", "71314300-5", "71315100-0", "71315200-1", "71315210-4",
        "71316000-6", "71317000-3", "71317100-4", "71317210-8", "71318000-0",
        "71321300-7", "71321400-8", "71351200-5", "71351210-8", "71351220-1",
        "71530000-2", "71600000-4", "71621000-7", "71800000-6", "72000000-5",
        "72100000-6", "72110000-9", "72120000-2", "72130000-5", "72140000-8",
        "72150000-1", "72200000-7", "72220000-3", "72221000-0", "72224000-1",
        "72226000-5", "72227000-2", "72228000-9", "72246000-1", "72266000-7",
        "72413000-8", "72415000-2", "72600000-6", "73000000-2", "73200000-4",
        "73210000-7", "73220000-0", "79000000-4", "79110000-8", "79111000-5",
        "79120000-1", "79121000-8", "79121100-9", "79140000-7", "79221000-9",
        "79341100-7", "79400000-8", "79410000-1", "79411000-8", "79411100-9",
        "79412000-5", "79413000-2", "79414000-9", "79415000-6", "79415200-8",
        "79416200-5", "79417000-0", "79418000-7", "79419000-4", "85141220-7",
        "85312300-2", "85312320-8", "90490000-8", "90492000-2", "90713000-8",
        "90713100-9", "90732400-1", "90742400-4", "98200000-5"
    ]
    codes.extend(additional_codes)
    
    # Remove duplicates and sort
    return sorted(list(set(codes)))


def get_default_social_criteria_codes() -> List[str]:
    """Get the default CPV codes for social criteria - returns actual codes from DB."""
    # These are the actual CPV codes that exist in the database
    # within the specified ranges
    codes = [
        # Range 50700000-2 to 50760000-0
        "50700000-2", "50710000-5", "50711000-2", "50712000-9", "50720000-8",
        "50721000-5", "50730000-1", "50740000-4", "50750000-7", "50760000-0",
        # Range 55300000-3 to 55400000-4
        "55300000-3", "55310000-6", "55311000-3", "55312000-0", "55320000-9",
        "55321000-6", "55322000-3", "55330000-2", "55400000-4",
        # Range 55410000-7 to 55512000-2
        "55410000-7", "55500000-5", "55510000-8", "55511000-5", "55512000-2",
        # Range 55520000-1 to 55524000-9
        "55520000-1", "55521000-8", "55521100-9", "55521200-0", "55522000-5",
        "55523000-2", "55523100-3", "55524000-9",
        # Range 60100000-9 to 60183000-4
        "60100000-9", "60112000-6", "60120000-5", "60130000-8", "60140000-1",
        "60150000-4", "60160000-7", "60161000-4", "60170000-0", "60171000-7",
        "60172000-4", "60180000-3", "60181000-0", "60182000-7", "60183000-4",
        # Range 90600000-3 to 90690000-0
        "90600000-3", "90610000-6", "90611000-3", "90612000-0", "90620000-9",
        "90630000-2", "90640000-5", "90641000-2", "90642000-9", "90650000-8",
        "90660000-1", "90670000-4", "90680000-7", "90690000-0",
        # Range 90900000-6 to 90919300-5
        "90900000-6", "90910000-9", "90911000-6", "90911100-7", "90911200-8",
        "90911300-9", "90913000-0", "90913100-1", "90913200-2", "90914000-7",
        "90915000-4", "90916000-1", "90917000-8", "90918000-5", "90919000-2",
        "90919100-3", "90919200-4", "90919300-5",
        # Individual codes
        "70330000-3", "79713000-5"
    ]
    
    return codes


def render_criteria_management_tab():
    """Render the criteria management tab content."""
    with st.container():
        st.markdown("### ⚖️ Upravljanje meril za CPV kode")
        st.info("Določite CPV kode, kjer veljajo posebna merila za ocenjevanje ponudb.")
        
        # Ensure CPV data is initialized (should already be done at app startup)
        from init_database import ensure_cpv_data_initialized
        if not ensure_cpv_data_initialized():
            st.error("CPV podatki niso na voljo. Prosimo, preverite namestitev.")
            return
        
        # Check if migration from JSON is needed
        from utils import criteria_manager
        import os
        json_path = os.path.join('json_files', 'cpv_criteria_settings.json')
        
        # Initialize criteria types (creates defaults if not exist)
        criteria_manager.init_criteria_types()
        
        # Check if we need to migrate from JSON
        if os.path.exists(json_path):
            with st.spinner("Migriram obstoječe nastavitve v bazo podatkov..."):
                migration_result = criteria_manager.migrate_from_json()
                if migration_result['success']:
                    st.success(f"✅ Uspešno migrirano: {migration_result['migrated_price']} cenovnih meril, {migration_result['migrated_social']} socialnih meril")
                elif migration_result['error'] and migration_result['error'] != 'No JSON file to migrate':
                    st.warning(f"⚠️ Migracija delno uspešna: {migration_result['error']}")
        
        # Load current settings from database
        settings = load_criteria_settings()
        
        # Get all available CPV codes with descriptions
        from utils.cpv_manager import get_all_cpv_codes, get_cpv_count
        
        # Check if we have CPV data
        cpv_count = get_cpv_count()
        if cpv_count == 0:
            st.warning("⚠️ Ni CPV kod v bazi. Prosimo, uvozite CPV kode preko CPV upravljanja.")
            return
        
        all_cpv_codes, _ = get_all_cpv_codes(page=1, per_page=15000)  # Get all codes
        
        # Create a mapping of code to description
        cpv_map = {cpv['code']: cpv['description'] for cpv in all_cpv_codes}
        
        # Filter to only include codes that exist in database
        available_codes = list(cpv_map.keys())
        
        # Initialize with defaults if empty, but filter to only existing codes
        if not settings["price_criteria"]:
            default_price = get_default_price_criteria_codes()
            # Filter to only codes that exist in database
            settings["price_criteria"] = [code for code in default_price if code in cpv_map]
            # Save defaults to database
            save_criteria_settings(settings)
        
        if not settings["social_criteria"]:
            default_social = get_default_social_criteria_codes()
            # Filter to only codes that exist in database
            settings["social_criteria"] = [code for code in default_social if code in cpv_map]
            # Save defaults to database
            save_criteria_settings(settings)
        
        # Create tabs for better organization
        tab1, tab2, tab3 = st.tabs(["💰 Cenovna merila", "👥 Socialna merila", "📊 Pregled"])
        
        with tab1:
            st.markdown("#### Merila - cena")
            st.markdown("*CPV kode, kjer cena ne sme biti edino merilo za izbor*")
            
            # Show current selection count
            st.info(f"Trenutno izbranih: **{len(settings['price_criteria'])}** CPV kod")
            
            # Prepare options for price criteria
            price_options = []
            price_defaults = []
            
            for code in available_codes:
                display = f"{code} - {cpv_map[code]}"
                price_options.append(display)
                if code in settings["price_criteria"]:
                    price_defaults.append(display)
            
            # Price criteria multiselect
            selected_price = st.multiselect(
                "Izberite CPV kode za cenovna merila",
                options=price_options,
                default=price_defaults,
                key="price_criteria_select",
                help="Začnite tipkati kodo ali opis za iskanje"
            )
            
            # Extract codes from selected display values
            selected_price_codes = []
            for display in selected_price:
                if ' - ' in display:
                    code = display.split(' - ')[0]
                    selected_price_codes.append(code)
            
            # Show selected codes in an expander
            if selected_price_codes:
                with st.expander(f"📋 Seznam izbranih kod ({len(selected_price_codes)})", expanded=False):
                    for code in sorted(selected_price_codes):
                        st.write(f"• **{code}** - {cpv_map[code]}")
        
        with tab2:
            st.markdown("#### Merila - socialna merila")
            st.markdown("*CPV kode, kjer veljajo socialna merila*")
            
            # Show current selection count
            st.info(f"Trenutno izbranih: **{len(settings['social_criteria'])}** CPV kod")
            
            # Prepare options for social criteria
            social_options = []
            social_defaults = []
            
            for code in available_codes:
                display = f"{code} - {cpv_map[code]}"
                social_options.append(display)
                if code in settings["social_criteria"]:
                    social_defaults.append(display)
            
            # Social criteria multiselect
            selected_social = st.multiselect(
                "Izberite CPV kode za socialna merila",
                options=social_options,
                default=social_defaults,
                key="social_criteria_select",
                help="Začnite tipkati kodo ali opis za iskanje"
            )
            
            # Extract codes from selected display values
            selected_social_codes = []
            for display in selected_social:
                if ' - ' in display:
                    code = display.split(' - ')[0]
                    selected_social_codes.append(code)
            
            # Show selected codes in an expander
            if selected_social_codes:
                with st.expander(f"📋 Seznam izbranih kod ({len(selected_social_codes)})", expanded=False):
                    for code in sorted(selected_social_codes):
                        st.write(f"• **{code}** - {cpv_map[code]}")
        
        with tab3:
            st.markdown("#### 📊 Pregled trenutnih nastavitev")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 💰 Cenovna merila")
                st.metric("Število kod", len(settings['price_criteria']))
                
                if settings['price_criteria']:
                    st.markdown("**Izbrane kode:**")
                    # Show first 10 with scroll for more
                    container = st.container(height=300)
                    with container:
                        for code in sorted(settings['price_criteria']):
                            st.markdown(f"• `{code}` - {cpv_map.get(code, 'Opis ni na voljo')}")
                else:
                    st.info("Ni izbranih kod")
            
            with col2:
                st.markdown("##### 👥 Socialna merila")
                st.metric("Število kod", len(settings['social_criteria']))
                
                if settings['social_criteria']:
                    st.markdown("**Izbrane kode:**")
                    # Show first 10 with scroll for more
                    container = st.container(height=300)
                    with container:
                        for code in sorted(settings['social_criteria']):
                            st.markdown(f"• `{code}` - {cpv_map.get(code, 'Opis ni na voljo')}")
                else:
                    st.info("Ni izbranih kod")
            
            # Check for overlaps
            overlap = set(settings['price_criteria']) & set(settings['social_criteria'])
            if overlap:
                st.warning(f"⚠️ **Opozorilo:** {len(overlap)} kod je izbranih v obeh kategorijah!")
                with st.expander("Prikaži prekrivanje"):
                    for code in sorted(overlap):
                        st.write(f"• {code} - {cpv_map.get(code, 'Opis ni na voljo')}")
        
        st.markdown("---")
        
        # Save buttons - available from all tabs
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Shrani nastavitve", type="primary", use_container_width=True):
                # Get the selected codes based on which tab was active
                if 'selected_price_codes' not in locals():
                    selected_price_codes = settings['price_criteria']
                if 'selected_social_codes' not in locals():
                    selected_social_codes = settings['social_criteria']
                
                # Save the settings
                new_settings = {
                    "price_criteria": selected_price_codes,
                    "social_criteria": selected_social_codes
                }
                save_criteria_settings(new_settings)
                st.success("✅ Nastavitve uspešno shranjene!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Ponastavi na privzeto", type="secondary", use_container_width=True):
                # Reset to defaults (filtered to existing codes)
                default_price = get_default_price_criteria_codes()
                default_social = get_default_social_criteria_codes()
                
                default_settings = {
                    "price_criteria": [code for code in default_price if code in cpv_map],
                    "social_criteria": [code for code in default_social if code in cpv_map]
                }
                save_criteria_settings(default_settings)
                st.success("✅ Nastavitve ponastavljene na privzete vrednosti!")
                st.rerun()


def render_logging_management_tab():
    """Render the logging management tab with viewing, filtering, and export capabilities."""
    st.subheader("📋 Upravljanje dnevniških zapisov")
    
    # Import LogQueryBuilder for optimized queries
    from utils.log_query_builder import LogQueryBuilder
    
    # Initialize session state for filters
    if 'log_filters' not in st.session_state:
        st.session_state.log_filters = {
            'log_levels': [],
            'organization_id': None,
            'date_from': None,
            'date_to': None,
            'time_from': None,  # NEW: time filtering
            'time_to': None,    # NEW: time filtering
            'search_query': '',
            'log_type': None,
            'use_quick_filter': None  # NEW: quick filter tracking
        }
    
    # Filters section in main content area
    with st.expander("🔍 Filtri", expanded=True):
        # Quick filters row (NEW)
        st.markdown("**Hitri filtri:**")
        qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
        
        with qcol1:
            if st.button("📅 Danes", use_container_width=True, key="quick_today"):
                st.session_state.log_filters['date_from'] = datetime.now().date()
                st.session_state.log_filters['date_to'] = datetime.now().date()
                st.session_state.log_filters['use_quick_filter'] = 'today'
                st.rerun()
        
        with qcol2:
            if st.button("⏰ 24 ur", use_container_width=True, key="quick_24h"):
                st.session_state.log_filters['date_from'] = (datetime.now() - timedelta(days=1)).date()
                st.session_state.log_filters['date_to'] = datetime.now().date()
                st.session_state.log_filters['use_quick_filter'] = '24h'
                st.rerun()
        
        with qcol3:
            if st.button("📆 Ta teden", use_container_width=True, key="quick_week"):
                today = datetime.now().date()
                start_week = today - timedelta(days=today.weekday())
                st.session_state.log_filters['date_from'] = start_week
                st.session_state.log_filters['date_to'] = today
                st.session_state.log_filters['use_quick_filter'] = 'week'
                st.rerun()
        
        with qcol4:
            if st.button("📊 Zadnjih 100", use_container_width=True, key="quick_last100"):
                st.session_state.log_filters['date_from'] = None
                st.session_state.log_filters['date_to'] = None
                st.session_state.log_filters['use_quick_filter'] = 'last100'
                st.rerun()
        
        with qcol5:
            if st.button("🔴 Samo napake", use_container_width=True, key="quick_errors"):
                st.session_state.log_filters['log_levels'] = ['ERROR', 'CRITICAL']
                st.session_state.log_filters['use_quick_filter'] = 'errors'
                st.rerun()
        
        st.markdown("---")
        
        # First row of filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Log level filter
            log_levels = st.multiselect(
                "Nivo zapisov",
                options=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                default=st.session_state.log_filters.get('log_levels', []),  # Empty by default to show all
                key='filter_log_levels'
            )
        
        with col2:
            # Date from filter
            date_from = st.date_input(
                "Od datuma",
                value=st.session_state.log_filters.get('date_from', None),  # No default date filter
                key='filter_date_from'
            )
        
        with col3:
            # Date to filter
            date_to = st.date_input(
                "Do datuma",
                value=st.session_state.log_filters.get('date_to', None),  # No default date filter
                key='filter_date_to'
            )
        
        with col4:
            # Organization filter
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT organization_name FROM application_logs WHERE organization_name IS NOT NULL")
                orgs = [row[0] for row in cursor.fetchall()]
            
            if orgs:
                org_filter = st.selectbox(
                    "Organizacija",
                    options=['Vse'] + orgs,
                    key='filter_org'
                )
                organization_name = None if org_filter == 'Vse' else org_filter
            else:
                organization_name = None
                st.selectbox("Organizacija", options=['Vse'], key='filter_org')
        
        # Second row with time filters (NEW)
        tcol1, tcol2, tcol3, tcol4 = st.columns(4)
        
        with tcol1:
            # Time from filter
            time_from = st.time_input(
                "Od časa (neobvezno)",
                value=st.session_state.log_filters.get('time_from'),
                key='filter_time_from',
                help="Filtriraj zapise po času dneva"
            )
        
        with tcol2:
            # Time to filter
            time_to = st.time_input(
                "Do časa (neobvezno)",
                value=st.session_state.log_filters.get('time_to'),
                key='filter_time_to',
                help="Filtriraj zapise po času dneva"
            )
        
        with tcol3:
            # Business hours preset
            if st.button("🏢 Delovni čas (8-17)", use_container_width=True):
                st.session_state.log_filters['time_from'] = datetime.strptime("08:00", "%H:%M").time()
                st.session_state.log_filters['time_to'] = datetime.strptime("17:00", "%H:%M").time()
                st.rerun()
        
        with tcol4:
            # Night hours preset
            if st.button("🌙 Nočni čas (22-06)", use_container_width=True):
                st.session_state.log_filters['time_from'] = datetime.strptime("22:00", "%H:%M").time()
                st.session_state.log_filters['time_to'] = datetime.strptime("06:00", "%H:%M").time()
                st.rerun()
        
        # Third row with search and apply button
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Search filter
            search_query = st.text_input(
                "Iskanje v sporočilih",
                value=st.session_state.log_filters.get('search_query', ''),
                key='filter_search',
                placeholder="Vnesite iskalni niz..."
            )
        
        with col2:
            # Apply filters button
            if st.button("🔄 Uporabi filtre", type="primary", use_container_width=True):
                st.session_state.log_filters = {
                    'log_levels': log_levels,
                    'organization_name': organization_name,
                    'date_from': date_from,
                    'date_to': date_to,
                    'time_from': time_from,  # NEW
                    'time_to': time_to,      # NEW
                    'search_query': search_query,
                    'log_type': None,
                    'use_quick_filter': None
                }
                st.rerun()
        
        with col3:
            # Clear filters button
            if st.button("🗑️ Počisti filtre", use_container_width=True):
                st.session_state.log_filters = {
                    'log_levels': [],
                    'organization_name': None,
                    'date_from': None,  # No default date
                    'date_to': None,    # No default date
                    'time_from': None,  # NEW
                    'time_to': None,    # NEW
                    'search_query': '',
                    'log_type': None,
                    'use_quick_filter': None
                }
                st.rerun()
    
    # Main content area header
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("### 📊 Pregled zapisov")
    
    with col2:
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Samodejno osveževanje", value=False)
        if auto_refresh:
            st.rerun()
    
    with col3:
        # Export button
        if st.button("📥 Izvozi CSV", use_container_width=True):
            export_logs_to_csv()
    
    # Fetch and display logs
    # Check if filters have been explicitly applied (not just defaults)
    filters_applied = any([
        st.session_state.log_filters.get('log_levels'),
        st.session_state.log_filters.get('date_from'),
        st.session_state.log_filters.get('date_to'),
        st.session_state.log_filters.get('organization_name'),
        st.session_state.log_filters.get('search_query'),
        st.session_state.log_filters.get('use_quick_filter')
    ])
    
    if not filters_applied:
        # No filters applied - show recent logs
        st.info("📋 Prikazujem zadnjih 100 zapisov. Uporabite filtre za prilagojeno iskanje.")
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            logs_df = pd.read_sql_query("""
                SELECT * FROM application_logs 
                ORDER BY id DESC 
                LIMIT 100
            """, conn)
            if not logs_df.empty:
                logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    else:
        # Use filters
        logs_df = fetch_logs_with_filters(st.session_state.log_filters)
    
    if not logs_df.empty:
        # Statistics
        st.markdown("#### 📈 Statistika")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Skupaj zapisov", len(logs_df))
        
        with col2:
            error_count = len(logs_df[logs_df['log_level'].isin(['ERROR', 'CRITICAL'])])
            st.metric("Napake", error_count, delta_color="inverse")
        
        with col3:
            warning_count = len(logs_df[logs_df['log_level'] == 'WARNING'])
            st.metric("Opozorila", warning_count)
        
        with col4:
            # NEW: Enhanced statistics based on available columns
            if len(logs_df) > 0:
                from utils.log_query_builder import LogQueryBuilder
                query_builder = LogQueryBuilder()
                
                if query_builder.has_optimized_columns() and 'log_time' in logs_df.columns:
                    # Peak hour analysis with new columns
                    if 'hour' in logs_df.columns:
                        peak_hour = logs_df.groupby('hour').size().idxmax() if not logs_df.empty else 0
                        st.metric("Najbolj aktivna ura", f"{peak_hour:02d}:00")
                else:
                    # Fallback to average logs per hour
                    time_span = (logs_df['timestamp'].max() - logs_df['timestamp'].min()).total_seconds() / 3600
                    avg_per_hour = len(logs_df) / max(time_span, 1)
                    st.metric("Zapisov/uro", f"{avg_per_hour:.1f}")
        
        # Display logs table
        st.markdown("#### 📜 Dnevniški zapisi")
        
        # Configure display columns
        display_columns = ['timestamp', 'log_level', 'module', 'message', 'organization_name']
        
        # Color code by log level
        def highlight_log_level(row):
            colors = {
                'DEBUG': 'background-color: #f0f0f0',
                'INFO': 'background-color: #d4edda',
                'WARNING': 'background-color: #fff3cd',
                'ERROR': 'background-color: #f8d7da',
                'CRITICAL': 'background-color: #d1a3a4; font-weight: bold'
            }
            return [colors.get(row['log_level'], '') for _ in row]
        
        # Display with pagination
        logs_per_page = 50
        total_pages = (len(logs_df) - 1) // logs_per_page + 1
        
        page = st.number_input(
            f"Stran (od {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            key='log_page'
        )
        
        start_idx = (page - 1) * logs_per_page
        end_idx = min(start_idx + logs_per_page, len(logs_df))
        
        page_df = logs_df.iloc[start_idx:end_idx][display_columns]
        
        # Style and display
        styled_df = page_df.style.apply(highlight_log_level, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Log details expander
        with st.expander("🔍 Podrobnosti izbranega zapisa"):
            selected_idx = st.number_input(
                "ID zapisa",
                min_value=0,
                max_value=len(logs_df)-1,
                value=0,
                key='selected_log'
            )
            
            if selected_idx < len(logs_df):
                selected_log = logs_df.iloc[selected_idx]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Čas:** {selected_log['timestamp']}")
                    st.write(f"**Nivo:** {selected_log['log_level']}")
                    st.write(f"**Modul:** {selected_log['module']}")
                    st.write(f"**Funkcija:** {selected_log.get('function_name', 'N/A')}")
                
                with col2:
                    st.write(f"**Organizacija:** {selected_log.get('organization_name', 'N/A')}")
                    st.write(f"**Retencija:** {selected_log.get('retention_hours', 'N/A')} ur")
                    st.write(f"**Tip:** {selected_log.get('log_type', 'N/A')}")
                    st.write(f"**Vrstica:** {selected_log.get('line_number', 'N/A')}")
                
                st.write(f"**Sporočilo:**")
                st.code(selected_log['message'])
                
                if selected_log.get('additional_context'):
                    st.write(f"**Dodatni kontekst:**")
                    st.json(selected_log['additional_context'])
    else:
        st.info("📭 Ni zapisov, ki bi ustrezali filtrom.")
    
    # Cleanup section
    st.markdown("---")
    st.markdown("### 🧹 Čiščenje zapisov")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Počisti potekle zapise", use_container_width=True):
            deleted = database.cleanup_expired_logs()
            st.success(f"Izbrisanih {deleted} poteklih zapisov.")
    
    with col2:
        if st.button("🧹 Počisti DEBUG zapise", use_container_width=True):
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM application_logs WHERE log_level = 'DEBUG'")
                deleted = cursor.rowcount
                conn.commit()
            st.success(f"Izbrisanih {deleted} DEBUG zapisov.")
    
    with col3:
        if st.button("⚠️ Počisti vse zapise", type="secondary", use_container_width=True):
            if st.checkbox("Potrdi brisanje vseh zapisov"):
                with sqlite3.connect(database.DATABASE_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM application_logs")
                    deleted = cursor.rowcount
                    conn.commit()
                st.success(f"Izbrisanih {deleted} zapisov.")
    
    # Storage statistics
    st.markdown("---")
    st.markdown("### 💾 Statistika shranjevanja")
    
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Get retention summary
        cursor.execute("""
            SELECT log_level, retention_hours, COUNT(*) as count
            FROM application_logs
            GROUP BY log_level, retention_hours
            ORDER BY log_level, retention_hours
        """)
        
        retention_data = cursor.fetchall()
        
        if retention_data:
            retention_df = pd.DataFrame(retention_data, columns=['Nivo', 'Retencija (ur)', 'Število'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(retention_df, use_container_width=True)
            
            with col2:
                # Get storage size estimate
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_logs,
                        SUM(LENGTH(message) + LENGTH(COALESCE(additional_context, ''))) as total_size
                    FROM application_logs
                """)
                
                total_logs, total_size = cursor.fetchone()
                
                if total_size:
                    st.metric("Skupno zapisov", total_logs)
                    st.metric("Ocenjena velikost", f"{total_size / 1024 / 1024:.2f} MB")
                    st.metric("Povprečna velikost zapisa", f"{total_size / max(total_logs, 1):.0f} B")


def fetch_logs_with_filters(filters):
    """Fetch logs from database with applied filters using optimized queries."""
    from utils.log_query_builder import LogQueryBuilder
    import time
    
    # Initialize query builder
    query_builder = LogQueryBuilder()
    
    # Track query performance
    start_time = time.time()
    
    # Special handling for quick filters
    if filters.get('use_quick_filter') == 'last100':
        query, params = query_builder.recent_logs_query(100)
    else:
        # Build optimized query based on filters
        query, params = query_builder.filtered_query(filters.copy())
    
    # Add LIMIT if not already present
    if "LIMIT" not in query:
        query += " LIMIT 1000"
    
    # Execute query
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
        # Track query time
        query_time = time.time() - start_time
        
        # Show performance metric if enabled
        if st.session_state.get('show_performance', False):
            st.sidebar.metric("Query Time", f"{query_time:.3f}s")
        
        # Convert timestamp to datetime
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Add time analysis columns if new columns exist
            if query_builder.has_optimized_columns() and 'log_time' in df.columns:
                df['hour'] = pd.to_datetime(df['log_time']).dt.hour
        
        return df
    
    return pd.DataFrame()


def export_logs_to_csv():
    """Export filtered logs to CSV file."""
    logs_df = fetch_logs_with_filters(st.session_state.log_filters)
    
    if not logs_df.empty:
        # Convert to CSV
        csv_buffer = StringIO()
        logs_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Download button
        st.download_button(
            label="💾 Prenesi CSV",
            data=csv_data,
            file_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("Ni podatkov za izvoz.")


def render_admin_panel():
    """Render the complete admin panel with modern interface."""
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        render_login_form()
    else:
        render_admin_header()
        
        # Tabbed interface for different admin sections
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📄 Predloge", "💾 Osnutki", "🗄️ Baza podatkov", 
            "🏢 Organizacije", "🔢 CPV kode", "⚖️ Merila", "📋 Dnevnik", "🤖 AI Management", "🧪 Test dokumentov"
        ])
        
        with tab1:
            render_template_management_tab()
        
        with tab2:
            render_draft_management_tab()
        
        with tab3:
            render_database_management_tab()
        
        with tab4:
            render_organization_management_tab()
        
        with tab5:
            render_cpv_management_tab()
        
        with tab6:
            render_criteria_management_tab()
        
        with tab7:
            render_logging_management_tab()
        
        with tab8:
            from ui.ai_manager import render_ai_manager
            render_ai_manager()
        
        with tab9:
            from ui.admin_document_tester import render_document_testing_tab
            render_document_testing_tab()