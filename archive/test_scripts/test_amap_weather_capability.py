"""测试高德地图MCP是否支持天气查询"""
import os
import subprocess
import json
import time

def test_amap_mcp_tools():
    """列出高德MCP支持的所有工具"""
    api_key = os.getenv("AMAP_API_KEY", "").strip()
    if not api_key:
        print("❌ AMAP_API_KEY not set")
        return
    
    env = os.environ.copy()
    env["AMAP_MAPS_API_KEY"] = api_key
    
    # Start MCP server
    process = subprocess.Popen(
        ["npx", "-y", "@amap/amap-maps-mcp-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1,
    )
    
    try:
        # Wait for server to start
        time.sleep(2)
        
        # List tools
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        }
        
        request_line = json.dumps(request) + "\n"
        process.stdin.write(request_line)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            
            if "result" in response:
                tools = response["result"].get("tools", [])
                print(f"✅ 高德MCP支持 {len(tools)} 个工具:\n")
                
                weather_tools = []
                for tool in tools:
                    name = tool.get("name", "")
                    description = tool.get("description", "")
                    print(f"  - {name}: {description}")
                    
                    if "weather" in name.lower() or "天气" in description:
                        weather_tools.append(tool)
                
                if weather_tools:
                    print(f"\n✅ 发现 {len(weather_tools)} 个天气相关工具:")
                    for tool in weather_tools:
                        print(f"  - {tool['name']}: {tool['description']}")
                        print(f"    参数: {json.dumps(tool.get('inputSchema', {}), ensure_ascii=False, indent=6)}")
                else:
                    print("\n❌ 未发现天气相关工具")
            else:
                print(f"❌ Error: {response.get('error')}")
        else:
            print("❌ No response from MCP server")
    
    finally:
        process.terminate()
        process.wait(timeout=5)

if __name__ == "__main__":
    test_amap_mcp_tools()
