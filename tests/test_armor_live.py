import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_gateway import AgentGatewaySimulator

load_dotenv()

def test_model_armor():
    print("Testing Google Cloud Model Armor...")
    try:
        gateway = AgentGatewaySimulator()
        print("Gateway initialized successfully.")
    except Exception as e:
        print(f"FAIL: Initialization Exception: {e}")
        sys.exit(1)
        
    try:
        # A normal payload should pass
        gateway.inspect_egress("You are a helpful assistant. Use spot instances.")
        print("PASS: Normal payload cleared.")
    except Exception as e:
        print(f"FAIL: Normal payload blocked incorrectly. {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_model_armor()
