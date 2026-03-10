"""新浪财经Provider - 股票行情和财经新闻"""
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ProviderResult:
    """Provider result"""
    success: bool
    data: dict
    error: str | None = None
    message: str | None = None


class SinaFinanceProvider:
    """新浪财经数据提供者"""

    def __init__(self, timeout: float = 10.0):
        self.name = "sina_finance"
        self.timeout = timeout
        self.headers = {"Referer": "https://finance.sina.com.cn"}

    def get_stock_quote(self, symbol: str) -> ProviderResult:
        """获取股票实时行情
        
        Args:
            symbol: 新浪格式的股票代码 (如 sh000001, sz399001, sh600519)
        """
        if not symbol:
            return ProviderResult(
                success=False,
                data={},
                error="missing_symbol",
                message="缺少股票代码"
            )

        url = f"https://hq.sinajs.cn/list={symbol}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析返回数据: var hq_str_sh000001="上证指数,3000.00,..."
            content = response.text.strip()
            if not content or "Forbidden" in content:
                return ProviderResult(
                    success=False,
                    data={},
                    error="access_denied",
                    message="访问被拒绝，请检查Referer设置"
                )
            
            # 提取数据部分
            match = re.search(r'="([^"]+)"', content)
            if not match:
                return ProviderResult(
                    success=False,
                    data={},
                    error="parse_error",
                    message=f"无法解析数据: {content[:100]}"
                )
            
            data_str = match.group(1)
            fields = data_str.split(",")
            
            if len(fields) < 32:
                return ProviderResult(
                    success=False,
                    data={},
                    error="invalid_data",
                    message=f"数据字段不足: {len(fields)}"
                )
            
            # 解析字段 (新浪财经标准格式)
            quote_data = {
                "name": fields[0],
                "open": fields[1],
                "prev_close": fields[2],
                "current": fields[3],
                "high": fields[4],
                "low": fields[5],
                "volume": fields[8],
                "amount": fields[9],
                "date": fields[30],
                "time": fields[31],
            }
            
            # 计算涨跌
            try:
                current = float(quote_data["current"])
                prev_close = float(quote_data["prev_close"])
                change = current - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                quote_data["change"] = f"{change:+.2f}"
                quote_data["change_percent"] = f"{change_pct:+.2f}%"
            except (ValueError, ZeroDivisionError):
                quote_data["change"] = "0.00"
                quote_data["change_percent"] = "0.00%"
            
            return ProviderResult(
                success=True,
                data={
                    "provider": "sina_finance",
                    "symbol": symbol,
                    "quote": quote_data
                },
                error=None,
                message=None
            )
            
        except requests.Timeout:
            return ProviderResult(
                success=False,
                data={},
                error="timeout",
                message=f"请求超时 ({self.timeout}s)"
            )
        except requests.RequestException as e:
            return ProviderResult(
                success=False,
                data={},
                error="request_failed",
                message=f"请求失败: {str(e)}"
            )
        except Exception as e:
            return ProviderResult(
                success=False,
                data={},
                error="unknown_error",
                message=f"未知错误: {str(e)}"
            )

    def get_finance_news(self, num: int = 10, page: int = 1, category: str = "2509") -> ProviderResult:
        """获取财经新闻
        
        Args:
            num: 每页数量 (默认10)
            page: 页码 (默认1)
            category: 新闻分类 (2509=财经滚动, 2510=股票, 2511=基金, 2512=期货, 2513=外汇)
        """
        url = "https://feed.mix.sina.com.cn/api/roll/get?" + urllib.parse.urlencode({
            "pageid": "153",
            "lid": category,
            "num": str(num),
            "page": str(page),
        })
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("result", {}).get("status", {}).get("code") != 0:
                return ProviderResult(
                    success=False,
                    data={},
                    error="api_error",
                    message="API返回错误状态"
                )
            
            result_data = data.get("result", {})
            news_items = result_data.get("data", [])
            
            # 提取关键信息
            news_list = []
            for item in news_items:
                news_list.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "intro": item.get("intro", ""),
                    "ctime": item.get("ctime", ""),
                })
            
            return ProviderResult(
                success=True,
                data={
                    "provider": "sina_finance",
                    "total": result_data.get("total", 0),
                    "news": news_list,
                    "category": category
                },
                error=None,
                message=None
            )
            
        except requests.Timeout:
            return ProviderResult(
                success=False,
                data={},
                error="timeout",
                message=f"请求超时 ({self.timeout}s)"
            )
        except requests.RequestException as e:
            return ProviderResult(
                success=False,
                data={},
                error="request_failed",
                message=f"请求失败: {str(e)}"
            )
        except Exception as e:
            return ProviderResult(
                success=False,
                data={},
                error="unknown_error",
                message=f"未知错误: {str(e)}"
            )


