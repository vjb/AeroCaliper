import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8081"

def test_homepage_has_title_and_trigger_btn(page: Page):
    page.goto(BASE_URL)
    expect(page).to_have_title(re.compile("AeroCaliper"))
    btn = page.locator("#triggerBtn")
    expect(btn).to_be_visible()
    expect(btn).to_have_text(re.compile("Trigger Autonomous Remediation"))

def test_policy_dropdown_updates_ui(page: Page):
    page.goto(BASE_URL)
    
    # Check default policy is finops
    dropdown = page.locator("#policyDropdown")
    expect(dropdown).to_have_value("finops")
    
    # Change to hr
    dropdown.select_option("hr")
    
    # Check the UI updates accordingly
    label = page.locator("#backtestLabel")
    expect(label).to_have_text("HR/Privacy Use Case (PII test cases):")
    
    desc = page.locator("#phase1Desc")
    expect(desc).to_contain_text("HR agent leaks PII")

import re
