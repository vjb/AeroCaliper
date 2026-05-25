import asyncio
from mcp_client import StandardMCPClient

def fetch_failed_traces() -> dict:
    """
    Fetch the most recent failed execution traces from the Arize Phoenix MCP server.
    Returns a structured dictionary representing the failed span.
    """
    async def _run():
        client = StandardMCPClient()
        try:
            return await client.get_failed_spans()
        finally:
            await client.close()

    return asyncio.run(_run())

def deploy_prompt_patch(patched_prompt: str, domain: str) -> str:
    """
    Deploys a patched system prompt back to the Arize Prompt Registry via the MCP server.
    """
    async def _run():
        client = StandardMCPClient()
        try:
            success = await client.upsert_prompt(patched_prompt, target_use_case=domain)
            if success:
                return "SUCCESS: Prompt successfully deployed to Arize Prompt Registry."
            return "FAILURE"
        finally:
            await client.close()
    
    return asyncio.run(_run())
