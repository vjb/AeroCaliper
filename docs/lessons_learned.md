# Lessons Learned: Hardening AeroCaliper

## Google Cloud Platform (GCP)
1. **Model Armor Configuration:** 
   - **Regional Endpoints are Mandatory:** When interacting with the Model Armor API via Python SDK or REST, you must explicitly configure a regional endpoint (e.g., `modelarmor.us-central1.rep.googleapis.com`). Defaulting to the global endpoint will silently route requests incorrectly, leading to `404 Not Found` or `TEMPLATE_NOT_FOUND` errors even when the template exists.
   - **Template Propagation:** Model Armor templates created via the UI or SDK may take a few moments to propagate across the control plane. Tests executed immediately after creation might fail with `TEMPLATE_NOT_FOUND`.

2. **Vertex AI Search (RAG):**
   - **Unstructured Datastore Indexing:** Creating a Datastore and importing an unstructured document (like a `.txt` policy) is just the first step. The Vertex AI backend can take anywhere from 10 to 30 minutes to fully process, chunk, and index the document. Queries made immediately will return empty results (`0 snippets`).
   - **GCS Import Reliability:** Direct file uploads via the browser or API can sometimes face permission or workspace blockers. Staging documents in a dedicated Cloud Storage bucket (`gs://aerocaliper-rag-bucket`) and importing from GCS is the most robust pipeline.

## Arize & Phoenix
1. **Package Disambiguation (`arize` vs `arize-phoenix`):** 
   - The `arize` package is for the enterprise Arize AX platform. 
   - For open-source observability, prompt registries, and local tracing, you must use `arize-phoenix` (and its dependencies like `arize-phoenix-client`).
2. **Prompt Registry API Changes:** 
   - Older documentation references `arize.experimental.datasets.experiments.prompts`. This is deprecated/incorrect for Phoenix setups. 
   - The modern approach is to initialize `from phoenix.client import Client` and use `client.prompts.get(name="prompt-name")`.
3. **MCP Integration and Environment Variables:**
   - The `@arizeai/phoenix-mcp` server connects seamlessly, but relies on proper header configuration (`api_key=...` or `Authorization: Bearer`). 
   - **Dynamic Space Routing:** Hardcoding the `PHOENIX_SPACE_URL` (e.g., `/s/vjbeltrani`) causes deployment pipelines to fail if the workspace ID changes. Always use an environment variable like `ARIZE_SPACE_ID` to inject the workspace suffix dynamically into the `--baseUrl` argument.
