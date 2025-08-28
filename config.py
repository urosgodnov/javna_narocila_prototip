"""Configuration constants and environment variables - Unified version."""
import os
from dotenv import load_dotenv

load_dotenv()

# Admin authentication
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Base form steps - always included (shared across all lots)
BASE_STEPS = [
    # Step 1: Client information
    ["clientInfo"],
    
    # Step 2: Basic project info
    ["projectInfo"],
    
    # Step 3: Legal basis
    ["legalBasis"],
    
    # Step 4: Submission procedure and lots decision
    ["submissionProcedure", "lotsInfo"],
]

# Step 5: Lot configuration (ONLY lot names, no procurement details)
LOT_CONFIG_STEP = ["lotConfiguration"]

# Steps that are repeated per lot (or used once if no lots)
LOT_SPECIFIC_STEPS = [
    # Order type (per lot or general)
    ["orderType"],
    
    # Technical specifications (per lot)
    ["technicalSpecifications"],
    
    # Execution deadline (per lot)
    ["executionDeadline"],
    
    # Price info (per lot)
    ["priceInfo"],
    
    # Inspection and negotiations (per lot)
    ["inspectionInfo", "negotiationsInfo"],
    
    # Participation criteria (per lot)
    ["participationAndExclusion", "participationConditions"],
    
    # Financial and variant offers (per lot)
    ["financialGuarantees", "variantOffers"],
    
    # Selection criteria (per lot)
    ["selectionCriteria"],
]

# Final steps - always included at the end
FINAL_STEPS = [
    # Contract info
    ["contractInfo"],
    # Additional info with submit button
    ["otherInfo"]
]

# For backward compatibility - single final step
FINAL_STEP = ["otherInfo"]

def get_dynamic_form_steps(session_state):
    """Generate dynamic form steps based on lots configuration.
    
    Unified version that handles both old and new lot systems.
    """
    steps = BASE_STEPS.copy()
    
    # Check lot mode from lotsInfo checkbox
    has_lots = session_state.get("lotsInfo.hasLots", False)
    lot_mode = session_state.get("lot_mode", "none")  # 'none', 'single', 'multiple'
    
    # Only add lot configuration step if user selected to have lots
    if has_lots:
        # Add lot configuration step
        steps.append(LOT_CONFIG_STEP)
        
        # Determine lot mode based on configured lots
        lots = session_state.get("lots", [])
        lot_names = session_state.get("lot_names", [])
        
        # Use lot_names if available (new system) or lots (old system)
        if lot_names:
            num_lots = len(lot_names)
        elif lots:
            num_lots = len(lots)
        else:
            num_lots = 0
            
        if num_lots > 1:
            lot_mode = "multiple"
        elif num_lots == 1:
            lot_mode = "single"
        else:
            # User wants lots but hasn't configured them yet
            lot_mode = "none"  # Will change after configuration
        session_state["lot_mode"] = lot_mode
    else:
        # No lots - proceed with general procurement
        lot_mode = "none"
        session_state["lot_mode"] = lot_mode
    
    if lot_mode == "none":
        # No lots - add procurement steps once for general
        steps.extend(LOT_SPECIFIC_STEPS)
        
    elif lot_mode == "single":
        # Single lot - add procurement steps once
        steps.extend(LOT_SPECIFIC_STEPS)
        
    elif lot_mode == "multiple":
        # Multiple lots handling
        current_lot_index = session_state.get("current_lot_index", 0)
        
        # Check if we're loading a draft, in edit mode, or need all steps
        is_loading_draft = session_state.get("current_draft_id") is not None
        is_edit_mode = session_state.get("edit_mode", False)
        show_all_lots = session_state.get("show_all_lot_steps", False)
        
        # Determine which lots to show steps for
        if is_loading_draft or is_edit_mode or show_all_lots:
            # Show steps for ALL lots (for navigation and editing)
            lots_to_show = range(num_lots)
        else:
            # Normal mode: Only show current lot's steps
            lots_to_show = [current_lot_index] if current_lot_index < num_lots else []
        
        # Add steps for each lot to show
        for i in lots_to_show:
            # Add lot context step (shows lot name/header)
            steps.append([f"lot_context_{i}"])
            
            # Add all procurement steps for this lot
            for step in LOT_SPECIFIC_STEPS:
                # Prefix each field with lot index
                lot_step = [f"lot_{i}_{field}" for field in step]
                steps.append(lot_step)
    
    # Always add final steps at the end
    steps.extend(FINAL_STEPS)
    
    return steps

