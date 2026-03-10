#!/usr/bin/env python3
"""Final fix for mcp_gateway.py _news method."""

# Read file
with open('agent_service/infra/tool_clients/mcp_gateway.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the _news method - replace the entire legacy part
old_legacy = '''        # Legacy implementation (fallback if provider chain not available)
        if not self.tavily_key:
            return mock_get_news(topic=topic)

        query = f"{topic} 最新新闻"
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": self.news_depth or "basic",
            "topic": "news",
            "max_results": max(1, self.search_max_results),
        }
        try:
            body = _http_post_json("https://api.tavily.com/search", payload, timeout=self.timeout)
            results = body.get("results") or []
            if not results:
                return ToolResult(ok=False, text=f"未检索到"{topic}"相关新闻", error="no_news_results")

            packed = _pack_search_results(results, max_results=self.search_max_results, snippet_chars=self.search_snippet_chars)
            lines = [f"{i}. {r['title']} | {r['url']} | {r['snippet']}" for i, r in enumerate(packed, 1)]
            text = f""{topic}"相关新闻：\\n" + "\\n".join(lines)
            return ToolResult(ok=True, text=text, raw={"provider": "tavily_news", "topic": topic, "results": packed})
        except Exception as e:  # noqa: BLE001
            fallback = self._network_fallback(
                original_tool="get_news",
                query=f"{topic} 最新新闻",
                hard_fallback=lambda: mock_get_news(topic=topic),
            )
            fallback.error = f"tavily_news_fail:{e}|{fallback.error or ''}"
            return fallback'''

new_legacy = '''        # Legacy implementation (fallback if provider chain not available)
        if not self.tavily_key:
            return mock_get_news(topic=topic)

        query = f"{topic} 最新新闻"
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": self.news_depth or "basic",
            "topic": "news",
            "max_results": max(1, self.search_max_results),
        }
        try:
            body = _http_post_json("https://api.tavily.com/search", payload, timeout=self.timeout)
            results = body.get("results") or []
            if not results:
                return ToolResult(ok=False, text=f'未检索到"{topic}"相关新闻', error="no_news_results")

            packed = _pack_search_results(results, max_results=self.search_max_results, snippet_chars=self.search_snippet_chars)
            lines = [f"{i}. {r['title']} | {r['url']} | {r['snippet']}" for i, r in enumerate(packed, 1)]
            text = f'"{topic}"相关新闻：\\n' + "\\n".join(lines)
            return ToolResult(ok=True, text=text, raw={"provider": "tavily_news", "topic": topic, "results": packed})
        except Exception as e:  # noqa: BLE001
            fallback = self._network_fallback(
                original_tool="get_news",
                query=f"{topic} 最新新闻",
                hard_fallback=lambda: mock_get_news(topic=topic),
            )
            fallback.error = f"tavily_news_fail:{e}|{fallback.error or ''}"
            return fallback'''

# Replace
content_new = content.replace(old_legacy, new_legacy)

if content_new == content:
    print("ERROR: Replacement failed, trying line-by-line fix")
    # Alternative: fix specific lines
    lines = content.split('\\n')
    for i, line in enumerate(lines):
        if '未检索到' in line and '"相关新闻"' in line:
            lines[i] = line.replace('text=f"未检索到"{topic}"相关新闻"', 'text=f\\'未检索到"{topic}"相关新闻\\'')
            print(f"Fixed line {i+1}: {lines[i][:80]}")
        if '"相关新闻：' in line:
            lines[i] = line.replace('f""{topic}"相关新闻：', 'f\\'"{topic}"相关新闻：')
            print(f"Fixed line {i+1}: {lines[i][:80]}")
    content_new = '\\n'.join(lines)

# Write
with open('agent_service/infra/tool_clients/mcp_gateway.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print("✅ Fixed mcp_gateway.py")
