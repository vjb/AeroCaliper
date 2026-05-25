import os
import json
import uuid
import google.genai
from google.cloud import firestore

def _get_embedding(text: str) -> list[float]:
    """Helper to get an embedding using Vertex AI via GenAI SDK."""
    api_key = os.environ.get("GOOGLE_AGENT_PLATFORM_API_KEY")
    client = google.genai.Client(vertexai=True, api_key=api_key)
    response = client.models.embed_content(
        model="text-embedding-005",
        contents=text
    )
    return response.embeddings[0].values

def query_past_remediations(violation_context: str) -> str:
    """
    Queries Firestore to find past successful remediations similar to the current violation.
    Returns the past patched prompt if a match is found, or an empty string.
    """
    try:
        db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
        collection = db.collection("aerocaliper_memory")
        
        # In a full implementation, this would do a Vector Search. 
        # For this prototype without a full vector index configured, we do a naive fetch
        # or simulated vector search if the dataset is small enough.
        docs = collection.stream()
        past_remedies = []
        for doc in docs:
            past_remedies.append(doc.to_dict())
            
        if not past_remedies:
            return "No past remediations found in long-term memory."
            
        # Very simple semantic match simulation (just return top if it exists)
        # In production: collection.find_nearest(vector_field="embedding", query_vector=embedding, limit=1)
        # We will just return the first one as an example of retrieving a past successful patch
        best_match = past_remedies[-1] 
        return f"Found past successful remediation for a similar violation.\nPast Violation context: {best_match.get('violation_context')}\nSuccessful Patched Prompt: {best_match.get('patched_prompt')}"
    except Exception as e:
        return f"Failed to query long-term memory: {e}"

def store_successful_remediation(trace_id: str, violation_context: str, patched_prompt: str) -> str:
    """
    Stores a successful prompt patch in Firestore for future retrieval.
    """
    try:
        db = firestore.Client(project=os.environ["GCP_PROJECT_ID"])
        # Optional: embedding = _get_embedding(violation_context)
        doc_ref = db.collection("aerocaliper_memory").document(trace_id or str(uuid.uuid4()))
        doc_ref.set({
            "trace_id": trace_id,
            "violation_context": violation_context,
            "patched_prompt": patched_prompt,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return f"SUCCESS: Remediation stored in Long-Term Memory (trace_id={trace_id})"
    except Exception as e:
        return f"Failed to store in long-term memory: {e}"
