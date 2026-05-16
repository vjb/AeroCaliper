from fastapi import FastAPI, BackgroundTasks, HTTPException
import uvicorn
import os
from aerocaliper import AeroCaliperAgent
import asyncio

app = FastAPI(title="AeroCaliper Remediation Webhook")

@app.post("/remediate")
async def trigger_remediation():
    """
    Webhook endpoint triggered by Arize Phoenix when a FinOps violation occurs.
    """
    try:
        agent = AeroCaliperAgent()
        # Execute the full diagnostic and patching loop autonomously
        patched_prompt = await agent.execute_remediation()
        return {"status": "success", "message": "Remediation complete", "patched_prompt": patched_prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
