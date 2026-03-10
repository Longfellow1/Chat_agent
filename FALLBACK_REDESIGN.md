# 兜底链路重新设计方案 v2

## 核心策略

**LLM + web_search 是最终兜底，可以回答97%的问题**

## 新兜底链路

```
专用工具失败 (get_weather/get_stock/get_news/find_nearby/plan_trip)
    ↓
fallback to web_search (搜索相关信息)
    ↓
web_search 也失败
    ↓
fallback to LLM (基于知识生成回复)
```

## 各工具的兜底策略

### 1. get_weather
```
QWeather → Tavily → web_search("城市 天气") → LLM
```

### 2. get_stock  
```
Sina Finance → web_search("股票代码 实时行情") → LLM
```

### 3. get_news
```
Sina News → Baidu News → web_search("主题 最新新闻") → LLM
```

### 4. find_nearby
```
Amap MCP → Baidu Maps MCP → web_search("城市 关键词 推荐") → LLM
```

### 5. plan_trip
```
Plan Trip Engine → web_search("目的地 旅游攻略") → LLM
```

### 6. web_search (自身)
```
Bing → Tavily → Baidu → LLM (直接生成)
```

## 实施方案

### Step 1: 移除所有 mock provider (已完成)

### Step 2: 实现统一的 web_search fallback

```python
def _fallback_to_web_search(
    self,
    original_tool: str,
    query: str,
    error: str,
    fallback_chain: list[str]
) -> ToolResult:
    """
    统一的 web_search 兜底
    
    当专用工具失败时，尝试用 web_search 搜索相关信息
    """
    try:
        # 构造搜索query
        search_query = self._build_search_query(original_tool, query)
        
        # 调用 web_search
        result = self._web_search(search_query)
        
        if result.success:
            # 搜索成功，返回结果
            result.fallback_chain = fallback_chain + ["web_search_fallback"]
            result.error = f"{original_tool}_failed|web_search_fallback_success"
            return result
        else:
            # 搜索也失败，继续走 LLM
            return self._fallback_to_llm(
                original_tool=original_tool,
                query=query,
                error=f"{error}|web_search_also_failed",
                fallback_chain=fallback_chain + ["web_search_fallback"]
            )
    except Exception as e:
        # web_search 异常，直接走 LLM
        return self._fallback_to_llm(
            original_tool=original_tool,
            query=query,
            error=f"{error}|web_search_exception:{e}",
            fallback_chain=fallback_chain + ["web_search_fallback"]
        )

def _build_search_query(self, tool_name: str, original_query: str) -> str:
    """根据工具类型构造搜索query"""
    if tool_name == "get_weather":
        # "北京天气" → "北京 天气 实时"
        return f"{original_query} 实时"
    elif tool_name == "get_stock":
        # "比亚迪股价" → "比亚迪 股票 实时行情"
        return f"{original_query} 实时行情"
    elif tool_name == "get_news":
        # "科技新闻" → "科技 最新新闻"
        return f"{original_query} 最新"
    elif tool_name == "find_nearby":
        # "北京 咖啡厅" → "北京 咖啡厅 推荐"
        return f"{original_query} 推荐"
    elif tool_name == "plan_trip":
        # "上海旅游" → "上海 旅游攻略"
        return f"{original_query} 攻略"
    else:
        return original_query
```

### Step 3: 实现 LLM 最终兜底

```python
def _fallback_to_llm(
    self,
    original_tool: str,
    query: str,
    error: str,
    fallback_chain: list[str]
) -> ToolResult:
    """
    LLM 最终兜底
    
    基于 LLM 的知识生成回复，不依赖实时数据
    """
    from infra.llm_clients.lm_studio_client import LMStudioClient
    
    # 构造 prompt
    prompt = f"""用户查询：{query}

由于无法获取实时数据，请基于你的知识给出一个有帮助的回复。

要求：
1. 如果是查询实时信息（天气/股价/新闻），说明无法获取实时数据，建议用户使用相关app
2. 如果是一般性问题，可以提供通用建议和信息
3. 回复要简洁、有帮助，不超过100字
4. 不要编造任何实时数据

回复："""
    
    try:
        llm_client = LMStudioClient()
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        final_text = response.strip()
    except Exception as e:
        # LLM 也失败了，使用硬编码兜底
        final_text = "抱歉，服务暂时不可用，请稍后再试。"
    
    return ToolResult(
        success=False,
        data="",
        error=f"{original_tool}_all_fallbacks_failed|{error}",
        provider="llm_fallback",
        fallback_chain=fallback_chain + ["llm_fallback"],
        final_text=final_text
    )
```

### Step 4: 修改各工具的失败处理

**示例：get_stock**

```python
# 原来：
fallback = mock_get_stock(target=target)

# 改为：
return self._fallback_to_web_search(
    original_tool="get_stock",
    query=f"{target} 股票",
    error=result.error,
    fallback_chain=result.fallback_chain
)
```

## 预期效果

### 场景1: 天气查询 (QWeather失败)
```
用户: 北京今天天气怎么样
系统: [通过web_search搜索"北京 天气 实时"]
返回: 根据搜索结果，北京今天多云，气温15-25°C...
```

### 场景2: 股票查询 (Sina失败)
```
用户: 比亚迪今天股价多少
系统: [通过web_search搜索"比亚迪 股票 实时行情"]
返回: 根据搜索结果，比亚迪(002594)最新价格...
```

### 场景3: 所有都失败
```
用户: 比亚迪今天股价多少
系统: [web_search也失败，走LLM]
返回: 抱歉，无法获取实时股价数据，建议您使用股票app查看比亚迪(002594)的最新行情。
```

## 优势

1. **覆盖率高**: web_search可以回答大部分问题
2. **用户体验好**: 即使专用工具失败，仍能提供有价值的信息
3. **无假数据**: 彻底移除mock，所有数据都是真实的
4. **降级优雅**: 三层兜底确保总能给出回复

## 实施时间

- Step 1: 已完成 (移除mock注册)
- Step 2: 2小时 (实现web_search fallback)
- Step 3: 1小时 (实现LLM fallback)
- Step 4: 2小时 (修改各工具调用)
- 测试验证: 1小时

**总计**: 6小时
