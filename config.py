"""Configuration constants and environment variables - Unified version."""
import os
from dotenv import load_dotenv

load_dotenv()

# Admin authentication
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "potocnikgodnov2025!")

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
    # UNIFIED LOT ARCHITECTURE: Default to 'single' instead of 'none'
    lot_mode = session_state.get("lot_mode", "single")  # 'single', 'multiple'
    
    # Also check if lot fields exist in session state (for cases where hasLots might be incorrect)
    # This happens when editing forms that have lot data but hasLots is False
    has_lot_fields = any(k.startswith('lot_0') or k.startswith('lot_1') or k.startswith('lot_2') 
                         for k in session_state.keys())
    
    # If we detect lot fields, assume lots exist
    if has_lot_fields and not has_lots:
        has_lots = True
        session_state["lotsInfo.hasLots"] = True
    
    # Handle lot configuration (now integrated into lotsInfo step)
    if has_lots:
        # Determine lot mode based on configured lots
        lots = session_state.get("lots", [])
        lot_names = session_state.get("lot_names", [])
        
        # Use lot_names if available (new system) or lots (old system)
        if lot_names:
            num_lots = len(lot_names)
        elif lots:
            num_lots = len(lots)
        else:
            # Check for lot fields to determine number of lots
            lot_indices = set()
            for key in session_state.keys():
                if key.startswith('lot_'):
                    # Extract lot index from keys like lot_0.something or lot_1_something
                    parts = key.split('_')
                    if len(parts) > 1 and parts[1].isdigit():
                        lot_indices.add(int(parts[1]))
                    elif len(parts) > 1 and '.' in key:
                        # Handle lot_0.field format
                        lot_part = key.split('.')[0]
                        if '_' in lot_part:
                            idx = lot_part.split('_')[1]
                            if idx.isdigit():
                                lot_indices.add(int(idx))
            
            num_lots = len(lot_indices) if lot_indices else 0
            
            # If we found lot indices but no lots array, create placeholder lots
            if num_lots > 0 and not lots:
                session_state["lots"] = [{"name": f"Sklop {i+1}"} for i in range(num_lots)]
            
        if num_lots > 1:
            lot_mode = "multiple"
        elif num_lots == 1:
            lot_mode = "single"
        else:
            # User wants lots but hasn't configured them yet
            # UNIFIED LOT ARCHITECTURE: Use 'single' as default
            lot_mode = "single"  # Will change after configuration
        session_state["lot_mode"] = lot_mode
    else:
        # No lots - proceed with general procurement
        # UNIFIED LOT ARCHITECTURE: Always use 'single' for forms without explicit lots
        lot_mode = "single"
        session_state["lot_mode"] = lot_mode
    
    # UNIFIED LOT ARCHITECTURE: Treat 'single' as the base case (was 'none')
    if lot_mode == "single" and not has_lots:
        # No lots - add procurement steps once for general
        steps.extend(LOT_SPECIFIC_STEPS)
        # Add final steps (contractInfo and otherInfo)
        steps.extend(FINAL_STEPS)
        
    elif lot_mode == "single":
        # Single lot - add procurement steps once
        steps.extend(LOT_SPECIFIC_STEPS)
        # Add final steps (contractInfo and otherInfo)
        steps.extend(FINAL_STEPS)
        
    elif lot_mode == "multiple":
        # Multiple lots handling
        current_lot_index = session_state.get("current_lot_index", 0)
        
        # Check if we're loading a draft, in edit mode, or need all steps
        is_loading_draft = session_state.get("current_draft_id") is not None
        is_edit_mode = session_state.get("edit_mode", False)
        show_all_lots = session_state.get("show_all_lot_steps", False)
        
        import logging
        logging.info(f"[get_dynamic_form_steps] lot_mode=multiple, current_lot={current_lot_index}, "
                    f"is_loading_draft={is_loading_draft}, is_edit_mode={is_edit_mode}, "
                    f"show_all_lots={show_all_lots}, num_lots={num_lots}")
        
        # Important: For normal form filling, we should ONLY show current lot steps
        # to prevent premature lot switching
        if is_edit_mode:
            # Edit mode: show all lots for navigation
            lots_to_show = range(num_lots)
        elif is_loading_draft:
            # Draft loading: temporarily show all, but should revert after load
            lots_to_show = range(num_lots)
            # Clear the draft flag after initial load
            if session_state.get("draft_loaded"):
                session_state["current_draft_id"] = None
        else:
            # Normal mode: ALWAYS show ALL lots to ensure proper navigation
            # This ensures contractInfo and otherInfo are always accessible
            lots_to_show = range(num_lots)
        
        # Add steps for each lot to show
        for i, lot_idx in enumerate(lots_to_show):
            # Add lot context step (shows lot name/header)
            steps.append([f"lot_context_{lot_idx}"])
            
            # Add all procurement steps for this lot
            for step in LOT_SPECIFIC_STEPS:
                # Prefix each field with lot index using dot notation for consistency
                lot_step = [f"lot_{lot_idx}.{field}" for field in step]
                steps.append(lot_step)
            
            # Add contractInfo and otherInfo after EACH lot
            # These are lot-specific final steps that should be prefixed with lot index
            import logging
            logging.info(f"[get_dynamic_form_steps] Adding lot-specific FINAL_STEPS for lot_{lot_idx}")
            for step in FINAL_STEPS:
                # Prefix FINAL_STEPS with lot index for consistency
                lot_final_step = [f"lot_{lot_idx}.{field}" for field in step]
                steps.append(lot_final_step)
    
    # Log the final steps configuration
    import logging
    
    logging.info(f"[get_dynamic_form_steps] Total steps: {len(steps)}")
    logging.info(f"[get_dynamic_form_steps] Last 3 steps: {steps[-3:] if len(steps) >= 3 else steps}")
    
    return steps

