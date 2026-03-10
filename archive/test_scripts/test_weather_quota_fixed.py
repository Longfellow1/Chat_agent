"""修复编码问题的天气额度评估"""
import os
import subprocess
import json
import time
import urllib.request
import urllib.error
import urllib.parse

def test_qweather_api():
    """测试和风天气API"""
    api_key = "REDACTED"
    api_host = "https://devapi.qweather.com"
    
    print("=" * 80)
    print("和风天气 API 测试")
    print("=" * 80)
    
    cities = ["上海", "北京", "深圳"]
    success_count = 0
    
    for city in cities:
        try:
            # URL encode city name
            encoded_city = urllib.parse.quote(city)
            url = f"{api_host}/v7/geo/lookup?location={encoded_city}&key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get("code") == "200" and data.get("location"):
                    city_id = data["location"][0]["id"]
                    print(f"✅ {city} 城市ID查询成功: {city_id}")
                    
                    # Query weather
                    weather_url = f"{api_host}/v7/weather/now?location={city_id}&key={api_key}"
                    weather_req = urllib.request.Request(weather_url, headers={"User-Agent": "Mozilla/5.0"})
                    
                    with urllib.request.urlopen(weather_req, timeout=5) as weather_response:
                        weather_data = json.loads(weather_response.read().decode('utf-8'))
                        
                        if weather_data.get("code") == "200":
                            now = weather_data.get("now", {})
                            print(f"   天气: {now.get('text')}, 温度: {now.get('temp')}°C")
                            success_count += 1
                        else:
                            print(f"   ❌ 天气查询失败: code={weather_data.get('code')}")
                else:
                    print(f"❌ {city} 城市ID查询失败: code={data.get('code')}")
        
        except urllib.error.URLError as e:
            print(f"❌ {city} 网络错误: {e.reason if hasattr(e, 'reason') else e}")
        except Exception as e:
            print(f"❌ {city} 错误: {type(e).__name__}: {e}")
    
    print(f"\n和风天气成功率: {success_count}/{len(cities)} ({success_count*100//len(cities) if len(cities) > 0 else 0}%)")
    return success_count

def test_amap_weather():
    """测试高德MCP天气"""
    api_key = "REDACTED"
    
    print("\n" + "=" * 80)
    print("高德地图 MCP 天气测试")
    print("=" * 80)
    
    env = os.environ.copy()
    env["AMAP_MAPS_API_KEY"] = api_key
    
    try:
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
                            
                            if "forecasts" in weather_data and weather_data["forecasts"]:
                                casts = weather_data["forecasts"][0].get("casts", [])
                                if casts:
                                    today = casts[0]
                                    print(f"✅ {city}: {today.get('dayweather')}, {today.get('nighttemp')}~{today.get('daytemp')}°C")
                                    success_count += 1
                                else:
                                    print(f"❌ {city}: 无预报数据")
                            else:
                                print(f"❌ {city}: 数据格式错误")
                    else:
                        error = response.get('error', {})
                        print(f"❌ {city}: {error.get('message', error)}")
                else:
                    print(f"❌ {city}: 无响应")
            except Exception as e:
                print(f"❌ {city}: {type(e).__name__}: {e}")
        
        process.terminate()
        process.wait(timeout=5)
        
        print(f"\n高德MCP天气成功率: {success_count}/{len(cities)} ({success_count*100//len(cities) if len(cities) > 0 else 0}%)")
        return success_count
    
    except Exception as e:
        print(f"❌ 高德MCP初始化失败: {type(e).__name__}: {e}")
        return 0

def print_quota_summary(qweather_success, amap_success):
    """打印额度总结"""
    print("\n" + "=" * 80)
    print("额度评估总结")
    print("=" * 80)
    
    print("\n📊 当前状态:")
    print(f"  和风天气: {'✅ 可用' if qweather_success > 0 else '❌ 不可用'}")
    print(f"  高德MCP天气: {'✅ 可用' if amap_success > 0 else '❌ 不可用'}")
    
    print("\n💰 额度信息:")
    print("\n  【和风天气 API】")
    print("    免费版额度: 1000次/天")
    print("    控制台: https://console.qweather.com")
    if qweather_success == 0:
        print("    状态: ⚠️  当前不可用")
        print("    可能原因:")
        print("      1. SSL证书问题 (UNEXPECTED_EOF_WHILE_READING)")
        print("      2. API Host配置错误 (可能需要自定义域名)")
        print("      3. API Key失效或额度用完")
    else:
        print("    状态: ✅ 正常工作")
        print("    剩余额度: 需登录控制台查看")
    
    print("\n  【高德地图 API - 天气查询】")
    print("    免费版额度: 5000次/天")
    print("    控制台: https://console.amap.com/dev/key/app")
    print("    特点: 独立额度，不影响地图搜索 (30万次/天)")
    if amap_success > 0:
        print("    状态: ✅ 正常工作")
        print("    剩余额度: 需登录控制台查看")
    else:
        print("    状态: ⚠️  测试失败 (可能是临时问题)")
    
    print("\n  【Tavily 搜索 - 降级方案】")
    print("    免费版额度: 1000次/月")
    print("    特点: 返回搜索结果，非结构化天气数据")
    print("    状态: 作为最后降级方案")
    
    print("\n💡 建议:")
    if qweather_success == 0 and amap_success > 0:
        print("\n  方案1: 使用高德MCP天气作为主要方案")
        print("    降级链: 高德MCP天气 → Tavily搜索 → Mock")
        print("    优点: 5000次/天额度充足")
        print("    实施: 修改 mcp_gateway.py 的 _weather() 方法")
        
    elif qweather_success > 0 and amap_success > 0:
        print("\n  方案1: 优化降级链，最大化利用免费额度")
        print("    降级链: 和风天气 → 高德MCP天气 → Tavily搜索 → Mock")
        print("    总额度: 1000 + 5000 = 6000次/天")
        print("    实施: 在 _weather() 方法中添加高德MCP作为第二级降级")
        
        print("\n  方案2: 保持现状 (推荐)")
        print("    降级链: 和风天气 → Tavily搜索 → Mock")
        print("    优点: 简单稳定，1000次/天通常够用")
        print("    何时切换: 当和风天气额度不足时")
        
    elif qweather_success > 0 and amap_success == 0:
        print("\n  当前方案: 和风天气 → Tavily搜索 → Mock")
        print("    状态: ✅ 正常工作")
        print("    额度: 1000次/天")
        print("    建议: 保持现状，监控额度使用情况")
        
    else:
        print("\n  ⚠️  两个天气源都不可用")
        print("    当前只能依赖 Tavily 搜索降级 (1000次/月)")
        print("    建议:")
        print("      1. 优先修复和风天气 (检查API Host配置)")
        print("      2. 或使用高德MCP天气 (检查MCP服务)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    qweather_success = test_qweather_api()
    amap_success = test_amap_weather()
    print_quota_summary(qweather_success, amap_success)
