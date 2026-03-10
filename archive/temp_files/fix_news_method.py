#!/usr/bin/env python3
"""Fix _news method in mcp_gateway.py to use provider chain."""

import re

# Read the file
with open('agent_service/infra/tool_clients/mcp_gateway.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new _news method
new_news_method = '''    def _news(self, topic: str) -> ToolResult:
        # Use provider chain if available
        if hasattr(self, 'use_get_news_chain') and self.use_get_news_chain and self.get_news_chain:
            try:
                result = self.get_news_chain.execute("get_news", query=topic)
                
                if result.ok and result.data:
                    # Add fallback chain info if present
                    if result.fallback_chain:
                        if result.data.raw is None:
                            result.data.raw = {}
                        result.data.raw["fallback_chain"] = result.fallback_chain
                    return result.data
                
                # All providers failed, fallback to mock
                fallback = mock_get_news(topic=topic)
                fallback.error = result.error or "all_providers_failed"
                if result.fallback_chain:
                    fallback = _with_fallback_chain(fallback, result.fallback_chain + ["mock"])
                else:
                    fallback = _with_fallback_chain(fallback, ["get_news_chain", "mock"])
                return fallback
                
            except Exception as e:
                print(f"Provider chain error: {e}, falling back to legacy")
                # Fall through to legacy implementation
        
        # Legacy implementation (fallback if provider chain not available)
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

# Find and replace the _news method
pattern = r'    def _news\(self, topic: str\) -> ToolResult:.*?(?=\n    def _nearby)'
replacement = new_news_method + '\n'

content_new = re.sub(pattern, replacement, content, flags=re.DOTALL)

if content_new == content:
    print("ERROR: Pattern not found or replacement failed")
    exit(1)

# Write back
with open('agent_service/infra/tool_clients/mcp_gateway.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print("✅ Successfully updated _news method in mcp_gateway.py")
