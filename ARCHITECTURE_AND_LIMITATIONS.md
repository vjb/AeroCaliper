# Architecture and Limitations

Last audited: 2026-05-17, Version: v4.0 Universal

This document provides a technical account of the AeroCaliper Universal Platform architecture, specifically outlining production-ready components for the Google Cloud & Arize Partner Track. **As of the final hardening phase, ALL simulated systems, mocks, and "graceful fallbacks" have been strictly removed.** The system relies 100% on live external APIs and implements a strict fail-closed architecture if any dependency is unreachable.

## Arize Partner Track Compliance

The system is compliant with the Arize Partner Track requirements.
The rules for this track state: *"The Arize track requires a code-owned agent runtime. The visual Agent Builder alone is not supported for tracing integration."* 

The Python asynchronous orchestrator utilizes the `google-genai` SDK and `arize-phoenix-otel` to fulfill this requirement. It natively generates, exports, and introspects its own OpenTelemetry traces without relying on visual builders.

## Production-Grade Components

1. **Gemini 3.1 Pro:** Every LLM call executes an HTTPS POST to `aiplatform.googleapis.com` via the `google-genai` SDK.
2. **Arize Phoenix MCP Server:** Spawned via `npx @arizeai/phoenix-mcp` communicating over JSON-RPC 2.0. The `baseUrl` dynamically targets the Arize Cloud workspace by parsing the `ARIZE_SPACE_ID` environment variable, ensuring portability across enterprise deployments.
3. **Vertex AI Search (RAG):** Retrieval-Augmented Generation dynamically fetches enterprise policies (e.g., Cloud FinOps Spot Instance rules or HR PII restrictions) to ground the Gemini diagnostic phase based on the selected governance domain.
4. **LLM-as-a-Judge Evaluation:** A secondary Gemini 3.1 session independently evaluates the candidate system prompt against a dynamic universal rubric corresponding to the active governance policy.
5. **A2A Interceptors:** `before_request` hooks wrap all calls to validate scopes and block unauthorized infrastructure deployment.
6. **Multi-Layer Anomaly Detection:** Deterministic regex scans combined with Gemini intent analysis dynamically calculate risk across multiple domains (FinOps vs. Privacy).
7. **OTLP Exporting:** `arize-phoenix-otel` and OpenInference seamlessly export spans to the hosted Arize Phoenix Cloud (`app.phoenix.arize.com`).
8. **Arize Trace Fetching:** The system executes Phase 2.5 (MCP Environment Discovery) to profile the workspace via `get-projects` and `get-datasets`, then uses the `get-spans` tool to retrieve live trace data directly from the populated Arize Phoenix workspace.
9. **A2UI Admin Approval Gate:** The backend pipeline uses native `asyncio.Event()` to block and suspend execution until the admin clicks Approve or Reject via the SSE frontend.
10. **Google Secret Manager and Logging:** API keys are natively mounted, and `google-cloud-logging` streams structured orchestration data to the GCP Logs Explorer.
11. **Google Cloud Model Armor:** Native SDK validating payloads against enterprise security templates via the `SanitizeUserPrompt` API in the `us-central1` region.
12. **Zero-Trust Fail-Closed Mechanism:** If Vertex AI Search returns 0 snippets (e.g., due to the 30-minute Datastore indexing delay for new policies), the platform throws a fatal `RuntimeError`. If the MCP handshake fails, the platform halts. There are zero mock responses.

## Summary Table

| Component | Status | Track Requirement |
|---|---|---|
| Code-Owned Agent Runtime | REAL | Required by Arize Track |
| Gemini 3.1 Pro inference | REAL | Core Requirement |
| @arizeai/phoenix-mcp | REAL | Core Requirement |
| OpenInference auto-instrumentation | REAL | Core Requirement |
| Arize trace data (get-spans) | REAL | Core Requirement |
| LLM-as-a-Judge evaluation | REAL | Core Requirement |
| Vertex AI Search (RAG) | REAL (SDK Integrated) | Architecture Best Practice |
| Google Secret Manager and Cloud Logging | REAL | Enterprise Specification |
| Universal Governance (FinOps + PII) | REAL | Value Add |
| Native GCP Model Armor APIs | REAL | Defined Scope |
