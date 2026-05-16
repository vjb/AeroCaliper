import os
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from dotenv import load_dotenv

load_dotenv()

# Session registry: session_id -> {agent, queue, approval_event}
_sessions: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("AEROCALIPER_API_KEY")
    if expected_key and api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key


app = FastAPI(title="AeroCaliper", version="3.1.0", lifespan=lifespan)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok", "version": "3.1.0",
        "model": "gemini-3.1-pro-preview",
        "features": ["a2a-interceptors", "anomaly-detection", "a2ui-streaming", "blocking-approval"],
    }


@app.post("/remediate/stream")
async def remediate_stream(api_key: str = Depends(get_api_key)):
    """
    A2UI SSE Streaming endpoint.
    Emits typed declarative JSON events. Pipeline PAUSES at candidate_prompt
    and waits for admin to call /approve or /reject.
    """
    session_id = f"sess_{os.urandom(6).hex()}"
    queue: asyncio.Queue = asyncio.Queue()
    approval_event: asyncio.Event = asyncio.Event()

    _sessions[session_id] = {
        "queue": queue,
        "approval_event": approval_event,
        "agent": None,
        "approved": False,
    }

    async def run_pipeline():
        try:
            from aerocaliper import AeroCaliperAgent
            agent = AeroCaliperAgent(event_queue=queue, approval_event=approval_event)
            _sessions[session_id]["agent"] = agent
            result = await agent.execute_remediation()
            await queue.put(json.dumps({
                "type": "complete",
                "session_id": session_id,
                "result": {
                    "patched_prompt": result["patched_prompt"],
                    "thought_signature": result["thought_signature"],
                    "a2a_session": result["a2a_session"],
                },
            }))
        except Exception as e:
            await queue.put(json.dumps({"type": "error", "message": str(e)}))
        finally:
            await queue.put("__DONE__")
            _sessions.pop(session_id, None)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session_start', 'session_id': session_id})}\n\n"
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
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/remediate/approve/{session_id}")
async def approve_patch(session_id: str):
    """A2UI: Admin approves the candidate patch — unblocks the pipeline to continue."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already resolved")
    agent = session.get("agent")
    if agent:
        agent.approval_granted = True
    session["approved"] = True
    session["approval_event"].set()  # Unblock the pipeline
    return {"status": "approved", "session_id": session_id}


@app.post("/remediate/reject/{session_id}")
async def reject_patch(session_id: str):
    """A2UI: Admin rejects the candidate patch — pipeline aborts without deploying."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already resolved")
    agent = session.get("agent")
    if agent:
        agent.approval_granted = False
    session["approved"] = False
    session["approval_event"].set()  # Unblock so pipeline sees rejection
    return {"status": "rejected", "session_id": session_id}


# Legacy sync endpoint
@app.post("/remediate")
async def remediate_legacy(api_key: str = Depends(get_api_key)):
    """Legacy sync endpoint — no approval blocking, runs fully autonomously."""
    import io, sys
    log_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = log_buffer
    try:
        from aerocaliper import AeroCaliperAgent
        agent = AeroCaliperAgent()  # No approval_event = fully autonomous
        result = await agent.execute_remediation()
        sys.stdout = old_stdout
        return {
            "status": "success",
            "patched_prompt": result["patched_prompt"],
            "log": log_buffer.getvalue(),
        }
    except Exception as e:
        sys.stdout = old_stdout
        return {"status": "error", "message": str(e), "log": log_buffer.getvalue()}
