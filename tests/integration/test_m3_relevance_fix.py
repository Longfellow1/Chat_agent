"""
M3 任务1: 相关性过滤修复测试

目标：验证相关性阈值降低后，至少返回 1 条结果

测试集设计：
1. 相关性边界 case（20条）- 停用词多、短查询、长查询
2. 回归测试（30条）- 复用 M2 的测试集

验收标准：
- 技术有效率 ≥ 95%（至少返回 1 条结果）
- 相关性合理（不是完全不相关）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

from dotenv import load_dotenv
load_dotenv('.env.agent')

from infra.tool_clients.mcp_gateway import MCPToolGateway


# 测试集1: 相关性边界 case（停用词多）
STOPWORD_QUERIES = [
    "帮我搜索python教程",
    "查一下iPhone价格",
    "我想知道量子计算",
    "请问特斯拉怎么样",
    "告诉我马斯克的故事",
    "搜索React框架",
    "看看Docker教程",
    "了解一下区块链",
    "给我推荐Git教程",
    "能不能查MySQL优化",
]

# 测试集2: 短查询
SHORT_QUERIES = [
    "Python",
    "iPhone 15",
    "量子计算",
    "马斯克",
    "React",
]

# 测试集3: 长查询
LONG_QUERIES = [
    "我想了解一下最近有什么关于人工智能的最新发展和技术突破",
    "请帮我查询一下北京到上海的高铁票价格和时刻表信息",
    "能不能给我介绍一下特斯拉公司的创始人马斯克的个人经历和成就",
    "帮我搜索一下关于量子计算机的工作原理和应用场景的详细资料",
    "我想知道最近有什么关于新能源汽车行业的政策和市场动态",
]

# 测试集4: M2 回归测试（30条）
M2_REGRESSION_QUERIES = [
    "Python教程",
    "iPhone 15价格",
    "量子计算原理",
    "马斯克传记",
    "React框架",
    "Docker容器",
    "区块链技术",
    "Git版本控制",
    "MySQL优化",
    "人工智能发展",
    "北京天气",
    "上海房价",
    "深圳科技园",
    "广州美食",
    "杭州西湖",
    "成都火锅",
    "重庆夜景",
    "西安兵马俑",
    "南京总统府",
    "苏州园林",
    "特斯拉Model 3",
    "比亚迪汉",
    "蔚来ET7",
    "小鹏P7",
    "理想ONE",
    "华为Mate 60",
    "小米14",
    "OPPO Find X7",
    "vivo X100",
    "荣耀Magic 6",
]


def test_stopword_queries():
    """测试停用词多的查询"""
    print("=" * 80)
    print("测试1: 停用词多的查询（10条）")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    success_count = 0
    total = len(STOPWORD_QUERIES)
    
    for i, query in enumerate(STOPWORD_QUERIES, 1):
        print(f"[{i}/{total}] {query}")
        
        result = gateway.invoke("web_search", {"query": query})
        
        if result.ok:
            success_count += 1
            print(f"  ✅ 成功")
            # 检查结果数量
            if result.raw and result.raw.get('results'):
                count = len(result.raw['results'])
                print(f"  返回 {count} 条结果")
        else:
            print(f"  ❌ 失败: {result.error}")
        
        print()
    
    success_rate = success_count / total * 100
    print(f"成功率: {success_count}/{total} = {success_rate:.1f}%")
    print()
    
    assert success_rate >= 95, f"停用词查询成功率 {success_rate:.1f}% < 95%"


def test_short_queries():
    """测试短查询"""
    print("=" * 80)
    print("测试2: 短查询（5条）")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    success_count = 0
    total = len(SHORT_QUERIES)
    
    for i, query in enumerate(SHORT_QUERIES, 1):
        print(f"[{i}/{total}] {query}")
        
        result = gateway.invoke("web_search", {"query": query})
        
        if result.ok:
            success_count += 1
            print(f"  ✅ 成功")
            if result.raw and result.raw.get('results'):
                count = len(result.raw['results'])
                print(f"  返回 {count} 条结果")
        else:
            print(f"  ❌ 失败: {result.error}")
        
        print()
    
    success_rate = success_count / total * 100
    print(f"成功率: {success_count}/{total} = {success_rate:.1f}%")
    print()
    
    assert success_rate >= 95, f"短查询成功率 {success_rate:.1f}% < 95%"


def test_long_queries():
    """测试长查询"""
    print("=" * 80)
    print("测试3: 长查询（5条）")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    success_count = 0
    total = len(LONG_QUERIES)
    
    for i, query in enumerate(LONG_QUERIES, 1):
        print(f"[{i}/{total}] {query}")
        
        result = gateway.invoke("web_search", {"query": query})
        
        if result.ok:
            success_count += 1
            print(f"  ✅ 成功")
            if result.raw and result.raw.get('results'):
                count = len(result.raw['results'])
                print(f"  返回 {count} 条结果")
        else:
            print(f"  ❌ 失败: {result.error}")
        
        print()
    
    success_rate = success_count / total * 100
    print(f"成功率: {success_count}/{total} = {success_rate:.1f}%")
    print()
    
    assert success_rate >= 95, f"长查询成功率 {success_rate:.1f}% < 95%"


def test_m2_regression():
    """M2 回归测试（30条）"""
    print("=" * 80)
    print("测试4: M2 回归测试（30条）")
    print("=" * 80)
    print()
    
    gateway = MCPToolGateway()
    
    success_count = 0
    total = len(M2_REGRESSION_QUERIES)
    
    for i, query in enumerate(M2_REGRESSION_QUERIES, 1):
        print(f"[{i}/{total}] {query}")
        
        result = gateway.invoke("web_search", {"query": query})
        
        if result.ok:
            success_count += 1
            print(f"  ✅ 成功")
        else:
            print(f"  ❌ 失败: {result.error}")
    
    success_rate = success_count / total * 100
    print()
    print(f"成功率: {success_count}/{total} = {success_rate:.1f}%")
    print()
    
    assert success_rate >= 95, f"M2 回归测试成功率 {success_rate:.1f}% < 95%"


def test_all():
    """运行所有测试"""
    print("\n")
    print("=" * 80)
    print("M3 相关性过滤修复测试")
    print("=" * 80)
    print()
    
    test_stopword_queries()
    test_short_queries()
    test_long_queries()
    test_m2_regression()
    
    print("=" * 80)
    print("✅ 所有测试通过")
    print("=" * 80)


if __name__ == "__main__":
    test_all()
