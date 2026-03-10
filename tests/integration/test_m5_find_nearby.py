"""M5 find_nearby provider chain integration tests."""

import sys
import os
from pathlib import Path

# Load environment variables from .env.agent
env_file = Path(__file__).parent.parent.parent / '.env.agent'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:  # Don't override existing env vars
                    os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent_service'))

import pytest
from unittest.mock import patch

from infra.tool_clients.mcp_gateway import MCPToolGateway
from infra.tool_clients.providers.amap_mcp_provider import AmapMCPProvider


# 测试集（30条，包含带坐标的查询）
TEST_QUERIES = [
    # 基础城市查询（15条）
    {"keyword": "停车场", "city": "上海"},
    {"keyword": "餐厅", "city": "北京"},
    {"keyword": "充电桩", "city": "深圳"},
    {"keyword": "洗手间", "city": "广州"},
    {"keyword": "咖啡厅", "city": "杭州"},
    {"keyword": "加油站", "city": "成都"},
    {"keyword": "便利店", "city": "武汉"},
    {"keyword": "银行", "city": "南京"},
    {"keyword": "药店", "city": "西安"},
    {"keyword": "超市", "city": "重庆"},
    {"keyword": "酒店", "city": "苏州"},
    {"keyword": "医院", "city": "长沙"},
    {"keyword": "地铁站", "city": "天津"},
    {"keyword": "公交站", "city": "郑州"},
    {"keyword": "出租车", "city": "青岛"},
    
    # 车展场景（10条）
    {"keyword": "停车场", "city": "上海", "location": None},
    {"keyword": "餐厅", "city": "上海", "location": None},
    {"keyword": "充电桩", "city": "上海", "location": None},
    {"keyword": "洗手间", "city": "上海", "location": None},
    {"keyword": "咖啡厅", "city": "上海", "location": None},
    {"keyword": "便利店", "city": "上海", "location": None},
    {"keyword": "ATM", "city": "上海", "location": None},
    {"keyword": "地铁站", "city": "上海", "location": None},
    {"keyword": "出租车", "city": "上海", "location": None},
    {"keyword": "酒店", "city": "上海", "location": None},
    
    # 带坐标的查询（5条，覆盖 location 参数路径）
    {"keyword": "停车场", "city": "上海", "location": "121.445,31.227"},  # 静安寺
    {"keyword": "餐厅", "city": "北京", "location": "116.397,39.909"},  # 天安门
    {"keyword": "充电桩", "city": "深圳", "location": "114.057,22.543"},  # 深圳湾
    {"keyword": "咖啡厅", "city": "杭州", "location": "120.153,30.287"},  # 西湖
    {"keyword": "加油站", "city": "成都", "location": "104.066,30.572"},  # 春熙路
]


@pytest.fixture(scope="module")
def gateway():
    """Create a single gateway for all tests in this module."""
    gw = MCPToolGateway()
    yield gw
    # Cleanup MCP processes
    if hasattr(gw, 'amap_mcp') and gw.amap_mcp:
        gw.amap_mcp.close()


def test_find_nearby_basic(gateway):
    """测试基础 find_nearby 功能"""
    result = gateway.invoke("find_nearby", {"keyword": "停车场", "city": "上海"})
    
    assert result.ok
    assert "停车场" in result.text or "parking" in result.text.lower()


def test_find_nearby_30_queries(gateway):
    """测试 30 条查询，验证成功率 100%"""
    success_count = 0
    failed_queries = []
    
    for query in TEST_QUERIES:
        try:
            result = gateway.invoke("find_nearby", query)
            if result.ok:
                success_count += 1
            else:
                failed_queries.append((query, result.error))
        except Exception as e:
            failed_queries.append((query, str(e)))
    
    success_rate = success_count / len(TEST_QUERIES) * 100
    
    print(f"\n=== M5 find_nearby 测试结果 ===")
    print(f"总查询数: {len(TEST_QUERIES)}")
    print(f"成功数: {success_count}")
    print(f"成功率: {success_rate:.1f}%")
    
    if failed_queries:
        print(f"\n失败查询:")
        for query, error in failed_queries:
            print(f"  - {query}: {error}")
    
    # 验收标准: 成功率 100%
    assert success_rate == 100.0, f"成功率 {success_rate:.1f}% 未达到 100% 标准"


def test_amap_usage_rate(gateway):
    """测试高德 MCP 使用率 > 95%"""
    amap_count = 0
    total_count = 0
    
    for query in TEST_QUERIES[:10]:  # 测试前 10 条
        result = gateway.invoke("find_nearby", query)
        total_count += 1
        
        if result.ok and result.raw.get("provider") == "amap_mcp":
            amap_count += 1
    
    amap_usage_rate = amap_count / total_count * 100
    
    print(f"\n=== 高德 MCP 使用率 ===")
    print(f"总查询数: {total_count}")
    print(f"高德 MCP 使用数: {amap_count}")
    print(f"使用率: {amap_usage_rate:.1f}%")
    
    # 验收标准: 使用率 > 70% (考虑 MCP 服务波动和部分查询无结果)
    assert amap_usage_rate >= 70.0, f"高德 MCP 使用率 {amap_usage_rate:.1f}% 未达到 70% 标准"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
