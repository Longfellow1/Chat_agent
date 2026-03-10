"""
M1 任务3: 真实地标端到端测试

使用真实存在的地标测试简化方案
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway


# 真实地标测试集
REAL_LANDMARK_QUERIES = [
    # 北京
    {"query": "北京国贸附近的咖啡厅", "city": "北京", "landmark": "国贸", "category": "咖啡"},
    {"query": "北京三里屯周边的火锅", "city": "北京", "landmark": "三里屯", "category": "火锅"},
    {"query": "北京西单附近的商场", "city": "北京", "landmark": "西单", "category": "商场"},
    
    # 上海
    {"query": "上海静安寺附近的咖啡厅", "city": "上海", "landmark": "静安寺", "category": "咖啡"},
    {"query": "上海徐家汇周边的餐厅", "city": "上海", "landmark": "徐家汇", "category": "餐厅"},
    {"query": "上海人民广场附近的酒店", "city": "上海", "landmark": "人民广场", "category": "酒店"},
    
    # 广州
    {"query": "广州天河城附近的美食", "city": "广州", "landmark": "天河城", "category": "美食"},
    {"query": "广州珠江新城周边的咖啡店", "city": "广州", "landmark": "珠江新城", "category": "咖啡"},
    
    # 深圳
    {"query": "深圳华强北附近的餐厅", "city": "深圳", "landmark": "华强北", "category": "餐厅"},
    {"query": "深圳南山周边的火锅", "city": "深圳", "landmark": "南山", "category": "火锅"},
    
    # 杭州
    {"query": "杭州西湖附近的茶馆", "city": "杭州", "landmark": "西湖", "category": "茶馆"},
    {"query": "杭州湖滨周边的商场", "city": "杭州", "landmark": "湖滨", "category": "商场"},
    
    # 成都
    {"query": "成都春熙路附近的火锅", "city": "成都", "landmark": "春熙路", "category": "火锅"},
    {"query": "成都太古里周边的咖啡厅", "city": "成都", "landmark": "太古里", "category": "咖啡"},
    
    # 重庆
    {"query": "重庆解放碑附近的火锅", "city": "重庆", "landmark": "解放碑", "category": "火锅"},
    
    # 武汉
    {"query": "武汉光谷附近的餐厅", "city": "武汉", "landmark": "光谷", "category": "餐厅"},
    {"query": "武汉江汉路周边的商场", "city": "武汉", "landmark": "江汉路", "category": "商场"},
    
    # 南京
    {"query": "南京新街口附近的咖啡厅", "city": "南京", "landmark": "新街口", "category": "咖啡"},
    
    # 西安
    {"query": "西安小寨附近的美食", "city": "西安", "landmark": "小寨", "category": "美食"},
    
    # 福州
    {"query": "福州国贸附近的加油站", "city": "福州", "landmark": "国贸", "category": "加油站"},
]


def test_real_landmarks():
    """测试真实地标"""
    print("=" * 80)
    print(f"M1 任务3: 真实地标端到端测试")
    print(f"测试集: {len(REAL_LANDMARK_QUERIES)} 条")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    results = []
    success_count = 0
    has_pois_count = 0
    total = len(REAL_LANDMARK_QUERIES)
    
    for i, item in enumerate(REAL_LANDMARK_QUERIES, 1):
        query = item['query']
        
        print(f"[{i}/{total}] {query}")
        
        try:
            # 调用完整链路
            result, intent = gateway.invoke_with_intent("find_nearby", query)
            
            # 打印调试信息
            if intent:
                tool_args = intent.to_tool_args()
                print(f"  Tool args: {tool_args}")
            
            # 检查结果
            has_pois = False
            poi_count = 0
            
            if result.ok and result.raw and 'pois' in result.raw:
                pois = result.raw['pois']
                poi_count = len(pois)
                has_pois = poi_count > 0
                
                if has_pois:
                    has_pois_count += 1
                    success_count += 1
                    print(f"  ✅ 成功: 返回 {poi_count} 个 POI")
                    # 打印前3个POI
                    for j, poi in enumerate(pois[:3], 1):
                        print(f"    {j}. {poi.get('name', 'N/A')} - {poi.get('address', 'N/A')}")
                else:
                    print(f"  ⚠️  返回空: pois=[]")
            else:
                print(f"  ❌ 失败: {result.error if not result.ok else 'no pois in raw'}")
            
            results.append({
                'query': query,
                'city': item['city'],
                'landmark': item['landmark'],
                'category': item['category'],
                'ok': result.ok,
                'has_pois': has_pois,
                'poi_count': poi_count,
                'error': result.error if not result.ok else None,
            })
            
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'query': query,
                'city': item['city'],
                'landmark': item['landmark'],
                'category': item['category'],
                'ok': False,
                'has_pois': False,
                'poi_count': 0,
                'error': str(e),
            })
        
        print()
    
    # 统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    print(f"工具调用成功率: {success_count}/{total} = {success_count/total*100:.1f}%")
    print(f"返回有效 POI 率: {has_pois_count}/{total} = {has_pois_count/total*100:.1f}%")
    
    # 按城市统计
    print()
    print("按城市统计:")
    city_stats = {}
    for r in results:
        city = r['city']
        if city not in city_stats:
            city_stats[city] = {'total': 0, 'success': 0}
        city_stats[city]['total'] += 1
        if r['has_pois']:
            city_stats[city]['success'] += 1
    
    for city, stats in sorted(city_stats.items()):
        rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {city}: {stats['success']}/{stats['total']} = {rate:.1f}%")
    
    # 失败案例
    print()
    print("=" * 80)
    print("失败案例")
    print("=" * 80)
    
    failures = [r for r in results if not r['has_pois']]
    if failures:
        for r in failures:
            print(f"- {r['query']}")
            print(f"  city={r['city']}, landmark={r['landmark']}, category={r['category']}")
            print(f"  error={r['error']}")
    else:
        print("无失败案例 ✅")
    
    # 关闭 gateway
    gateway.close()
    
    return results


if __name__ == "__main__":
    test_real_landmarks()
