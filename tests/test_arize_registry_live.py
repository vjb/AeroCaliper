import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_arize_registry():
    print("Testing Arize Prompt Registry (phoenix.client.get_prompt)...")
    try:
        from phoenix.client import Client
        client = Client()
        prompt_obj = client.prompts.get(name="aerocaliper-finops-routing-agent")
        print(f"PASS: Successfully retrieved prompt. Template starts with: {prompt_obj.template[:50]}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: Failed to pull prompt from Arize Registry. {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_arize_registry()
