# AeroCaliper: Hackathon Architecture & Limitations Audit

*Last audited: 2026-05-16 | Version: v4.0*

This document provides a transparent account of AeroCaliper's architecture, specifically outlining which components are production-ready and which are simulated for the sake of the hackathon demonstration.

## 🏆 Arize Partner Track Compliance

**AeroCaliper is 100% compliant with the Arize Partner Track requirements.**
The hackathon rules for this track explicitly state: *"The Arize track requires a code-owned agent runtime — Gemini CLI, Gemini Enterprise Agent Platform SDK, Google ADK, Agent Runtime, or Cloud Run. The visual Agent Builder alone is not supported for tracing integration."* 

Our custom Python async orchestrator utilizing the `google-genai` SDK and `arize-phoenix-otel` perfectly fulfills this requirement. It natively generates, exports, and introspects its own OpenTelemetry traces without relying on visual builders.

---

## ✅ REAL — Production-Grade Components

1. **Gemini 3.1 Pro — Live AI Inference:** Every LLM call makes a live HTTPS POST to `aiplatform.googleapis.com` via the official `google-genai` SDK.
2. **Arize Phoenix MCP Server:** Spawned via `npx @arizeai/phoenix-mcp` communicating over strict JSON-RPC 2.0. Exposes all 27 MCP tools natively.
3. **LLM-as-a-Judge Evaluation:** A live secondary Gemini 3.1 session independently evaluates the candidate system prompt against a strict security rubric.
4. **A2A Zero-Trust Interceptors:** Live `before_request` hooks wrap all calls to validate scopes and block unauthorized infrastructure deployment.
5. **Multi-Layer Anomaly Detection:** Deterministic regex scans combined with live Gemini intent analysis.
6. **arize-phoenix-otel Instrumentation:** Real OTLP spans are actively exported to the hosted Arize Phoenix Cloud (`app.phoenix.arize.com`). 
7. **Arize Trace Fetching:** The `get-spans` MCP tool retrieves LIVE trace data directly from the populated Arize Phoenix workspace.

---

## ⚠️ MOCKED / SIMULATED — Pending Roadmap Upgrades

These components are currently simulated but are slated for production replacement:

### 1. Model Armor / Agent Gateway
- **What's simulated:** `AgentGatewaySimulator` reads local YAML rules (`infra/model_armor_policy.yaml`) and applies regex matching. This is a behavioral simulation of Google Cloud Model Armor. No actual GCP API calls are made.
- **Production Path:** Deploy actual Cloud Armor policies via Service Extensions (Phase 6).

### 2. A2UI Admin Approval
- **What's simulated:** The Approve/Reject panel appears in the UI, but the backend pipeline does not block via an `asyncio.Event()`. The UI requires proactive clicking.
- **Production Path:** Implement true blocking in the SSE stream during the `candidate_prompt` emission.

### 3. Cloud Deployment
- **What's simulated:** The system is currently running as local Python processes.
- **Production Path:** Containerize via the provided `Dockerfile` and deploy using `gcloud run deploy aerocaliper`.

### 4. `upsert-prompt` Tool Persistence
- **What's simulated:** The tool executes flawlessly over JSON-RPC, but the target Arize Cloud REST endpoint occasionally drops the prompt update due to API stability limits, resulting in a 'fetch failed'. We gracefully degrade and continue the pipeline.
- **Production Path:** Await Arize prompt registry API stabilization.

---

## Summary Table

| Component | Status | Track Requirement |
|---|---|---|
| Code-Owned Agent Runtime | ✅ REAL | **Required by Arize Track** |
| Gemini 3.1 Pro inference | ✅ REAL | Core Requirement |
| @arizeai/phoenix-mcp | ✅ REAL | Core Requirement |
| arize-phoenix-otel export | ✅ REAL | Core Requirement |
| Arize trace data (get-spans) | ✅ REAL | Core Requirement |
| LLM-as-a-Judge evaluation | ✅ REAL | Core Requirement |
| Anomaly Detection Layer 1 & 2 | ✅ REAL | Value Add |
| Model Armor / Agent Gateway | ⚠️ SIMULATED | Hackathon Scope |
| A2UI Approve/Reject blocking | ⚠️ SIMULATED | Hackathon Scope |
| Cloud Run deployment | ❌ NOT YET | Final Phase |
