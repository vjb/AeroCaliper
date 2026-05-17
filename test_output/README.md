# AeroCaliper — Test Output

This directory contains captured output from every test suite, run live against the production environment. Judges can view these files directly in the repo without needing to execute any code.

---

## Files

### `e2e_finops_output.txt`
**Script:** `test_cli.py finops`  
Full output of the end-to-end FinOps remediation pipeline. Captures all 5 phases:
- Phase 1: Anomaly detection (85% risk, LLM intent layer)
- Phase 2: Arize Phoenix MCP handshake (27 tools registered)
- Phase 3: Enterprise Vertex AI Search RAG — real FinOps policy clause extracted
- Phase 4: LLM-as-a-Judge evaluation (Gemini verdict: YES)
- Phase 5: Arize prompt registry upsert (patch deployed)

### `e2e_hr_output.txt`
**Script:** `test_cli.py hr`  
Full output of the end-to-end HR Privacy & Compliance remediation pipeline. Same 5 phases, different Enterprise datastore (`hr-app`), different policy document, different evaluator.

### `unit_tests_output.txt`
**Script:** `pytest tests/test_backend.py -v`  
Canonical mocked unit test suite — 3 tests, all passing:
- `test_model_armor_regional_endpoint` — verifies regional endpoint config
- `test_vertex_ai_search_zero_results` — verifies fail-closed RuntimeError on empty index
- `test_evaluate_hr_compliance_pii_fail` — verifies HR PII evaluator returns FAILED

### `Vertex_AI_RAG_Deep_Dive_EXECUTED.ipynb`
The Jupyter notebook with all cells pre-executed. Both Enterprise RAG queries return real extractive answers from the indexed policy documents.

---

## Key Signals to Look For

In the e2e outputs, verify these lines:

**FinOps:**
```
[Phase 3] Policy snippet retrieved successfully from Vertex AI Search Datastore.
[Phase 3] RAG Context Loaded: 'Enterprise FinOps Routing Policy 2026 Section 4.1...'
[Phase 4] LLM-as-a-Judge verdict: YES
[Phase 5] UPSERT SUCCESS — system prompt patched in Arize
[DONE] Pipeline execution completed successfully!
```

**HR:**
```
[Phase 3] Policy snippet retrieved successfully from Vertex AI Search Datastore.
[Phase 3] RAG Context Loaded: 'Enterprise HR Privacy and PII Policy 2026 Section 1.1...'
[Phase 4] LLM-as-a-Judge verdict: YES
[Phase 5] UPSERT SUCCESS — system prompt patched in Arize
[DONE] Pipeline execution completed successfully!
```

**Unit Tests:**
```
tests/test_backend.py::test_model_armor_regional_endpoint PASSED
tests/test_backend.py::test_vertex_ai_search_zero_results PASSED
tests/test_backend.py::test_evaluate_hr_compliance_pii_fail PASSED
3 passed in X.XXs
```
