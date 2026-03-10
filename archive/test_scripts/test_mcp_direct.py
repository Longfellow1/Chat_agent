"""Test MCP server directly."""
import json
import subprocess
import sys

# Test MCP server via stdio
process = subprocess.Popen(
    ["npx", "open-websearch@latest"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env={"MODE": "stdio", "DEFAULT_SEARCH_ENGINE": "bing"}
)

# Send MCP request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search",
        "arguments": {
            "query": "特斯拉 Model 3 价格",
            "limit": 3,
            "engines": ["bing"]
        }
    }
}

print("发送请求:")
print(json.dumps(request, indent=2, ensure_ascii=False))
print("\n" + "="*60)

try:
    stdout, stderr = process.communicate(
        input=json.dumps(request) + "\n",
        timeout=10
    )
    
    print("响应:")
    print(stdout[:1000])
    
    if stderr:
        print("\n错误:")
        print(stderr[:500])
        
except subprocess.TimeoutExpired:
    process.kill()
    print("✗ 超时")
except Exception as e:
    print(f"✗ 异常: {e}")
