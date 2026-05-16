import yaml
import re

class AgentGatewaySimulator:
    """
    Simulates Google Cloud Agent Gateway & Model Armor.
    Intercepts outbound payloads and applies deep packet inspection.
    """
    def __init__(self):
        try:
            with open("infra/model_armor_policy.yaml", "r") as f:
                policy = yaml.safe_load(f)
                self.rules = policy.get("policy", {}).get("rules", [])
        except FileNotFoundError:
            self.rules = []

    def inspect_egress(self, payload: str):
        """
        Inspects the outbound string payload against Model Armor regex rules.
        Raises an exception simulating a 403 Forbidden if malicious intent is detected.
        """
        for rule in self.rules:
            if rule.get("action") == "BLOCK":
                patterns = rule.get("match", {}).get("regex", [])
                for pattern in patterns:
                    if re.search(pattern, payload):
                        raise PermissionError(f"403 Forbidden: Model Armor blocked egress payload. Rule trigger: {rule['rule_id']}")
        
        return True
