"""评估天气工具的额度使用情况"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway

def test_weather_providers():
    """测试各个天气provider的可用性"""
    gateway = MCPToolGateway()
    
    print("=" * 80)
    print("天气工具额度评估报告")
    print("=" * 80)
    
    # 1. 检查配置
    print("\n1️⃣ 配置检查:")
    print(f"  和风天气 API Key: {'✅ 已配置' if gateway.qweather_key else '❌ 未配置'}")
    print(f"  和风天气 API Host: {gateway.qweather_host or 'https://devapi.qweather.com (默认)'}")
    print(f"  高德地图 API Key: {'✅ 已配置' if gateway.amap_key else '❌ 未配置'}")
    print(f"  Tavily API Key: {'✅ 已配置' if gateway.tavily_key else '❌ 未配置'}")
    
    # 2. 测试和风天气
    print("\n2️⃣ 和风天气 API 测试:")
    cities = ["上海", "北京", "深圳"]
    qweather_success = 0
    qweather_errors = []
    
    for city in cities:
        result = gateway._weather(city)
        provider = result.raw.get("provider") if result.raw else None
        
        if result.ok and provider == "qweather":
            qweather_success += 1
            print(f"  ✅ {city}: 成功 (和风天气)")
        else:
            error = result.error or "unknown"
            qweather_errors.append(f"{city}: {error}")
            print(f"  ❌ {city}: 失败 -> {provider or 'unknown'} (错误: {error})")
    
    print(f"\n  和风天气成功率: {qweather_success}/{len(cities)} ({qweather_success*100//len(cities)}%)")
    
    # 3. 测试高德MCP天气
    print("\n3️⃣ 高德地图 MCP 天气测试:")
    if gateway.amap_mcp:
        try:
            # 直接调用高德MCP的天气工具
            import subprocess
            import json
            import time
            
            env = os.environ.copy()
            env["AMAP_MAPS_API_KEY"] = gateway.amap_key
            
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
            
            amap_success = 0
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
                
                request_line = json.dumps(request) + "\n"
                process.stdin.write(request_line)
                process.stdin.flush()
                
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    if "result" in response:
                        amap_success += 1
                        print(f"  ✅ {city}: 成功 (高德MCP)")
                    else:
                        print(f"  ❌ {city}: 失败 (错误: {response.get('error')})")
            
            process.terminate()
            process.wait(timeout=5)
            
            print(f"\n  高德MCP天气成功率: {amap_success}/{len(cities)} ({amap_success*100//len(cities)}%)")
            
        except Exception as e:
            print(f"  ❌ 高德MCP初始化失败: {e}")
    else:
        print("  ⚠️  高德MCP未初始化")
    
    # 4. 额度评估
    print("\n4️⃣ 额度评估:")
    print("\n  和风天气 API:")
    print("    - 免费版额度: 1000次/天")
    print("    - 当前使用: 未知 (需要查看控制台)")
    print("    - 控制台: https://console.qweather.com")
    if qweather_success == 0:
        print("    - ⚠️  当前不可用，建议检查:")
        print("      1. API Host 是否正确 (可能需要自定义域名)")
        print("      2. API Key 是否有效")
        print("      3. 额度是否用完")
    
    print("\n  高德地图 API (天气):")
    print("    - 免费版额度: 5000次/天 (天气查询)")
    print("    - 当前使用: 未知 (需要查看控制台)")
    print("    - 控制台: https://console.amap.com/dev/key/app")
    print("    - ✅ 可作为和风天气的备用方案")
    
    print("\n  Tavily 搜索 (降级方案):")
    print("    - 免费版额度: 1000次/月")
    print("    - 当前使用: 未知")
    print("    - ⚠️  仅作为最后降级方案，返回搜索结果而非结构化数据")
    
    # 5. 建议
    print("\n5️⃣ 建议:")
    if qweather_success == 0:
        print("  ⚠️  和风天气当前不可用，建议:")
        print("    1. 优先修复和风天气 API (检查 API Host 配置)")
        print("    2. 或者将高德MCP天气作为主要方案")
        print("    3. 保留 Tavily 搜索作为最后降级")
    else:
        print("  ✅ 和风天气正常工作，当前降级链合理:")
        print("    和风天气 → Tavily 搜索 → Mock")
        print("  💡 可选优化: 在和风天气和Tavily之间插入高德MCP天气")
        print("    和风天气 → 高德MCP天气 → Tavily 搜索 → Mock")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_weather_providers()
