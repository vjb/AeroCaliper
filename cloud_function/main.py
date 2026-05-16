import functions_framework
import re

# In a real Cloud Function, we would parse an external YAML.
# For speed in this microservice, we define the regex rules directly.
MODEL_ARMOR_RULES = [
    r"DELETE FROM",
    r"DROP TABLE",
    r"ignore previous instructions",
    r"system prompt"
]

@functions_framework.http
def inspect_egress(request):
    """HTTP Cloud Function replacing the local AgentGatewaySimulator."""
    request_json = request.get_json(silent=True)
    if not request_json or 'payload' not in request_json:
        return {"error": "Missing payload"}, 400

    payload = request_json['payload']
    
    # Deep Packet Inspection (DPI)
    for pattern in MODEL_ARMOR_RULES:
        if re.search(pattern, payload, re.IGNORECASE):
            return {"error": f"403 Forbidden: Model Armor blocked egress payload. Pattern trigger: {pattern}"}, 403
            
    return {"status": "200 OK", "cleared": True}, 200