def normalize_to_sina_symbol(target: str) -> str:
    """将用户输入转换为新浪股票代码格式
    
    Args:
        target: 用户输入 (中文名称、代码等)
        
    Returns:
        新浪格式代码 (如 sh000001, sz399001, sh600519)
    """
    s = target.strip().upper()
    
    # 中文名称映射
    name_mapping = {
        "上证指数": "sh000001",
        "上证": "sh000001",
        "上证综指": "sh000001",
        "深证指数": "sz399001",
        "深证成指": "sz399001",
        "深证": "sz399001",
        "创业板指数": "sz399006",
        "创业板": "sz399006",
        "沪深300": "sh000300",
        "贵州茅台": "sh600519",
        "茅台": "sh600519",
        "中国平安": "sh601318",
        "平安": "sh601318",
        "招商银行": "sh600036",
        "工商银行": "sh601398",
        "建设银行": "sh601939",
        "中国银行": "sh601988",
        "农业银行": "sh601288",
        "比亚迪": "sz002594",
        "宁德时代": "sz300750",
        "五粮液": "sz000858",
        "中国石油": "sh601857",
        "中国石化": "sh600028",
        "中国移动": "sh600941",
        "中国联通": "sh600050",
        "中国电信": "sh601728",
        "腾讯控股": "hk00700",
        "阿里巴巴": "hk09988",
    }
    
    if s in name_mapping:
        return name_mapping[s]
    
    # 清理输入
    cleaned = s
    for rm in ("股价", "股票", "行情", "价格", "最新", "现在", "查询", "查一下", "查", "一下", "涨跌", "怎么样", "情况"):
        cleaned = cleaned.replace(rm, " ")
    
    # 提取代码
    for token in cleaned.replace("，", " ").replace(",", " ").split():
        token = token.strip()
        if not token:
            continue
        
        # 6位数字代码
        if token.isdigit() and len(token) == 6:
            if token.startswith("6"):
                return f"sh{token}"  # 沪市
            elif token.startswith(("0", "3")):
                return f"sz{token}"  # 深市
        
        # 已带前缀的代码 (sh600519, sz000001)
        if token.lower().startswith(("sh", "sz", "hk")) and len(token) >= 8:
            return token.lower()
    
    # 中文名称模糊匹配
    for zh_name, code in name_mapping.items():
        if zh_name in target:
            return code
    
    return ""


def format_stock_display(quote_data: dict, symbol: str, target: str) -> str:
    """格式化股票显示文本
    
    Args:
        quote_data: 行情数据
        symbol: 股票代码
        target: 用户原始输入
        
    Returns:
        格式化的显示文本
    """
    name = quote_data.get("name", symbol)
    current = quote_data.get("current", "-")
    change = quote_data.get("change", "-")
    change_pct = quote_data.get("change_percent", "-")
    open_price = quote_data.get("open", "-")
    high = quote_data.get("high", "-")
    low = quote_data.get("low", "-")
    prev_close = quote_data.get("prev_close", "-")
    volume = quote_data.get("volume", "-")
    date = quote_data.get("date", "-")
    time = quote_data.get("time", "-")
    
    text = (
        f"{name}（{symbol}）最新价 {current}，涨跌 {change}（{change_pct}），"
        f"交易时间 {date} {time}；"
        f"开盘 {open_price}，最高 {high}，最低 {low}，昨收 {prev_close}，成交量 {volume}。"
    )
    
    return text
