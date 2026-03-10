"""测试新浪财经Provider"""
import sys
sys.path.insert(0, 'agent_service')

from infra.tool_clients.providers.sina_finance_provider import (
    SinaFinanceProvider,
    normalize_to_sina_symbol,
    format_stock_display
)

provider = SinaFinanceProvider()

print("=== 测试1: 股票代码标准化 ===")
test_cases = [
    "上证指数",
    "贵州茅台",
    "600519",
    "000001",
    "茅台股价",
    "sh600519",
    "比亚迪",
]

for case in test_cases:
    symbol = normalize_to_sina_symbol(case)
    print(f"{case:15s} -> {symbol}")

print("\n=== 测试2: 获取股票行情 ===")
symbols = ["sh000001", "sh600519", "sz399001"]
for symbol in symbols:
    result = provider.get_stock_quote(symbol)
    if result.success:
        quote = result.data["quote"]
        text = format_stock_display(quote, symbol, symbol)
        print(f"\n✅ {symbol}")
        print(text)
    else:
        print(f"\n❌ {symbol}: {result.error} - {result.message}")

print("\n=== 测试3: 获取财经新闻 ===")
result = provider.get_finance_news(num=5)
if result.success:
    print(f"✅ 新闻总数: {result.data['total']}")
    print(f"本次返回: {len(result.data['news'])} 条\n")
    for i, news in enumerate(result.data['news'][:3], 1):
        print(f"{i}. {news['title']}")
        print(f"   {news['url'][:80]}...")
else:
    print(f"❌ {result.error}: {result.message}")
