# AeroCaliper: Reality vs. Simulation Log

Per project requirements, this document transparently tracks exactly what components of the AeroCaliper architecture are utilizing live, production infrastructure versus what has been simulated locally for the purpose of the hackathon demonstration.

## ✅ What is REAL (Production-Grade)

1. **Target Agent AI Logic (`target_agent.py`)**
   - **Real:** The "Confused Deputy" hallucination is not hardcoded in Python. The agent makes live POST requests to the `generativelanguage.googleapis.com` Gemini REST API, dynamically prompting it to select a cluster and proving that the LLM forgets the budget tag.
2. **The Arize MCP Client (`aerocaliper.py`)**
   - **Real:** We do not mock the MCP server. Our Python client uses `subprocess` to download and spawn the **OFFICIAL `@arizeai/phoenix-mcp` NPM package** via `npx`. It communicates securely over `stdio` using the strict JSON-RPC 2.0 protocol.
3. **The "Interactions API" & "Thought Signatures"**
   - **Real:** To validate our fix, we spawn a secondary, live Gemini AI session acting as an `LLM-as-a-Judge`. It evaluates the candidate prompt (Thought Signature) against a strict grading rubric before authorizing the patch.
4. **FinOps Code Evaluator (`evaluators.py`)**
   - **Real:** The OpenTelemetry trace evaluation logic deterministically parses the JSON payload to enforce standard FinOps governance.

## ⚠️ What is MOCKED (Simulated for Demo Stability)

1. **Model Armor & Agent Gateway (`agent_gateway.py`)**
   - **Mocked:** We have not deployed actual Google Cloud Model Armor infrastructure. Instead, we built a local Python middleware (`AgentGatewaySimulator`) that parses local YAML files (`infra/model_armor_policy.yaml`) to perform deep packet inspection and block outbound prompt injections, perfectly simulating the GCP service.
2. **Hosting Environment**
   - **Mocked:** The system is currently running as local Python processes on a Windows development machine. It has not yet been containerized and deployed to Google Cloud Run (which is the goal of Phase 5).
