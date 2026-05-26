import subprocess
import time
import os
import sys
import socket
import pytest
from playwright.sync_api import sync_playwright

# Helper to check if port is open
def wait_for_port(port, host="127.0.0.1", timeout=30):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except (OSError, ConnectionRefusedError):
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.5)

@pytest.fixture(scope="module", autouse=True)
def run_fastapi_server():
    """Boots the local FastAPI server in a subprocess on port 8000."""
    print("\n[Playwright E2E Setup] Starting local FastAPI server via Uvicorn...")
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    
    proc = subprocess.Popen(
        cmd,
        cwd=base_dir,
        env=env,
        stdout=None,
        stderr=None
    )
    
    if not wait_for_port(8000):
        proc.terminate()
        raise RuntimeError("FastAPI server failed to start on port 8000.")
        
    print("[Playwright E2E Setup] FastAPI server is up and listening on port 8000.")
    yield
    print("\n[Playwright E2E Teardown] Stopping local FastAPI server...")
    proc.terminate()
    proc.wait()

def test_e2e_browser_workflow():
    """
    Executes the following E2E state transitions:
    1. Navigates to http://localhost:8000
    2. Clicks #btn-trigger-remediation
    3. Waits for the .log-output DOM element to contain '[🚀 ARIZE MCP SERVER] Executing tool: get-spans'
    4. Waits for the UI to pause at the Human-in-the-Loop boundary (Candidate Prompt displayed)
    5. Playwright captures a full-page screenshot at the HITL pause and saves it to docs/judge_evidence/01_candidate_prompt_review.png
    6. Clicks #btn-approve-patch
    7. Asserts the UI transitions to a green REMEDIATION COMPLETE state
    8. Playwright captures a full-page screenshot at Step 7 and saves it to docs/judge_evidence/02_remediation_success.png
    """
    evidence_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "judge_evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        
        # 1. Navigate to http://localhost:8000
        print("[Playwright] Navigating to http://localhost:8000...")
        page.goto("http://localhost:8000", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        # 2. Click the trigger button
        print("[Playwright] Clicking #triggerBtn...")
        page.click("#triggerBtn")
        
        # 3. Wait for the .log-output DOM element to contain '[🚀 ARIZE MCP SERVER] Executing tool: get-spans'
        print("[Playwright] Waiting for get-spans tool execution log...")
        log_selector = ".log-output"
        
        start_time = time.time()
        mcp_logged = False
        while time.time() - start_time < 300:
            log_content = page.text_content(log_selector)
            if "[🚀 ARIZE MCP SERVER] Executing tool: get-spans" in log_content:
                mcp_logged = True
                break
            time.sleep(1)
            
        assert mcp_logged, "Failed to find '[🚀 ARIZE MCP SERVER] Executing tool: get-spans' in logs"
        print("[Playwright] Found get-spans tool execution in log panel.")
        
        # 4. Wait for the UI to pause at the Human-in-the-Loop boundary (Candidate Prompt displayed)
        print("[Playwright] Waiting for Human-in-the-Loop approval modal...")
        page.wait_for_selector("#approvalPanel.visible", timeout=300_000)
        
        # 5. Playwright captures a full-page screenshot at the HITL pause
        screenshot_path1 = os.path.join(evidence_dir, "01_candidate_prompt_review.png")
        page.screenshot(path=screenshot_path1, full_page=True)
        print(f"[Playwright] Captured screenshot at HITL pause: {screenshot_path1}")
        
        # 6. Click #approveBtn
        print("[Playwright] Clicking #approveBtn...")
        page.click("#approveBtn")
        
        # 7. Assert the UI transitions to a green REMEDIATION COMPLETE state
        print("[Playwright] Waiting for REMEDIATION COMPLETE confirmation...")
        start_time = time.time()
        remediation_complete = False
        while time.time() - start_time < 300:
            log_content = page.text_content(log_selector)
            if "REMEDIATION COMPLETE" in log_content:
                remediation_complete = True
                break
            time.sleep(1)
            
        assert remediation_complete, "Failed to transition to REMEDIATION COMPLETE state."
        print("[Playwright] Remediation completed successfully.")
        
        # Assert the success log line is green
        success_line = page.locator(".log-msg.success").last
        success_line.wait_for(state="visible", timeout=15000)
        success_text = success_line.text_content()
        assert "REMEDIATION COMPLETE" in success_text
        
        # 8. Playwright captures a full-page screenshot of remediation success
        screenshot_path2 = os.path.join(evidence_dir, "02_remediation_success.png")
        page.screenshot(path=screenshot_path2, full_page=True)
        print(f"[Playwright] Captured screenshot of remediation success: {screenshot_path2}")
        
        context.close()
        browser.close()
