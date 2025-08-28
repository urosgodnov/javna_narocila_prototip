
"""Main Streamlit application for public procurement document generation."""
import streamlit as st
import database
import logging
from config import (
    get_dynamic_form_steps,
    is_final_lot_step,
    get_lot_navigation_buttons,
    SCHEMA_FILE
)
from utils.schema_utils import load_json_schema, get_form_data_from_session, clear_form_data, resolve_schema_ref
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
    
    # IMPORT REDIRECT FIX: Force back to dashboard if we just imported
    if st.session_state.get('JUST_IMPORTED'):
        st.session_state.current_page = 'dashboard'
        st.session_state.edit_mode = False
        st.session_state.edit_record_id = None
        del st.session_state['JUST_IMPORTED']
    
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
    
    # Initialize step tracking for smart navigation
    initialize_step_tracking()
    
    # Load data if in edit mode but data not yet loaded
    if st.session_state.get('edit_mode') and st.session_state.get('edit_record_id'):
        import logging
        logging.info(f"=== CHECKING EDIT MODE: edit_mode={st.session_state.get('edit_mode')}, edit_record_id={st.session_state.get('edit_record_id')}, current_page={st.session_state.get('current_page')}")
        # Check if we need to load the data
        if 'edit_data_loaded' not in st.session_state:
            from ui.dashboard import load_procurement_to_form
            logging.info(f"=== AUTO-LOADING procurement {st.session_state.edit_record_id} for editing ===")
            try:
                load_procurement_to_form(st.session_state.edit_record_id)
                st.session_state.edit_data_loaded = True
                logging.info(f"=== AUTO-LOADING COMPLETED ===")
            except Exception as e:
                logging.error(f"=== AUTO-LOADING ERROR: {e} ===")
                import traceback
                logging.error(traceback.format_exc())
        else:
            logging.info(f"=== EDIT DATA ALREADY LOADED ===")
    else:
        if st.session_state.get('current_page') == 'form':
            import logging
            logging.debug(f"Form page but not edit mode: edit_mode={st.session_state.get('edit_mode')}, edit_record_id={st.session_state.get('edit_record_id')}")

    # Route to appropriate page based on current_page state
    if st.session_state.current_page == 'dashboard':
        render_dashboard()
    elif st.session_state.current_page == 'form':
        # Load data if in edit mode but data not yet loaded - moved here for proper timing
        if st.session_state.get('edit_mode') and st.session_state.get('edit_record_id'):
            import logging
            logging.info(f"=== FORM PAGE EDIT CHECK: edit_mode={st.session_state.get('edit_mode')}, edit_record_id={st.session_state.get('edit_record_id')}")
            if 'edit_data_loaded' not in st.session_state:
                from ui.dashboard import load_procurement_to_form
                logging.info(f"=== LOADING procurement {st.session_state.edit_record_id} for editing ===")
                try:
                    load_procurement_to_form(st.session_state.edit_record_id)
                    st.session_state.edit_data_loaded = True
                    logging.info(f"=== LOADING COMPLETED ===")
                except Exception as e:
                    logging.error(f"=== LOADING ERROR: {e} ===")
                    import traceback
                    logging.error(traceback.format_exc())
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

def save_form_draft(include_files=True, show_success=True, location="navigation", is_confirmation=False):
    """Unified function to save current form state as a draft.
    
    Args:
        include_files: Whether to also save uploaded files (default: True)
        show_success: Whether to show success message (default: True)
        location: Where the save was triggered from ("navigation" or "sidebar")
        is_confirmation: Whether this save is from the confirmation step (default: False)
    
    Returns:
        draft_id if successful, None otherwise
    """
    try:
        import json
        import datetime
        
        # Get current form data
        form_data = get_form_data_from_session()
        
        # Add status based on save type
        form_data['status'] = 'osnutek' if is_confirmation else 'delno izpolnjen'
        
        # Add metadata
        form_data['_save_metadata'] = {
            'saved_at': datetime.datetime.now().isoformat(),
            'current_step': st.session_state.current_step,
            'save_type': 'confirmation' if is_confirmation else 'progress',
            'save_location': location
        }
        
        # Check if we're already working on a draft
        if 'current_draft_id' in st.session_state and st.session_state.current_draft_id:
            # Check if we're in edit mode for an existing procurement
            if st.session_state.get('edit_mode') and st.session_state.get('edit_record_id'):
                # Update the existing procurement, not the draft
                draft_id = st.session_state.edit_record_id
                success = database.update_procurement(draft_id, form_data)
                if not success:
                    draft_id = None
                else:
                    import logging
                    logging.info(f"Updated existing procurement ID: {draft_id}")
            else:
                # Update existing draft using the new update_draft function
                draft_id = st.session_state.current_draft_id
                success = database.update_draft(draft_id, form_data)
                if success:
                    import logging
                    logging.info(f"Updated existing draft ID: {draft_id}")
                else:
                    # If update fails (draft was deleted?), create new one
                    import logging
                    logging.warning(f"Failed to update draft {draft_id}, creating new one")
                    draft_id = database.save_draft(form_data)
                    st.session_state.current_draft_id = draft_id
                    logging.info(f"Created new draft ID: {draft_id}")
        else:
            # Create new draft
            draft_id = database.save_draft(form_data)
            st.session_state.current_draft_id = draft_id
            import logging
            logging.info(f"Created initial draft ID: {draft_id}")
        
        if draft_id:
            
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
                        # Check for either 'data' (new format) or 'content' (old format)
                        file_data = file_info.get('data') if file_info else None
                        if not file_data:
                            file_data = file_info.get('content') if file_info else None
                            
                        if file_info and file_data:
                            # Extract field name from the key
                            field_name = file_key.replace('_file_info', '')
                            
                            # Save file to document service
                            doc_id, is_new = doc_service.save_document(
                                form_id=draft_id,
                                form_type='draft',
                                field_name=field_name,
                                file_name=file_info['name'],
                                file_content=BytesIO(file_data) if isinstance(file_data, bytes) else file_data,
                                file_size=file_info.get('size', len(file_data) if isinstance(file_data, bytes) else 0)
                            )
                            
                            # Clear from session after successful save
                            del st.session_state[file_key]
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

