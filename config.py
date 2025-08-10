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
    
    # Step 2: Basic project info (7 fields) - OK  
    ["projectInfo"],
    
    # Step 3: Submission procedure (2 fields) - Combined with lots
    ["submissionProcedure", "lotsInfo"], # Total: 6 fields
    
    # Step 4: Order type (enum selection) - Combined with others
    ["orderType", "technicalSpecifications"], # Split technical specs
    
    # Step 5: Execution deadline (6 fields) - Standalone
    ["executionDeadline"],
    
    # Step 6: Price info only (7 fields) - Split from overloaded step
    ["priceInfo"],
    
    # Step 7: Inspection and negotiations (10 fields combined) - More manageable
    ["inspectionInfo", "negotiationsInfo"],
    
    # Step 8: Participation criteria - Combined related sections
    ["exclusionReasons", "participationConditions"],
    
    # Step 9: Financial and variant offers (4 fields)
    ["financialGuarantees", "variantOffers"],
    
    # Step 10: Selection criteria (complex section)
    ["selectionCriteria"],
    
    # Step 11: Final contract info (6 fields)
    ["contractInfo"],
    
    # Step 12: Additional information and completion
    ["otherInfo"]
]

# Schema file path
SCHEMA_FILE = "SEZNAM_POTREBNIH_PODATKOV.json"