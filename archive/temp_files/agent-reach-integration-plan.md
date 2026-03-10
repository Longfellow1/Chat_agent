# Agent-Reach 技能集成方案

> 将 Agent-Reach 在线媒体查询技能集成到闲聊智能体，实现新闻搜索功能

**文档版本**: v1.0  
**创建时间**: 2026-03-01  
**作者**: AI Assistant

---

## 📋 目录

1. [技能概述](#技能概述)
2. [集成方案对比](#集成方案对比)
3. [方案一：直接导入模块](#方案一直接导入模块)
4. [方案二：MCP Server 封装](#方案二mcp-server-封装)
5. [方案三：HTTP API 封装](#方案三http-api-封装)
6. [工具调用配置](#工具调用配置)
7. [使用示例](#使用示例)
8. [快速集成步骤](#快速集成步骤)
9. [优化建议](#优化建议)

---

## 技能概述

### Agent-Reach 功能

| 函数 | 功能 | 适用场景 |
|------|------|---------|
| `read_web(url)` | 读取任意网页内容 | 文章阅读、网页分析 |
| `search_web(query)` | 全网搜索 | 新闻查询、信息检索 |
| `read_rss(url)` | 读取 RSS 订阅 | 订阅源监控 |
| `read_youtube(url)` | 提取 YouTube 字幕 | 视频内容分析 |

### 技术栈

- **核心依赖**: `requests`
- **API**: Jina Reader (`https://r.jina.ai/`, `https://s.jina.ai/`)
- **位置**: `/Users/Harland/.openclaw/workspace/CLaw/skills/agent-reach-skill/reach_skill.py`

---

## 集成方案对比

| 方案 | 复杂度 | 性能 | 适用场景 |
|------|--------|------|---------|
| **直接导入** | ⭐ 低 | ⭐⭐⭐ 高 | 同进程、Python 项目 |
| **MCP Server** | ⭐⭐ 中 | ⭐⭐ 中 | 标准化协议、多智能体 |
| **HTTP API** | ⭐⭐ 中 | ⭐⭐ 中 | 跨语言、远程调用 |

---

## 方案一：直接导入模块

### 适用场景

- 闲聊智能体是 Python 项目
- 与 Agent-Reach 在同一进程运行
- 追求最低延迟

### 代码实现

```python
# chatbot_with_news.py
from reach_skill import read_web, search_web, read_rss

class NewsEnabledChatbot:
    """支持新闻搜索的闲聊智能体"""
    
    def __init__(self):
        self.tools = {
            "search_news": self.search_news,
            "read_article": self.read_article,
        }
    
    def search_news(self, query: str, limit: int = 5) -> dict:
        """搜索 AI 新闻"""
        result = search_web(f"AI news {query}")
        return {
            "success": result.get("success", False),
            "results": result.get("results", [])[:limit],
            "query": result.get("query", query)
        }
    
    def read_article(self, url: str) -> dict:
        """读取文章内容"""
        result = read_web(url)
        return {
            "success": result.get("success", False),
            "title": result.get("title", ""),
            "content": result.get("content", "")[:2000],  # 限制长度
            "url": result.get("url", url)
        }
    
    def handle_message(self, user_input: str) -> str:
        """处理用户消息"""
        # 检测意图
        if any(kw in user_input.lower() for kw in ["新闻", "news", "搜索", "search"]):
            # 调用搜索工具
            result = self.search_news(user_input)
            return self.format_search_result(result)
        
        # 检测 URL
        if "http" in user_input:
            import re
            urls = re.findall(r'https?://\S+', user_input)
            if urls:
                result = self.read_article(urls[0])
                return self.format_article_result(result)
        
        # 普通闲聊
        return self.chat_response(user_input)
    
    def format_search_result(self, result: dict) -> str:
        """格式化搜索结果"""
        if not result["success"]:
            return "抱歉，搜索失败了，请稍后重试。"
        
        response = f"🔍 关于 \"{result['query']}\" 的搜索结果：\n\n"
        for i, item in enumerate(result["results"][:5], 1):
            response += f"{i}. **{item.get('title', '无标题')}**\n"
            response += f"   {item.get('snippet', '')[:100]}...\n"
            response += f"   🔗 {item.get('url', '')}\n\n"
        return response
    
    def format_article_result(self, result: dict) -> str:
        """格式化文章内容"""
        if not result["success"]:
            return "抱歉，读取文章失败了。"
        
        return f"📄 **{result['title']}**\n\n{result['content'][:1500]}..."
    
    def chat_response(self, message: str) -> str:
        """普通闲聊回复"""
        # 这里接入你的 LLM
        return "这是一个闲聊回复..."


# 使用示例
if __name__ == "__main__":
    bot = NewsEnabledChatbot()
    
    # 搜索新闻
    print(bot.handle_message("今天有什么 AI 新闻？"))
    
    # 读取文章
    print(bot.handle_message("帮我看看这个链接 https://example.com"))
```

---

## 方案二：MCP Server 封装

### 适用场景

- 需要标准化协议
- 多智能体共享工具
- 计划扩展更多工具

### 安装依赖

```bash
pip install mcp
```

### 创建 MCP Server

```python
# agent_reach_mcp_server.py
#!/usr/bin/env python3
"""Agent-Reach MCP Server"""

from mcp.server.fastmcp import FastMCP
from reach_skill import read_web, search_web, read_rss

mcp = FastMCP("Agent-Reach News")


@mcp.tool()
def search_news(query: str, limit: int = 5) -> str:
    """
    搜索最新的 AI 新闻和资讯
    
    Args:
        query: 搜索关键词，如 "AI news today"
        limit: 返回结果数量 (默认 5)
    
    Returns:
        格式化的搜索结果
    """
    result = search_web(query)
    
    if not result.get("success"):
        return "搜索失败，请稍后重试。"
    
    response = f"🔍 搜索结果：{query}\n\n"
    for i, item in enumerate(result.get("results", [])[:limit], 1):
        response += f"{i}. **{item.get('title', '无标题')}**\n"
        response += f"   {item.get('snippet', '')[:150]}...\n"
        response += f"   🔗 {item.get('url', '')}\n\n"
    
    return response


@mcp.tool()
def read_article(url: str) -> str:
    """
    读取网页文章内容
    
    Args:
        url: 文章 URL
    
    Returns:
        文章标题和内容摘要
    """
    result = read_web(url)
    
    if not result.get("success"):
        return f"读取失败：{result.get('error', '未知错误')}"
    
    content = result.get("content", "")
    # 限制内容长度
    if len(content) > 2000:
        content = content[:2000] + "\n\n[内容过长，已截断...]"
    
    return f"📄 **{result.get('title', '无标题')}**\n\n{content}"


@mcp.tool()
def subscribe_rss(feed_url: str, limit: int = 10) -> str:
    """
    读取 RSS 订阅源
    
    Args:
        feed_url: RSS Feed URL
        limit: 返回条目数量
    
    Returns:
        格式化的 RSS 条目列表
    """
    result = read_rss(feed_url, limit=limit)
    
    if not result.get("success"):
        return f"读取 RSS 失败：{result.get('error', '未知错误')}"
    
    response = f"📡 **{result.get('feed_title', 'RSS Feed')}**\n\n"
    for i, entry in enumerate(result.get("entries", [])[:limit], 1):
        response += f"{i}. **{entry.get('title', '无标题')}**\n"
        response += f"   {entry.get('summary', '')[:100]}...\n"
        if entry.get('published'):
            response += f"   📅 {entry['published']}\n"
        response += f"   🔗 {entry.get('link', '')}\n\n"
    
    return response


if __name__ == "__main__":
    # 运行 MCP Server
    mcp.run()
```

### 闲聊智能体配置

```json
{
  "mcp_servers": [
    {
      "name": "agent-reach",
      "command": "python",
      "args": ["/path/to/agent_reach_mcp_server.py"],
      "env": {}
    }
  ],
  "tools": [
    "search_news",
    "read_article",
    "subscribe_rss"
  ]
}
```

### 启动命令

```bash
# 后台运行 MCP Server
nohup python /path/to/agent_reach_mcp_server.py > /tmp/mcp.log 2>&1 &

# 验证运行
curl http://localhost:8765/health
```

---

## 方案三：HTTP API 封装

### 适用场景

- 跨语言调用
- 远程部署
- 需要认证/限流

### 创建 Flask API

```python
# agent_reach_api.py
#!/usr/bin/env python3
"""Agent-Reach HTTP API Server"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from reach_skill import read_web, search_web, read_rss
import hashlib
import time

app = Flask(__name__)
CORS(app)

# 简单的请求缓存
cache = {}
CACHE_TTL = 300  # 5 分钟


def get_cache_key(func_name: str, **kwargs) -> str:
    """生成缓存键"""
    key_str = f"{func_name}:{str(kwargs)}"
    return hashlib.md5(key_str.encode()).hexdigest()


def get_from_cache(key: str) -> dict | None:
    """从缓存获取"""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
        del cache[key]
    return None


def save_to_cache(key: str, data: dict):
    """保存到缓存"""
    cache[key] = (data, time.time())


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "cache_size": len(cache)})


@app.route('/search', methods=['POST'])
def search():
    """搜索新闻"""
    data = request.json
    query = data.get('query', '')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({"error": "query is required"}), 400
    
    # 检查缓存
    cache_key = get_cache_key('search', query=query)
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify({**cached, "from_cache": True})
    
    # 执行搜索
    result = search_web(query)
    result["results"] = result.get("results", [])[:limit]
    
    # 保存缓存
    save_to_cache(cache_key, result)
    
    return jsonify({**result, "from_cache": False})


@app.route('/read', methods=['POST'])
def read():
    """读取网页"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({"error": "url is required"}), 400
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # 检查缓存
    cache_key = get_cache_key('read', url=url)
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify({**cached, "from_cache": True})
    
    # 读取网页
    result = read_web(url)
    
    # 限制内容长度
    if "content" in result and len(result["content"]) > 3000:
        result["content"] = result["content"][:3000] + "\n\n[内容过长，已截断...]"
    
    # 保存缓存
    save_to_cache(cache_key, result)
    
    return jsonify({**result, "from_cache": False})


@app.route('/rss', methods=['POST'])
def rss():
    """读取 RSS"""
    data = request.json
    feed_url = data.get('url', '')
    limit = data.get('limit', 10)
    
    if not feed_url:
        return jsonify({"error": "url is required"}), 400
    
    result = read_rss(feed_url, limit=limit)
    result["entries"] = result.get("entries", [])[:limit]
    
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 安装依赖

```bash
pip install flask flask-cors
```

### 启动服务

```bash
# 开发模式
python agent_reach_api.py

# 生产模式 (gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 agent_reach_api:app
```

### 闲聊智能体调用

```python
# chatbot_http_client.py
import requests

class AgentReachClient:
    """Agent-Reach HTTP API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search_news(self, query: str, limit: int = 5) -> dict:
        """搜索新闻"""
        resp = self.session.post(
            f"{self.base_url}/search",
            json={"query": query, "limit": limit}
        )
        return resp.json()
    
    def read_article(self, url: str) -> dict:
        """读取文章"""
        resp = self.session.post(
            f"{self.base_url}/read",
            json={"url": url}
        )
        return resp.json()
    
    def subscribe_rss(self, feed_url: str, limit: int = 10) -> dict:
        """订阅 RSS"""
        resp = self.session.post(
            f"{self.base_url}/rss",
            json={"url": feed_url, "limit": limit}
        )
        return resp.json()


# 使用示例
if __name__ == "__main__":
    client = AgentReachClient()
    
    # 搜索
    result = client.search_news("AI news today")
    print(result)
    
    # 读取
    result = client.read_article("https://example.com")
    print(result)
```

---

## 工具调用配置

### OpenAI 风格工具定义

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_ai_news",
        "description": "搜索最新的 AI 新闻和资讯",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "搜索关键词，如 'AI news today'"
            },
            "limit": {
              "type": "integer",
              "description": "返回结果数量",
              "default": 5,
              "minimum": 1,
              "maximum": 20
            }
          },
          "required": ["query"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "read_article",
        "description": "读取网页文章内容并总结",
        "parameters": {
          "type": "object",
          "properties": {
            "url": {
              "type": "string",
              "description": "文章 URL"
            },
            "summary_length": {
              "type": "integer",
              "description": "摘要长度（字符数）",
              "default": 1500
            }
          },
          "required": ["url"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "subscribe_rss",
        "description": "读取 RSS 订阅源的最新内容",
        "parameters": {
          "type": "object",
          "properties": {
            "feed_url": {
              "type": "string",
              "description": "RSS Feed URL"
            },
            "limit": {
              "type": "integer",
              "description": "返回条目数量",
              "default": 10
            }
          },
          "required": ["feed_url"]
        }
      }
    }
  ]
}
```

### Claude 风格工具定义

```python
tools = [
    {
        "name": "search_ai_news",
        "description": "Search for latest AI news and information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g., 'AI news today'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    # ... 其他工具
]
```

---

## 使用示例

### 示例 1：搜索新闻

**用户**: "今天有什么 AI 新闻？"

**智能体处理流程**：
```python
# 1. 检测意图
intent = detect_intent("今天有什么 AI 新闻？")
# → intent = "search_news"

# 2. 提取参数
params = extract_params("今天有什么 AI 新闻？")
# → params = {"query": "AI news March 1 2026", "limit": 5}

# 3. 调用工具
result = tools.search_ai_news(**params)

# 4. 格式化回复
response = format_news_result(result)
```

**回复**：
```
🔍 关于 "AI news March 1 2026" 的搜索结果：

1. **OpenAI 发布新模型 GPT-5**
   OpenAI 今天发布了新一代模型，性能提升显著...
   🔗 https://openai.com/blog/gpt-5

2. **Google AI 新研究：多模态理解**
   Google 研究团队提出新的多模态架构...
   🔗 https://ai.google/research/multimodal

3. **Anthropic 融资 20 亿美元**
   Anthropic 完成新一轮融资，估值达到...
   🔗 https://anthropic.com/news/funding
```

---

### 示例 2：读取文章

**用户**: "帮我看看这个链接 https://example.com/ai-news"

**智能体处理流程**：
```python
# 1. 检测 URL
url = extract_url("帮我看看这个链接 https://example.com/ai-news")
# → url = "https://example.com/ai-news"

# 2. 调用工具
result = tools.read_article(url=url)

# 3. 总结内容
summary = llm_summarize(result["content"])
```

**回复**：
```
📄 **AI 行业最新动态**

这篇文章主要讲了以下内容：

1. OpenAI 发布了 GPT-5，性能提升 50%
2. Google 提出新的多模态架构
3. Anthropic 完成 20 亿美元融资

文章认为，2026 年将是 AI 应用落地的重要一年...

[阅读全文](https://example.com/ai-news)
```

---

### 示例 3：订阅 RSS

**用户**: "我想看机器之心的最新内容"

**智能体处理流程**：
```python
# 1. 匹配已知订阅源
feed_url = find_rss_feed("机器之心")
# → feed_url = "https://www.jiqizhixin.com/rss"

# 2. 调用工具
result = tools.subscribe_rss(feed_url=feed_url, limit=5)

# 3. 格式化回复
response = format_rss_result(result)
```

**回复**：
```
📡 **机器之心** 最新 5 条内容：

1. **2026 AI 十大趋势预测**
   专家预测 2026 年 AI 领域将...
   📅 2026-03-01
   🔗 https://www.jiqizhixin.com/article/123

2. **大模型推理优化新方案**
   研究团队提出新的推理优化方法...
   📅 2026-02-28
   🔗 https://www.jiqizhixin.com/article/124
```

---

## 快速集成步骤

### 步骤 1：复制技能文件

```bash
# 创建目录
mkdir -p /path/to/your/bot/tools

# 复制技能文件
cp /Users/Harland/.openclaw/workspace/CLaw/skills/agent-reach-skill/reach_skill.py \
   /path/to/your/bot/tools/

# 复制依赖文件（如果有）
cp /Users/Harland/.openclaw/workspace/CLaw/skills/agent-reach-skill/requirements.txt \
   /path/to/your/bot/
```

### 步骤 2：安装依赖

```bash
cd /path/to/your/bot
pip install requests
```

### 步骤 3：导入并使用

```python
# 在你的智能体中
from tools.reach_skill import read_web, search_web

# 直接使用
result = search_web("AI news today")
print(result)
```

### 步骤 4：测试验证

```python
# test_reach.py
from tools.reach_skill import read_web, search_web

def test_search():
    result = search_web("AI news")
    assert result.get("success") == True
    assert len(result.get("results", [])) > 0
    print("✅ 搜索测试通过")

def test_read():
    result = read_web("https://example.com")
    assert result.get("success") == True
    assert "content" in result
    print("✅ 读取测试通过")

if __name__ == "__main__":
    test_search()
    test_read()
```

---

## 优化建议

### 1. 添加缓存层

```python
# cache.py
import hashlib
import time
from functools import wraps

class Cache:
    def __init__(self, ttl: int = 300):
        self._cache = {}
        self._ttl = ttl
    
    def _key(self, func_name: str, **kwargs) -> str:
        key_str = f"{func_name}:{str(kwargs)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            del self._cache[key]
        return None
    
    def set(self, key: str, data: dict):
        self._cache[key] = (data, time.time())

# 使用
cache = Cache(ttl=300)  # 5 分钟缓存

def cached_search(query: str):
    key = cache._key('search', query=query)
    cached = cache.get(key)
    if cached:
        return cached
    result = search_web(query)
    cache.set(key, result)
    return result
```

### 2. 结果摘要

```python
# summarizer.py
def summarize_results(results: list, llm_client) -> str:
    """用 LLM 总结搜索结果"""
    if not results:
        return "没有找到相关内容。"
    
    # 提取关键信息
    texts = []
    for r in results[:5]:
        texts.append(f"标题：{r.get('title', '')}\n摘要：{r.get('snippet', '')}")
    
    # 调用 LLM 总结
    prompt = f"请总结以下搜索结果：\n\n" + "\n---\n".join(texts)
    summary = llm_client.chat(prompt)
    
    return summary
```

### 3. 来源标注

```python
def format_with_source(result: dict) -> str:
    """添加来源标注"""
    response = ""
    for item in result.get("results", []):
        response += f"• {item.get('title', '')}\n"
        response += f"  来源：{extract_domain(item.get('url', ''))}\n"
        response += f"  {item.get('snippet', '')[:100]}...\n\n"
    return response

def extract_domain(url: str) -> str:
    """从 URL 提取域名"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')
```

### 4. 时效性提示

```python
def add_time_context(result: dict) -> str:
    """添加时间上下文"""
    current_time = datetime.now()
    
    response = f"📅 截至 {current_time.strftime('%Y-%m-%d %H:%M')} 的信息：\n\n"
    response += format_results(result)
    
    # 添加时效性提示
    response += "\n⚠️ 以上信息可能不是最新的，建议核实重要信息。"
    
    return response
```

---

## 故障排查

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 搜索失败 | API 限流 | 添加缓存，降低请求频率 |
| 读取超时 | 网页加载慢 | 增加 timeout 参数 |
| 内容乱码 | 编码问题 | 检查 `read_web` 的编码处理 |
| 缓存失效 | 内存限制 | 使用 Redis 等外部缓存 |

### 日志配置

```python
# logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/agent_reach.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('agent_reach')
```

---

## 参考资料

- [Agent-Reach 技能源码](https://github.com/Panniantong/Agent-Reach)
- [Jina Reader API](https://jina.ai/reader)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Flask 文档](https://flask.palletsprojects.com)

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-03-01 | 初始版本 |

---

**文档结束**