def render_confirmation_step():
    """Render the final confirmation step."""
    st.markdown("## 📋 Potrditev naročila")
    st.markdown("---")
    
    # Confirmation info
    st.info("ℹ️ S klikom na 'Potrdi' bo naročilo shranjeno s statusom 'osnutek'")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        if st.button("◀ Nazaj", key="conf_back", use_container_width=True):
            st.session_state.current_step -= 1
            st.rerun()
    
    with col3:
        if st.button("✅ Potrdi naročilo", type="primary", key="confirm_order", use_container_width=True):
            with st.spinner("Shranjujem naročilo..."):
                # Create the actual procurement (not just a draft)
                from utils.schema_utils import get_form_data_from_session
                final_form_data = get_form_data_from_session()
                
                # Create new procurement
                new_id = database.create_procurement(final_form_data)
                
                if new_id:
                    st.success(f"✅ Novo naročilo uspešno ustvarjeno z ID: {new_id}")
                    # Removed balloons - too distracting as requested
                    
                    # Show options for next actions
                    st.markdown("---")
                    st.markdown("### Kaj želite narediti zdaj?")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📊 Nazaj na pregled", key="to_dashboard", use_container_width=True):
                            st.session_state.current_page = 'dashboard'
                            st.session_state.current_step = 0
                            clear_form_data()
                            st.rerun()
                    with col2:
                        if st.button("➕ Novo naročilo", key="new_order", use_container_width=True):
                            st.session_state.current_step = 0
                            clear_form_data()
                            st.rerun()
                else:
                    st.error("❌ Napaka pri ustvarjanju naročila. Prosim, poskusite znova.")

# Story 31.2: Smart Navigation Implementation
def initialize_step_tracking():
    """Initialize step completion tracking in session state."""
    if 'completed_steps' not in st.session_state:
        st.session_state['completed_steps'] = {}
    
    # For lot-based forms
    if st.session_state.get('lot_mode') == 'multiple':
        if 'lot_completed_steps' not in st.session_state:
            st.session_state['lot_completed_steps'] = {}

def mark_step_completed(step_index, lot_id=None):
    """Mark a step as completed when moving forward."""
    initialize_step_tracking()
    
    if lot_id:
        if lot_id not in st.session_state['lot_completed_steps']:
            st.session_state['lot_completed_steps'][lot_id] = {}
        st.session_state['lot_completed_steps'][lot_id][step_index] = True
    else:
        st.session_state['completed_steps'][step_index] = True

def is_step_accessible(step_index, lot_id=None):
    """Check if a step can be accessed based on completion history."""
    # In edit mode, allow access to all steps since we're editing existing data
    if st.session_state.get('edit_mode', False):
        return True
    
    # Allow access to current and previous steps
    current_step = st.session_state.get('current_step', 0)
    if step_index <= current_step:
        return True
    
    # Check completion tracking
    if lot_id:
        lot_steps = st.session_state.get('lot_completed_steps', {}).get(lot_id, {})
        completed = lot_steps
    else:
        completed = st.session_state.get('completed_steps', {})
    
    # Verify all previous steps are completed
    for i in range(step_index):
        if not completed.get(i, False):
            return False
    
    return completed.get(step_index, False)

def navigate_to_step(target_step, lot_id=None):
    """Navigate to a specific step with validation."""
    if is_step_accessible(target_step, lot_id):
        # Mark current step as completed if moving forward
        current = st.session_state.get('current_step', 0)
        if target_step > current:
            mark_step_completed(current, lot_id)
        
        # Update navigation
        if lot_id:
            st.session_state['current_lot'] = lot_id
        st.session_state['current_step'] = target_step
        st.rerun()
    else:
        st.warning("⚠️ Ne morete skočiti na ta korak - prejšnji koraki niso izpolnjeni")

def render_quick_navigation():
    """Render quick navigation dropdown for completed steps."""
    from config import get_dynamic_form_steps
    
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    is_edit_mode = st.session_state.get('edit_mode', False)
    
    # Build accessible steps list
    accessible_steps = []
    step_names = get_step_names(steps)  # Use helper function to get names
    
    for idx, step in enumerate(steps):
        # In edit mode, all steps are accessible; otherwise check if completed or current/previous
        if is_edit_mode or idx <= current or completed.get(idx, False):
            step_name = step_names[idx] if idx < len(step_names) else f"Korak {idx+1}"
            # Add step number to the name for clarity
            accessible_steps.append((idx, f"{idx+1}. {step_name}"))
    
    if accessible_steps and len(accessible_steps) > 1:
        with st.sidebar:
            st.markdown("### 🧭 Hitra navigacija")
            if is_edit_mode:
                st.info("Pri urejanju lahko skočite na katerikoli korak")
            else:
                st.info("Skočite na že izpolnjene korake")
            
            # Show overall progress
            total_steps = len(steps)
            # Ensure progress stays within [0.0, 1.0] range
            # This can happen when loading a draft with different step configuration
            if total_steps > 0:
                progress = min(1.0, max(0.0, (current + 1) / total_steps))
            else:
                progress = 0.0
            st.progress(progress)
            # Also clamp the displayed step number
            display_current = min(current + 1, total_steps)
            st.markdown(f"**Napredek:** Korak {display_current} od {total_steps}")
            
            # Current step indicator with step number
            current_name = step_names[current] if current < len(step_names) else f"Korak {current+1}"
            st.markdown(f"**Trenutni korak:** {current+1}. {current_name}")
            
            # Navigation dropdown
            selected = st.selectbox(
                "Pojdi na korak:",
                options=[idx for idx, _ in accessible_steps],
                format_func=lambda x: next(title for idx, title in accessible_steps if idx == x),
                index=[idx for idx, _ in accessible_steps].index(current) if current in [idx for idx, _ in accessible_steps] else 0,
                key="quick_nav_select"
            )
            
            if st.button("➡️ Pojdi", key="quick_nav_go", use_container_width=True):
                navigate_to_step(selected)

def get_step_names(steps):
    """Helper function to get readable names for steps."""
    step_names = []
    for i, step_fields in enumerate(steps):
        if step_fields and len(step_fields) > 0:
            field_name = step_fields[0] if isinstance(step_fields, list) else str(step_fields)
            # Map field names to readable format
            name_map = {
                "clientInfo": "Podatki naročnika",
                "projectInfo": "Podatki projekta",
                "legalBasis": "Pravna podlaga",
                "submissionProcedure": "Postopek oddaje",
                "lotsInfo": "Konfiguracija sklopov",
                "lotConfiguration": "Konfiguracija sklopov",
                "orderType": "Vrsta naročila",
                "technicalSpecifications": "Tehnične zahteve",
                "executionDeadline": "Roki izvajanja",
                "priceInfo": "Informacije o ceni",
                "inspectionInfo": "Ogledi in pogajanja",
                "participationAndExclusion": "Pogoji sodelovanja",
                "financialGuarantees": "Zavarovanja",
                "selectionCriteria": "Merila izbire",
                "contractInfo": "Pogodba",
                "otherInfo": "Dodatne informacije",
                "confirmation": "Potrditev"
            }
            
            # Handle lot-specific steps
            if field_name.startswith("lot_context_"):
                lot_index = int(field_name.split('_')[-1])
                # Get actual lot name from session state
                lots = st.session_state.get('lots', [])
                if lot_index < len(lots):
                    lot_name = lots[lot_index].get('name', f'Sklop {lot_index + 1}') if isinstance(lots[lot_index], dict) else f'Sklop {lot_index + 1}'
                else:
                    lot_name = f"Sklop {lot_index + 1}"
                step_name = lot_name
            elif field_name.startswith("lot_"):
                # Extract the actual field name from lot_0_orderType
                parts = field_name.split('_', 2)
                if len(parts) >= 3:
                    base_field = parts[2]
                    step_name = name_map.get(base_field, f"Korak {i+1}")
                else:
                    step_name = f"Korak {i+1}"
            else:
                step_name = name_map.get(field_name, f"Korak {i+1}")
            
            step_names.append(step_name)
        else:
            step_names.append(f"Korak {i+1}")
    
    return step_names

