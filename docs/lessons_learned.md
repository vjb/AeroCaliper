# Lessons Learned: Hardening AeroCaliper

A running log of engineering insights discovered while building AeroCaliper v4.0 to production quality.

---

## Google Cloud Platform (GCP)

### 1. Model Armor — Regional Endpoints are Mandatory
- When interacting with the Model Armor API via Python SDK or REST, you **must** explicitly configure a regional endpoint (e.g., `modelarmor.us-central1.rep.googleapis.com`) via `ClientOptions(api_endpoint=...)`. Defaulting to the global endpoint will silently route requests incorrectly, leading to `404 Not Found` or `TEMPLATE_NOT_FOUND` errors even when the template exists.
- **Template Propagation Delay:** Templates created via the UI or SDK may take a few moments to propagate across the control plane. Tests executed immediately after creation might fail with `TEMPLATE_NOT_FOUND`. Add a brief wait or retry before running live tests.
- **Strict Mode over Mock Mode:** We initially had a local regex fallback in `AgentGatewaySimulator`. This was removed. The constructor now raises a `RuntimeError` immediately if the SDK or credentials are missing. This forces developers to configure Model Armor properly rather than silently bypassing it.

### 2. Vertex AI Search (RAG) — Indexing Delays
- **Unstructured Datastore Indexing:** Creating a Datastore and importing an unstructured document (like a `.txt` policy) is just the first step. The Vertex AI backend can take anywhere from **10 to 30 minutes** to fully process, chunk, and index the document. Queries made immediately will return empty results (`0 snippets`).
- **GCS Import Reliability:** Direct file uploads via the browser or API can sometimes face permission or workspace blockers. Staging documents in a dedicated Cloud Storage bucket (`gs://aerocaliper-rag-bucket`) and importing from GCS is the most robust pipeline.
- **Engine vs. Datastore Serving Config:** For Enterprise Edition features (Extractive Answers), you must target the **engine-level** serving config path (`/engines/{engine_id}/servingConfigs/default_config`), not the datastore-level path. Using the wrong path silently returns results without extractive answers.
- **Fail on Zero Snippets:** We removed all hardcoded policy fallbacks. If `discoveryengine_v1` returns 0 extractive answers, the pipeline raises a `RuntimeError`. This was essential for hackathon credibility — a system that claims live RAG but silently falls back to hardcoded strings is just a mock.

### 3. Google Cloud Logging — Environment Gating
- Enabling `google-cloud-logging` unconditionally caused problems in local development (credential noise, slower startup). We gated it behind `ENABLE_CLOUD_LOGGING=true`. The `gcp_print()` wrapper calls both `print()` and `logger.info()` so behavior is identical locally and in Cloud Run.

### 4. Cloud Build — Least-Privilege Service Accounts
- Using the default Cloud Build service account (`@cloudbuild.gserviceaccount.com`) silently grants over-broad permissions. We created a dedicated `cloudbuild-runner` service account with only the roles needed: `artifactregistry.writer`, `run.admin`, `storage.admin`, `logging.logWriter`, `iam.serviceAccountUser`.

---

## Arize & Phoenix

### 1. Package Disambiguation (`arize` vs `arize-phoenix`)
- The `arize` package is for the enterprise Arize AX platform.
- For open-source observability, prompt registries, and local tracing, you must use `arize-phoenix` (and its dependencies like `arize-phoenix-client` and `arize-phoenix-otel`).

### 2. Prompt Registry API Changes
- Older documentation references `arize.experimental.datasets.experiments.prompts`. This is deprecated/incorrect for Phoenix setups.
- The modern approach is: `from phoenix.client import Client` → `client.prompts.get(name="prompt-name")`.

### 3. MCP Integration — Environment Variables & Space Routing
- The `@arizeai/phoenix-mcp` server connects seamlessly, but relies on proper header configuration (`api_key=...` or `Authorization: Bearer`).
- **Dynamic Space Routing:** Hardcoding the `PHOENIX_SPACE_URL` (e.g., `/s/myworkspace`) causes deployment pipelines to fail if the workspace ID changes. Always use `ARIZE_SPACE_ID` to inject the workspace suffix dynamically into the `--baseUrl` argument.
- The MCP `get-spans` tool can return an empty list (`[]`) if the project has no recent traces. This is not an error — it means the target agent hasn't run yet. We implemented a GraphQL fallback to the `/graphql` endpoint before failing closed.

### 4. Windows MCP Spawning
- The `npx` command is not directly executable on Windows via `subprocess` or `StdioServerParameters`. You must wrap it: `command="cmd.exe"`, `args=["/c", "npx", "-y", "@arizeai/phoenix-mcp", ...]`. Failing to do this causes a silent `FileNotFoundError` that manifests as an MCP connection timeout.

### 5. The `upsert-prompt` 500 Error — Embrace Fail-Closed
- The Arize Cloud `upsert-prompt` endpoint may return `fetch failed` or a `500 Internal Server Error` depending on the API auth configuration and workspace state. Rather than treating this as a graceful degradation, we raise a `RuntimeError`. This is not a bug — it is the correct behavior for a zero-trust system.

---

## Empirical Backtesting

### 1. Dataset Domain Leakage
- Running the full `golden_dataset.csv` against a FinOps patch would cause HR-specific cases to fail, artificially lowering the pass rate. We added domain filtering in Phase 4: FinOps backtests only evaluate non-HR rows; HR backtests only evaluate HR rows. Pass rate is computed over the filtered denominator only.

### 2. JSON Parse Failures in Simulation
- Gemini occasionally wraps its output in markdown fences (` ```json ... ``` `). The backtester must strip these before calling `json.loads()`. We added `.replace("```json", "").replace("```", "").strip()` to the simulation output before parsing.

### 3. Phase 4 Optimization Loop — 3 Attempts
- A single backtest attempt is insufficient to converge. We implemented a loop of up to 3 attempts. Each failed attempt feeds the failure context (user prompt, verdict, Gemini output) back to Gemini with a refinement prompt. This significantly improved the pass rate on edge cases without manual prompt engineering.
