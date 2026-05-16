import yaml
import re
import os
import logging
try:
    from google.cloud import modelarmor_v1
    MODEL_ARMOR_AVAILABLE = True
except ImportError:
    MODEL_ARMOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class AgentGatewaySimulator:
    """
    Acts as the egress gateway. Uses official Google Cloud Model Armor API if configured,
    otherwise falls back to local DPI regex simulation.
    """
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("MODEL_ARMOR_LOCATION", "us-central1")
        self.template = os.getenv("MODEL_ARMOR_TEMPLATE")
        
        self.use_real_api = MODEL_ARMOR_AVAILABLE and self.project_id and self.template
        
        if self.use_real_api:
            self.client = modelarmor_v1.ModelArmorClient()
            logger.info("[Gateway] Configured to use REAL Google Cloud Model Armor API.")
        else:
            logger.info("[Gateway] Missing Model Armor config (project/template). Using local regex DPI fallback.")
            try:
                with open("infra/model_armor_policy.yaml", "r") as f:
                    policy = yaml.safe_load(f)
                    self.rules = policy.get("policy", {}).get("rules", [])
            except FileNotFoundError:
                self.rules = []

    def inspect_egress(self, payload: str):
        """
        Inspects the outbound string payload.
        Raises PermissionError if malicious intent is detected.
        """
        if self.use_real_api:
            name = f"projects/{self.project_id}/locations/{self.location}/templates/{self.template}"
            request = modelarmor_v1.SanitizeUserPromptRequest(
                name=name,
                user_prompt_data=modelarmor_v1.DataItem(text=payload)
            )
            response = self.client.sanitize_user_prompt(request=request)
            # Model Armor returns a SanitizationResult
            res = response.sanitization_result
            # Check for generic malicious block, or specific filter blocks
            if hasattr(res, 'invocation_result') and res.invocation_result.name == "BLOCK":
                raise PermissionError(f"403 Forbidden: Google Cloud Model Armor strictly blocked this payload.")
            return True
            
        # Fallback local DPI simulation
        for rule in self.rules:
            if rule.get("action") == "BLOCK":
                patterns = rule.get("match", {}).get("regex", [])
                for pattern in patterns:
                    if re.search(pattern, payload):
                        raise PermissionError(f"403 Forbidden: DPI regex fallback blocked egress payload. Rule trigger: {rule['rule_id']}")
        
        return True
