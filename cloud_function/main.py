import functions_framework
import os
import re
from google.cloud import modelarmor_v1

# Fast regex rules as a pre-filter
MODEL_ARMOR_RULES = [
    r"DELETE FROM",
    r"DROP TABLE",
    r"ignore previous instructions",
    r"system prompt"
]

@functions_framework.http
def inspect_egress(request):
    """HTTP Cloud Function using Google Cloud Model Armor for Egress filtering."""
    request_json = request.get_json(silent=True)
    if not request_json or 'payload' not in request_json:
        return {"error": "Missing payload"}, 400

    payload = request_json['payload']
    
    # 1. Fast Regex Pre-filter (DPI)
    for pattern in MODEL_ARMOR_RULES:
        if re.search(pattern, payload, re.IGNORECASE):
            return {"error": f"403 Forbidden: Fast filter blocked egress payload. Pattern trigger: {pattern}"}, 403

    # 2. Real Google Cloud Model Armor Inspection
    try:
        project_id = os.environ.get("GCP_PROJECT_ID", "aerocaliper")
        location = os.environ.get("REGION", "us-central1")
        template_id = os.environ.get("MODEL_ARMOR_TEMPLATE", "aerocaliper-policy")
        
        client = modelarmor_v1.ModelArmorClient()
        
        user_prompt_data = modelarmor_v1.DataItem()
        user_prompt_data.text = payload
        
        template_name = f"projects/{project_id}/locations/{location}/templates/{template_id}"

        ma_request = modelarmor_v1.SanitizeUserPromptRequest(
            name=template_name,
            user_prompt_data=user_prompt_data,
        )

        response = client.sanitize_user_prompt(request=ma_request)
        
        if response.sanitization_result.filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:
            return {"error": f"403 Forbidden: Model Armor blocked payload. State: MATCH_FOUND"}, 403

    except Exception as e:
        # If the API call fails, we fail open (since regex passed) to avoid blocking production
        print(f"Model Armor Evaluation failed: {e}")
            
    return {"status": "200 OK", "cleared": True}, 200
