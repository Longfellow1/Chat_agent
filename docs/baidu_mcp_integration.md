# 百度千帆 MCP 工具接入方案

## 概述

百度千帆提供两个 MCP 工具：
1. **百度搜索 MCP** (`mcp_baidu_web_search`): 网络信息搜索
2. **百度百科 MCP** (`baidu_baike`): 百科词条查询

## 路由策略：百科 vs 搜索

### 百科问答特征（优先使用百度百科）

**适用场景**：
- 概念定义："什么是电动汽车"
- 词条解释："特斯拉公司介绍"
- 专业术语："锂电池原理"
- 人物介绍："马斯克是谁"
- 历史事件："新能源汽车发展史"

**关键词特征**：
- 包含：是什么、什么是、介绍、定义、概念、原理、历史
- 查询对象：单一实体（公司、人物、技术、概念）
- 查询意图：了解、学习、认知

### 网络搜索特征（使用百度搜索）

**适用场景**：
- 实时信息："特斯拉 Model 3 价格"
- 对比评测："比亚迪和特斯拉哪个好"
- 使用指南："电动车充电注意事项"
- 新闻资讯："蔚来最新消息"
- 多维度查询："上海电动车补贴政策"

**关键词特征**：
- 包含：价格、多少钱、怎么样、哪个好、最新、如何、攻略
- 查询对象：多个实体或复杂场景
- 查询意图：决策、对比、操作

## MCP 调用方式

### 认证方式

使用 BCE Access Key 作为 Bearer Token：

```python
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_KEY}",
}
```

### 百度搜索 MCP

```python
import requests

url = "https://qianfan.baidubce.com/v2/app/conversation/runs"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_KEY}",
}

payload = {
    "app_id": "mcp_baidu_web_search",
    "query": "特斯拉 Model 3 价格",
    "stream": False,
    "tools": [
        {
            "type": "baidu_search",
            "baidu_search": {
                "top_n": 5  # 返回前5个结果
            }
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

# 提取搜索结果
results = data.get("result", {}).get("search_results", [])
for r in results:
    print(f"{r['title']}: {r['url']}")
```

### 百度百科 MCP

```python
payload = {
    "app_id": "baidu_baike",
    "query": "电动汽车",
    "stream": False,
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

# 提取百科内容
summary = data.get("result", {}).get("summary", "")
print(summary)
```

## Provider 实现

### 百度百科 Provider

```python
"""agent_service/infra/tool_clients/providers/baidu_baike_provider.py"""

import os
import requests
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduBaikeProvider(ToolProvider):
    """Baidu Baike (Encyclopedia) provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
        self.timeout = config.timeout
        self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute Baidu Baike query."""
        if not self.access_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_access_key_missing",
                result_type=ResultType.SUMMARIZED,
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.SUMMARIZED,
            )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}",
        }
        
        payload = {
            "app_id": "baidu_baike",
            "query": query,
            "stream": False,
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 提取百科内容
            result_data = data.get("result", {})
            summary = result_data.get("summary", "")
            
            if not summary:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_content",
                    result_type=ResultType.SUMMARIZED,
                )
            
            # 提取参考链接
            url = result_data.get("url", "")
            
            # 创建结果
            result = ToolResult(
                ok=True,
                text=summary,  # 百科摘要，直接使用
                raw={
                    "provider": "baidu_baike",
                    "query": query,
                    "summary": summary,
                    "url": url,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.SUMMARIZED,  # 百科内容，直接使用
            )
            
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.SUMMARIZED,
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"http_error:{e.response.status_code}"
            if e.response.status_code == 429:
                error_msg = "rate_limit"
            elif e.response.status_code == 403:
                error_msg = "quota_exceeded"
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=error_msg,
                result_type=ResultType.SUMMARIZED,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"error:{e}",
                result_type=ResultType.SUMMARIZED,
            )
    
    def health_check(self) -> bool:
        """Check if access key is available."""
        return bool(self.access_key)
```

### 百度搜索 MCP Provider

