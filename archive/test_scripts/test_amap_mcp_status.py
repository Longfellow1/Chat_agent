"""验证高德 MCP 是否已打通"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway

def test_amap_mcp():
    """测试高德 MCP 是否返回真实数据"""
    gateway = MCPToolGateway()
    
    # 测试1: 基础查询
    print("=" * 60)
    print("测试1: 上海静安寺附近的咖啡厅")
    print("=" * 60)
    result = gateway.invoke("find_nearby", {
        "keyword": "咖啡厅",
        "city": "上海",
        "location": "静安寺"
    })
    
    print(f"Status: {'✅ OK' if result.ok else '❌ FAIL'}")
    print(f"Provider: {result.raw.get('provider') if result.raw else 'unknown'}")
    print(f"Text: {result.text[:200]}...")
    
    if result.raw and 'pois' in result.raw:
        pois = result.raw['pois']
        print(f"POI Count: {len(pois)}")
        if pois:
            print(f"First POI: {pois[0].get('name', 'unknown')}")
            print(f"Is Mock: {'[mock-nearby]' in result.text}")
    
    print()
    
    # 测试2: 无location的查询
    print("=" * 60)
    print("测试2: 北京的火锅")
    print("=" * 60)
    result2 = gateway.invoke("find_nearby", {
        "keyword": "火锅",
        "city": "北京",
        "location": None
    })
    
    print(f"Status: {'✅ OK' if result2.ok else '❌ FAIL'}")
    print(f"Provider: {result2.raw.get('provider') if result2.raw else 'unknown'}")
    print(f"Text: {result2.text[:200]}...")
    
    if result2.raw and 'pois' in result2.raw:
        pois = result2.raw['pois']
        print(f"POI Count: {len(pois)}")
        if pois:
            print(f"First POI: {pois[0].get('name', 'unknown')}")
            print(f"Is Mock: {'[mock-nearby]' in result2.text}")
    
    print()
    print("=" * 60)
    print("总结")
    print("=" * 60)
    
    is_real_data = (
        result.ok and 
        result.raw and 
        result.raw.get('provider') == 'amap_mcp' and
        '[mock-nearby]' not in result.text
    )
    
    if is_real_data:
        print("✅ 高德 MCP 已打通，返回真实 POI 数据")
    else:
        print("❌ 高德 MCP 未打通，仍返回 mock 数据")
        print(f"   - Provider: {result.raw.get('provider') if result.raw else 'none'}")
        print(f"   - Has mock marker: {'[mock-nearby]' in result.text}")

if __name__ == "__main__":
    test_amap_mcp()
