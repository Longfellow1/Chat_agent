"""M5.2 get_weather provider chain integration tests."""

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
                if key not in os.environ:
                    os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agent_service'))

import pytest

from infra.tool_clients.mcp_gateway import MCPToolGateway


# 测试集（20条，覆盖车展场景）
TEST_QUERIES = [
    # 基础城市天气（10条）
    {"city": "北京"},
    {"city": "上海"},
    {"city": "深圳"},
    {"city": "广州"},
    {"city": "成都"},
    {"city": "杭州"},
    {"city": "武汉"},
    {"city": "南京"},
    {"city": "西安"},
    {"city": "重庆"},
    
    # 车展相关场景（10条）
    {"city": "嘉定"},
    {"city": "青浦"},
    {"city": "松江"},
    {"city": "浦东"},
    {"city": "闵行"},
    {"city": "宝山"},
    {"city": "徐汇"},
    {"city": "静安"},
    {"city": "黄浦"},
    {"city": "虹口"},
]


@pytest.fixture(scope="module")
def gateway():
    """Create a single gateway for all tests in this module."""
    gw = MCPToolGateway()
    yield gw


def test_get_weather_basic(gateway):
    """测试基础 get_weather 功能"""
    result = gateway.invoke("get_weather", {"city": "上海"})
    
    assert result.ok
    assert "上海" in result.text
    assert "°C" in result.text


def test_get_weather_20_queries(gateway):
    """测试 20 条查询，验证成功率 100%"""
    success_count = 0
    failed_queries = []
    
    for query in TEST_QUERIES:
        try:
            result = gateway.invoke("get_weather", query)
            if result.ok:
                success_count += 1
            else:
                failed_queries.append((query, result.error))
        except Exception as e:
            failed_queries.append((query, str(e)))
    
    success_rate = success_count / len(TEST_QUERIES) * 100
    
    print(f"\n=== M5.2 get_weather 测试结果 ===")
    print(f"总查询数: {len(TEST_QUERIES)}")
    print(f"成功数: {success_count}")
    print(f"成功率: {success_rate:.1f}%")
    
    if failed_queries:
        print(f"\n失败查询:")
        for query, error in failed_queries:
            print(f"  - {query}: {error}")
    
    # 验收标准: 成功率 100%
    assert success_rate == 100.0, f"成功率 {success_rate:.1f}% 未达到 100% 标准"


def test_qweather_usage_rate(gateway):
    """测试和风天气使用率 > 70%"""
    qweather_count = 0
    total_count = 0
    
    for query in TEST_QUERIES[:10]:  # 测试前 10 条
        result = gateway.invoke("get_weather", query)
        total_count += 1
        
        if result.ok and result.raw and result.raw.get("provider") == "qweather":
            qweather_count += 1
    
    qweather_usage_rate = qweather_count / total_count * 100
    
    print(f"\n=== 和风天气使用率 ===")
    print(f"总查询数: {total_count}")
    print(f"和风天气使用数: {qweather_count}")
    print(f"使用率: {qweather_usage_rate:.1f}%")
    
    # 验收标准: 使用率 > 70% (考虑 API 限制和 fallback)
    assert qweather_usage_rate >= 70.0, f"和风天气使用率 {qweather_usage_rate:.1f}% 未达到 70% 标准"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
