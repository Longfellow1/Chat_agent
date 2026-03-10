"""
相关性检查：验证高德返回的 POI 是否与 query 相关

目标：
1. 确认 CategoryFilter 是否还有必要
2. 定义"有效"的口径：非空 vs 相关
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.amap_mcp_client import AmapMCPClient


TEST_CASES = [
    # 明确类别
    {"query": "北京国贸附近的咖啡厅", "city": "北京", "keyword": "国贸 咖啡厅", "expected_category": "咖啡"},
    {"query": "上海静安寺周边的火锅", "city": "上海", "keyword": "静安寺 火锅", "expected_category": "火锅"},
    {"query": "深圳南山附近的加油站", "city": "深圳", "keyword": "南山 加油站", "expected_category": "加油站"},
    
    # 模糊类别
    {"query": "北京国贸附近有什么好吃的", "city": "北京", "keyword": "国贸 好吃的", "expected_category": "餐饮"},
    {"query": "上海静安寺周边的美食", "city": "上海", "keyword": "静安寺 美食", "expected_category": "餐饮"},
    
    # 品牌
    {"query": "北京国贸附近的星巴克", "city": "北京", "keyword": "国贸 星巴克", "expected_category": "星巴克"},
]


def check_relevance_manual(poi_name: str, expected_category: str) -> bool:
    """人工判断 POI 是否与期望类别相关"""
    name_lower = poi_name.lower()
    
    # 咖啡
    if expected_category == "咖啡":
        return any(kw in name_lower for kw in ["咖啡", "coffee", "cafe", "星巴克", "瑞幸", "manner", "costa"])
    
    # 火锅
    if expected_category == "火锅":
        return any(kw in name_lower for kw in ["火锅", "hotpot", "海底捞", "呷哺", "小肥羊", "巴奴"])
    
    # 加油站
    if expected_category == "加油站":
        return any(kw in name_lower for kw in ["加油", "中石油", "中石化", "壳牌", "bp"])
    
    # 餐饮（宽泛）
    if expected_category == "餐饮":
        return any(kw in name_lower for kw in ["餐", "饭", "食", "厅", "馆", "店", "火锅", "烤肉", "面", "粥", "菜"])
    
    # 星巴克
    if expected_category == "星巴克":
        return "星巴克" in name_lower or "starbucks" in name_lower
    
    return False


def test_relevance():
    """测试相关性"""
    print("=" * 80)
    print("相关性检查测试")
    print("=" * 80)
    print()
    
    client = AmapMCPClient()
    
    total_queries = len(TEST_CASES)
    total_pois = 0
    relevant_pois = 0
    
    for i, case in enumerate(TEST_CASES, 1):
        query = case['query']
        city = case['city']
        keyword = case['keyword']
        expected = case['expected_category']
        
        print(f"[{i}/{total_queries}] {query}")
        print(f"  Keyword: {keyword}")
        print(f"  Expected: {expected}")
        
        result = client.find_nearby(city=city, keyword=keyword)
        
        if result.ok and result.raw and result.raw.get('pois'):
            pois = result.raw['pois'][:5]  # 只看前5个
            print(f"  返回 {len(pois)} 个 POI:")
            
            for j, poi in enumerate(pois, 1):
                name = poi.get('name', 'N/A')
                is_relevant = check_relevance_manual(name, expected)
                total_pois += 1
                if is_relevant:
                    relevant_pois += 1
                
                status = "✅" if is_relevant else "❌"
                print(f"    {j}. {status} {name}")
        else:
            print(f"  ❌ 无结果")
        
        print()
    
    # 统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    print(f"总查询数: {total_queries}")
    print(f"总 POI 数: {total_pois}")
    print(f"相关 POI 数: {relevant_pois}")
    print(f"相关率: {relevant_pois/total_pois*100:.1f}%" if total_pois > 0 else "N/A")
    
    client.close()


if __name__ == "__main__":
    test_relevance()
