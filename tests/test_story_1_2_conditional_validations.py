"""
Test Story 1.2: Conditional Validations
Tests dynamic asterisk indicators, array validations, and lot checkbox warnings.
"""

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
from utils.form_helpers import FormContext
from ui.renderers.validation_renderer import ValidationRenderer


class TestDynamicRequiredIndicators:
    """Test dynamic asterisk indicators based on field conditions."""
    
    def test_single_client_fields_become_required(self):
        """When isSingleClient=true, single client fields should be required."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "clientInfo": {
                "isSingleClient": True
            }
        }
        
        renderer.update_dynamic_requirements(form_data)
        
        # Single client fields should be required
        assert renderer._dynamic_required_fields["clientInfo.singleClientName"] == True
        assert renderer._dynamic_required_fields["clientInfo.singleClientStreetAddress"] == True
        assert renderer._dynamic_required_fields["clientInfo.singleClientPostalCode"] == True
        
        # Multiple client fields should not be required
        assert renderer._dynamic_required_fields["clientInfo.clients"] == False
    
    def test_multiple_client_fields_become_required(self):
        """When isSingleClient=false, multiple client fields should be required."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "clientInfo": {
                "isSingleClient": False
            }
        }
        
        renderer.update_dynamic_requirements(form_data)
        
        # Multiple client fields should be required
        assert renderer._dynamic_required_fields["clientInfo.clients"] == True
        
        # Single client fields should not be required
        assert renderer._dynamic_required_fields["clientInfo.singleClientName"] == False
        assert renderer._dynamic_required_fields["clientInfo.singleClientStreetAddress"] == False
        assert renderer._dynamic_required_fields["clientInfo.singleClientPostalCode"] == False
    
    def test_procedure_justification_conditional(self):
        """Justification becomes required for non-open procedures."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test with open procedure - no justification needed
        form_data = {
            "submissionProcedure": {
                "procedure": "odprti postopek"
            }
        }
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["submissionProcedure.justification"] == False
        
        # Test with restricted procedure - justification needed
        form_data["submissionProcedure"]["procedure"] = "omejeni postopek"
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["submissionProcedure.justification"] == True
    
    def test_order_type_conditionals(self):
        """Delivery/service type fields become required based on order type."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test goods order
        form_data = {"orderType": {"type": "blago"}}
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["orderType.deliveryType"] == True
        assert renderer._dynamic_required_fields["orderType.serviceType"] == False
        
        # Test services order  
        form_data["orderType"]["type"] = "storitve"
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["orderType.deliveryType"] == False
        assert renderer._dynamic_required_fields["orderType.serviceType"] == True
    
    def test_deadline_type_conditionals(self):
        """Deadline fields become required based on deadline type."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test date-based deadline
        form_data = {"executionDeadline": {"type": "datumsko"}}
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["executionDeadline.startDate"] == True
        assert renderer._dynamic_required_fields["executionDeadline.endDate"] == True
        assert renderer._dynamic_required_fields["executionDeadline.days"] == False
        
        # Test days-based deadline
        form_data["executionDeadline"]["type"] = "v dnevih"
        renderer.update_dynamic_requirements(form_data)
        assert renderer._dynamic_required_fields["executionDeadline.days"] == True
        assert renderer._dynamic_required_fields["executionDeadline.startDate"] == False
        assert renderer._dynamic_required_fields["executionDeadline.endDate"] == False


class TestArrayValidations:
    """Test minimum array element validations."""
    
    def test_multiple_clients_minimum_validation(self):
        """Multiple client mode requires at least 2 clients."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test with only 1 client - should fail
        form_data = {
            "clientInfo": {
                "isSingleClient": False,
                "clients": [{"name": "Client 1"}]
            }
        }
        
        is_valid, errors = renderer.validate_array_minimums(form_data)
        assert is_valid == False
        assert any("vsaj 2 naročnika" in error for error in errors)
        
        # Test with 2 clients - should pass
        form_data["clientInfo"]["clients"].append({"name": "Client 2"})
        is_valid, errors = renderer.validate_array_minimums(form_data)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_lots_minimum_validation(self):
        """When hasLots=true, at least 2 lots are required."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test with hasLots=true but only 1 lot - should fail
        form_data = {
            "lotsInfo": {"hasLots": True},
            "lots": [{"name": "Lot 1"}]
        }
        
        is_valid, errors = renderer.validate_array_minimums(form_data)
        assert is_valid == False
        assert any("vsaj 2 sklopa" in error for error in errors)
        
        # Test with 2 lots - should pass
        form_data["lots"].append({"name": "Lot 2"})
        is_valid, errors = renderer.validate_array_minimums(form_data)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_single_order_no_lot_requirement(self):
        """When hasLots=false, no minimum lot requirement."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "lotsInfo": {"hasLots": False},
            "lots": []  # No lots
        }
        
        is_valid, errors = renderer.validate_array_minimums(form_data)
        assert is_valid == True
        assert len(errors) == 0


