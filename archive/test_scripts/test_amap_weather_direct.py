"""直接测试高德MCP天气"""
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

cities = ["上海", "北京", "深圳"]

for city in cities:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "maps_weather",
            "arguments": {"city": city},
        },
    }
    
    request_line = json.dumps(request, ensure_ascii=False) + "\n"
    process.stdin.write(request_line)
    process.stdin.flush()
    
    response_line = process.stdout.readline()
    if response_line:
        response = json.loads(response_line.strip())
        
        if "result" in response:
            content = response["result"].get("content", [])
            if content:
                weather_text = content[0].get("text", "")
                weather_data = json.loads(weather_text) if isinstance(weather_text, str) else weather_text
                
                print(f"\n{city}:")
                print(f"  city: {weather_data.get('city')}")
                print(f"  forecasts: {len(weather_data.get('forecasts', []))}")
                
                if "forecasts" in weather_data and weather_data["forecasts"]:
                    forecast = weather_data["forecasts"][0]
                    print(f"  forecast.city: {forecast.get('city')}")
                    print(f"  forecast.casts: {len(forecast.get('casts', []))}")
                    
                    casts = forecast.get("casts", [])
                    if casts:
                        print(f"  ✅ 有预报数据")
                        for cast in casts[:2]:
                            print(f"    {cast.get('date')}: {cast.get('dayweather')}, {cast.get('nighttemp')}~{cast.get('daytemp')}°C")
                    else:
                        print(f"  ❌ casts为空")
                else:
                    print(f"  ❌ 无forecasts")

process.terminate()
process.wait(timeout=5)
