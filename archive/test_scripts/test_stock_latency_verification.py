"""验证 get_stock 41ms 延迟的真实性

测试是否真实发起网络请求，还是返回了缓存/Mock数据
"""

import sys
import time
from pathlib import Path

# Add agent_service to path
agent_service_root = Path(__file__).parent / "agent_service"
sys.path.insert(0, str(agent_service_root))

import requests

# 测试1: 直接调用新浪财经API (绕过所有框架)
print("="*80)
print("测试1: 直接调用新浪财经API (原始HTTP请求)")
print("="*80)

test_symbols = ["sh000001", "sh600519", "sz002594"]

for symbol in test_symbols:
    url = f"https://hq.sinajs.cn/list={symbol}"
    headers = {"Referer": "https://finance.sina.com.cn"}
    
    print(f"\n查询: {symbol}")
    print(f"URL: {url}")
    
    start = time.time()
    response = requests.get(url, headers=headers, timeout=10.0)
    latency = (time.time() - start) * 1000
    
    print(f"HTTP状态码: {response.status_code}")
    print(f"延迟: {latency:.0f}ms")
    print(f"响应长度: {len(response.text)} bytes")
    print(f"响应内容 (前200字符): {response.text[:200]}")
    
    time.sleep(0.5)

# 测试2: 通过 SinaFinanceProvider
print("\n" + "="*80)
print("测试2: 通过 SinaFinanceProvider")
print("="*80)

from infra.tool_clients.providers.sina_finance_provider import SinaFinanceProvider

provider = SinaFinanceProvider(timeout=10.0)

for symbol in test_symbols:
    print(f"\n查询: {symbol}")
    
    start = time.time()
    result = provider.get_stock_quote(symbol)
    latency = (time.time() - start) * 1000
    
    print(f"成功: {result.success}")
    print(f"延迟: {latency:.0f}ms")
    if result.success:
        print(f"股票名称: {result.data['quote']['name']}")
        print(f"最新价: {result.data['quote']['current']}")
    else:
        print(f"错误: {result.error}")
    
    time.sleep(0.5)

# 测试3: 通过完整的 MCPToolGateway
print("\n" + "="*80)
print("测试3: 通过 MCPToolGateway (完整链路)")
print("="*80)

from infra.tool_clients.mcp_gateway import MCPToolGateway

gateway = MCPToolGateway()

test_queries = ["上证指数", "贵州茅台", "比亚迪"]

for query in test_queries:
    print(f"\n查询: {query}")
    
    start = time.time()
    result = gateway.invoke("get_stock", {"target": query})
    latency = (time.time() - start) * 1000
    
    print(f"成功: {result.ok}")
    print(f"延迟: {latency:.0f}ms")
    if result.raw:
        print(f"Provider: {result.raw.get('provider', 'unknown')}")
        print(f"Symbol: {result.raw.get('symbol', 'unknown')}")
    print(f"响应文本 (前100字符): {result.text[:100] if result.text else 'None'}")
    
    time.sleep(0.5)

print("\n" + "="*80)
print("结论")
print("="*80)
print("如果三个测试的延迟都在 30-60ms 范围，说明:")
print("1. 新浪财经API响应确实很快 (可能是CDN加速)")
print("2. 没有缓存或Mock干扰")
print("3. 41ms 是真实网络延迟")
print("\n如果测试1延迟明显更高 (>100ms)，说明:")
print("1. 框架层有缓存")
print("2. 或者测试环境有问题")