class TestLotCheckboxWarning:
    """Test warning when user has 2+ lots without checking hasLots."""
    
    def test_warning_appears_with_unchecked_lots(self):
        """Warning should appear when 2+ lots exist but hasLots is false."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "lotsInfo": {"hasLots": False},
            "lots": [
                {"name": "Lot 1"},
                {"name": "Lot 2"}
            ]
        }
        
        warning = renderer.validate_lot_checkbox_warning(form_data)
        assert warning is not None
        assert "2 sklope" in warning  # "sklope" not "sklopa" in the actual message
        assert "Naročilo je razdeljeno na sklope" in warning
    
    def test_no_warning_with_checked_lots(self):
        """No warning when hasLots is properly checked."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "lotsInfo": {"hasLots": True},
            "lots": [
                {"name": "Lot 1"},
                {"name": "Lot 2"}
            ]
        }
        
        warning = renderer.validate_lot_checkbox_warning(form_data)
        assert warning is None
    
    def test_no_warning_with_single_lot(self):
        """No warning with only 1 lot regardless of checkbox."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        form_data = {
            "lotsInfo": {"hasLots": False},
            "lots": [{"name": "Lot 1"}]
        }
        
        warning = renderer.validate_lot_checkbox_warning(form_data)
        assert warning is None


class TestDynamicLabelFormatting:
    """Test that labels are dynamically updated with asterisks."""
    
    def test_mark_required_field_with_dynamic_check(self):
        """Test mark_required_field uses dynamic requirements."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Set up dynamic requirement
        renderer._dynamic_required_fields["test.field"] = True
        
        # Test with dynamic requirement
        label = renderer.mark_required_field("Test Field", False, "test.field")
        assert label == "Test Field *"
        
        # Test without dynamic requirement
        renderer._dynamic_required_fields["test.field"] = False
        label = renderer.mark_required_field("Test Field", False, "test.field")
        assert label == "Test Field"
    
    def test_static_required_still_works(self):
        """Static required flag should still work."""
        session_state = {}
        context = FormContext(session_state)
        renderer = ValidationRenderer(context)
        
        # Test with static required=True
        label = renderer.mark_required_field("Test Field", True)
        assert label == "Test Field *"
        
        # Test with static required=False
        label = renderer.mark_required_field("Test Field", False)
        assert label == "Test Field"


class TestIntegrationWithFormController:
    """Test integration with form controller enhancement."""
    
    @patch('streamlit.warning')
    def test_lot_warning_displayed_during_validation(self, mock_warning):
        """Lot checkbox warning should be displayed during step validation."""
        from ui.controllers.form_controller import FormController
        from ui.renderers.validation_renderer import enhance_form_validation
        
        # Create mock form controller
        controller = MagicMock(spec=FormController)
        session_state = {}
        controller.context = FormContext(session_state)
        controller.validate_step = MagicMock(return_value=True)
        controller.get_form_data = MagicMock(return_value={
            "lotsInfo": {"hasLots": False},
            "lots": [{"name": "Lot 1"}, {"name": "Lot 2"}]
        })
        
        # Enhance with validation
        enhance_form_validation(controller)
        
        # Trigger validation
        controller.validate_step("lotsInfo")
        
        # Check that warning was called
        mock_warning.assert_called_once()
        warning_text = str(mock_warning.call_args[0][0])
        assert "2 sklope" in warning_text  # "sklope" not "sklopa" in the actual message


if __name__ == "__main__":
    # Run specific test classes
    pytest.main([__file__, "-v", "-k", "TestDynamicRequiredIndicators"])
    pytest.main([__file__, "-v", "-k", "TestArrayValidations"])
    pytest.main([__file__, "-v", "-k", "TestLotCheckboxWarning"])