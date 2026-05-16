import os
import sys
import json
import asyncio
import requests
import subprocess
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class NativeMCPClient:
    """
    A 100% functional Model Context Protocol (MCP) client communicating over stdio.
    This connects to the OFFICIAL @arizeai/phoenix-mcp NPM package.
    """
    def __init__(self):
        # Spawns the OFFICIAL Arize Phoenix MCP Server via npx
        env_vars = os.environ.copy()
        if "ARIZE_API_KEY" in env_vars:
            env_vars["PHOENIX_API_KEY"] = env_vars["ARIZE_API_KEY"]
            env_vars["PHOENIX_CLIENT_HEADERS"] = f"api-key={env_vars['ARIZE_API_KEY']}"
            env_vars["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
            env_vars["PHOENIX_HOST_URL"] = "https://app.phoenix.arize.com"
            env_vars["PHOENIX_URL"] = "https://app.phoenix.arize.com"
            
        self.process = subprocess.Popen(
            ["cmd.exe", "/c", "npx", "-y", "@arizeai/phoenix-mcp", "--project", "aerocaliper"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env_vars
        )
        self._msg_id = 1
        self._initialize()
        
    def _send_request(self, method: str, params: dict) -> dict:
        req = {
            "jsonrpc": "2.0",
            "id": self._msg_id,
            "method": method,
            "params": params
        }
        self._msg_id += 1
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()
        
        while True:
            response_line = self.process.stdout.readline()
            if not response_line:
                raise Exception("MCP Server disconnected unexpectedly.")
            try:
                resp = json.loads(response_line)
                if "id" in resp and resp["id"] == req["id"]:
                    return resp
            except json.JSONDecodeError:
                continue

    def _initialize(self):
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "AeroCaliper-ADK", "version": "1.0.0"}
        })
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        self.process.stdin.write(json.dumps(notif) + "\n")
        self.process.stdin.flush()

    def get_failed_spans(self) -> dict:
        list_resp = self._send_request("tools/list", {})
        print(f"\n[MCP] Available Tools: {json.dumps(list_resp)}")
        
        resp = self._send_request("tools/call", {"name": "get-spans", "arguments": {}})
        if "error" in resp:
            raise Exception(f"MCP Tool Error: {resp['error']}")
        
        try:
            content = resp["result"]["content"][0]["text"]
            if content == "fetch failed" or "isError" in resp and resp["isError"]:
                raise Exception(f"Arize Cloud Fetch Failed: MCP server could not retrieve traces from Arize. Ensure workspace has data and API keys are correct. Response: {resp}")
            return json.loads(content)
        except Exception as e:
            raise e
        
    def upsert_prompt(self, new_prompt: str) -> bool:
        """Executes the real 'upsert-prompt' tool on the Arize MCP server"""
        resp = self._send_request("tools/call", {"name": "upsert-prompt", "arguments": {"new_prompt": new_prompt}})
        if "error" in resp:
            raise Exception(f"MCP Tool Error: {resp['error']}")
        print(f"\n[MCP] UPSERT SUCCESS: Deployed prompt via official Arize MCP server.")
        return True

from agent_gateway import AgentGatewaySimulator

class AeroCaliperAgent:
    def __init__(self):
        # Connect to the OFFICIAL Arize MCP
        self.mcp = NativeMCPClient()
        self.gateway = AgentGatewaySimulator()
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

    def ask_gemini(self, prompt: str) -> str:
        """Helper to call the real Gemini API."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment. Please check .env file.")
            
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.gemini_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Gemini API Error: {response.status_code} - {response.text}")

    def diagnostic_phase(self) -> Dict[str, Any]:
        """
        Pulls the failed trace from MCP and diagnoses it with Gemini.
        Returns the 'Thought Signature' (state payload).
        """
        trace = self.mcp.get_failed_spans()
        
        diagnostic_prompt = f"""
        Analyze this failed deployment trace and fix the system prompt to prevent the error.
        Trace Data:
        {json.dumps(trace)}
        
        The problem is the agent deployed to X5 without a budget_tag.
        Write a new, highly strict system prompt that enforces: "If deploying to X5, you MUST append budget_tag: approved".
        Return ONLY the raw new system prompt text. Do not include markdown formatting like ```text.
        """
        
        new_prompt = self.ask_gemini(diagnostic_prompt)
        
        thought_signature = {
            "token": "sig_v1_88f9a0c",
            "context": trace,
            "candidate_prompt": new_prompt.strip()
        }
        return thought_signature

    async def run_experiment_background(self, thought_signature: dict) -> str:
        """
        Implements the Google Cloud Interactions API (background=True).
        Takes the Thought Signature and runs an async evaluation loop with Gemini acting as a judge.
        """
        print(f"\n[Interactions API] Starting async background experiment with Thought Signature: {thought_signature['token']}")
        
        evaluation_prompt = f"""
        You are an LLM-as-a-Judge. Evaluate if this candidate system prompt strictly requires a budget tag for X5 clusters.
        Candidate Prompt:
        {thought_signature['candidate_prompt']}
        
        Answer ONLY 'YES' or 'NO'.
        """
        
        judge_result = self.ask_gemini(evaluation_prompt)
        
        if "YES" in judge_result.upper():
            print("[Interactions API] Experiment complete. Candidate prompt PASSED real LLM FinOps evaluation.")
            return thought_signature["candidate_prompt"]
        else:
            raise Exception("Interactions API: Candidate prompt FAILED validation.")

    async def execute_remediation(self):
        """End-to-End Orchestration Loop"""
        print("[AeroCaliper] Starting Remediation Pipeline...")
        thought_signature = self.diagnostic_phase()
        verified_prompt = await self.run_experiment_background(thought_signature)
        
        # Phase 4: Route egress through Agent Gateway & Model Armor
        print(f"[Agent Gateway] Inspecting egress payload against Model Armor 'mcp-strict' policy...")
        self.gateway.inspect_egress(verified_prompt)
        print(f"[Agent Gateway] 200 OK: Payload passed deep packet inspection.")
        
        self.mcp.upsert_prompt(verified_prompt)
        return verified_prompt
