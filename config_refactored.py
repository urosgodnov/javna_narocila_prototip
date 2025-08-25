"""Refactored configuration for new lot system - Phase 1."""
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
    # Step 6: Order type
    ["orderType"],
    
    # Step 7: Technical specifications
    ["technicalSpecifications"],
    
    # Step 8: Execution deadline
    ["executionDeadline"],
    
    # Step 9: Price info
    ["priceInfo"],
    
    # Step 10: Inspection and negotiations
    ["inspectionInfo", "negotiationsInfo"],
    
    # Step 11: Participation criteria
    ["participationAndExclusion", "participationConditions"],
    
    # Step 12: Financial and variant offers
    ["financialGuarantees", "variantOffers"],
    
    # Step 13: Selection criteria
    ["selectionCriteria"],
    
    # Step 14: Contract info and additional info (last step per lot)
    ["contractInfo", "otherInfo"]
]

def get_dynamic_form_steps_refactored(session_state):
    """
    Generate dynamic form steps based on the NEW lot configuration approach.
    
    Key differences from old system:
    1. Lot configuration only collects names
    2. Procurement details are entered after configuration
    3. Supports lot iteration with "Nov sklop" functionality
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
        lots = session_state.get("lot_names", [])
        if len(lots) > 1:
            lot_mode = "multiple"
        elif len(lots) == 1:
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
        # After lot config, add procurement steps once
        steps.extend(LOT_SPECIFIC_STEPS)
        
    elif lot_mode == "single":
        # Single lot - add procurement steps once after config
        steps.extend(LOT_SPECIFIC_STEPS)
        
    elif lot_mode == "multiple":
        
        # Get current lot being edited
        current_lot_index = session_state.get("current_lot_index", 0)
        lot_names = session_state.get("lot_names", [])
        
        # Only add lot-specific steps if we have configured lots
        if lot_names and current_lot_index is not None and current_lot_index < len(lot_names):
            # Add lot header/context indicator
            steps.append([f"lot_context_{current_lot_index}"])
            
            # Add all procurement steps for current lot
            for step in LOT_SPECIFIC_STEPS:
                # Prefix each field with lot index
                lot_step = [f"lot_{current_lot_index}_{field}" for field in step]
                steps.append(lot_step)
    
    return steps

def is_final_lot_step(session_state, current_step):
    """Check if we're on the final step of a lot."""
    steps = get_dynamic_form_steps_refactored(session_state)
    
    # Check if this is the last step
    if current_step != len(steps) - 1:
        return False
    
    # Check if we're in multi-lot mode
    lot_mode = session_state.get("lot_mode", "none")
    if lot_mode != "multiple":
        return False
    
    return True

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
    lot_names = session_state.get("lot_names", [])
    total_lots = len(lot_names)
    
    # Always have save button
    buttons.append(("Shrani", "save", "secondary"))
    
    if current_lot_index < total_lots - 1:
        # More configured lots to fill
        next_lot_name = lot_names[current_lot_index + 1]
        buttons.append((f"Nadaljuj s: {next_lot_name}", "next_lot", "primary"))
    
    # Option to add new lot
    buttons.append(("Nov sklop", "new_lot", "secondary"))
    
    # Option to finish
    if current_lot_index == total_lots - 1:
        buttons.append(("Zaključi vnos", "submit", "primary"))
    
    return buttons

# Schema file path
SCHEMA_FILE = "json_files/SEZNAM_POTREBNIH_PODATKOV.json"

# Log retention configuration (unchanged)
LOG_RETENTION_HOURS = {
    'CRITICAL': 720,  # 30 days
    'ERROR': 168,     # 7 days
    'WARNING': 72,    # 3 days
    'INFO': 24,       # 1 day
    'DEBUG': 6        # 6 hours
}

SPECIAL_LOG_RETENTION = {
    'form_submission': 720,      # 30 days for audit trail
    'validation_error': 72,       # 3 days for pattern analysis
    'admin_action': 720,          # 30 days for security audit
    'login_event': 168,           # 7 days for security review
    'system_maintenance': 24      # 1 day for maintenance logs
}