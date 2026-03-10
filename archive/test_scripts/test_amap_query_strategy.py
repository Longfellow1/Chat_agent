"""
测试高德 API 对两种查询策略的支持

方案A: 结构化查询（先查地标 → 再查周边）
方案B: 直接查询（把实体直接发给高德）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.amap_mcp_client import AmapMCPClient


def test_strategy_a_structured():
    """方案A: 结构化查询"""
    print("=" * 80)
    print("方案A: 结构化查询（先查地标 → 再查周边）")
    print("=" * 80)
    
    client = AmapMCPClient()
    
    # 测试案例: "帮我找福州国贸周边的加油站"
    print("\n测试案例: 帮我找福州国贸周边的加油站")
    print("-" * 80)
    
    # Step 1: 查询地标坐标
    print("\nStep 1: 查询地标")
    print("调用: find_nearby(city='福州', location='国贸', keyword='加油站')")
    
    try:
        result = client.find_nearby(
            city="福州",
            location="国贸",
            keyword="加油站"
        )
        
        if result.ok:
            print(f"✅ 成功:")
            print(result.text)
            if result.raw and 'pois' in result.raw:
                print(f"\n共找到 {len(result.raw['pois'])} 个结果")
        else:
            print(f"❌ 失败: {result.error}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        client.close()


def test_strategy_b_direct():
    """方案B: 直接查询"""
    print("\n" + "=" * 80)
    print("方案B: 直接查询（把实体直接发给高德）")
    print("=" * 80)
    
    client = AmapMCPClient()
    
    # 测试案例: "帮我找福州国贸周边的加油站"
    print("\n测试案例: 帮我找福州国贸周边的加油站")
    print("-" * 80)
    
    # 直接查询
    print("\n直接查询:")
    print("调用: find_nearby(city='福州', keyword='国贸 加油站')")
    
    try:
        result = client.find_nearby(
            city="福州",
            keyword="国贸 加油站"
        )
        
        if result.ok:
            print(f"✅ 成功:")
            print(result.text)
            if result.raw and 'pois' in result.raw:
                print(f"\n共找到 {len(result.raw['pois'])} 个结果")
        else:
            print(f"❌ 失败: {result.error}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 对比: 只查加油站
    print("\n对比: 只查加油站（不带地标）")
    print("调用: find_nearby(city='福州', keyword='加油站')")
    
    try:
        result = client.find_nearby(
            city="福州",
            keyword="加油站"
        )
        
        if result.ok:
            print(f"✅ 成功:")
            print(result.text)
            if result.raw and 'pois' in result.raw:
                print(f"\n共找到 {len(result.raw['pois'])} 个结果")
        else:
            print(f"❌ 失败: {result.error}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        client.close()


def test_ambiguous_landmark():
    """测试歧义地标"""
    print("\n" + "=" * 80)
    print("测试歧义地标: 国贸（多个城市都有）")
    print("=" * 80)
    
    client = AmapMCPClient()
    
    cities = ["福州", "北京", "厦门"]
    
    for city in cities:
        print(f"\n{city} 的国贸:")
        print("-" * 80)
        
        try:
            result = client.find_nearby(
                city=city,
                keyword="国贸"
            )
            
            if result.ok:
                print(result.text)
            else:
                print(f"  ❌ 未找到: {result.error}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    client.close()


if __name__ == "__main__":
    test_strategy_a_structured()
    test_strategy_b_direct()
    test_ambiguous_landmark()
