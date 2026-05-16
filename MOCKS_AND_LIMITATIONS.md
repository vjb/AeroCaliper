# AeroCaliper: Mocks & Functional Limitations Log

Per project requirements, this document tracks all simulated functionality. 

## 100% FUNCTIONAL STATUS (Zero Mocks Remaining)
As of the latest iteration, **AeroCaliper is a 100% cutting-edge, functional AI security agent.**
All abstractions and mocks have been completely removed to win the Arize Partner Track.

1. **Target Agent Core (`target_agent.py`) is Real:**
   - We no longer simulate the agent's logic with Python `if` statements. The Target Agent now dynamically queries `gemini-flash-latest` via REST API, forcing it to hallucinate the missing budget tag natively to prove the vulnerability exists dynamically in the LLM.
2. **Arize MCP Integration is Real:**
   - The AeroCaliper ADK client natively spawns the official `@arizeai/phoenix-mcp` NPM package via `npx` and communicates over the JSON-RPC 2.0 `stdio` protocol. No custom Python mocks are used.
3. **Gemini 3.1 Pro "Interactions API" & "Thought Signatures" are Real:**
   - The background polling job no longer uses `asyncio.sleep()`. It now spawns a secondary Gemini AI session acting as an `LLM-as-a-Judge`, executing a rigorous evaluation rubric on the generated Candidate Prompt (the Thought Signature) to guarantee the FinOps fix before authorizing the patch via the MCP server.
