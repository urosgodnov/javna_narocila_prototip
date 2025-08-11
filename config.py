"""Configuration constants and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# Admin authentication
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Default for demonstration

# Base form steps - always included
BASE_STEPS = [
    # Step 1: Client information
    ["clientInfo"],
    
    # Step 2: Basic project info
    ["projectInfo"],
    
    # Step 3: Legal basis
    ["legalBasis"],
    
    # Step 4: Submission procedure
    ["submissionProcedure"],
    
    # Step 5: Lots configuration
    ["lotsInfo", "lots"],
]

# Steps that are repeated per lot (or used for general lot if no lots)
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
    
    # Additional information and completion
    ["otherInfo"]
]

def get_dynamic_form_steps(session_state):
    """Generate dynamic form steps based on lots configuration."""
    steps = BASE_STEPS.copy()
    
    # Check if lots are configured
    has_lots = session_state.get("lotsInfo.hasLots", False)
    lots = session_state.get("lots", [])
    
    if not has_lots or len(lots) == 0:
        # No lots - treat as general lot
        steps.extend(LOT_SPECIFIC_STEPS)
    else:
        # Per-lot steps
        for i, lot in enumerate(lots):
            lot_name = lot.get("name", f"Sklop {i+1}")
            # Add lot context step
            steps.append([f"lot_context_{i}"])
            # Add all lot-specific steps for this lot
            for step in LOT_SPECIFIC_STEPS:
                lot_step = [f"lot_{i}_{field}" for field in step]
                steps.append(lot_step)
    
    # Add final steps
    steps.extend(FINAL_STEPS)
    
    return steps

# Backward compatibility - will be dynamically generated
FORM_STEPS = BASE_STEPS + LOT_SPECIFIC_STEPS + FINAL_STEPS

# Schema file path
SCHEMA_FILE = "SEZNAM_POTREBNIH_PODATKOV.json"