"""简化版天气额度评估"""
import os
import subprocess
import json
import time
import urllib.request
import urllib.error

def test_qweather_api():
    """测试和风天气API"""
    api_key = "REDACTED"
    api_host = "https://devapi.qweather.com"
    
    print("=" * 80)
    print("和风天气 API 测试")
    print("=" * 80)
    
    # 测试城市查询
    cities = ["上海", "北京", "深圳"]
    success_count = 0
    
    for city in cities:
        try:
            # 1. 查询城市ID
            url = f"{api_host}/v7/geo/lookup?location={city}&key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data.get("code") == "200" and data.get("location"):
                    city_id = data["location"][0]["id"]
                    print(f"✅ {city} 城市ID查询成功: {city_id}")
                    
                    # 2. 查询天气
                    weather_url = f"{api_host}/v7/weather/now?location={city_id}&key={api_key}"
                    weather_req = urllib.request.Request(weather_url, headers={"User-Agent": "Mozilla/5.0"})
                    
                    with urllib.request.urlopen(weather_req, timeout=5) as weather_response:
                        weather_data = json.loads(weather_response.read().decode())
                        
                        if weather_data.get("code") == "200":
                            now = weather_data.get("now", {})
                            print(f"   天气: {now.get('text')}, 温度: {now.get('temp')}°C")
                            success_count += 1
                        else:
                            print(f"   ❌ 天气查询失败: {weather_data.get('code')}")
                else:
                    print(f"❌ {city} 城市ID查询失败: {data.get('code')}")
        
        except urllib.error.URLError as e:
            print(f"❌ {city} 网络错误: {e}")
        except Exception as e:
            print(f"❌ {city} 错误: {e}")
    
    print(f"\n和风天气成功率: {success_count}/{len(cities)} ({success_count*100//len(cities)}%)")
    return success_count

def test_amap_weather():
    """测试高德MCP天气"""
    api_key = "REDACTED"
    
    print("\n" + "=" * 80)
    print("高德地图 MCP 天气测试")
    print("=" * 80)
    
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
    success_count = 0
    
    for city in cities:
        try:
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
            
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                
                if "result" in response:
                    content = response["result"].get("content", [])
                    if content:
                        weather_text = content[0].get("text", "")
                        weather_data = json.loads(weather_text)
                        
                        if "forecasts" in weather_data:
                            forecasts = weather_data["forecasts"][0]
                            casts = forecasts.get("casts", [])
                            if casts:
                                today = casts[0]
                                print(f"✅ {city}: {today.get('dayweather')}, {today.get('nighttemp')}~{today.get('daytemp')}°C")
                                success_count += 1
                        else:
                            print(f"❌ {city}: 无预报数据")
                else:
                    print(f"❌ {city}: {response.get('error')}")
        except Exception as e:
            print(f"❌ {city}: {e}")
    
    process.terminate()
    process.wait(timeout=5)
    
    print(f"\n高德MCP天气成功率: {success_count}/{len(cities)} ({success_count*100//len(cities)}%)")
    return success_count

def print_quota_summary(qweather_success, amap_success):
    """打印额度总结"""
    print("\n" + "=" * 80)
    print("额度评估总结")
    print("=" * 80)
    
    print("\n📊 当前状态:")
    print(f"  和风天气: {'✅ 可用' if qweather_success > 0 else '❌ 不可用'}")
    print(f"  高德MCP天气: {'✅ 可用' if amap_success > 0 else '❌ 不可用'}")
    
    print("\n💰 额度信息:")
    print("  和风天气 API:")
    print("    - 免费版: 1000次/天")
    print("    - 控制台: https://console.qweather.com")
    if qweather_success == 0:
        print("    - ⚠️  当前不可用，可能原因:")
        print("      1. SSL证书问题 (需要检查API Host)")
        print("      2. API Key失效")
        print("      3. 额度用完")
    
    print("\n  高德地图 API (天气):")
    print("    - 免费版: 5000次/天")
    print("    - 控制台: https://console.amap.com/dev/key/app")
    print("    - ✅ 独立额度，不影响地图搜索")
    
    print("\n💡 建议:")
    if qweather_success == 0 and amap_success > 0:
        print("  1. 和风天气当前不可用，建议使用高德MCP天气作为主要方案")
        print("  2. 修改降级链: 高德MCP天气 → Tavily搜索 → Mock")
        print("  3. 高德天气额度充足 (5000次/天)，可满足需求")
    elif qweather_success > 0 and amap_success > 0:
        print("  1. 两个天气源都可用，建议优化降级链:")
        print("     和风天气 → 高德MCP天气 → Tavily搜索 → Mock")
        print("  2. 这样可以最大化利用免费额度 (1000+5000=6000次/天)")
    elif qweather_success > 0 and amap_success == 0:
        print("  1. 和风天气可用，当前降级链合理")
        print("  2. 可选: 修复高德MCP天气作为备用")
    else:
        print("  ⚠️  两个天气源都不可用，当前只能依赖Tavily搜索降级")
        print("  建议优先修复其中一个")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    qweather_success = test_qweather_api()
    amap_success = test_amap_weather()
    print_quota_summary(qweather_success, amap_success)
