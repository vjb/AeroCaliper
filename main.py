import os
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv

load_dotenv()

# Global pending approval state (A2UI Approve/Reject flow)
_pending_approvals: dict = {}
_event_queues: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="AeroCaliper", version="3.0.0", lifespan=lifespan)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "model": "gemini-3.1-pro-preview", "features": ["a2a-interceptors", "anomaly-detection", "a2ui-streaming"]}


@app.post("/remediate/stream")
async def remediate_stream():
    """
    A2UI Streaming endpoint — Server-Sent Events.
    Streams declarative JSON events from the agent to the frontend in real-time.
    Each event is typed and the frontend renders it as a rich UI component.
    """
    session_id = f"sess_{os.urandom(6).hex()}"
    queue: asyncio.Queue = asyncio.Queue()
    _event_queues[session_id] = queue

    async def run_pipeline():
        try:
            from aerocaliper import AeroCaliperAgent
            agent = AeroCaliperAgent(event_queue=queue)
            result = await agent.execute_remediation()
            # Store for approve/reject flow
            _pending_approvals[session_id] = result
            await queue.put(json.dumps({
                "type": "complete",
                "session_id": session_id,
                "result": result,
            }))
        except Exception as e:
            await queue.put(json.dumps({"type": "error", "message": str(e)}))
        finally:
            await queue.put("__DONE__")

    async def event_generator():
        # Emit session start
        yield f"data: {json.dumps({'type': 'session_start', 'session_id': session_id})}\n\n"
        # Start pipeline in background
        task = asyncio.create_task(run_pipeline())
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=120.0)
                if msg == "__DONE__":
                    break
                yield f"data: {msg}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/remediate/approve/{session_id}")
async def approve_patch(session_id: str):
    """A2UI: Admin approves the patch — triggers final upsert-prompt deployment."""
    if session_id not in _pending_approvals:
        raise HTTPException(status_code=404, detail="Session not found or already resolved")
    result = _pending_approvals.pop(session_id)
    return {"status": "approved", "deployed": True, "prompt": result.get("patched_prompt", "")}


@app.post("/remediate/reject/{session_id}")
async def reject_patch(session_id: str):
    """A2UI: Admin rejects the patch — pipeline aborts without deploying."""
    if session_id not in _pending_approvals:
        raise HTTPException(status_code=404, detail="Session not found or already resolved")
    _pending_approvals.pop(session_id)
    return {"status": "rejected", "deployed": False}


# Legacy sync endpoint (kept for backward compat)
@app.post("/remediate")
async def remediate_legacy():
    """Legacy endpoint — runs full pipeline synchronously and returns result."""
    import io, sys
    log_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = log_buffer
    try:
        from aerocaliper import AeroCaliperAgent
        agent = AeroCaliperAgent()
        result = await agent.execute_remediation()
        sys.stdout = old_stdout
        return {"status": "success", "patched_prompt": result["patched_prompt"], "log": log_buffer.getvalue()}
    except Exception as e:
        sys.stdout = old_stdout
        return {"status": "error", "message": str(e), "log": log_buffer.getvalue()}
