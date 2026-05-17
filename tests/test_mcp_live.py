import os
import sys
import asyncio
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aerocaliper import StandardMCPClient

load_dotenv()

async def run_test():
    print("Testing Arize Phoenix MCP Integration...")
    client = StandardMCPClient()
    try:
        await client.connect()
        # Test fetching span
        try:
            span = await client.get_failed_spans()
            print(f"PASS: span retrieved: {span}")
        except Exception as e:
            print(f"FAIL: get_failed_spans raised exception: {e}")
            sys.exit(1)
            

    except Exception as e:
        print(f"FAIL: MCP connection failed: {e}")
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_test())
