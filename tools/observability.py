import asyncio
import threading
from mcp_client import StandardMCPClient
from opentelemetry import trace
import functools
import inspect

tracer = trace.get_tracer(__name__)

def trace_chain(name: str):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                t = trace.get_tracer(func.__module__)
                if hasattr(t, "chain"):
                    return await t.chain(name=name)(func)(*args, **kwargs)
                else:
                    with t.start_as_current_span(name):
                        return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                t = trace.get_tracer(func.__module__)
                if hasattr(t, "chain"):
                    return t.chain(name=name)(func)(*args, **kwargs)
                else:
                    with t.start_as_current_span(name):
                        return func(*args, **kwargs)
            return sync_wrapper
    return decorator



_global_emit = None
_global_use_case = None

def set_observability_emit(emit_fn):
    global _global_emit
    _global_emit = emit_fn

def set_observability_use_case(use_case):
    global _global_use_case
    _global_use_case = use_case

def _run_in_new_thread(coro):
    result = None
    exception = None

    def target():
        nonlocal result, exception
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro)
            loop.close()
        except Exception as e:
            exception = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result

@trace_chain(name="fetch_failed_traces")
def fetch_failed_traces() -> dict:

    """
    Fetch the most recent failed execution traces from the Arize Phoenix MCP server.
    Returns a structured dictionary representing the failed span.
    """
    async def _run():
        client = StandardMCPClient(emit_fn=_global_emit)
        try:
            return await client.get_failed_spans(use_case=_global_use_case)
        finally:
            await client.close()

    return _run_in_new_thread(_run())

@trace_chain(name="deploy_prompt_patch")
def deploy_prompt_patch(patched_prompt: str, domain: str) -> str:


    """
    Deploys a patched system prompt back to the Arize Prompt Registry via the MCP server.
    """
    async def _run():
        client = StandardMCPClient(emit_fn=_global_emit)
        try:
            success = await client.upsert_prompt(patched_prompt, target_use_case=domain)
            if success:
                return "SUCCESS: Prompt successfully deployed to Arize Prompt Registry."
            return "FAILURE"
        finally:
            await client.close()
    
    return _run_in_new_thread(_run())