```python
"""agent_service/infra/tool_clients/providers/baidu_search_mcp_provider.py"""

import os
import requests
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduSearchMCPProvider(ToolProvider):
    """Baidu Search MCP provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.access_key = os.getenv("BAIDU_BCE_ACCESS_KEY", "").strip()
        self.timeout = config.timeout
        self.base_url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "5"))
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute Baidu Search via MCP."""
        if not self.access_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_access_key_missing",
                result_type=ResultType.RAW,
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.RAW,
            )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_key}",
        }
        
        payload = {
            "app_id": "mcp_baidu_web_search",
            "query": query,
            "stream": False,
            "tools": [
                {
                    "type": "baidu_search",
                    "baidu_search": {
                        "top_n": self.max_results
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 提取搜索结果
            result_data = data.get("result", {})
            search_results = result_data.get("search_results", [])
            
            if not search_results:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                    result_type=ResultType.RAW,
                )
            
            # 处理结果（使用 search_result_processor）
            from infra.tool_clients.search_result_processor import process_search_results
            processed = process_search_results(
                search_results,
                query=query,
                max_results=self.max_results,
                relevance_threshold=0.3,
            )
            
            if not processed:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_relevant_results",
                    result_type=ResultType.RAW,
                )
            
            # 格式化输出
            lines = []
            for i, r in enumerate(processed, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:80]
                credibility = r.get("credibility", 5)
                
                trust_mark = ""
                if credibility >= 9:
                    trust_mark = " [官方]"
                elif credibility >= 7:
                    trust_mark = " [可信]"
                
                lines.append(f"{i}. {title}{trust_mark} | {url} | {snippet}")
            
            text = f"已搜索{query}，结果如下：\n" + "\n".join(lines)
            
            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "baidu_search_mcp",
                    "query": query,
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,  # 原始结果，需处理
            )
            
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.RAW,
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"http_error:{e.response.status_code}"
            if e.response.status_code == 429:
                error_msg = "rate_limit"
            elif e.response.status_code == 403:
                error_msg = "quota_exceeded"
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=error_msg,
                result_type=ResultType.RAW,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"error:{e}",
                result_type=ResultType.RAW,
            )
    
    def health_check(self) -> bool:
        """Check if access key is available."""
        return bool(self.access_key)
```

## 查询路由器

```python
"""agent_service/domain/intents/encyclopedia_router.py"""

import re


class EncyclopediaRouter:
    """Route queries to encyclopedia or web search."""
    
    # 百科问答关键词
    ENCYCLOPEDIA_KEYWORDS = [
        "是什么", "什么是", "介绍", "定义", "概念", "原理",
        "历史", "发展", "起源", "由来", "背景",
        "是谁", "谁是", "人物", "创始人",
    ]
    
    # 网络搜索关键词
    WEB_SEARCH_KEYWORDS = [
        "价格", "多少钱", "售价", "报价",
        "怎么样", "如何", "哪个好", "对比", "评测",
        "最新", "新闻", "消息", "动态",
        "攻略", "指南", "教程", "方法",
        "政策", "补贴", "优惠",
    ]
    
    def should_use_encyclopedia(self, query: str) -> bool:
        """Check if query should use encyclopedia.
        
        Args:
            query: User query
            
        Returns:
            True if should use encyclopedia, False otherwise
        """
        query_lower = query.lower()
        
        # 检查百科关键词
        for keyword in self.ENCYCLOPEDIA_KEYWORDS:
            if keyword in query_lower:
                return True
        
        # 检查是否是单一实体查询（简单启发式）
        # 如果查询很短且不包含搜索关键词，可能是百科查询
        if len(query) < 10 and not any(kw in query_lower for kw in self.WEB_SEARCH_KEYWORDS):
            return True
        
        return False
    
    def route(self, query: str) -> str:
        """Route query to appropriate tool.
        
        Args:
            query: User query
            
        Returns:
            "encyclopedia" or "web_search"
        """
        if self.should_use_encyclopedia(query):
            return "encyclopedia"
        return "web_search"
```

## 环境变量配置

```bash
# .env 文件

# 百度 BCE Access Key
export BAIDU_BCE_ACCESS_KEY=bce-v3/ALTAK-xxx/xxx

# 超时配置
export BAIDU_BAIKE_TIMEOUT=2.5
export BAIDU_SEARCH_MCP_TIMEOUT=3.0
```

## 使用示例

```python
from agent_service.domain.intents.encyclopedia_router import EncyclopediaRouter
from agent_service.infra.tool_clients.mcp_gateway_v3 import MCPToolGatewayV3

router = EncyclopediaRouter()
gateway = MCPToolGatewayV3()

# 示例1: 百科查询
query1 = "什么是电动汽车"
tool = router.route(query1)  # 返回 "encyclopedia"
result = gateway.invoke(tool, {"query": query1})
print(result.text)  # 百科摘要

# 示例2: 网络搜索
query2 = "特斯拉 Model 3 价格"
tool = router.route(query2)  # 返回 "web_search"
result = gateway.invoke(tool, {"query": query2})
print(result.text)  # 搜索结果列表
```

## 降级链配置

```python
# 百科查询降级链
encyclopedia:
  baidu_baike (2.5s, SUMMARIZED)
    ↓ 失败
  baidu_search_mcp (3s, RAW)
    ↓ 失败
  tavily (3s, RAW)

# 网络搜索降级链
web_search:
  baidu_search_mcp (3s, RAW)
    ↓ 失败
  tavily (3s, RAW)
```

## 总结

1. **百度百科**: 适合概念、定义、人物、历史等百科类查询
2. **百度搜索**: 适合实时信息、价格、对比、新闻等网络搜索
3. **路由策略**: 基于关键词和查询特征自动路由
4. **Result Type**: 百科返回 SUMMARIZED，搜索返回 RAW
5. **降级机制**: 百科失败可降级到搜索，确保有结果
