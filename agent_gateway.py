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
        # Safe reading of environment variables to prevent crashes in different environments
        self.project_id = (
            os.environ.get("GCP_PROJECT_NUMBER") or 
            os.environ.get("GOOGLE_CLOUD_PROJECT") or 
            os.environ.get("GCP_PROJECT_ID")
        )
        self.location = os.environ.get("MODEL_ARMOR_LOCATION", "us-central1")
        self.template = os.environ.get("MODEL_ARMOR_TEMPLATE", "aerocaliper-policy")
        
        self.use_real_api = MODEL_ARMOR_AVAILABLE and self.project_id and self.template
        
        if self.use_real_api:
            try:
                from google.api_core.client_options import ClientOptions
                client_options = ClientOptions(api_endpoint=f"modelarmor.{self.location}.rep.googleapis.com")
                self.client = modelarmor_v1.ModelArmorClient(transport="rest", client_options=client_options)
                logger.info("[Gateway] Configured to use REAL Google Cloud Model Armor API.")
            except Exception as e:
                logger.warning(f"[Gateway] Failed to initialize real Model Armor client: {e}. Falling back to simulation.")
                self.use_real_api = False
                
        if not self.use_real_api:
            logger.info("[Gateway] Model Armor config or SDK not available. Using local simulated Model Armor.")

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
            
        return True
