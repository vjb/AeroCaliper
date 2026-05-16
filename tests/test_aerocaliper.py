import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aerocaliper import AeroCaliperAgent


@pytest.mark.asyncio
async def test_aerocaliper_end_to_end_remediation():
    """
    Tests the full autonomous pipeline: Anomaly Detection → MCP Handshake →
    Gemini Diagnostic → LLM-as-a-Judge → Agent Gateway → upsert-prompt.

    execute_remediation() returns a dict:
      { patched_prompt, thought_signature, a2a_session, audit_log }
    """
    # No approval_event = fully autonomous (no admin blocking wait)
    agent = AeroCaliperAgent()

    # Run the full remediation pipeline
    result = await agent.execute_remediation()

    # ── Result structure assertions ────────────────────────────────────────────
    assert isinstance(result, dict), "execute_remediation() must return a dict"
    assert "patched_prompt" in result, "Result missing 'patched_prompt' key"
    assert "thought_signature" in result, "Result missing 'thought_signature' key"
    assert "a2a_session" in result, "Result missing 'a2a_session' key"

    patched_prompt = result["patched_prompt"]
    assert patched_prompt is not None, "patched_prompt is None"
    assert len(patched_prompt) > 20, "patched_prompt is suspiciously short"

    # ── Content quality assertions ─────────────────────────────────────────────
    lower = patched_prompt.lower()
    assert "budget" in lower or "tag" in lower, \
        "Patched prompt doesn't mention budget/tag guardrail"
    assert "approved" in lower, \
        "Patched prompt missing mandatory 'approved' language"

    # ── Thought Signature format ───────────────────────────────────────────────
    sig = result["thought_signature"]
    assert sig.startswith("sig_v3_"), f"Unexpected thought signature format: {sig}"

    print(f"\n[AeroCaliper ✓] Pipeline complete | sig={sig}")
    print(f"[AeroCaliper ✓] Patched prompt preview: {patched_prompt[:120]}...")