# Story 31.3: Visual Progress Indicator
def render_visual_progress_indicator():
    """Render horizontal progress indicator with visual states and navigation."""
    from config import get_dynamic_form_steps
    
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    step_names = get_step_names(steps)
    
    # Skip if only one step
    if len(steps) <= 1:
        return
    
    # Create progress container
    st.markdown("### 📊 Napredek obrazca")
    
    # Calculate how many columns we need (limit to avoid too narrow columns)
    num_steps = len(steps)
    if num_steps > 7:
        # For many steps, show compact view
        render_compact_progress_indicator()
        return
    
    # Create columns for steps
    cols = st.columns(num_steps)
    
    for idx, col in enumerate(cols):
        with col:
            # Determine step status
            if idx == current:
                # Current step
                status_icon = "🔵"
                status_color = "#2196F3"
                is_clickable = False
                button_type = "primary"
            elif completed.get(idx, False):
                # Completed step
                status_icon = "✅"
                status_color = "#4CAF50"
                is_clickable = True
                button_type = "secondary"
            elif idx < current:
                # Skipped/incomplete step
                status_icon = "⚠️"
                status_color = "#FF9800"
                is_clickable = True
                button_type = "secondary"
            else:
                # Locked step
                status_icon = "🔒"
                status_color = "#9E9E9E"
                is_clickable = False
                button_type = None
            
            # Get step name
            step_name = step_names[idx] if idx < len(step_names) else f"Korak {idx+1}"
            # Truncate long names
            if len(step_name) > 12:
                display_name = step_name[:10] + "..."
            else:
                display_name = step_name
            
            # Render step indicator
            if is_clickable:
                # Clickable step button
                if st.button(
                    f"{status_icon}\\n{display_name}",
                    key=f"progress_{idx}",
                    use_container_width=True,
                    type=button_type,
                    help=f"{step_name}"
                ):
                    navigate_to_step(idx)
            else:
                # Non-clickable step (current or locked)
                st.markdown(
                    f"""
                    <div style="
                        text-align: center;
                        padding: 8px 4px;
                        border-radius: 8px;
                        background-color: {'#e3f2fd' if idx == current else '#f5f5f5'};
                        border: 2px solid {status_color};
                        min-height: 70px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                    ">
                        <div style="font-size: 20px; margin-bottom: 4px;">{status_icon}</div>
                        <div style="font-size: 10px; color: #666;">
                            {display_name}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Add progress bar below steps
    # Ensure progress stays within valid range
    if num_steps > 0:
        progress_percentage = min(100, max(0, int(((current + 1) / num_steps) * 100)))
    else:
        progress_percentage = 0
    st.progress(progress_percentage / 100)
    st.caption(f"Korak {current + 1} od {num_steps} ({progress_percentage}% dokončano)")

def render_compact_progress_indicator():
    """Compact progress indicator for many steps or mobile view."""
    from config import get_dynamic_form_steps
    
    steps = get_dynamic_form_steps(st.session_state)
    current = st.session_state.current_step
    completed = st.session_state.get('completed_steps', {})
    step_names = get_step_names(steps)
    total = len(steps)
    
    # Progress metrics
    completed_count = sum(1 for v in completed.values() if v)
    # Calculate real progress based on completed steps
    if total > 0:
        # Use completed steps for progress calculation if available
        if completed_count > 0:
            progress_percent = min(100, max(0, int((completed_count / total) * 100)))
        else:
            progress_percent = min(100, max(0, int(((current + 1) / total) * 100)))
    else:
        progress_percent = 0
    
    # Current step info
    current_name = step_names[current] if current < len(step_names) else f"Korak {current+1}"
    
    # Group steps by lot for better display
    lot_groups = {}
    general_steps = []
    
    for i, step_fields in enumerate(steps):
        if step_fields and len(step_fields) > 0:
            first_field = step_fields[0]
            if first_field.startswith('lot_'):
                # Extract lot index
                if first_field.startswith('lot_context_'):
                    lot_idx = int(first_field.split('_')[-1])
                elif '_' in first_field:
                    parts = first_field.split('_')
                    if len(parts) >= 2 and parts[1].isdigit():
                        lot_idx = int(parts[1])
                    else:
                        lot_idx = -1
                else:
                    lot_idx = -1
                    
                if lot_idx >= 0:
                    if lot_idx not in lot_groups:
                        lot_groups[lot_idx] = []
                    lot_groups[lot_idx].append(i)
            else:
                general_steps.append(i)
    
    # Render compact view
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Trenutni korak {current + 1} od {total}**: {current_name}")
        st.progress(progress_percent / 100)
        
        # Show step status summary
        status_text = []
        if completed_count > 0:
            status_text.append(f"✅ Dokončani: {completed_count}")
        
        # Show lot-specific progress if in multiple lot mode
        if lot_groups:
            for lot_idx in sorted(lot_groups.keys()):
                lot_steps = lot_groups[lot_idx]
                lot_completed = sum(1 for step_idx in lot_steps if completed.get(step_idx, False))
                lot_name = st.session_state.get('lot_names', [f'Sklop {lot_idx+1}'])[lot_idx] if lot_idx < len(st.session_state.get('lot_names', [])) else f'Sklop {lot_idx+1}'
                status_text.append(f"📦 {lot_name}: {lot_completed}/{len(lot_steps)}")
        
        if current < total - 1:
            remaining = total - completed_count
            status_text.append(f"⏳ Preostali: {remaining}")
        
        if status_text:
            st.caption(" | ".join(status_text))
    
    with col2:
        # Quick jump menu for completed steps
        accessible = []
        for i in range(total):
            if i < current or completed.get(i, False):
                accessible.append(i)
        
        if len(accessible) > 1:
            selected = st.selectbox(
                "Skoči na:",
                options=accessible,
                format_func=lambda x: f"{x+1}. {step_names[x][:15]}" if x < len(step_names) else f"{x+1}. Korak",
                index=accessible.index(current) if current in accessible else 0,
                key="compact_nav",
                label_visibility="collapsed"
            )
            if selected != current:
                navigate_to_step(selected)

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
    # Import get_dynamic_form_steps function
    from config import get_dynamic_form_steps
    
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
                                    import logging
                                    logging.info(f"[DRAFT LOAD] Loading draft with keys: {list(loaded_data.keys())}")
                                    if 'lots' in loaded_data:
                                        logging.info(f"[DRAFT LOAD] Found {len(loaded_data['lots'])} lots in draft")
                                    
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
                                                st.session_state['lot_mode'] = 'multiple' if len(v) > 0 else 'none'
                                                # Also set lotsInfo.hasLots for proper form configuration
                                                if len(v) > 0:
                                                    st.session_state['lotsInfo.hasLots'] = True
                                                
                                                # Extract lot names
                                                lot_names = [lot.get('name', f'Sklop {i+1}') for i, lot in enumerate(v)]
                                                st.session_state['lot_names'] = lot_names
                                                
                                                # Flatten each lot's data into lot-scoped keys
                                                for i, lot in enumerate(v):
                                                    for lot_key, lot_value in lot.items():
                                                        if lot_key != 'name' and not isinstance(lot_value, dict):
                                                            # Store with regular prefix
                                                            items.append((f'lot_{i}.{lot_key}', lot_value))
                                                            # Also store with double prefix for compatibility
                                                            if lot_key.startswith('orderType') or lot_key in ['technicalSpecifications', 'executionDeadline']:
                                                                items.append((f'lot_{i}.lot_{i}_{lot_key}', lot_value))
                                                        elif isinstance(lot_value, dict):
                                                            # Recursively flatten nested lot data
                                                            nested_items = flatten_dict(lot_value, f'lot_{i}.{lot_key}', sep=sep)
                                                            items.extend(nested_items.items())
                                                            # Also handle double-prefix pattern for nested fields
                                                            if lot_key == 'orderType' or lot_key in ['technicalSpecifications', 'executionDeadline']:
                                                                double_nested = flatten_dict(lot_value, f'lot_{i}.lot_{i}_{lot_key}', sep=sep)
                                                                items.extend(double_nested.items())
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
                                    
                                    import logging
                                    lot_keys = [k for k in flattened_data.keys() if k.startswith('lot_')]
                                    logging.info(f"[DRAFT LOAD] Flattened data has {len(lot_keys)} lot-prefixed keys")
                                    if lot_keys:
                                        logging.info(f"[DRAFT LOAD] Sample lot keys: {lot_keys[:5]}")
                                    
                                    # Check if we're in general mode (no lots)
                                    has_lots = loaded_data.get('lotsInfo', {}).get('hasLots', False)
                                    logging.info(f"[DRAFT LOAD] has_lots from lotsInfo: {has_lots}")
                                    
                                    # If we have lots in the data but lotsInfo.hasLots is False, fix it
                                    if 'lots' in loaded_data and isinstance(loaded_data['lots'], list) and len(loaded_data['lots']) > 0:
                                        has_lots = True
                                        st.session_state['lotsInfo.hasLots'] = True
                                        logging.info(f"[DRAFT LOAD] Corrected has_lots to True based on lots data")
                                    
                                    for key, value in flattened_data.items():
                                        # Don't add general prefix to lot keys even if has_lots is False
                                        # (lot keys should be preserved as-is)
                                        if key.startswith('lot_'):
                                            st.session_state[key] = value
                                        # In general mode, add "general." prefix to form fields
                                        elif not has_lots and not key.startswith('general.'):
                                            # Skip special keys that shouldn't have prefix
                                            special_keys = ['lots', 'lot_names', 'lot_mode', 'current_lot_index', 
                                                          'lotsInfo.hasLots', 'current_step', 'completed_steps']
                                            if key not in special_keys and not key.startswith('_'):
                                                # Add general. prefix for form fields in general mode
                                                st.session_state[f'general.{key}'] = value
                                            else:
                                                st.session_state[key] = value
                                        else:
                                            st.session_state[key] = value
                                    
                                    st.session_state.current_draft_id = draft['id']
                                    
                                    # Ensure lot configuration is properly set if we have lots
                                    if st.session_state.get('lot_mode') == 'multiple':
                                        # Set current lot index if not already set
                                        if 'current_lot_index' not in st.session_state:
                                            st.session_state['current_lot_index'] = 0
                                        logging.info(f"[DRAFT LOAD] Set lot configuration: mode={st.session_state.get('lot_mode')}, index={st.session_state.get('current_lot_index')}")
                                    
                                    # Restore step if saved
                                    if '_save_metadata' in loaded_data:
                                        metadata = loaded_data['_save_metadata']
                                        if 'current_step' in metadata:
                                            st.session_state.current_step = metadata['current_step']
                                    
                                    # Mark all steps with data as completed for navigation
                                    steps = get_dynamic_form_steps(st.session_state)
                                    import logging
                                    logging.info(f"[DRAFT LOAD] After loading, have {len(steps)} total steps")
                                    logging.info(f"[DRAFT LOAD] lot_mode: {st.session_state.get('lot_mode')}")
                                    logging.info(f"[DRAFT LOAD] Number of lots: {len(st.session_state.get('lots', []))}")
                                    logging.info(f"[DRAFT LOAD] lotsInfo.hasLots: {st.session_state.get('lotsInfo.hasLots')}")
                                    logging.info(f"[DRAFT LOAD] lot_names: {st.session_state.get('lot_names')}")
                                    logging.info(f"[DRAFT LOAD] First 3 steps: {steps[:3] if steps else 'No steps'}")
                                    
                                    # Log all keys starting with lot_
                                    lot_keys = [k for k in st.session_state.keys() if k.startswith('lot_')]
                                    logging.info(f"[DRAFT LOAD] Found {len(lot_keys)} lot_ keys in session state")
                                    if lot_keys:
                                        logging.info(f"[DRAFT LOAD] First 10 lot keys: {lot_keys[:10]}")
                                    
                                    completed_steps = {}
                                    
                                    for i, step_keys in enumerate(steps):
                                        # Check if step has any data
                                        has_data = False
                                        for key in step_keys:
                                            # Check various key patterns
                                            if has_lots:
                                                # Lot mode - check lot-specific keys
                                                if st.session_state.get(key):
                                                    has_data = True
                                                    break
                                            else:
                                                # General mode - check with general. prefix
                                                check_keys = [
                                                    f'general.{key}',
                                                    key
                                                ]
                                                for check_key in check_keys:
                                                    # Check if there's any nested data
                                                    for session_key in st.session_state.keys():
                                                        if session_key.startswith(check_key):
                                                            value = st.session_state.get(session_key)
                                                            if value and value not in [False, '', 0, []]:
                                                                has_data = True
                                                                break
                                                    if has_data:
                                                        break
                                            if has_data:
                                                break
                                        
                                        if has_data:
                                            completed_steps[i] = True
                                    
                                    st.session_state.completed_steps = completed_steps
                                    
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
    
    # Render quick navigation in sidebar
    render_quick_navigation()
    
    # Render lot navigation in sidebar (Rule of Three: Location 3)
    render_lot_sidebar()
    
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
        # Ensure progress percentage is between 0 and 1
        progress_percentage = min(1.0, current_step_num / total_steps)
        # Show accurate step count even if it exceeds expected total
        st.progress(progress_percentage, text=f"{get_text('progress')}: {current_step_num}/{max(total_steps, current_step_num)}")
        
        # Lot visibility header (Rule of Three: Location 1)
        render_lot_header()
        
        # Step navigation breadcrumbs
        render_step_breadcrumbs()

        # Get properties for the current step and render the form
        # Protect against IndexError if current_step is out of range
        if st.session_state.current_step < 0:
            st.error(f"Step index {st.session_state.current_step} is negative. Resetting to step 0.")
            st.session_state.current_step = 0
            st.rerun()
        elif st.session_state.current_step >= len(dynamic_form_steps):
            st.error(f"Step index {st.session_state.current_step} is out of range. Maximum step is {len(dynamic_form_steps) - 1}.")
            st.write(f"Debug: dynamic_form_steps has {len(dynamic_form_steps)} steps: {[i for i in range(len(dynamic_form_steps))]}")
            st.session_state.current_step = len(dynamic_form_steps) - 1  # Reset to last valid step
            st.rerun()
            
        current_step_keys = dynamic_form_steps[st.session_state.current_step]
        
        # Get lot context for current step
        lot_context = get_current_lot_context(current_step_keys)
        
        # Debug edit mode
        if st.session_state.get('edit_mode'):
            import logging
            logging.info(f"=== EDIT MODE DEBUG ===")
            logging.info(f"Current step keys: {current_step_keys}")
            logging.info(f"Lot context: {lot_context}")
            logging.info(f"Lot mode in session: {st.session_state.get('lot_mode', 'NOT SET')}")
            # Check for sample data
            test_key = 'general.clientInfo.name' if lot_context['mode'] == 'general' else 'clientInfo.name'
            logging.info(f"Looking for key: {test_key}")
            if test_key in st.session_state:
                logging.info(f"Found: {st.session_state[test_key]}")
            else:
                logging.info(f"NOT FOUND in session state")
        
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
                # Use dot notation: lot_0.orderType -> orderType
                original_key = key.split('.', 1)[1] if '.' in key else key
                if original_key in st.session_state.schema["properties"]:
                    # Copy the schema property 
                    prop_copy = st.session_state.schema["properties"][original_key].copy()
                    
                    # If this property has a $ref, resolve it and merge properties
                    if "$ref" in prop_copy:
                        ref_definition = resolve_schema_ref(st.session_state.schema, prop_copy["$ref"])
                        if ref_definition and "properties" in ref_definition:
                            # Merge the referenced properties into prop_copy
                            prop_copy["properties"] = ref_definition["properties"]
                            # Ensure type is set to object
                            prop_copy["type"] = "object"
                            # Remove the $ref since we've resolved it
                            del prop_copy["$ref"]
                            
                            # Special debug for orderType
                            if original_key == "orderType":
                                st.write(f"🔍 OrderType after resolution in lot mode:")
                                st.write(f"  - Has $ref: {'$ref' in prop_copy}")
                                st.write(f"  - Has properties: {'properties' in prop_copy}")
                                st.write(f"  - Number of properties: {len(prop_copy.get('properties', {}))}")
                                st.write(f"  - Type field: {prop_copy.get('type')}")
                    
                    # For orderType specifically, remove render_if condition in lot mode
                    # The render_if condition checks hasLots==false which prevents rendering in lot mode
                    if original_key == "orderType":
                        if "render_if" in prop_copy:
                            del prop_copy["render_if"]
                    
                    # Don't remove render_if conditions for other fields - they're needed for nested field visibility
                    # The form renderer will handle lot scoping for the conditions
                    current_step_properties[key] = prop_copy
            else:
                # Regular properties
                if key in st.session_state.schema["properties"]:
                    prop_copy = st.session_state.schema["properties"][key].copy()
                    
                    # If this property has a $ref, resolve it and merge properties
                    if "$ref" in prop_copy:
                        ref_definition = resolve_schema_ref(st.session_state.schema, prop_copy["$ref"])
                        if ref_definition and "properties" in ref_definition:
                            # Merge the referenced properties into prop_copy
                            prop_copy["properties"] = ref_definition["properties"]
                            # Ensure type is set to object
                            prop_copy["type"] = "object"
                            # Remove the $ref since we've resolved it
                            del prop_copy["$ref"]
                            
                            # Special debug for orderType
                            if key == "orderType":
                                st.write(f"🔍 OrderType after resolution in regular mode:")
                                st.write(f"  - Has $ref: {'$ref' in prop_copy}")
                                st.write(f"  - Has properties: {'properties' in prop_copy}")
                                st.write(f"  - Number of properties: {len(prop_copy.get('properties', {}))}")
                                st.write(f"  - Type field: {prop_copy.get('type')}")
                    
                    # For orderType in lot mode or general mode, remove render_if condition
                    # The render_if condition checks hasLots==false which prevents rendering in lot mode
                    if key == "orderType":
                        if "render_if" in prop_copy:
                            del prop_copy["render_if"]
                    
                    current_step_properties[key] = prop_copy
        
        # Debug section to troubleshoot contractInfo visibility
        if st.checkbox("🐛 Show Debug Info", key="debug_toggle"):
            st.write("**Debug Information:**")
            st.write(f"**Current Step:** {st.session_state.current_step + 1} of {len(dynamic_form_steps)}")
            st.write(f"**Step Keys:** {current_step_keys}")
            st.write(f"**Current Step Properties Keys:** {list(current_step_properties.keys())}")
            
            # Check if we're on priceInfo step for debugging validation
            price_info_keys = [k for k in current_step_keys if 'priceInfo' in k]
            if price_info_keys:
                st.checkbox("🔍 Debug price validation", key="debug_price_validation")
                if st.session_state.get('debug_price_validation'):
                    st.write(f"✓ This is a priceInfo step: {price_info_keys}")
                    st.write("**Session state keys for price clause:**")
                    for key in st.session_state:
                        if 'priceInfo' in key and 'priceClause' in key:
                            st.write(f"  - {key}: {st.session_state[key]}")
                    st.write(f"**Current lot index:** {st.session_state.get('current_lot_index', 'Not set')}")
            
            # Check if we're on orderType or lot_*_orderType step
            order_type_keys = [k for k in current_step_keys if 'orderType' in k]
            if order_type_keys:
                st.success(f"✓ This is an orderType step: {order_type_keys}")
                for order_key in order_type_keys:
                    if order_key in current_step_properties:
                        order_props = current_step_properties[order_key]
                        st.write(f"**{order_key} structure:**")
                        st.write(f"  - Has $ref: {'$ref' in order_props}")
                        st.write(f"  - Has type: {'type' in order_props}")
                        if 'type' in order_props:
                            st.write(f"  - Type value: {order_props['type']}")
                        st.write(f"  - Has properties: {'properties' in order_props}")
                        if 'properties' in order_props:
                            prop_count = len(order_props['properties'])
                            st.write(f"  - Number of properties: {prop_count}")
                            if prop_count > 0:
                                st.write("  - First 5 properties:")
                                for prop_name in list(order_props['properties'].keys())[:5]:
                                    st.write(f"    • {prop_name}")
                        else:
                            st.error(f"✗ {order_key} has no properties!")
                        
                        # Show full structure for debugging
                        with st.expander("Full orderType structure"):
                            st.json({k: v for k, v in order_props.items() if k != 'properties'})
                    else:
                        st.error(f"✗ {order_key} NOT in current_step_properties!")
            
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
                        lot_index = int(field_name.split('_')[-1])
                        # Get actual lot name from session state
                        lots = st.session_state.get('lots', [])
                        if lot_index < len(lots):
                            lot_name = lots[lot_index].get('name', f'Sklop {lot_index + 1}') if isinstance(lots[lot_index], dict) else f'Sklop {lot_index + 1}'
                        else:
                            lot_name = f"Sklop {lot_index + 1}"
                        step_name = lot_name
                    elif field_name.startswith("lot_"):
                        # Handle lot_N_fieldName pattern (e.g., lot_0_orderType)
                        parts = field_name.split('_', 2)
                        if len(parts) >= 3:
                            lot_index = int(parts[1])
                            base_field = parts[2]
                            # Get lot name prefix
                            lots = st.session_state.get('lots', [])
                            if lot_index < len(lots):
                                lot_name = lots[lot_index].get('name', f'Sklop {lot_index + 1}') if isinstance(lots[lot_index], dict) else f'Sklop {lot_index + 1}'
                            else:
                                lot_name = f"Sklop {lot_index + 1}"
                            # Map the base field to its display name
                            field_display_name = {
                                "orderType": "Vrsta naročila",
                                "technicalSpecifications": "Tehnične zahteve",
                                "executionDeadline": "Roki izvajanja",
                                "priceInfo": "Informacije o ceni",
                                "inspectionInfo": "Ogledi in pogajanja",
                                "participationAndExclusion": "Pogoji sodelovanja",
                                "financialGuarantees": "Zavarovanja",
                                "merila": "Merila",
                                "selectionCriteria": "Merila izbire",
                                "contractInfo": "Sklepanje pogodbe",
                                "otherInfo": "Dodatne informacije"
                            }.get(base_field, base_field)
                            step_name = f"{lot_name}: {field_display_name}"
                        else:
                            step_name = f"Korak {i+1}"
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
                    elif field_name == "selectionCriteria":
                        step_name = "Merila izbire"
                    elif field_name == "contractInfo":
                        step_name = "Sklepanje pogodbe"
                    elif field_name == "otherInfo":
                        step_name = "Dodatne informacije"
                    elif field_name == "confirmation":
                        step_name = "Potrditev"
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
                # Ensure progress stays within [0.0, 1.0] range
                if len(form_steps) > 0:
                    progress = min(1.0, max(0.0, (st.session_state.current_step + 1) / len(form_steps)))
                else:
                    progress = 0.0
                st.progress(progress)
                st.write(f"Korak {st.session_state.current_step + 1} od {len(form_steps)}: {step_names[st.session_state.current_step] if st.session_state.current_step < len(step_names) else 'Korak'}")
        
        # Story 22.1: Add master validation toggle on first step
        if st.session_state.current_step == 0:
            render_master_validation_toggle()
        
        # Render form with enhanced styling and lot context
        st.markdown('<div class="form-content">', unsafe_allow_html=True)
        
        # Special handling for step 15 - otherInfo
        if 'otherInfo' in current_step_keys:
            # Get the session key for otherInfo field
            session_key = 'otherInfo'
            if lot_context and lot_context['mode'] == 'general':
                session_key = 'general.otherInfo'
            
            # Initialize if not exists
            if session_key not in st.session_state:
                st.session_state[session_key] = ""
            
            # Render the textarea
            st.subheader("Potrditev naročila")
            other_info_value = st.text_area(
                "Dodatne informacije in posebne zahteve",
                value=st.session_state.get(session_key, ""),
                help="Bi nam želeli še kaj sporočiti?",
                height=150,
                key=f"widget_{session_key}"
            )
            
            # Update session state
            if other_info_value != st.session_state.get(session_key):
                st.session_state[session_key] = other_info_value
        else:
            # Render normal form for all other steps including step 14 (contractInfo)
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
    
    /* === LOT VISIBILITY STYLES === */
    .lot-context-header {
        background: #E3F2FD;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        font-weight: 500;
        animation: fadeIn 0.3s ease-out;
    }
    
    .lot-context-header strong {
        color: #1976D2;
    }
    
    .lot-sidebar-section {
        background: var(--gray-50);
        border-radius: var(--radius-md);
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid var(--gray-300);
    }
    
    .lot-sidebar-active {
        background: #E3F2FD !important;
        border-left: 4px solid #2196F3 !important;
        font-weight: 600;
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
        border-radius: var(--radius-md) !important;
    }
    
    .lot-sidebar-completed {
        background: #E8F5E9 !important;
        border-left: 4px solid #4CAF50 !important;
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
        border-radius: var(--radius-md) !important;
    }
    
    .lot-sidebar-pending {
        background: var(--gray-100) !important;
        border-left: 4px solid var(--gray-400) !important;
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
        border-radius: var(--radius-md) !important;
        opacity: 0.8;
    }
    
    .lot-progress-badge {
        background: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
        display: inline-block;
    }
    
    .lot-transition-indicator {
        background: #FFF3CD;
        border-left: 4px solid #FFC107;
        padding: 0.75rem;
        margin: 1rem 0;
        border-radius: var(--radius-md);
        font-size: 0.9rem;
    }
    
    .lot-breadcrumb-active {
        background: #E3F2FD !important;
        border: 2px solid #2196F3 !important;
        font-weight: 600 !important;
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

def render_lot_header():
    """Display lot context header at the top of the form (Rule of Three: Location 1)."""
    if st.session_state.get('lot_mode') == 'multiple':
        lots = st.session_state.get('lots', [])
        current_lot_index = st.session_state.get('current_lot_index', 0)
        
        # Fix TypeError: Handle None case for current_lot_index
        if lots and current_lot_index is not None and current_lot_index < len(lots):
            current_lot = lots[current_lot_index]
            lot_name = current_lot.get('name', f'Sklop {current_lot_index + 1}') if isinstance(current_lot, dict) else f'Sklop {current_lot_index + 1}'
            
            st.markdown(
                f'<div class="lot-context-header">'
                f'🏷️ Trenutno urejate sklop: <strong>{lot_name}</strong>'
                f'</div>',
                unsafe_allow_html=True
            )

def calculate_lot_progress(lot_index):
    """Calculate completion percentage for a specific lot."""
    from config import LOT_SPECIFIC_STEPS, get_dynamic_form_steps
    
    # Get all steps for the form
    steps = get_dynamic_form_steps(st.session_state)
    completed_steps = st.session_state.get('completed_steps', {})
    
    # Count lot-specific steps
    lot_step_count = 0
    lot_completed = 0
    
    for i, step_fields in enumerate(steps):
        # Check if this step belongs to the specific lot
        if step_fields and len(step_fields) > 0:
            first_field = step_fields[0]
            # Check if it's a lot-specific step for this lot index
            if first_field.startswith(f'lot_{lot_index}_') or first_field == f'lot_context_{lot_index}':
                lot_step_count += 1
                if completed_steps.get(i, False):
                    lot_completed += 1
    
    # If no lot-specific steps found, check general lot progress
    if lot_step_count == 0:
        # For single lot or general mode
        total_lot_steps = len(LOT_SPECIFIC_STEPS)
        lot_completed = sum(1 for i, step in enumerate(steps) 
                          if any(field in str(step) for field in ['orderType', 'technicalSpecifications', 'executionDeadline']) 
                          and completed_steps.get(i, False))
        lot_step_count = total_lot_steps
    
    if lot_step_count == 0:
        return 0
    
    return min(100, int((lot_completed / lot_step_count) * 100))

def switch_to_lot(lot_index):
    """Switch to a different lot with validation."""
    # Check for unsaved changes
    if st.session_state.get('unsaved_changes'):
        st.warning("⚠️ Imate neshranjene spremembe. Prosim, shranite pred preklopom.")
        return
    
    # Update current lot index
    st.session_state['current_lot_index'] = lot_index
    st.success(f"Preklop na sklop: {st.session_state.get('lots', [])[lot_index].get('name', f'Sklop {lot_index + 1}')}")
    st.rerun()

def render_lot_sidebar():
    """Display lot navigation in sidebar (Rule of Three: Location 3)."""
    if st.session_state.get('lot_mode') == 'multiple':
        with st.sidebar:
            st.markdown('<div class="lot-sidebar-section">', unsafe_allow_html=True)
            st.markdown("### 📦 Sklopi")
            
            lots = st.session_state.get('lots', [])
            current_lot_index = st.session_state.get('current_lot_index', 0)
            
            for i, lot in enumerate(lots):
                lot_name = lot.get('name', f'Sklop {i+1}') if isinstance(lot, dict) else f'Sklop {i+1}'
                progress = calculate_lot_progress(i)
                
                if i == current_lot_index:
                    # Active lot
                    st.markdown(
                        f'<div class="lot-sidebar-active">'
                        f'📝 <strong>{lot_name}</strong>'
                        f'<span class="lot-progress-badge">{progress}%</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                elif progress == 100:
                    # Completed lot
                    st.markdown(
                        f'<div class="lot-sidebar-completed">'
                        f'✅ {lot_name}'
                        f'<span class="lot-progress-badge">100%</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Pending lot
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"⏳ {lot_name}", key=f"lot_nav_{i}", use_container_width=True):
                            switch_to_lot(i)
                    with col2:
                        st.markdown(f'<small>{progress}%</small>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def get_current_lot_name():
    """Get the name of the current lot being edited."""
    lots = st.session_state.get('lots', [])
    current_lot_index = st.session_state.get('current_lot_index', 0)
    
    # Fix TypeError: Handle None case for current_lot_index
    if lots and current_lot_index is not None and current_lot_index < len(lots):
        lot = lots[current_lot_index]
        if isinstance(lot, dict):
            return lot.get('name', f'Sklop {current_lot_index + 1}')
        else:
            return f'Sklop {current_lot_index + 1}'
    
    return None

def render_step_breadcrumbs():
    """Render step navigation breadcrumbs with lot context highlighting (Rule of Three: Location 2)."""
    from localization import get_dynamic_step_label
    from config import get_dynamic_form_steps
    
    # Get dynamic form steps for breadcrumbs
    dynamic_form_steps = get_dynamic_form_steps(st.session_state)
    
    # Check if lots are enabled
    has_lots = st.session_state.get("lotsInfo.hasLots", False)
    lot_mode = st.session_state.get('lot_mode', 'none')
    
    breadcrumbs_html = '<div class="step-breadcrumbs">'
    
    for i, step_keys in enumerate(dynamic_form_steps):
        step_num = i + 1
        step_label = get_dynamic_step_label(step_keys, step_num, has_lots)
        
        # Check if this is a lot-specific step
        is_lot_step = any(key.startswith('lot_context_') for key in step_keys) if step_keys else False
        
        if i < st.session_state.current_step:
            css_class = "completed"
        elif i == st.session_state.current_step:
            # Highlight lot-specific steps differently
            if is_lot_step and lot_mode == 'multiple':
                css_class = "current lot-breadcrumb-active"
                # Add lot name to breadcrumb
                lot_name = get_current_lot_name()
                if lot_name:
                    step_label = f"{step_label} ({lot_name})"
            else:
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
    # Don't skip for any step - step 15 needs buttons too
    
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
                # Check if we're on a lot_context step - beginning of a new lot
                current_step_fields = dynamic_form_steps[st.session_state.current_step]
                if current_step_fields and len(current_step_fields) > 0:
                    first_field = current_step_fields[0]
                    if first_field.startswith('lot_context_'):
                        # We're at the beginning of a lot - show lot name in button
                        lot_idx = int(first_field.split('_')[-1])
                        lot_names = st.session_state.get('lot_names', [])
                        if lot_idx < len(lot_names):
                            lot_name = lot_names[lot_idx]
                            button_text = f"Začni vnos: {lot_name} →"
                        else:
                            button_text = f"{get_text('next_button')} →"
                    else:
                        button_text = f"{get_text('next_button')} →"
                else:
                    button_text = f"{get_text('next_button')} →"
                    
                if st.button(
                    button_text, 
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
                        # Mark current step as completed
                        current = st.session_state.current_step
                        lot_id = st.session_state.get('current_lot') if st.session_state.get('lot_mode') == 'multiple' else None
                        mark_step_completed(current, lot_id)
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
                                    # Clear edit mode and return to dashboard immediately
                                    st.session_state.edit_mode = False
                                    st.session_state.edit_record_id = None
                                    # Clear current draft ID if it exists
                                    if 'current_draft_id' in st.session_state:
                                        del st.session_state['current_draft_id']
                                    # Clear form data and navigate to dashboard
                                    clear_form_data()
                                    st.session_state.current_page = 'dashboard'
                                    st.rerun()
                                else:
                                    st.error("❌ Napaka pri posodabljanju naročila")
                            else:
                                # Create new procurement
                                new_id = database.create_procurement(final_form_data)
                                if new_id:
                                    st.success(f"✅ Javno naročilo uspešno ustvarjeno! ID: {new_id}")
                                    # Clear current draft ID since procurement is now saved
                                    if 'current_draft_id' in st.session_state:
                                        del st.session_state['current_draft_id']
                                    # Clear form data and navigate to dashboard immediately
                                    clear_form_data()
                                    st.session_state.current_page = 'dashboard'
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
                        st.session_state['lot_mode'] = 'multiple' if len(v) > 0 else 'none'
                        # Also set lotsInfo.hasLots for proper form configuration
                        if len(v) > 0:
                            st.session_state['lotsInfo.hasLots'] = True
                        
                        # Extract lot names
                        lot_names = [lot.get('name', f'Sklop {i+1}') for i, lot in enumerate(v)]
                        st.session_state['lot_names'] = lot_names
                        
                        # Flatten each lot's data into lot-scoped keys
                        for i, lot in enumerate(v):
                            for lot_key, lot_value in lot.items():
                                if lot_key == 'name':
                                    continue  # Skip name as it's already in lot_names
                                elif not isinstance(lot_value, dict):
                                    # Store with regular prefix
                                    items.append((f'lot_{i}.{lot_key}', lot_value))
                                    # Also store with double prefix for compatibility
                                    if lot_key.startswith('orderType') or lot_key in ['technicalSpecifications', 'executionDeadline']:
                                        items.append((f'lot_{i}.lot_{i}_{lot_key}', lot_value))
                                elif isinstance(lot_value, dict):
                                    # Recursively flatten nested lot data
                                    nested_items = flatten_dict(lot_value, f'lot_{i}.{lot_key}', sep=sep)
                                    items.extend(nested_items.items())
                                    # Also handle double-prefix pattern for nested fields
                                    # Include all nested orderType fields (customers, cofinancers, etc.)
                                    if lot_key == 'orderType':
                                        double_nested = flatten_dict(lot_value, f'lot_{i}.lot_{i}_{lot_key}', sep=sep)
                                        items.extend(double_nested.items())
                                        # Also handle without double prefix for nested fields
                                        for nested_key, nested_value in lot_value.items():
                                            if isinstance(nested_value, list):
                                                # Handle arrays like customers, cofinancers
                                                st.session_state[f'lot_{i}.{lot_key}.{nested_key}'] = nested_value
                                            elif isinstance(nested_value, dict):
                                                # Further nested objects
                                                nested_flat = flatten_dict(nested_value, f'lot_{i}.{lot_key}.{nested_key}', sep=sep)
                                                items.extend(nested_flat.items())
                                    elif lot_key in ['technicalSpecifications', 'executionDeadline']:
                                        double_nested = flatten_dict(lot_value, f'lot_{i}.lot_{i}_{lot_key}', sep=sep)
                                        items.extend(double_nested.items())
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
            
            # Check if we're in general mode (no lots)
            has_lots = loaded_data.get('lotsInfo', {}).get('hasLots', False)
            
            for key, value in flattened_data.items():
                # In general mode, add "general." prefix to form fields
                if not has_lots and not key.startswith('lot_') and not key.startswith('general.'):
                    # Skip special keys that shouldn't have prefix
                    special_keys = ['lots', 'lot_names', 'lot_mode', 'current_lot_index', 
                                  'lotsInfo.hasLots', 'current_step', 'completed_steps']
                    if key not in special_keys and not key.startswith('_'):
                        # Add general. prefix for form fields in general mode
                        st.session_state[f'general.{key}'] = value
                    else:
                        st.session_state[key] = value
                else:
                    st.session_state[key] = value
            
            # Restore metadata if present
            if '_save_metadata' in loaded_data:
                metadata = loaded_data['_save_metadata']
                if 'current_step' in metadata:
                    st.session_state.current_step = metadata['current_step']
            
            # Mark all steps with data as completed for navigation
            # Need to import here as we're not in render_main_form scope
            from config import get_dynamic_form_steps
            steps = get_dynamic_form_steps(st.session_state)
            completed_steps = {}
            
            for i, step_keys in enumerate(steps):
                # Check if step has any data
                has_data = False
                for key in step_keys:
                    # Handle lot context steps (always mark as completed if lot exists)
                    if key.startswith('lot_context_'):
                        lot_idx = int(key.split('_')[-1])
                        if lot_idx < len(st.session_state.get('lot_names', [])):
                            has_data = True
                            break
                    
                    # Check various key patterns
                    if has_lots:
                        # Lot mode - check lot-specific keys with different patterns
                        patterns_to_check = [
                            key,  # Direct key
                            f'{key}.',  # Key prefix for nested fields
                        ]
                        
                        # For lot-specific fields, also check without lot_ prefix
                        if key.startswith('lot_'):
                            # Extract base field name
                            parts = key.split('_', 2)
                            if len(parts) >= 3:
                                lot_idx = parts[1]
                                field_name = parts[2]
                                patterns_to_check.extend([
                                    f'lot_{lot_idx}.{field_name}',
                                    f'lot_{lot_idx}.lot_{lot_idx}_{field_name}',
                                ])
                        
                        for pattern in patterns_to_check:
                            for session_key in st.session_state.keys():
                                if session_key == pattern or session_key.startswith(f'{pattern}.'):
                                    value = st.session_state.get(session_key)
                                    if value and value not in [False, '', 0, []]:
                                        has_data = True
                                        break
                            if has_data:
                                break
                    else:
                        # General mode - check with general. prefix
                        check_keys = [
                            f'general.{key}',
                            key
                        ]
                        for check_key in check_keys:
                            # Check if there's any nested data
                            for session_key in st.session_state.keys():
                                if session_key.startswith(check_key):
                                    value = st.session_state.get(session_key)
                                    if value and value not in [False, '', 0, []]:
                                        has_data = True
                                        break
                            if has_data:
                                break
                    if has_data:
                        break
                
                if has_data:
                    completed_steps[i] = True
            
            st.session_state.completed_steps = completed_steps
            
            # Story 28.3: Store form_id for file loading
            st.session_state.form_id = selected_draft_id
            st.session_state.current_draft_id = selected_draft_id
            st.success(get_text("draft_loaded"))
            st.rerun()
        else:
            st.error(get_text("draft_load_error"))

if __name__ == "__main__":
    main()
