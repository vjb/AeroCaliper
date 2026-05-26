import sys
import pytest
import asyncio
from mcp_client import StandardMCPClient

@pytest.mark.asyncio
async def test_mcp_visibility_get_spans(monkeypatch, capsys):
    """
    TDD Assertion: Mocking the orchestrator's get-spans tool call and capturing
    sys.stdout MUST yield a string containing [🚀 ARIZE MCP SERVER] Executing tool: get-spans.
    """
    client = StandardMCPClient()
    
    # Mock connect to avoid launching the actual mcp subprocess via npx
    async def mock_connect():
        class MockContent:
            text = '{"spans": [{"trace_id": "test_trace_123", "status": {"code": "ERROR"}, "evaluation_detail": "POLICY VIOLATION"}]}'
        class MockResult:
            isError = False
            content = [MockContent()]
            
        class MockSession:
            async def call_tool(self, name, arguments=None):
                return MockResult()
                
        client.session = MockSession()
        
    monkeypatch.setattr(client, "connect", mock_connect)
    
    # Call get_failed_spans
    await client.get_failed_spans()
    
    # Assert sys.stdout contains the aggressive visibility log
    captured = capsys.readouterr()
    assert "[🚀 ARIZE MCP SERVER] Executing tool: get-spans" in captured.out