# Alias for backward compatibility with refactored version
get_dynamic_form_steps_refactored = get_dynamic_form_steps

# Backward compatibility - static steps list
FORM_STEPS = BASE_STEPS + LOT_SPECIFIC_STEPS + FINAL_STEPS

# Schema file path
SCHEMA_FILE = "json_files/SEZNAM_POTREBNIH_PODATKOV.json"

# ============ LOGGING CONFIGURATION ============

# Log retention hours by level
LOG_RETENTION_HOURS = {
    'CRITICAL': 720,  # 30 days
    'ERROR': 168,     # 7 days
    'WARNING': 72,    # 3 days
    'INFO': 24,       # 1 day
    'DEBUG': 12       # 12 hours
}

# Default log level
DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Log file settings
LOG_DIR = 'logs'
LOG_FILE = 'app.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# ============ FEATURE FLAGS ============

# Enable/disable specific features
ENABLE_AI_SUGGESTIONS = os.getenv('ENABLE_AI_SUGGESTIONS', 'true').lower() == 'true'
ENABLE_DOCUMENT_GENERATION = os.getenv('ENABLE_DOCUMENT_GENERATION', 'true').lower() == 'true'
ENABLE_DRAFT_AUTOSAVE = os.getenv('ENABLE_DRAFT_AUTOSAVE', 'false').lower() == 'true'

# ============ UI CONFIGURATION ============

# Maximum file upload size (in MB)
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))

# Number of items per page in lists
ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '10'))

# ============ HELPER FUNCTIONS ============

def is_final_lot_step(session_state, current_step):
    """Check if we're on the final step of a lot."""
    steps = get_dynamic_form_steps(session_state)
    
    # Check if this is the last step before the next lot context
    # or before the final steps
    if current_step >= len(steps) - 1:
        return False
    
    current_step_fields = steps[current_step]
    next_step_fields = steps[current_step + 1]
    
    # Check if next step is a lot context or final step
    if next_step_fields and len(next_step_fields) > 0:
        next_field = next_step_fields[0]
        if next_field.startswith('lot_context_') or next_field in ['contractInfo', 'otherInfo']:
            return True
    
    return False

def get_next_lot_index(session_state):
    """Get the index of the next lot to process."""
    current_lot_index = session_state.get("current_lot_index", 0)
    lot_names = session_state.get("lot_names", [])
    
    if current_lot_index < len(lot_names) - 1:
        return current_lot_index + 1
    return None

def get_lot_navigation_buttons(session_state):
    """
    Get navigation buttons for lot iteration.
    Returns list of (button_text, action, button_type)
    """
    buttons = []
    lot_mode = session_state.get("lot_mode", "none")
    
    if lot_mode != "multiple":
        # Standard navigation for non-lot or single lot
        return [("Potrdi in zaključi", "submit", "primary")]
    
    current_lot_index = session_state.get("current_lot_index", 0)
    if current_lot_index is None:
        current_lot_index = 0
    
    lot_names = session_state.get("lot_names", [])
    if lot_names is None:
        lot_names = []
    
    total_lots = len(lot_names)
    
    # Always have save button
    buttons.append(("Shrani", "save", "secondary"))
    
    if current_lot_index < total_lots - 1:
        # More configured lots to fill
        # When we're starting a lot section, show the current lot name, not the next
        current_lot_name = lot_names[current_lot_index] if current_lot_index < len(lot_names) else f"Sklop {current_lot_index + 1}"
        next_lot_name = lot_names[current_lot_index + 1]
        
        # Check if we're at the beginning of a lot's data entry
        # This happens right after lot configuration or after completing a previous lot
        if not session_state.get(f"lot_{current_lot_index}_data_started", False):
            # Show we're starting the current lot
            buttons.append((f"Začni vnos: {current_lot_name}", "start_current_lot", "primary"))
        else:
            # We're in the middle of a lot, show next lot button
            buttons.append((f"Nadaljuj s: {next_lot_name}", "next_lot", "primary"))
    
    # Option to finish
    if current_lot_index == total_lots - 1:
        buttons.append(("Zaključi vnos", "submit", "primary"))
    
    return buttons