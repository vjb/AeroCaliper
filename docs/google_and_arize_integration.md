# Google Cloud and Arize Integration

AeroCaliper integrates Google Cloud Platform services with Arize Phoenix observability to create a fully autonomous, production-grade AI governance pipeline.

Last audited: 2026-05-24, Version: v4.0 Universal

## Google Cloud Technologies Utilized

1. **Google Agent Platform SDK (`google-genai`)**
   - The system utilizes the official Gemini API SDK for all LLM inference.
   - Models are executed via the `google-genai` client with Vertex AI routing for security and scale.
   - Gemini drives four distinct operations: root-cause analysis (Phase 3), backtest simulation (Phase 4), prompt refinement (Phase 4 optimization loop), and LLM-as-a-Judge evaluation (Phase 4 final gate).

2. **Google Cloud Run**
   - The primary remediation engine is containerized (`Dockerfile`) and hosted on Cloud Run.
   - Cloud Run fulfills the requirement for a Code-Owned Agent Runtime, allowing OpenTelemetry trace instrumentation via `arize-phoenix-otel`.

3. **Google Secret Manager**
   - API keys (`GOOGLE_AGENT_PLATFORM_API_KEY`, `PHOENIX_API_KEY`) are stored encrypted at rest.
   - Cloud Run injects these secrets as environment variables during runtime, avoiding local file leakage in production environments.

4. **Google Cloud Logging**
   - Standard stdout is dual-routed: `gcp_print()` in `aerocaliper.py` simultaneously prints locally and sends to Google Cloud Logging via the `google-cloud-logging` SDK.
   - Structured log shipping is gated by the `ENABLE_CLOUD_LOGGING=true` environment variable, defaulting to clean local console output during development.

5. **Google Cloud Model Armor**
   - The egress DPI mechanism in `agent_gateway.py` uses the `google-cloud-modelarmor` SDK targeting the regional endpoint `modelarmor.us-central1.rep.googleapis.com`.
   - The `SanitizeUserPrompt` API validates the candidate patch against an enterprise security template before it can reach the Arize Prompt Registry.
   - **Strict Mode:** If the SDK, project ID, or template ID are absent, `AgentGatewaySimulator.__init__()` raises a `RuntimeError` immediately. There is no local regex fallback or mock mode.
   - If a `GATEWAY_URL` env var is set, `aerocaliper.py` routes the payload to an external HTTP-triggered **Google Cloud Function** (2nd Gen) for distributed validation, implementing a distributed microservice architecture.

6. **Gemini CLI Config**
   - A native `gemini-cli-config.json` file configures the `@arizeai/phoenix-mcp` within the Gemini CLI for developer interactions and testing.

7. **Google Cloud Build (CI/CD)**
   - Continuous deployment is managed by Cloud Build triggers (`cloudbuild.yaml`).
   - Builds execute using a dedicated, least-privilege user-managed service account (`cloudbuild-runner@aerocaliper.iam.gserviceaccount.com`).
   - The runner is granted minimal scoped roles: `roles/artifactregistry.writer`, `roles/run.admin`, `roles/storage.admin`, `roles/logging.logWriter`, and `roles/iam.serviceAccountUser`.

8. **Vertex AI Search (RAG)**
   - AeroCaliper implements Retrieval-Augmented Generation to dynamically fetch enterprise policies.
   - Two Vertex AI Search engines are provisioned: `finops-app` (FinOps Policy Datastore) and `hr-app` (HR Privacy Datastore).
   - The `discoveryengine_v1.SearchServiceClient` is used with engine-level serving configs to enable **Extractive Answers** — returning exact policy clauses rather than broad document chunks.
   - If the datastore returns 0 snippets (e.g., due to the 10–30 minute indexing delay for newly uploaded documents), the pipeline throws a `RuntimeError`. There is no hardcoded policy fallback.
   - The active datastore is selected at runtime via `target_use_case` (`finops` → `VERTEX_ENGINE_ID_FINOPS`, `hr` → `VERTEX_ENGINE_ID_HR`).

---

## Arize Phoenix Integration

1. **Trace Exporting (OTLP)**
   - Both the Target Agent (`target_agent.py`) and AeroCaliper's remediation engine (`aerocaliper.py`) are instrumented using `arize-phoenix-otel` and `openinference-instrumentation-google-genai`.
   - Traces are exported to the Arize Phoenix Cloud (`app.phoenix.arize.com`) under separate projects (`aerocaliper` for the target agent, `aerocaliper-remediation-engine` for the orchestrator).
   - The OTLP endpoint is dynamically constructed using `ARIZE_SPACE_ID`: `https://app.phoenix.arize.com/s/{space_id}/v1/traces`.

2. **Arize MCP Server**
   - AeroCaliper spawns `@arizeai/phoenix-mcp` programmatically using the official `modelcontextprotocol.io` Python SDK (`mcp.ClientSession`, `StdioServerParameters`).
   - On Windows, the server is launched via `cmd.exe /c npx`; on Unix via `npx` directly.
   - Authentication uses a dynamically injected `--baseUrl` (from `ARIZE_SPACE_ID`) and `--apiKey` (from `PHOENIX_API_KEY` or `ARIZE_API_KEY`).
   - **Phase 2.5** executes `get-projects` and `get-datasets` to profile the workspace environment before any trace data is fetched.

3. **Span Fetching with GraphQL Fallback**
   - Phase 3 calls `get-spans` via MCP to retrieve the most recent failed execution trace.
   - If the MCP tool returns an empty response or a transport error, the system executes a native GraphQL fallback query directly against the Arize Phoenix API (`/graphql`), targeting the `aerocaliper` project.
   - If both the MCP call and the GraphQL fallback fail, the system raises a `RuntimeError` (fail-closed).

4. **Autonomous Patching and The Self-Improvement Loop**
   - Following admin approval and LLM-as-a-Judge validation, AeroCaliper calls `upsert-prompt` via MCP to deploy a hardened system prompt directly to the Arize Prompt Registry.
   - The UI reflects this continuous evolution with a live ✨ **Self-Improvement Loop Active** status badge.
   - The Target Agent dynamically pulls this new prompt on reboot via `get_prompt()` from the Phoenix client SDK (`from phoenix.client import Client`).
   - If `upsert-prompt` returns `fetch failed` or a `500` status, the system raises a `RuntimeError` (fail-closed). The patch is never silently abandoned.

5. **Live Evaluations**
   - An LLM-as-a-Judge evaluation pipeline assesses historical traces inside the Phoenix workspace to measure execution accuracy over time across multiple use cases (FinOps, Privacy).
   - Evaluation rubrics are defined in `evaluators.py` and graded by a separate Gemini session using the Vertex AI-extracted policy as the ground truth.
