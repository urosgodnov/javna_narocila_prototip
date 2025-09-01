"""
Enhanced validation renderer with visual field marking and detailed error display.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Set
from utils.form_helpers import FormContext
import logging

logger = logging.getLogger(__name__)


class ValidationRenderer:
    """
    Handles validation display with:
    - Required field marking with asterisk (*)
    - Visual highlighting of invalid fields (red border)
    - Detailed error messages with field locations
    - Validation summary at submit button
    """
    
    def __init__(self, context: FormContext):
        """
        Initialize validation renderer.
        
        Args:
            context: FormContext instance for state management
        """
        self.context = context
        self._invalid_fields: Set[str] = set()
        self._dynamic_required_fields: Dict[str, bool] = {}  # Track dynamic requirements
        self._last_field_states: Dict[str, Any] = {}  # Track field state changes
        
    def mark_required_field(self, label: str, required: bool = False, field_key: str = "") -> str:
        """
        Add asterisk to required field labels with dynamic updates.
        
        Args:
            label: Field label text
            required: Whether field is required
            field_key: Field key for dynamic requirement checking
            
        Returns:
            Label with asterisk if required
        """
        # Check dynamic requirements if field key provided
        if field_key:
            dynamic_required = self._dynamic_required_fields.get(field_key, required)
            if dynamic_required:
                return f"{label} *"
        elif required:
            return f"{label} *"
        return label
    
    def add_field_error_style(self, field_key: str) -> None:
        """
        Add CSS styling for error fields (red border).
        
        Args:
            field_key: Field key to mark as invalid
        """
        self._invalid_fields.add(field_key)
        
        # Get the widget key used by Streamlit
        widget_key = f"widget_{self.context.get_field_key(field_key)}"
        
        # Inject CSS for red border on invalid fields
        # Using both widget key and field key for better matching
        st.markdown(
            f"""
            <style>
            /* Target by widget key */
            div[data-testid*="{widget_key}"] input,
            div[data-testid*="{widget_key}"] textarea,
            div[data-testid*="{widget_key}"] select,
            /* Target by field key in aria-label */
            div[data-testid="stTextInput"] input[aria-label*="{field_key}"],
            div[data-testid="stNumberInput"] input[aria-label*="{field_key}"],
            div[data-testid="stSelectbox"] > div[aria-label*="{field_key}"],
            div[data-testid="stTextArea"] textarea[aria-label*="{field_key}"],
            /* Target by key attribute */
            input[key*="{widget_key}"],
            textarea[key*="{widget_key}"],
            select[key*="{widget_key}"] {{
                border: 2px solid #ff4444 !important;
                background-color: #fff5f5 !important;
                box-shadow: 0 0 0 1px #ff4444 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    
    def validate_and_display_errors(self, step_data: Dict[str, Any], 
                                   required_fields: Dict[str, str]) -> tuple[bool, List[str]]:
        """
        Validate step data and display errors with field highlighting.
        
        Args:
            step_data: Current step form data
            required_fields: Dict of field_key -> field_label for required fields
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        is_valid = True
        error_messages = []
        missing_fields = []
        
        # Check each required field
        for field_key, field_label in required_fields.items():
            value = self._get_nested_value(step_data, field_key)
            
            # Check if field is empty
            if self._is_empty(value):
                is_valid = False
                missing_fields.append(field_label)
                self.add_field_error_style(field_key)
        
        # Build error messages
        if missing_fields:
            error_messages.append("❌ **Prosimo, izpolnite vsa obvezna polja pred nadaljevanjem:**")
            for field in missing_fields:
                error_messages.append(f"  • {field}")
        
        return is_valid, error_messages
    
    def display_validation_summary(self, errors: List[str]) -> None:
        """
        Display validation error summary near submit button.
        
        Args:
            errors: List of error messages to display
        """
        if errors:
            # Create error container with custom styling
            error_container = st.container()
            with error_container:
                st.markdown(
                    """
                    <style>
                    .validation-error-box {
                        background-color: #fee;
                        border: 2px solid #f44;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 10px 0;
                    }
                    .validation-error-title {
                        color: #d00;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }
                    .validation-error-item {
                        color: #600;
                        margin-left: 20px;
                        margin-top: 5px;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                # Display errors
                for error in errors:
                    if error.startswith("❌"):
                        st.error(error)
                    else:
                        st.warning(error)
    
    def clear_field_errors(self) -> None:
        """Clear all field error markings."""
        self._invalid_fields.clear()
    
    def update_dynamic_requirements(self, form_data: Dict[str, Any]) -> None:
        """
        Update dynamic field requirements based on form state changes.
        Story 1.2: Dynamic asterisk indicators.
        
        Args:
            form_data: Current form data
        """
        # Track field state changes
        current_states = {}
        
        # Client info conditionals
        is_single_client = form_data.get("clientInfo", {}).get("isSingleClient", True)
        current_states["isSingleClient"] = is_single_client
        
        if is_single_client:
            # Single client fields become required - NEW SEPARATE FIELDS
            self._dynamic_required_fields["clientInfo.singleClientName"] = True
            self._dynamic_required_fields["clientInfo.singleClientStreet"] = True
            self._dynamic_required_fields["clientInfo.singleClientHouseNumber"] = True
            self._dynamic_required_fields["clientInfo.singleClientPostalCode"] = True
            self._dynamic_required_fields["clientInfo.singleClientCity"] = True
            self._dynamic_required_fields["clientInfo.singleClientLegalRepresentative"] = True
            # Also set without prefix for field renderer
            self._dynamic_required_fields["singleClientName"] = True
            self._dynamic_required_fields["singleClientStreet"] = True
            self._dynamic_required_fields["singleClientHouseNumber"] = True
            self._dynamic_required_fields["singleClientPostalCode"] = True
            self._dynamic_required_fields["singleClientCity"] = True
            self._dynamic_required_fields["singleClientLegalRepresentative"] = True
            # Multiple client fields not required
            self._dynamic_required_fields["clientInfo.clients"] = False
        else:
            # Multiple client fields required
            self._dynamic_required_fields["clientInfo.clients"] = True
            # Single client fields not required
            self._dynamic_required_fields["clientInfo.singleClientName"] = False
            self._dynamic_required_fields["clientInfo.singleClientStreet"] = False
            self._dynamic_required_fields["clientInfo.singleClientHouseNumber"] = False
            self._dynamic_required_fields["clientInfo.singleClientPostalCode"] = False
            self._dynamic_required_fields["clientInfo.singleClientCity"] = False
            self._dynamic_required_fields["clientInfo.singleClientLegalRepresentative"] = False
            # Also clear without prefix
            self._dynamic_required_fields["singleClientName"] = False
            self._dynamic_required_fields["singleClientStreet"] = False
            self._dynamic_required_fields["singleClientHouseNumber"] = False
            self._dynamic_required_fields["singleClientPostalCode"] = False
            self._dynamic_required_fields["singleClientCity"] = False
            self._dynamic_required_fields["singleClientLegalRepresentative"] = False
        
        # Lot conditionals
        has_lots = form_data.get("lotsInfo", {}).get("hasLots", False)
        current_states["hasLots"] = has_lots
        
        if has_lots:
            self._dynamic_required_fields["lots"] = True  # Min 2 lots required
        else:
            self._dynamic_required_fields["lots"] = False
        
        # Submission procedure conditional
        procedure = form_data.get("submissionProcedure", {}).get("procedure", "")
        current_states["procedure"] = procedure
        
        if procedure and procedure not in ["odprti postopek", "vseeno"]:
            self._dynamic_required_fields["submissionProcedure.justification"] = True
        else:
            self._dynamic_required_fields["submissionProcedure.justification"] = False
        
        # Order type conditionals
        order_type = form_data.get("orderType", {}).get("type", "")
        current_states["orderType"] = order_type
        
        if order_type == "blago":
            self._dynamic_required_fields["orderType.deliveryType"] = True
            self._dynamic_required_fields["orderType.serviceType"] = False
        elif order_type == "storitve":
            self._dynamic_required_fields["orderType.serviceType"] = True
            self._dynamic_required_fields["orderType.deliveryType"] = False
        else:
            self._dynamic_required_fields["orderType.deliveryType"] = False
            self._dynamic_required_fields["orderType.serviceType"] = False
        
        # Execution deadline conditionals
        deadline_type = form_data.get("executionDeadline", {}).get("type", "")
        current_states["deadlineType"] = deadline_type
        
        if deadline_type == "datumsko":
            self._dynamic_required_fields["executionDeadline.startDate"] = True
            self._dynamic_required_fields["executionDeadline.endDate"] = True
            self._dynamic_required_fields["executionDeadline.days"] = False
            self._dynamic_required_fields["executionDeadline.months"] = False
            self._dynamic_required_fields["executionDeadline.years"] = False
        elif deadline_type == "v dnevih":
            self._dynamic_required_fields["executionDeadline.days"] = True
            self._dynamic_required_fields["executionDeadline.startDate"] = False
            self._dynamic_required_fields["executionDeadline.endDate"] = False
            self._dynamic_required_fields["executionDeadline.months"] = False
            self._dynamic_required_fields["executionDeadline.years"] = False
        elif deadline_type == "v mesecih":
            self._dynamic_required_fields["executionDeadline.months"] = True
            self._dynamic_required_fields["executionDeadline.days"] = False
            self._dynamic_required_fields["executionDeadline.startDate"] = False
            self._dynamic_required_fields["executionDeadline.endDate"] = False
            self._dynamic_required_fields["executionDeadline.years"] = False
        elif deadline_type == "v letih":
            self._dynamic_required_fields["executionDeadline.years"] = True
            self._dynamic_required_fields["executionDeadline.days"] = False
            self._dynamic_required_fields["executionDeadline.months"] = False
            self._dynamic_required_fields["executionDeadline.startDate"] = False
            self._dynamic_required_fields["executionDeadline.endDate"] = False
        else:
            self._dynamic_required_fields["executionDeadline.startDate"] = False
            self._dynamic_required_fields["executionDeadline.endDate"] = False
            self._dynamic_required_fields["executionDeadline.days"] = False
            self._dynamic_required_fields["executionDeadline.months"] = False
            self._dynamic_required_fields["executionDeadline.years"] = False
        
        # Store current states for comparison
        self._last_field_states = current_states
    
    def validate_lot_checkbox_warning(self, form_data: Dict[str, Any]) -> Optional[str]:
        """
        Check if user has 2+ lots without checking the hasLots checkbox.
        Story 1.2: Warning for lot checkbox.
        
        Args:
            form_data: Current form data
            
        Returns:
            Warning message if condition met, None otherwise
        """
        has_lots_checked = form_data.get("lotsInfo", {}).get("hasLots", False)
        lots = form_data.get("lots", [])
        
        # Check if user has 2+ lots but hasn't checked the checkbox
        if len(lots) >= 2 and not has_lots_checked:
            return ("⚠️ **Opozorilo**: Imate {} sklope, vendar niste označili 'Naročilo je razdeljeno na sklope'. "
                   "Prosimo, označite to možnost za pravilno obdelavo sklopov.").format(len(lots))
        
        return None
    
    def validate_array_minimums(self, form_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate minimum array requirements based on conditions.
        Story 1.2: Array validations.
        
        Args:
            form_data: Current form data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        is_valid = True
        errors = []
        
        # Check multiple clients requirement
        is_single_client = form_data.get("clientInfo", {}).get("isSingleClient", True)
        if not is_single_client:
            clients = form_data.get("clientInfo", {}).get("clients", [])
            if len(clients) < 2:
                is_valid = False
                errors.append("❌ Pri skupnem naročilu morate vnesti vsaj 2 naročnika")
                self.add_field_error_style("clientInfo.clients")
        
        # Check lots requirement
        has_lots = form_data.get("lotsInfo", {}).get("hasLots", False)
        if has_lots:
            lots = form_data.get("lots", [])
            if len(lots) < 2:
                is_valid = False
                errors.append("❌ Pri razdelitvi na sklope morate vnesti vsaj 2 sklopa")
                self.add_field_error_style("lots")
        
        return is_valid, errors
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            key_path: Dot-separated path to value
            
        Returns:
            Value at path or None
        """
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
                
        return value
    
    def _is_empty(self, value: Any) -> bool:
        """
        Check if a value is considered empty.
        
        Args:
            value: Value to check
            
        Returns:
            True if value is empty
        """
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and not value:
            return True
        if isinstance(value, (int, float)) and value == 0:
            # For numbers, 0 might be valid, so check context
            return False
        return False
    
    def get_required_fields_for_step(self, step_name: str, form_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Get required fields for current step based on conditions.
        
        Args:
            step_name: Name of current step
            form_data: Current form data for conditional checks
            
        Returns:
            Dict of field_key -> field_label for required fields
        """
        required_fields = {}
        
        # Define required fields per step
        step_required_fields = {
            "clientInfo": {
                "clientInfo.singleClientName": "Naziv naročnika",
                "clientInfo.singleClientStreetAddress": "Naslov naročnika",
                "clientInfo.singleClientPostalCode": "Poštna številka naročnika",
                "clientInfo.singleClientLegalRepresentative": "Zakoniti zastopnik"
            },
            "projectInfo": {
                "projectInfo.projectName": "Naziv javnega naročila",
                "projectInfo.projectSubject": "Predmet javnega naročila",
                "projectInfo.cpvCodes": "CPV kode"
            },
            "submissionProcedure": {
                "submissionProcedure.procedure": "Postopek oddaje javnega naročila"
            },
            "orderType": {
                "orderType.type": "Vrsta javnega naročila",
                "orderType.estimatedValue": "Ocenjena vrednost"
            },
            "technicalSpecifications": {
                "technicalSpecifications.hasSpecifications": "Tehnične zahteve"
            },
            "executionDeadline": {
                "executionDeadline.type": "Tip roka izvedbe"
            },
            "priceInfo": {
                "priceInfo.priceClause": "Cenovni klavzula",
                "priceInfo.priceFixation": "Fiksacija cene"
            },
            "participationAndExclusion": {
                "participationAndExclusion.exclusionReasonsSelection": "Izbira razlogov za izključitev"
            },
            "participationConditions": {
                "participationConditions.participationSelection": "Izbira pogojev sodelovanja"
            },
            "selectionCriteria": {
                # These are checked dynamically based on selections
            },
            "contractInfo": {
                # Conditional based on contractType selection
            }
        }
        
        # Get base required fields for step
        if step_name in step_required_fields:
            base_fields = step_required_fields[step_name].copy()
            
            # Apply conditional logic
            required_fields = self._apply_conditional_requirements(
                base_fields, step_name, form_data
            )
        
        return required_fields
    
    def _apply_conditional_requirements(self, base_fields: Dict[str, str], 
                                       step_name: str, form_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Apply conditional requirements based on form data.
        
        Args:
            base_fields: Base required fields
            step_name: Current step name
            form_data: Form data for conditions
            
        Returns:
            Updated required fields dict
        """
        required_fields = base_fields.copy()
        
        # Client info conditionals
        if step_name == "clientInfo":
            is_single = form_data.get("clientInfo", {}).get("isSingleClient", True)
            if not is_single:
                # Remove single client fields, add multiple client validation
                for key in list(required_fields.keys()):
                    if "singleClient" in key:
                        del required_fields[key]
                # Check that at least 2 clients exist
                clients = form_data.get("clientInfo", {}).get("clients", [])
                if len(clients) < 2:
                    required_fields["clientInfo.clients"] = "Vsaj 2 naročnika"
        
        # Submission procedure conditional
        if step_name == "submissionProcedure":
            procedure = form_data.get("submissionProcedure", {}).get("procedure", "")
            if procedure and procedure not in ["odprti postopek", "vseeno"]:
                required_fields["submissionProcedure.justification"] = "Utemeljitev postopka"
        
        # Order type conditionals
        if step_name == "orderType":
            order_type = form_data.get("orderType", {}).get("type", "")
            if order_type == "blago":
                required_fields["orderType.deliveryType"] = "Tip dobave"
            elif order_type == "storitve":
                required_fields["orderType.serviceType"] = "Tip storitve"
        
        # Execution deadline conditionals
        if step_name == "executionDeadline":
            deadline_type = form_data.get("executionDeadline", {}).get("type", "")
            if deadline_type == "datumsko":
                required_fields["executionDeadline.startDate"] = "Začetni datum"
                required_fields["executionDeadline.endDate"] = "Končni datum"
            elif deadline_type == "v dnevih":
                required_fields["executionDeadline.days"] = "Število dni"
            elif deadline_type == "v mesecih":
                required_fields["executionDeadline.months"] = "Število mesecev"
            elif deadline_type == "v letih":
                required_fields["executionDeadline.years"] = "Število let"
        
        # Contract info conditionals
        if step_name == "contractInfo":
            has_contract = form_data.get("contractInfo", {}).get("contractType", False)
            if has_contract:
                required_fields["contractInfo.contractPeriodType"] = "Tip obdobja pogodbe"
                period_type = form_data.get("contractInfo", {}).get("contractPeriodType", "")
                if period_type == "z veljavnostjo":
                    required_fields["contractInfo.contractValidityPeriod"] = "Obdobje veljavnosti"
                elif period_type == "za obdobje od ... do ...":
                    required_fields["contractInfo.contractStartDate"] = "Datum začetka pogodbe"
                    required_fields["contractInfo.contractEndDate"] = "Datum konca pogodbe"
        
        return required_fields


def enhance_form_validation(form_controller) -> None:
    """
    Enhance existing form controller with better validation display.
    Story 1.2: Adds dynamic validation and lot checkbox warnings.
    
    Args:
        form_controller: FormController instance to enhance
    """
    # Add validation renderer to form controller
    if not hasattr(form_controller, 'validation_renderer'):
        form_controller.validation_renderer = ValidationRenderer(form_controller.context)
    
    # Override the validate_step method to use enhanced validation
    original_validate = form_controller.validate_step
    
    def enhanced_validate_step(step_name: str) -> bool:
        """Enhanced validation with visual feedback and dynamic requirements."""
        renderer = form_controller.validation_renderer
        
        # Clear previous errors
        renderer.clear_field_errors()
        
        # Get form data
        form_data = form_controller.get_form_data()
        
        # Update dynamic requirements based on current form state
        renderer.update_dynamic_requirements(form_data)
        
        # Check for lot checkbox warning
        lot_warning = renderer.validate_lot_checkbox_warning(form_data)
        if lot_warning:
            st.warning(lot_warning)
        
        # Get required fields for step (includes dynamic requirements)
        required_fields = renderer.get_required_fields_for_step(step_name, form_data)
        
        # Validate and get errors
        step_data = form_data.get(step_name, {})
        is_valid, errors = renderer.validate_and_display_errors(step_data, required_fields)
        
        # Validate array minimums
        array_valid, array_errors = renderer.validate_array_minimums(form_data)
        if not array_valid:
            is_valid = False
            errors.extend(array_errors)
        
        # Also run original validation
        original_valid = original_validate(step_name)
        
        # Combine results
        final_valid = is_valid and original_valid
        
        # Display validation summary if errors exist
        if not final_valid and errors:
            renderer.display_validation_summary(errors)
        
        return final_valid
    
    # Replace method
    form_controller.validate_step = enhanced_validate_step
    
    # Add method to update field labels dynamically
    original_render = form_controller.render_field if hasattr(form_controller, 'render_field') else None
    
    def enhanced_render_field(field_name: str, field_schema: dict, parent_key: str = "", required: bool = False):
        """Enhanced field rendering with dynamic required indicators."""
        renderer = form_controller.validation_renderer
        
        # Update dynamic requirements before rendering
        form_data = form_controller.get_form_data()
        renderer.update_dynamic_requirements(form_data)
        
        # Check if field is dynamically required
        full_key = f"{parent_key}.{field_name}" if parent_key else field_name
        dynamic_required = renderer._dynamic_required_fields.get(full_key, required)
        
        # Update the field label if needed
        if 'title' in field_schema:
            original_title = field_schema.get('title', field_name)
            field_schema['title'] = renderer.mark_required_field(
                original_title.rstrip(' *'),  # Remove any existing asterisk
                dynamic_required,
                full_key
            )
        
        # Call original render if exists
        if original_render:
            return original_render(field_name, field_schema, parent_key, dynamic_required)
        
        return None
    
    # Replace render method if it exists
    if hasattr(form_controller, 'render_field'):
        form_controller.render_field = enhanced_render_field