"""Configuration constants and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# Admin authentication
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Default for demonstration

# Optimized form configuration with better field distribution
FORM_STEPS = [
    # Step 1: Client information (7 fields) - OK
    ["clientInfo"],
    
    # Step 2: Basic project info (reduced) - Without legal basis
    ["projectInfo"],
    
    # Step 3: Legal basis - Now standalone with info icon
    ["legalBasis"],
    
    # Step 4: Submission procedure (2 fields) - Combined with lots
    ["submissionProcedure", "lotsInfo"], # Total: 6 fields
    
    # Step 5: Order type (enum selection) - Standalone for complex logic
    ["orderType"],
    
    # Step 6: Technical specifications - Now standalone with info icon
    ["technicalSpecifications"],
    
    # Step 7: Execution deadline (6 fields) - Standalone
    ["executionDeadline"],
    
    # Step 8: Price info only (7 fields) - Split from overloaded step
    ["priceInfo"],
    
    # Step 9: Inspection and negotiations (10 fields combined) - More manageable
    ["inspectionInfo", "negotiationsInfo"],
    
    # Step 10: Participation criteria - Combined related sections
    ["exclusionReasons", "participationConditions"],
    
    # Step 11: Financial and variant offers (4 fields)
    ["financialGuarantees", "variantOffers"],
    
    # Step 12: Selection criteria (complex section)
    ["selectionCriteria"],
    
    # Step 13: Final contract info (6 fields)
    ["contractInfo"],
    
    # Step 14: Additional information and completion
    ["otherInfo"]
]

# Schema file path
SCHEMA_FILE = "SEZNAM_POTREBNIH_PODATKOV.json"