"""测试M5.2天气工具集成"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from agent_service.infra.tool_clients.mcp_gateway import MCPToolGateway

def test_weather_integration():
    """测试天气工具的完整降级链"""
    gateway = MCPToolGateway()
    
    print("=" * 80)
    print("M5.2 天气工具集成测试")
    print("=" * 80)
    
    cities = ["上海", "北京", "深圳"]
    
    for city in cities:
        print(f"\n测试城市: {city}")
        print("-" * 80)
        
        result = gateway.invoke("get_weather", {"city": city})
        
        provider = result.raw.get("provider") if result.raw else "unknown"
        
        if result.ok:
            print(f"✅ 成功")
            print(f"Provider: {provider}")
            print(f"Text: {result.text[:200]}...")
            
            # Check provider priority
            if provider == "amap_mcp":
                print("🎯 使用高德MCP (主)")
            elif provider == "qweather":
                print("🔄 使用和风天气 (备)")
            elif provider == "tavily":
                print("⚠️  降级到Tavily搜索")
            else:
                print(f"❓ 未知provider: {provider}")
        else:
            print(f"❌ 失败")
            print(f"Error: {result.error}")
            print(f"Text: {result.text}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_weather_integration()
