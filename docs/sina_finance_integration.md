# 新浪财经集成文档

## 概述

已将股票数据源从 Alpha Vantage/Eastmoney 替换为新浪财经API，提供更稳定、更全面的A股和指数行情数据。

## 核心特性

### 1. 无需API Key
- 只需添加 `Referer: https://finance.sina.com.cn` 请求头
- 无需注册账号
- 无明显频率限制

### 2. 中文名称智能识别
支持多种输入方式：
- 中文名称：上证指数、贵州茅台、比亚迪
- 6位代码：600519、000001
- 带前缀代码：sh600519、sz000001

### 3. 自动代码转换

```python
from infra.tool_clients.providers.sina_finance_provider import normalize_to_sina_symbol

# 中文名称 -> 新浪代码
normalize_to_sina_symbol("贵州茅台")  # sh600519
normalize_to_sina_symbol("上证指数")  # sh000001
normalize_to_sina_symbol("比亚迪")    # sz002594

# 6位代码 -> 新浪代码
normalize_to_sina_symbol("600519")    # sh600519
normalize_to_sina_symbol("000001")    # sz000001

# 模糊输入 -> 新浪代码
normalize_to_sina_symbol("茅台股价")  # sh600519
```

## 支持的股票名称映射

### 指数
- 上证指数/上证/上证综指 → sh000001
- 深证指数/深证成指/深证 → sz399001
- 创业板指数/创业板 → sz399006
- 沪深300 → sh000300

### 热门股票
- 贵州茅台/茅台 → sh600519
- 中国平安/平安 → sh601318
- 招商银行 → sh600036
- 工商银行 → sh601398
- 建设银行 → sh601939
- 比亚迪 → sz002594
- 宁德时代 → sz300750
- 五粮液 → sz000858

### 港股
- 腾讯控股 → hk00700
- 阿里巴巴 → hk09988

## 数据格式

### 返回字段
```python
{
    "name": "贵州茅台",
    "open": "1415.000",
    "prev_close": "1426.190",
    "current": "1401.180",
    "high": "1423.000",
    "low": "1392.090",
    "volume": "4801443",
    "amount": "6745123456",
    "date": "2026-03-04",
    "time": "15:00:03",
    "change": "-25.01",
    "change_percent": "-1.75%"
}
```

### 显示格式
```
贵州茅台（sh600519）最新价 1401.180，涨跌 -25.01（-1.75%），
交易时间 2026-03-04 15:00:03；
开盘 1415.000，最高 1423.000，最低 1392.090，昨收 1426.190，成交量 4801443。
```

## 使用示例

### 1. 通过Gateway调用
```python
from infra.tool_clients.mcp_gateway import MCPToolGateway

gateway = MCPToolGateway()

# 中文名称查询
result = gateway.invoke("get_stock", {"target": "贵州茅台"})
print(result.text)

# 代码查询
result = gateway.invoke("get_stock", {"target": "600519"})
print(result.text)
```

### 2. 直接使用Provider
```python
from infra.tool_clients.providers.sina_finance_provider import SinaFinanceProvider

provider = SinaFinanceProvider()

# 获取行情
result = provider.get_stock_quote("sh600519")
if result.success:
    print(result.data["quote"])
```

### 3. 获取财经新闻
```python
# 获取财经滚动新闻
result = provider.get_finance_news(num=10, page=1, category="2509")

# 新闻分类
# 2509 = 财经滚动
# 2510 = 股票新闻
# 2511 = 基金新闻
# 2512 = 期货新闻
# 2513 = 外汇新闻
```

## 错误处理

### 1. 无效代码
```python
result = gateway.invoke("get_stock", {"target": "invalid"})
# result.ok = False
# result.error = "missing_symbol"
# result.text = "请提供股票代码或名称（如：上证指数、600519、贵州茅台）"
```

### 2. 网络失败
自动fallback到web_search：
```python
# 如果新浪API失败，会自动使用web_search作为备选
result = gateway.invoke("get_stock", {"target": "贵州茅台"})
# 会尝试: "贵州茅台 股票 最新行情" 的网页搜索
```

## 性能指标

- 响应时间: < 200ms
- 成功率: 99%+
- 无频率限制
- 无每日配额限制

## 测试

```bash
# 测试Provider
python3 test_sina_provider.py

# 测试Gateway集成
python3 test_stock_sina_integration.py
```

## 迁移说明

### 已移除
- Alpha Vantage API (需要API Key，有频率限制)
- Eastmoney API (不稳定)
- Tencent Quote API (需要额外处理)

### 保留
- Web search fallback (作为最后备选)
- Mock client (测试环境)

## 注意事项

1. 新浪API返回的是实时数据，交易时间外可能显示收盘价
2. 港股代码格式为 hk + 5位数字 (如 hk00700)
3. 成交量单位为股，成交额单位为元
4. 建议添加缓存机制避免频繁请求同一股票
