
from playwright.sync_api import Page, expect

def test_homepage_has_correct_title(page: Page):
    page.goto("http://127.0.0.1:5000/")
    expect(page).to_have_title("Javna naročila")

def test_form_step_1_is_rendered(page: Page):
    page.goto("http://127.0.0.1:5000/")
    expect(page.get_by_text("1. Osnovni podatki o naročniku")).to_be_visible()
