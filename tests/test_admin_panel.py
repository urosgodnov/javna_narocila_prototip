import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.admin_panel import render_organization_management_tab

class TestAdminPanel(unittest.TestCase):

    def setUp(self):
        # Create a dummy organizations.json file
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.org_file = os.path.join(self.dir_path, '..', 'organizations.json')
        with open(self.org_file, 'w') as f:
            json.dump([], f)

    def tearDown(self):
        # Remove the dummy organizations.json file
        if os.path.exists(self.org_file):
            os.remove(self.org_file)

    @patch('streamlit.form_submit_button')
    @patch('streamlit.text_input')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    @patch('streamlit.markdown')
    @patch('streamlit.rerun')
    def test_add_organization(self, mock_rerun, mock_markdown, mock_warning, mock_success, mock_text_input, mock_form_submit_button):
        # Simulate submitting the form with a new organization name
        mock_form_submit_button.return_value = True
        mock_text_input.return_value = "Nova organizacija"

        # Render the organization management tab
        render_organization_management_tab()

        # Check if the success message is displayed
        mock_success.assert_called_with("Organizacija 'Nova organizacija' dodana.")

        # Check if the organizations.json file is updated
        with open(self.org_file, 'r') as f:
            organizations = json.load(f)
            self.assertIn('Nova organizacija', organizations)

    @patch('streamlit.form_submit_button')
    @patch('streamlit.text_input')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    @patch('streamlit.markdown')
    @patch('streamlit.rerun')
    def test_add_existing_organization(self, mock_rerun, mock_markdown, mock_warning, mock_success, mock_text_input, mock_form_submit_button):
        # Add an organization to the file initially
        with open(self.org_file, 'w') as f:
            json.dump(['Obstoječa organizacija'], f)

        # Simulate submitting the form with an existing organization name
        mock_form_submit_button.return_value = True
        mock_text_input.return_value = "Obstoječa organizacija"

        # Render the organization management tab
        render_organization_management_tab()

        # Check if the warning message is displayed
        mock_warning.assert_called_with("Organizacija 'Obstoječa organizacija' že obstaja.")

    @patch('streamlit.button')
    @patch('streamlit.markdown')
    @patch('streamlit.rerun')
    def test_delete_organization(self, mock_rerun, mock_markdown, mock_button):
        # Add an organization to the file initially
        with open(self.org_file, 'w') as f:
            json.dump(['Organizacija za brisanje'], f)

        # Simulate clicking the delete button
        mock_button.return_value = True

        # Render the organization management tab
        render_organization_management_tab()

        # Check if the organizations.json file is updated
        with open(self.org_file, 'r') as f:
            organizations = json.load(f)
            self.assertNotIn('Organizacija za brisanje', organizations)

if __name__ == '__main__':
    unittest.main()