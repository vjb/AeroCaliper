import os
import pytest
from tools.compliance import search_enterprise_policy

def test_infrastructure_gcp_absent_fallback(monkeypatch):
    """
    TDD Assertion: Deleting GCP credentials and project config from the environment
    and calling search_enterprise_policy('hr') MUST return the contents of the local fallback
    file and NOT throw a DefaultCredentialsError or crash.
    """
    # Delete GCP config from env to simulate local judge environment
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCP_POLICY_BUCKET", raising=False)
    
    # Execute policy retrieval
    policy_content = search_enterprise_policy("hr")
    
    # Assertions
    assert "Enterprise HR Privacy and PII Policy 2026" in policy_content
    assert "Section 1.1" in policy_content
    assert "contains_pii" in policy_content
    
    # Do the same for finops
    finops_content = search_enterprise_policy("finops")
    assert "Enterprise FinOps Routing Policy 2026" in finops_content or "Section 1.1" in finops_content
