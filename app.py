
"""Main Streamlit application for public procurement document generation."""
import streamlit as st
import database
import logging
from config_refactored import (
    get_dynamic_form_steps_refactored as get_dynamic_form_steps,
    is_final_lot_step,
    get_lot_navigation_buttons,
    SCHEMA_FILE
)
from utils.schema_utils import load_json_schema, get_form_data_from_session, clear_form_data
from utils.lot_utils import (
    get_current_lot_context, initialize_lot_session_state, 
    migrate_existing_data_to_lot_structure, get_lot_progress_info
)
from utils.lot_navigation import handle_lot_action
from utils.validation_control import (
    should_validate, render_master_validation_toggle, 
    render_step_validation_toggle, get_validation_status_message
)
from ui.form_renderer import render_form
from ui.admin_panel import render_admin_panel
from ui.dashboard import render_dashboard
from localization import get_text, format_step_indicator
from init_database import initialize_cpv_data, check_cpv_data_status
from utils.optimized_database_logger import configure_optimized_logging as configure_database_logging
from utils.qdrant_init import init_qdrant_on_startup
from utils.loading_state import render_loading_indicator, set_loading_state, LOADING_MESSAGES

# Initialize CPV data on startup (outside of Streamlit context)
def init_app_data():
    """Initialize application data on startup."""
    # Configure logging
    configure_database_logging(level=logging.INFO)
    
    # Initialize CPV data
    status = check_cpv_data_status()
    if not status['initialized']:
        result = initialize_cpv_data()
        if result['success']:
            logging.info(f"CPV data initialized: {result['imported']} codes from {result['source']}")
        else:
            logging.warning(f"CPV initialization failed: {result['message']}")
    
    # Initialize Qdrant collection (non-blocking per Story 27.1)
    qdrant_result = init_qdrant_on_startup()
    if not qdrant_result['success']:
        # Log but continue - non-blocking requirement
        logging.info("App starting without vector database support")

# Run initialization before Streamlit
init_app_data()

def main():
    """Main application entry point."""
    st.set_page_config(layout="wide", page_title=get_text("app_title"))
    
    # Show loading message on initial startup
    if 'initialized' not in st.session_state:
        with st.spinner('Nalagam aplikacijo...'):
            st.session_state.initialized = True
    
    # Initialize navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'  # Start with dashboard
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_record_id' not in st.session_state:
        st.session_state.edit_record_id = None
    
    if 'schema' not in st.session_state:
        try:
            st.session_state['schema'] = load_json_schema(SCHEMA_FILE)
        except FileNotFoundError:
            st.error(get_text("schema_file_not_found", filename=SCHEMA_FILE))
            st.stop()

    # Initialize lot-aware session state
    initialize_lot_session_state()
    migrate_existing_data_to_lot_structure()

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0

    # Route to appropriate page based on current_page state
    if st.session_state.current_page == 'dashboard':
        render_dashboard()
    elif st.session_state.current_page == 'form':
        render_main_form()
    elif st.session_state.current_page == 'admin':
        render_admin_panel()

def _set_navigation_flags():
    """Set navigation flags to prevent auto-selection triggers during navigation."""
    # Set navigation flag for all form fields that might have auto-selection logic
    for key in st.session_state.keys():
        if key.endswith('submissionProcedure.procedure'):
            navigation_key = f"{key}_navigation_flag"
            st.session_state[navigation_key] = True

def save_form_draft(include_files=True, show_success=True, location="navigation"):
    """Unified function to save current form state as a draft.
    
    Args:
        include_files: Whether to also save uploaded files (default: True)
        show_success: Whether to show success message (default: True)
        location: Where the save was triggered from ("navigation" or "sidebar")
    
    Returns:
        draft_id if successful, None otherwise
    """
    try:
        import json
        import datetime
        
        # Get current form data
        form_data = get_form_data_from_session()
        
        # Add metadata
        form_data['_save_metadata'] = {
            'saved_at': datetime.datetime.now().isoformat(),
            'current_step': st.session_state.current_step,
            'save_type': 'progress',
            'save_location': location
        }
        
        # Save to database
        draft_id = database.save_draft(form_data)
        
        if draft_id:
            st.session_state.current_draft_id = draft_id
            
            # Handle file uploads if requested
            files_saved = 0
            files_removed = 0
            
            if include_files:
                try:
                    from services.form_document_service import FormDocumentService
                    from io import BytesIO
                    
                    doc_service = FormDocumentService()
                    
                    # Process document removals first
                    for key in list(st.session_state.keys()):
                        if key.startswith('_remove_document_'):
                            doc_id = key.replace('_remove_document_', '')
                            if st.session_state[key]:
                                try:
                                    doc_service.delete_document(int(doc_id))
                                    files_removed += 1
                                    del st.session_state[key]
                                except:
                                    pass
                    
                    # Process uploaded files (both old and new format)
                    # Check for new format (_uploaded_file_*)
                    for key in list(st.session_state.keys()):
                        if key.startswith('_uploaded_file_') and st.session_state[key] is not None:
                            file_obj = st.session_state[key]
                            field_name = key.replace('_uploaded_file_', '')
                            
                            file_content = file_obj.read()
                            if isinstance(file_content, bytes):
                                file_obj.seek(0)
                                
                                doc_id, is_new = doc_service.save_document(
                                    form_id=draft_id,
                                    field_name=field_name,
                                    file_name=file_obj.name,
                                    file_content=BytesIO(file_content),
                                    file_size=len(file_content)
                                )
                                
                                # Trigger AI processing for new documents
                                if is_new:
                                    try:
                                        from services.form_document_processor import trigger_document_processing
                                        trigger_document_processing(doc_id)
                                    except ImportError:
                                        pass
                                
                                # Clear from session after saving
                                del st.session_state[key]
                                files_saved += 1
                    
                    # Check for old format (*_file_info)
                    file_keys = [k for k in st.session_state.keys() if k.endswith('_file_info')]
                    for file_key in file_keys:
                        file_info = st.session_state[file_key]
                        if file_info and 'content' in file_info:
                            # Save file to document service
                            doc_service.save_form_document(
                                form_id=draft_id,
                                file_name=file_info['name'],
                                file_content=file_info['content'],
                                file_type=file_info.get('type', 'application/octet-stream'),
                                field_name=file_key.replace('_file_info', '')
                            )
                            files_saved += 1
                            
                except Exception as e:
                    logging.warning(f"Could not save files: {e}")
            
            # Store in browser storage for recovery
            st.session_state['last_saved'] = datetime.datetime.now().isoformat()
            st.session_state['last_saved_id'] = draft_id
            
            # Show success message if requested
            if show_success:
                messages = [f"✅ Napredek uspešno shranjen! (ID: {draft_id})"]
                if files_saved > 0:
                    messages.append(f"📎 {files_saved} datotek shranjenih")
                if files_removed > 0:
                    messages.append(f"🗑️ {files_removed} datotek odstranjenih")
                st.success(" | ".join(messages))
            
            return draft_id
        else:
            if show_success:
                st.error("❌ Napaka pri shranjevanju napredka")
            return None
            
    except Exception as e:
        logging.error(f"Error saving form draft: {e}")
        if show_success:
            st.error(f"❌ Napaka pri shranjevanju: {str(e)}")
        return None

