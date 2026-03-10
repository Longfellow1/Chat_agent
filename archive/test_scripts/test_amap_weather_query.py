"""测试高德MCP天气查询功能"""
import os
import subprocess
import json
import time

def test_weather_query(city: str):
    """测试天气查询"""
    api_key = os.getenv("AMAP_API_KEY", "REDACTED").strip()
    
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
        
        # Call weather tool
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "maps_weather",
                "arguments": {"city": city},
            },
        }
        
        request_line = json.dumps(request) + "\n"
        process.stdin.write(request_line)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            
            if "result" in response:
                content = response["result"].get("content", [])
                if content:
                    weather_text = content[0].get("text", "")
                    weather_data = json.loads(weather_text) if isinstance(weather_text, str) else weather_text
                    
                    print(f"✅ {city} 天气查询成功:")
                    print(json.dumps(weather_data, ensure_ascii=False, indent=2))
                    
                    # 检查数据结构
                    if "lives" in weather_data:
                        lives = weather_data["lives"]
                        if lives:
                            live = lives[0]
                            print(f"\n📊 实时天气:")
                            print(f"  城市: {live.get('city')}")
                            print(f"  天气: {live.get('weather')}")
                            print(f"  温度: {live.get('temperature')}°C")
                            print(f"  湿度: {live.get('humidity')}%")
                            print(f"  风向: {live.get('winddirection')}")
                            print(f"  风力: {live.get('windpower')}级")
                            print(f"  更新时间: {live.get('reporttime')}")
                    
                    if "forecasts" in weather_data:
                        forecasts = weather_data["forecasts"]
                        if forecasts and "casts" in forecasts[0]:
                            casts = forecasts[0]["casts"]
                            print(f"\n📅 未来天气预报 ({len(casts)}天):")
                            for cast in casts[:3]:
                                print(f"  {cast.get('date')}: {cast.get('dayweather')}, {cast.get('nighttemp')}~{cast.get('daytemp')}°C")
                else:
                    print(f"❌ 无天气数据")
            else:
                print(f"❌ Error: {response.get('error')}")
        else:
            print("❌ No response from MCP server")
    
    finally:
        process.terminate()
        process.wait(timeout=5)

if __name__ == "__main__":
    print("=" * 60)
    print("测试1: 上海天气")
    print("=" * 60)
    test_weather_query("上海")
    
    print("\n" + "=" * 60)
    print("测试2: 北京天气")
    print("=" * 60)
    test_weather_query("北京")
