# Architecture and Limitations

Last audited: 2026-05-24, Version: v4.0 Universal

This document provides a technical account of the AeroCaliper Universal Platform architecture, specifically outlining production-ready components for the Google Cloud & Arize Partner Track. **As of the final hardening phase, ALL simulated systems, mocks, and "graceful fallbacks" have been strictly removed.** The system relies 100% on live external APIs and implements a strict fail-closed architecture if any dependency is unreachable.

## Arize Partner Track Compliance

The system is compliant with the Arize Partner Track requirements.
The rules for this track state: *"The Arize track requires a code-owned agent runtime. The visual Agent Builder alone is not supported for tracing integration."* 

The Python asynchronous orchestrator utilizes the `google-genai` SDK and `arize-phoenix-otel` to fulfill this requirement. It natively generates, exports, and introspects its own OpenTelemetry traces without relying on visual builders.

## Production-Grade Components

1. **Gemini Inference:** Every LLM call executes an HTTPS POST to `aiplatform.googleapis.com` via the `google-genai` SDK. Gemini drives four pipeline operations: root-cause analysis, backtest simulation, prompt refinement (optimization loop), and LLM-as-a-Judge evaluation.
2. **Arize Phoenix MCP Server:** Spawned via `npx @arizeai/phoenix-mcp` (via `cmd.exe /c npx` on Windows) communicating over JSON-RPC 2.0 using the official `modelcontextprotocol.io` Python SDK. The `baseUrl` dynamically targets the Arize Cloud workspace using `ARIZE_SPACE_ID`.
3. **Vertex AI Search (RAG):** Retrieval-Augmented Generation dynamically fetches enterprise policies (Cloud FinOps Spot Instance rules or HR PII restrictions) via `discoveryengine_v1.SearchServiceClient` using engine-level serving configs for Extractive Answers.
4. **LLM-as-a-Judge Evaluation:** A secondary Gemini session independently evaluates the candidate system prompt against a dynamic universal rubric corresponding to the active governance policy.
5. **Phase 4 Optimization Loop:** Up to 3 backtesting attempts. Each failed attempt feeds failure context back to Gemini for prompt refinement. Pass rate is computed on a domain-filtered slice of `golden_dataset.csv` (no cross-domain contamination).
6. **A2A Interceptors:** `before_request` hooks in `a2a_interceptor.py` wrap all Gemini calls to validate scopes (`remediate:read`, `remediate:write`, `mcp:connect`) and block unauthorized infrastructure deployment.
7. **Multi-Layer Anomaly Detection:** Deterministic regex scans (Layer 1) combined with Gemini intent analysis (Layer 2) dynamically calculate risk across multiple domains (FinOps vs. Privacy).
8. **OTLP Exporting:** `arize-phoenix-otel` and OpenInference export spans from both the Target Agent and the remediation engine to the hosted Arize Phoenix Cloud (`app.phoenix.arize.com`).
9. **Arize Trace Fetching:** Phase 2.5 (MCP Environment Discovery) profiles the workspace via `get-projects` and `get-datasets`. Phase 3 uses `get-spans` to retrieve live trace data. If MCP returns empty, a GraphQL fallback queries the Phoenix API before failing closed.
10. **A2UI Admin Approval Gate:** The backend pipeline uses native `asyncio.Event()` to block and suspend execution for up to 5 minutes until the admin clicks Approve or Reject via the SSE frontend.
11. **Google Secret Manager and Logging:** API keys are natively mounted via Cloud Run secret injection, and `google-cloud-logging` streams structured orchestration data to the GCP Logs Explorer (gated by `ENABLE_CLOUD_LOGGING=true`).
12. **Google Cloud Model Armor:** Native SDK validating payloads against enterprise security templates via the `SanitizeUserPrompt` API at the `us-central1` regional endpoint. **Strict Mode:** raises `RuntimeError` on initialization if SDK or credentials are absent.
13. **Zero-Trust Fail-Closed Mechanism:** Three hard failure points with no mock fallback:
    - Vertex AI Search returns 0 snippets → `RuntimeError`
    - MCP handshake fails / `get-spans` returns nothing and GraphQL fallback fails → `RuntimeError`
    - `upsert-prompt` returns `fetch failed` or `500` → `RuntimeError`

## Summary Table

| Component | Status | Track Requirement |
|---|---|---|
| Code-Owned Agent Runtime | REAL | Required by Arize Track |
| Gemini inference (google-genai) | REAL | Core Requirement |
| @arizeai/phoenix-mcp | REAL | Core Requirement |
| OpenInference auto-instrumentation | REAL | Core Requirement |
| Arize trace data (get-spans) | REAL | Core Requirement |
| LLM-as-a-Judge evaluation | REAL | Core Requirement |
| Phase 4 Gemini Refinement Loop (3x) | REAL | Value Add |
| Vertex AI Search (RAG, Extractive Answers) | REAL | Architecture Best Practice |
| Google Secret Manager & Cloud Logging | REAL | Enterprise Specification |
| Universal Governance (FinOps + HR PII) | REAL | Value Add |
| Native GCP Model Armor API (Strict Mode) | REAL | Defined Scope |
| A2UI Blocking Admin Approval Gate | REAL | Value Add |
| GraphQL Fallback for Span Fetching | REAL | Resilience |