def save_form_progress():
    """Save current form state to persistent storage without validation.
    This is a wrapper for backward compatibility."""
    return save_form_draft(include_files=True, show_success=True, location="navigation")

def validate_step(step_keys, schema):
    """Validate the fields for the current step using centralized validation."""
    # Story 27.3: Refactored to use ValidationManager
    from utils.validations import ValidationManager
    import logging
    
    current_step = st.session_state.get('current_step', 0)
    logging.info(f"validate_step called for step {current_step} with keys: {step_keys}")
    
    # Check if validation should run for current step
    if not should_validate(current_step):
        # Skip validation but show indicator
        st.info("ℹ️ Validacija preskočena za ta korak")
        logging.info(f"Validation skipped for step {current_step}")
        return True  # Allow progression
    
    # Initialize centralized validator
    validator = ValidationManager(schema, st.session_state)
    
    # Run general validation
    is_valid, errors = validator.validate_step(step_keys, current_step)
    
    # Display general validation errors
    for error in errors:
        st.error(f"⚠️ {error}")
    
    # Display warnings if any (for Merila and other sections that generate warnings)
    for warning in validator.get_warnings():
        st.warning(f"ℹ️ {warning}")
    
    
    # The centralized ValidationManager now handles:
    # - Required fields validation
    # - Dropdown validation
    # - Multiple entries validation (multiple clients, lots)
    # - Conditional requirements
    # - Contract extension validation
    # - Framework agreement validation
    # - CPV code requirements
    # - Merila validation (points, social criteria, etc.)
    
    logging.info(f"validate_step returning: {is_valid}")
    return is_valid

