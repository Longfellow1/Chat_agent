"""查看高德MCP天气原始返回"""
import os
import subprocess
import json
import time

api_key = "REDACTED"

env = os.environ.copy()
env["AMAP_MAPS_API_KEY"] = api_key

process = subprocess.Popen(
    ["npx", "-y", "@amap/amap-maps-mcp-server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    text=True,
    bufsize=1,
)

time.sleep(2)

request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "maps_weather",
        "arguments": {"city": "上海"},
    },
}

request_line = json.dumps(request, ensure_ascii=False) + "\n"
process.stdin.write(request_line)
process.stdin.flush()

response_line = process.stdout.readline()
if response_line:
    response = json.loads(response_line.strip())
    print(json.dumps(response, ensure_ascii=False, indent=2))

process.terminate()
process.wait(timeout=5)