# Alias for backward compatibility with refactored version
get_dynamic_form_steps_refactored = get_dynamic_form_steps

# Backward compatibility - static steps list
FORM_STEPS = BASE_STEPS + LOT_SPECIFIC_STEPS + FINAL_STEPS

# Fixed form steps - always shown in the same order
FIXED_STEPS = [
    # Step 1: Podatki o naročniku
    ["clientInfo"],
    
    # Step 2: Osnovni podatki naročila
    ["projectInfo"],
    
    # Step 3: Pravna podlaga
    ["legalBasis"],
    
    # Step 4: Postopek oddaje
    ["submissionProcedure"],
    
    # Step 5: Konfiguracija sklopov
    ["lotsInfo"],
    
    # Step 6: Vrsta naročila
    ["orderType"],
    
    # Step 7: Tehnične zahteve
    ["technicalSpecifications"],
    
    # Step 8: Roki izvajanja
    ["executionDeadline"],
    
    # Step 9: Informacije o ceni
    ["priceInfo"],
    
    # Step 10: Ogledi in pogajanja
    ["inspectionInfo", "negotiationsInfo"],
    
    # Step 11: Pogoji za sodelovanje (SEPARATED - only conditions)
    ["participationConditions"],
    
    # Step 12: Razlogi za izključitev (SEPARATED - only exclusions)
    ["participationAndExclusion"],
    
    # Step 13: Zavarovanja in ponudbe (was Step 12)
    ["financialGuarantees", "variantOffers"],
    
    # Step 14: Merila izbire (was Step 13)
    ["selectionCriteria"],
    
    # Step 15: Sklepanje pogodbe (was Step 14)
    ["contractInfo"],
    
    # Step 16: Potrditev (was Step 15)
    ["otherInfo"]
]

def get_fixed_steps():
    """Return the fixed list of form steps."""
    return FIXED_STEPS.copy()

def get_step_name(step_index):
    """Get readable name for a step."""
    step_names = {
        0: "Podatki o naročniku",
        1: "Osnovni podatki naročila", 
        2: "Pravna podlaga",
        3: "Postopek oddaje",
        4: "Konfiguracija sklopov",
        5: "Vrsta naročila",
        6: "Tehnične zahteve",
        7: "Roki izvajanja",
        8: "Informacije o ceni",
        9: "Ogledi in pogajanja",
        10: "Pogoji za sodelovanje",      # Step 11 - only conditions
        11: "Pogoji za izključitev",      # Step 12 - only exclusions  
        12: "Zavarovanja in ponudbe",     # Was Step 12, now Step 13
        13: "Merila izbire",              # Was Step 13, now Step 14
        14: "Sklepanje pogodbe",          # Was Step 14, now Step 15
        15: "Potrditev"                   # Was Step 15, now Step 16
    }
    return step_names.get(step_index, f"Korak {step_index + 1}")

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
    # SIMPLE LOGIC: After selectionCriteria ALWAYS comes contractInfo
    # Never show lot navigation buttons after selectionCriteria
    # This function should ALWAYS return False
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
    import logging
    
    buttons = []
    # UNIFIED LOT ARCHITECTURE: Default to 'single' instead of 'none'
    lot_mode = session_state.get("lot_mode", "single")
    
    if lot_mode != "multiple":
        # Standard navigation for non-lot or single lot
        return []  # Return empty - let normal navigation handle it
    
    current_lot_index = session_state.get("current_lot_index", 0)
    if current_lot_index is None:
        current_lot_index = 0
    
    lot_names = session_state.get("lot_names", [])
    if lot_names is None:
        lot_names = []
    
    total_lots = len(lot_names)
    
    logging.info(f"[get_lot_navigation_buttons] current_lot={current_lot_index}, total_lots={total_lots}")
    
    # If we're on the LAST lot, return empty list - use normal navigation
    if current_lot_index >= total_lots - 1:
        logging.info(f"[get_lot_navigation_buttons] On last lot - returning empty (use normal nav)")
        return []  # Let normal navigation handle contract/final steps
    
    # Always have save button for non-last lots
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
    
    return buttons