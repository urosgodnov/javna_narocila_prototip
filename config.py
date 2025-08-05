"""Configuration constants and environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# Admin authentication
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Default for demonstration

# Form configuration
FORM_STEPS = [
    ["clientData", "projectName", "submissionProcedure"],  # Step 1: Basic project info
    ["orderType"],  # Step 2: Order type and details
    ["exclusionReasons", "participationConditions"],  # Step 3: Requirements and conditions
    ["financialGuarantees", "selectionCriteria", "socialCriteria", "otherCriteria", "contractType"]  # Step 4: Criteria and contract
]

# Schema file path
SCHEMA_FILE = "SEZNAM_POTREBNIH_PODATKOV.json"