def render_main_form():
    """Render the main multi-step form interface with enhanced UX."""
    # Check for saved progress on startup - only show if we're in edit mode or have a current draft
    if 'checked_saved_progress' not in st.session_state:
        st.session_state.checked_saved_progress = True
        
        # Only show load prompt if we're editing an existing record or continuing a draft
        if st.session_state.get('edit_mode', False) or st.session_state.get('current_draft_id'):
            # Check if there's a recent saved progress
            recent_drafts = database.get_recent_drafts(limit=1)
            if recent_drafts:
                draft = recent_drafts[0]
                # Show option to load saved progress
                with st.info("ℹ️ Najden je bil nedavno shranjen napredek"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"Osnutek ID: {draft['id']} | Shranjen: {draft.get('created_at', 'Neznano')}")
                    with col2:
                        if st.button("📂 Naloži", type="primary", key="load_saved_progress"):
                            with st.spinner(LOADING_MESSAGES['load_draft']):
                                loaded_data = database.load_draft(draft['id'])
                                if loaded_data:
                                    # Flatten nested dictionary to dot-notation for session state
                                    def flatten_dict(d, parent_key='', sep='.'):
                                        """Flatten nested dictionary into dot-notation keys."""
                                        items = []
                                        for k, v in d.items():
                                            # Skip metadata fields
                                            if k.startswith('_'):
                                                continue
                                            # Handle special lot structure
                                            if k == 'lots' and isinstance(v, list):
                                                # Store lot data in session state
                                                st.session_state['lots'] = v
                                                st.session_state['lot_mode'] = 'multiple'
                                                
                                                # Extract lot names
                                                lot_names = [lot.get('name', f'Sklop {i+1}') for i, lot in enumerate(v)]
                                                st.session_state['lot_names'] = lot_names
                                                
                                                # Flatten each lot's data into lot-scoped keys
                                                for i, lot in enumerate(v):
                                                    for lot_key, lot_value in lot.items():
                                                        if lot_key != 'name' and not isinstance(lot_value, dict):
                                                            items.append((f'lot_{i}.{lot_key}', lot_value))
                                                        elif isinstance(lot_value, dict):
                                                            # Recursively flatten nested lot data
                                                            nested_items = flatten_dict(lot_value, f'lot_{i}.{lot_key}', sep=sep)
                                                            items.extend(nested_items.items())
                                                continue
                                            elif k == 'lot_names':
                                                st.session_state['lot_names'] = v
                                                continue
                                            
                                            new_key = f"{parent_key}{sep}{k}" if parent_key else k
                                            if isinstance(v, dict):
                                                items.extend(flatten_dict(v, new_key, sep=sep).items())
                                            else:
                                                items.append((new_key, v))
                                        return dict(items)
                                    
                                    # Clear existing form data first
                                    clear_form_data()
                                    
                                    # Flatten and load into session state
                                    flattened_data = flatten_dict(loaded_data)
                                    for key, value in flattened_data.items():
                                        st.session_state[key] = value
                                    
                                    st.session_state.current_draft_id = draft['id']
                                    
                                    # Restore step if saved
                                    if '_save_metadata' in loaded_data:
                                        metadata = loaded_data['_save_metadata']
                                        if 'current_step' in metadata:
                                            st.session_state.current_step = metadata['current_step']
                                    
                                    st.success("✅ Napredek uspešno naložen!")
                                    st.rerun()
    
    # Modern form renderer configuration
    # Set to True to enable modern UI, False to use standard form
    # Can be controlled via environment variable or config
    import os
    USE_MODERN_FORM = os.environ.get('USE_MODERN_FORM', 'false').lower() == 'true'
    
    # Try to use modern form renderer if enabled and available
    use_modern_form = False
    if USE_MODERN_FORM:
        try:
            # Use the FIXED modern form renderer
            from ui.modern_form_renderer_fixed import (
                render_modern_form_fixed as render_modern_form,
                inject_modern_styles_once,
                render_progress_indicator
            )
            use_modern_form = True
            # Log that modern form is enabled
            if 'modern_form_status' not in st.session_state:
                st.session_state['modern_form_status'] = 'enabled'
                print("✅ Modern form renderer enabled")
        except ImportError as e:
            use_modern_form = False
            if 'modern_form_status' not in st.session_state:
                st.session_state['modern_form_status'] = 'import_error'
                print(f"⚠️ Modern form renderer not available: {e}")
    
    database.init_db()
    draft_metadata = database.get_all_draft_metadata()
    draft_options = {f"{ts} (ID: {id})": id for id, ts in draft_metadata}

    # Add custom CSS for better styling
    add_custom_css()
    
    # Add back to dashboard button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← Nazaj na pregled", type="secondary"):
            # Check for unsaved changes
            if st.session_state.get('unsaved_changes', False):
                st.warning("⚠️ Imate neshranjene spremembe. Ali res želite zapustiti obrazec?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Da, zapusti"):
                        st.session_state.current_page = 'dashboard'
                        st.session_state.unsaved_changes = False
                        st.rerun()
                with col_no:
                    if st.button("Ne, ostani"):
                        pass
            else:
                st.session_state.current_page = 'dashboard'
                st.rerun()
    
    with col_title:
        if st.session_state.edit_mode:
            st.title(f"✏️ Urejanje naročila ID: {st.session_state.edit_record_id}")
        else:
            st.title("➕ Novo javno naročilo")

    col1, col2 = st.columns([3, 1])

    with col1:
        # Get dynamic form steps based on lots
        dynamic_form_steps = get_dynamic_form_steps(st.session_state)
        
        # Enhanced header with step information
        current_step_num = st.session_state.current_step + 1
        total_steps = len(dynamic_form_steps)
        
        # Get lot progress info for enhanced header
        lot_progress = get_lot_progress_info()
        
        # Enhanced header with lot context
        header_content = f"<h1>{st.session_state.schema.get('title', 'Obrazec')}</h1>"
        if lot_progress['mode'] == 'lots':
            header_content += f"<h3>📦 {lot_progress['lot_name']} ({lot_progress['current_lot']}/{lot_progress['total_lots']})</h3>"
        elif lot_progress['mode'] == 'general':
            header_content += f"<h3>📄 {lot_progress['lot_name']}</h3>"
        
        st.markdown(f"""
        <div class="form-header">
            {header_content}
            <div class="step-indicator">
                {format_step_indicator(st.session_state.current_step, total_steps)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Enhanced Progress Bar with step labels
        progress_percentage = current_step_num / total_steps
        st.progress(progress_percentage, text=f"{get_text('progress')}: {current_step_num}/{total_steps}")
        
        # Step navigation breadcrumbs
        render_step_breadcrumbs()

        # Get properties for the current step and render the form
        current_step_keys = dynamic_form_steps[st.session_state.current_step]
        
        # Get lot context for current step
        lot_context = get_current_lot_context(current_step_keys)
        
        # Store current step keys for use in lot utilities
        st.session_state.current_step_keys = current_step_keys
        
        # Get properties - handle lot context steps and regular properties  
        current_step_properties = {}
        for key in current_step_keys:
            if key.startswith('lot_context_'):
                # Lot context steps don't need schema properties
                current_step_properties[key] = {"type": "lot_context"}
            elif key == 'lotConfiguration':
                # New lot configuration step - only collects lot names
                current_step_properties[key] = {"type": "lot_configuration"}
            elif key.startswith('lot_'):
                # Map lot-specific keys back to original schema properties
                original_key = key.split('_', 2)[2]  # lot_0_orderType -> orderType
                if original_key in st.session_state.schema["properties"]:
                    # Copy the schema property but remove render_if conditions for lot-specific fields
                    prop_copy = st.session_state.schema["properties"][original_key].copy()
                    if "render_if" in prop_copy:
                        del prop_copy["render_if"]  # Lot logic handles visibility
                    current_step_properties[key] = prop_copy
            else:
                # Regular properties
                if key in st.session_state.schema["properties"]:
                    prop_copy = st.session_state.schema["properties"][key].copy()
                    
                    # For orderType in general mode, remove render_if condition
                    if key == "orderType" and lot_context and lot_context['mode'] == 'general':
                        if "render_if" in prop_copy:
                            del prop_copy["render_if"]
                    
                    current_step_properties[key] = prop_copy
        
        # Debug section to troubleshoot contractInfo visibility
        if st.checkbox("🐛 Show Debug Info", key="debug_toggle"):
            st.write("**Debug Information:**")
            st.write(f"**Current Step:** {st.session_state.current_step + 1} of {len(dynamic_form_steps)}")
            st.write(f"**Step Keys:** {current_step_keys}")
            st.write(f"**Current Step Properties Keys:** {list(current_step_properties.keys())}")
            
            # Check if we're on contractInfo step
            if 'contractInfo' in current_step_keys:
                st.success("✓ This is the contractInfo step")
                if 'contractInfo' in current_step_properties:
                    contract_props = current_step_properties['contractInfo'].get('properties', {})
                    st.write(f"✓ contractInfo loaded with {len(contract_props)} properties")
                    
                    # Show what properties are in contractInfo
                    st.write("**contractInfo properties:**")
                    for prop_name in list(contract_props.keys())[:5]:
                        st.write(f"  - {prop_name}")
                    if len(contract_props) > 5:
                        st.write(f"  ... and {len(contract_props) - 5} more")
                else:
                    st.error("✗ contractInfo NOT in current_step_properties!")
            
            # Show what's in session state for contractInfo
            contract_keys = [k for k in st.session_state.keys() if 'contract' in k.lower()]
            if contract_keys:
                st.write("**Contract-related session state keys:**")
                for key in contract_keys:
                    st.write(f"- `{key}`: {st.session_state[key]}")

        # Render modern progress indicator if available
        if use_modern_form:
            form_steps = dynamic_form_steps
            # Handle form_steps as list of lists, not dictionaries
            step_names = []
            for i, step_fields in enumerate(form_steps):
                # Each step is a list of field names
                if step_fields and len(step_fields) > 0:
                    # Use the first field name as step identifier, or default
                    field_name = step_fields[0] if isinstance(step_fields, list) else str(step_fields)
                    # Convert field name to readable format
                    if field_name.startswith("lot_context_"):
                        step_name = f"Sklop {field_name.split('_')[-1]}"
                    elif field_name == "clientInfo":
                        step_name = "Podatki naročnika"
                    elif field_name == "projectInfo":
                        step_name = "Podatki projekta"
                    elif field_name == "legalBasis":
                        step_name = "Pravna podlaga"
                    elif field_name == "submissionProcedure":
                        step_name = "Postopek oddaje"
                    elif field_name == "lotsInfo":
                        step_name = "Konfiguracija sklopov"
                    elif field_name == "orderType":
                        step_name = "Vrsta naročila"
                    elif field_name == "technicalSpecifications":
                        step_name = "Tehnične zahteve"
                    elif field_name == "executionDeadline":
                        step_name = "Roki izvajanja"
                    elif field_name == "priceInfo":
                        step_name = "Informacije o ceni"
                    elif field_name == "inspectionInfo":
                        step_name = "Ogledi in pogajanja"
                    elif field_name == "participationAndExclusion":
                        step_name = "Pogoji sodelovanja"
                    elif field_name == "financialGuarantees":
                        step_name = "Zavarovanja"
                    elif field_name == "merila":
                        step_name = "Merila izbire"
                    elif field_name == "contractInfo":
                        step_name = "Pogodba in zaključek"
                    elif field_name == "otherInfo":
                        step_name = "Dodatne informacije"
                    else:
                        step_name = f"Korak {i+1}"
                    step_names.append(step_name)
                else:
                    step_names.append(f"Korak {i+1}")
            # Render progress indicator
            if use_modern_form:
                render_progress_indicator(st.session_state.current_step, len(form_steps), step_names)
            else:
                # Fallback progress indicator when modern form is not available
                progress = (st.session_state.current_step + 1) / len(form_steps)
                st.progress(progress)
                st.write(f"Korak {st.session_state.current_step + 1} od {len(form_steps)}: {step_names[st.session_state.current_step] if st.session_state.current_step < len(step_names) else 'Korak'}")
        
        # Story 22.1: Add master validation toggle on first step
        if st.session_state.current_step == 0:
            render_master_validation_toggle()
        
        # Render form with enhanced styling and lot context
        st.markdown('<div class="form-content">', unsafe_allow_html=True)
        if use_modern_form:
            # Use modern form renderer
            render_modern_form()
        else:
            # Fallback to original renderer
            render_form(current_step_properties, lot_context=lot_context)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Story 22.2: Add per-step validation toggle
        render_step_validation_toggle(st.session_state.current_step)
        
        # Show persistent navigation error if validation failed
        if st.session_state.get('navigation_blocked', False):
            if st.session_state.get('navigation_blocked_step') == st.session_state.current_step:
                st.error("❌ Navigacija blokirana zaradi neuspešne validacije. Prosimo, popravite napake zgoraj.")
                # Show specific CPV validation errors if they exist
                if st.session_state.get('cpv_validation_failed', False):
                    messages = st.session_state.get('cpv_validation_messages', [])
                    for msg in messages:
                        st.error(f"• {msg}")
                # Clear the flag after showing it once
                st.session_state['navigation_blocked'] = False

        # Enhanced Navigation buttons (outside form to avoid Enter key issues)
        render_navigation_buttons(current_step_keys)
        
        # Story 25.1: Cancel confirmation dialog
        if st.session_state.get('show_cancel_dialog', False):
            st.warning("⚠️ **Opozorilo**")
            st.write("Ali res želite opustiti? Vsi podatki bodo izgubljeni.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ne, nadaljuj", key="cancel_no", use_container_width=True):
                    st.session_state.show_cancel_dialog = False
                    st.rerun()
            
            with col2:
                if st.button("Da, opusti", type="secondary", key="cancel_yes", use_container_width=True):
                    clear_form_data()
                    st.session_state.show_cancel_dialog = False
                    st.session_state.current_page = 'dashboard'
                    st.rerun()

    with col2:
        render_drafts_sidebar(draft_options)

def add_custom_css():
    """Add premium custom CSS for professional government application styling."""
    st.markdown("""
    <style>
    /* Import Inter font for modern, professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* === CSS VARIABLES - DESIGN SYSTEM === */
    :root {
        /* Primary Colors - Government Professional */
        --primary-900: #1e3a8a;
        --primary-700: #1d4ed8;
        --primary-500: #3b82f6;
        --primary-100: #dbeafe;
        --primary-50: #eff6ff;
        
        /* Neutral Colors */
        --gray-900: #111827;
        --gray-700: #374151;
        --gray-500: #6b7280;
        --gray-300: #d1d5db;
        --gray-100: #f3f4f6;
        --gray-50: #f9fafb;
        --white: #ffffff;
        
        /* Semantic Colors */
        --success: #059669;
        --success-light: #d1fae5;
        --warning: #d97706;
        --warning-light: #fef3c7;
        --error: #dc2626;
        --error-light: #fee2e2;
        --info: #0ea5e9;
        --info-light: #e0f2fe;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        
        /* Border radius */
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
    }
    
    /* === GLOBAL TYPOGRAPHY === */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--gray-900);
        line-height: 1.6;
    }
    
    /* Typography Hierarchy */
    h1 { 
        font-size: 2.5rem; 
        font-weight: 700; 
        line-height: 1.2; 
        color: var(--gray-900);
        margin-bottom: 1rem;
    }
    h2 { 
        font-size: 2rem; 
        font-weight: 600; 
        line-height: 1.3; 
        color: var(--primary-900);
        margin-bottom: 0.75rem;
    }
    h3 { 
        font-size: 1.5rem; 
        font-weight: 600; 
        line-height: 1.4; 
        color: var(--primary-700);
        margin-bottom: 0.5rem;
    }
    
    /* === MAIN LAYOUT === */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* === FORM HEADER === */
    .form-header {
        background: linear-gradient(135deg, var(--primary-900) 0%, var(--primary-700) 100%);
        color: white;
        padding: 2rem;
        border-radius: var(--radius-lg);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }
    
    .form-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                    linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                    linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        opacity: 0.3;
        pointer-events: none;
    }
    
    .form-header h1 {
        margin: 0;
        font-size: 2.25rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    .form-header h3 {
        margin: 0.5rem 0 0 0;
        font-size: 1.125rem;
        font-weight: 500;
        opacity: 0.9;
        position: relative;
        z-index: 1;
        color: var(--primary-50);
    }
    
    .step-indicator {
        font-size: 0.875rem;
        font-weight: 500;
        opacity: 0.9;
        margin-top: 0.75rem;
        position: relative;
        z-index: 1;
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: var(--radius-md);
        display: inline-block;
    }
    
    /* === PROGRESS BAR === */
    .stProgress .st-bo {
        background-color: var(--primary-100) !important;
        height: 1rem !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }
    
    .stProgress .st-bp {
        background: linear-gradient(90deg, var(--primary-500), var(--primary-700)) !important;
        border-radius: var(--radius-md) !important;
        position: relative;
    }
    
    .stProgress .st-bp::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* === BREADCRUMBS === */
    .step-breadcrumbs {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0 2rem 0;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .breadcrumb-item {
        padding: 0.625rem 1.25rem;
        border-radius: var(--radius-lg);
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .breadcrumb-item.completed {
        background: var(--success-light);
        color: var(--success);
        border-color: var(--success);
        box-shadow: var(--shadow-sm);
    }
    
    .breadcrumb-item.current {
        background: var(--primary-700);
        color: white;
        border-color: var(--primary-700);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .breadcrumb-item.current::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.2), transparent);
    }
    
    .breadcrumb-item.pending {
        background: var(--gray-100);
        color: var(--gray-500);
        border-color: var(--gray-300);
    }
    
    .breadcrumb-item:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* === FORM CONTENT === */
    .form-content {
        background: white;
        padding: 2.5rem;
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--gray-200);
        margin-bottom: 2rem;
        position: relative;
    }
    
    .form-content::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-500), var(--primary-700));
        border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    }
    
    /* === NAVIGATION BUTTONS === */
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid var(--gray-200);
    }
    
    /* === STREAMLIT COMPONENT OVERRIDES === */
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, var(--primary-700), var(--primary-500)) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        color: white !important;
        text-transform: none !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(135deg, var(--primary-900), var(--primary-700)) !important;
    }
    
    .stButton button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* Secondary buttons */
    .stButton button[kind="secondary"] {
        background: white !important;
        color: var(--primary-700) !important;
        border: 2px solid var(--primary-700) !important;
    }
    
    .stButton button[kind="secondary"]:hover {
        background: var(--primary-50) !important;
        border-color: var(--primary-900) !important;
        color: var(--primary-900) !important;
    }
    
    /* Form Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        background: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px var(--primary-100) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea {
        min-height: 120px !important;
        resize: vertical !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px var(--primary-100) !important;
    }
    
    /* Checkboxes */
    .stCheckbox > label > div {
        background: white !important;
        border: 2px solid var(--gray-300) !important;
        border-radius: var(--radius-sm) !important;
    }
    
    .stCheckbox > label > div[data-checked="true"] {
        background: var(--primary-500) !important;
        border-color: var(--primary-500) !important;
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        border: 2px dashed var(--gray-300) !important;
        border-radius: var(--radius-lg) !important;
        padding: 2rem !important;
        background: var(--gray-50) !important;
        transition: all 0.2s ease !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: var(--primary-500) !important;
        background: var(--primary-50) !important;
    }
    
    /* === SECTION HEADERS === */
    [data-testid="stMarkdownContainer"] h2 {
        color: var(--primary-900) !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin: 2rem 0 1rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid var(--primary-100) !important;
        position: relative;
    }
    
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--primary-700) !important;
        font-weight: 500 !important;
        font-size: 1.25rem !important;
        margin: 1.5rem 0 0.75rem 0 !important;
    }
    
    /* === LOT/SLOT CARDS === */
    .lot-card {
        background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%) !important;
        border: 2px solid var(--primary-500) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        position: relative;
        overflow: hidden;
    }
    
    .lot-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-500);
    }
    
    .lot-card h4 {
        color: var(--primary-900) !important;
        margin: 0 0 0.5rem 0 !important;
        font-weight: 600 !important;
    }
    
    /* === SUCCESS/ERROR MESSAGES === */
    .stSuccess {
        background: var(--success-light) !important;
        border: 1px solid var(--success) !important;
        border-radius: var(--radius-md) !important;
        color: var(--success) !important;
    }
    
    .stError {
        background: var(--error-light) !important;
        border: 1px solid var(--error) !important;
        border-radius: var(--radius-md) !important;
        color: var(--error) !important;
    }
    
    .stWarning {
        background: var(--warning-light) !important;
        border: 1px solid var(--warning) !important;
        border-radius: var(--radius-md) !important;
        color: var(--warning) !important;
    }
    
    .stInfo {
        background: var(--info-light) !important;
        border: 1px solid var(--info) !important;
        border-radius: var(--radius-md) !important;
        color: var(--info) !important;
    }
    
    /* === SIDEBAR === */
    .sidebar .sidebar-content {
        padding: 1rem !important;
    }
    
    .sidebar-header {
        background: var(--gray-50) !important;
        padding: 1rem !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 1rem !important;
        border-left: 4px solid var(--primary-700) !important;
    }
    
    /* === RESPONSIVE DESIGN === */
    @media (max-width: 768px) {
        .form-header {
            padding: 1.5rem !important;
        }
        
        .form-header h1 {
            font-size: 1.75rem !important;
        }
        
        .form-content {
            padding: 1.5rem !important;
        }
        
        .step-breadcrumbs {
            gap: 0.25rem !important;
        }
        
        .breadcrumb-item {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.75rem !important;
        }
    }
    
    /* === ANIMATIONS === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .form-content {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* === ACCESSIBILITY === */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* === PRINT STYLES === */
    @media print {
        .form-header {
            background: var(--primary-900) !important;
            -webkit-print-color-adjust: exact !important;
            color-adjust: exact !important;
        }
        
        .navigation-buttons {
            display: none !important;
        }
        
        .step-breadcrumbs {
            display: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_step_breadcrumbs():
    """Render step navigation breadcrumbs."""
    from localization import get_dynamic_step_label
    
    # Get dynamic form steps for breadcrumbs
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
    # Check if lots are enabled
    has_lots = st.session_state.get("lotsInfo.hasLots", False)
    
    breadcrumbs_html = '<div class="step-breadcrumbs">'
    
    for i, step_keys in enumerate(dynamic_form_steps):
        step_num = i + 1
        step_label = get_dynamic_step_label(step_keys, step_num, has_lots)
        
        if i < st.session_state.current_step:
            css_class = "completed"
        elif i == st.session_state.current_step:
            css_class = "current"
        else:
            css_class = "pending"
            
        breadcrumbs_html += f'<span class="breadcrumb-item {css_class}">{step_num}. {step_label}</span>'
    
    breadcrumbs_html += '</div>'
    st.markdown(breadcrumbs_html, unsafe_allow_html=True)

def render_navigation_buttons_in_form(current_step_keys):
    """Render navigation buttons inside a Streamlit form."""
    # Get dynamic form steps for navigation
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
    st.markdown('<div class="navigation-buttons">', unsafe_allow_html=True)
    
    col_nav_left, col_nav_center, col_nav_right = st.columns([1, 1, 1])
    
    with col_nav_left:
        if st.session_state.current_step > 0:
            go_back = st.form_submit_button(
                f"← {get_text('back_button')}", 
                type="secondary",
                use_container_width=True
            )
            if go_back:
                # Set navigation flag for all form fields to prevent auto-selection triggers
                _set_navigation_flags()
                st.session_state.current_step -= 1
                st.rerun()

    with col_nav_right:
        if st.session_state.current_step < len(dynamic_form_steps) - 1:
            go_forward = st.form_submit_button(
                f"{get_text('next_button')} →", 
                type="primary",
                use_container_width=True
            )
            if go_forward:
                # Enhanced validation can be added here
                if validate_step(current_step_keys, st.session_state.schema):
                    # Set navigation flag for all form fields to prevent auto-selection triggers
                    _set_navigation_flags()
                    st.session_state.current_step += 1
                    st.rerun()
        else:
            button_text = "💾 Posodobi naročilo" if st.session_state.edit_mode else f"📄 {get_text('submit_button')}"
            submit_form = st.form_submit_button(
                button_text, 
                type="primary",
                use_container_width=True
            )
            if submit_form:
                # Story 22.3: Check if any steps had validation skipped
                validation_skipped = False
                for step_num in range(len(dynamic_form_steps)):
                    if not should_validate(step_num):
                        validation_skipped = True
                        break
                
                # Show warning if validation was skipped
                if validation_skipped:
                    st.warning("⚠️ **Opozorilo**: Nekateri koraki niso bili validirani. Ali ste prepričani, da želite nadaljevati?")
                    col1, col2 = st.columns(2)
                    with col1:
                        confirm_submit = st.checkbox("Da, razumem in želim nadaljevati", key="confirm_skip_validation")
                    if not confirm_submit:
                        st.error("Potrdite, da želite nadaljevati brez validacije")
                        return
                
                if validate_step(current_step_keys, st.session_state.schema) or validation_skipped:
                    final_form_data = get_form_data_from_session()
                    
                    # Save or update based on edit mode
                    if st.session_state.edit_mode:
                        # Update existing procurement
                        if database.update_procurement(st.session_state.edit_record_id, final_form_data):
                            st.success(f"✅ Naročilo ID {st.session_state.edit_record_id} uspešno posodobljeno!")
                            # Clear edit mode and return to dashboard
                            st.session_state.edit_mode = False
                            st.session_state.edit_record_id = None
                            st.session_state.current_page = 'dashboard'
                            clear_form_data()
                            st.rerun()
                        else:
                            st.error("❌ Napaka pri posodabljanju naročila")
                    else:
                        # Create new procurement
                        new_id = database.create_procurement(final_form_data)
                        if new_id:
                            st.success(f"✅ Novo naročilo uspešno ustvarjeno z ID: {new_id}")
                            # Return to dashboard
                            st.session_state.current_page = 'dashboard'
                            clear_form_data()
                            st.rerun()
                        else:
                            st.error("❌ Napaka pri ustvarjanju naročila")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_navigation_buttons(current_step_keys):
    """Render enhanced navigation buttons with proper state handling."""
    # Get dynamic form steps for navigation
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
    st.markdown('<div class="navigation-buttons">', unsafe_allow_html=True)
    
    # Check if we're at the final step of a lot
    is_lot_final = is_final_lot_step(st.session_state, st.session_state.current_step)
    
    if is_lot_final:
        # Special navigation for lot final steps
        lot_buttons = get_lot_navigation_buttons(st.session_state)
        
        if len(lot_buttons) == 1:
            # Single button - use full width
            col_nav_left, col_nav_center, col_nav_right = st.columns([1, 1, 1])
            with col_nav_left:
                if st.session_state.current_step > 0:
                    if st.button(
                        f"← {get_text('back_button')}", 
                        type="secondary",
                        use_container_width=True
                    ):
                        _set_navigation_flags()
                        st.session_state.current_step -= 1
                        st.rerun()
            
            with col_nav_right:
                button_text, action, button_type = lot_buttons[0]
                if st.button(
                    button_text,
                    type=button_type,
                    use_container_width=True
                ):
                    handle_lot_action(action)
        
        elif len(lot_buttons) == 2:
            # Two buttons
            col_nav_left, col_nav_btn1, col_nav_btn2 = st.columns([1, 1, 1])
            with col_nav_left:
                if st.session_state.current_step > 0:
                    if st.button(
                        f"← {get_text('back_button')}", 
                        type="secondary",
                        use_container_width=True
                    ):
                        _set_navigation_flags()
                        st.session_state.current_step -= 1
                        st.rerun()
            
            with col_nav_btn1:
                button_text, action, button_type = lot_buttons[0]
                if st.button(
                    button_text,
                    type=button_type,
                    use_container_width=True,
                    key=f"lot_btn_0"
                ):
                    handle_lot_action(action)
            
            with col_nav_btn2:
                button_text, action, button_type = lot_buttons[1]
                if st.button(
                    button_text,
                    type=button_type,
                    use_container_width=True,
                    key=f"lot_btn_1"
                ):
                    handle_lot_action(action)
        
        else:
            # Three or more buttons - use expandable layout
            cols = st.columns(len(lot_buttons) + 1)
            
            with cols[0]:
                if st.session_state.current_step > 0:
                    if st.button(
                        f"← {get_text('back_button')}", 
                        type="secondary",
                        use_container_width=True
                    ):
                        _set_navigation_flags()
                        st.session_state.current_step -= 1
                        st.rerun()
            
            for i, (button_text, action, button_type) in enumerate(lot_buttons):
                with cols[i + 1]:
                    if st.button(
                        button_text,
                        type=button_type,
                        use_container_width=True,
                        key=f"lot_btn_{i}"
                    ):
                        handle_lot_action(action)
    
    else:
        # Standard navigation
        col_nav_left, col_nav_center, col_nav_right = st.columns([1, 1, 1])
        
        with col_nav_left:
            if st.session_state.current_step > 0:
                if st.button(
                    f"← {get_text('back_button')}", 
                    type="secondary",
                    use_container_width=True
                ):
                    # Set navigation flag for all form fields to prevent auto-selection triggers
                    _set_navigation_flags()
                    st.session_state.current_step -= 1
                    st.rerun()
        
        with col_nav_center:
            # Save button - available on all steps
            if st.button(
                "Shrani", 
                type="secondary",
                use_container_width=True,
                help="Shrani trenutni napredek obrazca"
            ):
                with st.spinner(LOADING_MESSAGES['save_progress']):
                    save_form_progress()

        with col_nav_right:
            if st.session_state.current_step < len(dynamic_form_steps) - 1:
                if st.button(
                    f"{get_text('next_button')} →", 
                    type="primary",
                    use_container_width=True
                ):
                    import logging
                    logging.info(f"Next button clicked at step {st.session_state.current_step}")
                    # Enhanced validation can be added here
                    validation_passed = validate_step(current_step_keys, st.session_state.schema)
                    logging.info(f"Validation result: {validation_passed}")
                    
                    if validation_passed:
                        logging.info("Navigation allowed - moving to next step")
                        # Set navigation flag for all form fields to prevent auto-selection triggers
                        _set_navigation_flags()
                        st.session_state.current_step += 1
                        st.rerun()
                    else:
                        logging.info("Navigation blocked by validation")
                        # Store validation error in session state to persist it
                        st.session_state['navigation_blocked'] = True
                        st.session_state['navigation_blocked_step'] = st.session_state.current_step
            else:
                # Story 25.1: Replace single submit button with Cancel/Confirm buttons on last step
                col_cancel, col_confirm = st.columns(2)
                
                with col_cancel:
                    if st.button(
                        "🚫 Opusti", 
                        type="secondary",
                        use_container_width=True,
                        key="cancel_form"
                    ):
                        st.session_state.show_cancel_dialog = True
                        st.rerun()
                
                with col_confirm:
                    button_text = "✅ Potrdi" 
                    if st.button(
                        button_text, 
                        type="primary",
                        use_container_width=True,
                        key="confirm_form"
                    ):
                        if validate_step(current_step_keys, st.session_state.schema):
                            final_form_data = get_form_data_from_session()
                            
                            # Save or update based on edit mode
                            if st.session_state.edit_mode:
                                # Update existing procurement
                                if database.update_procurement(st.session_state.edit_record_id, final_form_data):
                                    st.success(f"✅ Naročilo ID {st.session_state.edit_record_id} uspešno posodobljeno!")
                                    # Clear edit mode and return to dashboard
                                    import time
                                    time.sleep(1)  # Show success message
                                    st.session_state.edit_mode = False
                                    st.session_state.edit_record_id = None
                                    st.session_state.current_page = 'dashboard'
                                    clear_form_data()
                                    st.rerun()
                                else:
                                    st.error("❌ Napaka pri posodabljanju naročila")
                            else:
                                # Create new procurement
                                new_id = database.create_procurement(final_form_data)
                                if new_id:
                                    st.success(f"✅ Osnutek uspešno shranjen! ID: {new_id}")
                                    # Return to dashboard
                                    import time
                                    time.sleep(1)  # Show success message
                                    st.session_state.current_page = 'dashboard'
                                    clear_form_data()
                                    st.rerun()
                                else:
                                    st.error("❌ Napaka pri ustvarjanju naročila")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_drafts_sidebar(draft_options):
    """Render the enhanced drafts management sidebar."""
    st.markdown(f'<div class="sidebar-header"><h3>{get_text("drafts_header")}</h3></div>', unsafe_allow_html=True)
    
    if not draft_options:
        st.info(get_text("no_drafts"))
        return

    selected_draft_label = st.selectbox(
        get_text("load_draft"), 
        options=list(draft_options.keys()),
        help="Izberite osnutek, ki ga želite naložiti"
    )
    
    # Single button for loading draft - no save button in sidebar
    if st.button(
        get_text("load_selected_draft"),
        type="secondary",
        use_container_width=True
    ):
        selected_draft_id = draft_options[selected_draft_label]
        loaded_data = database.load_draft(selected_draft_id)
        if loaded_data:
            # Flatten nested dictionary to dot-notation for session state
            def flatten_dict(d, parent_key='', sep='.'):
                """Flatten nested dictionary into dot-notation keys."""
                items = []
                for k, v in d.items():
                    # Skip metadata fields
                    if k.startswith('_'):
                        continue
                    # Handle special lot structure
                    if k == 'lots' and isinstance(v, list):
                        # Store lot data in session state
                        st.session_state['lots'] = v
                        st.session_state['lot_mode'] = 'multiple'
                        
                        # Extract lot names
                        lot_names = [lot.get('name', f'Sklop {i+1}') for i, lot in enumerate(v)]
                        st.session_state['lot_names'] = lot_names
                        
                        # Flatten each lot's data into lot-scoped keys
                        for i, lot in enumerate(v):
                            for lot_key, lot_value in lot.items():
                                if lot_key != 'name' and not isinstance(lot_value, dict):
                                    items.append((f'lot_{i}.{lot_key}', lot_value))
                                elif isinstance(lot_value, dict):
                                    # Recursively flatten nested lot data
                                    nested_items = flatten_dict(lot_value, f'lot_{i}.{lot_key}', sep=sep)
                                    items.extend(nested_items.items())
                        continue
                    elif k == 'lot_names':
                        st.session_state['lot_names'] = v
                        continue
                    
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)
            
            # Clear existing form data first
            clear_form_data()
            
            # Flatten and load into session state
            flattened_data = flatten_dict(loaded_data)
            for key, value in flattened_data.items():
                st.session_state[key] = value
            
            # Restore metadata if present
            if '_save_metadata' in loaded_data:
                metadata = loaded_data['_save_metadata']
                if 'current_step' in metadata:
                    st.session_state.current_step = metadata['current_step']
            
            # Story 28.3: Store form_id for file loading
            st.session_state.form_id = selected_draft_id
            st.session_state.current_draft_id = selected_draft_id
            st.success(get_text("draft_loaded"))
            st.rerun()
        else:
            st.error(get_text("draft_load_error"))

if __name__ == "__main__":
    main()
