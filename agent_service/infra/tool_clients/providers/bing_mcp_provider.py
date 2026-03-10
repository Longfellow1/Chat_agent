"""Bing MCP provider using open-websearch."""

import json
import os
import subprocess
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BingMCPProvider(ToolProvider):
    """Bing search via open-websearch MCP (free, no API key)."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.timeout = config.timeout
        self.max_results = int(os.getenv("TOOL_SEARCH_MAX_RESULTS", "5"))
        self.snippet_chars = int(os.getenv("TOOL_SEARCH_SNIPPET_CHARS", "200"))  # 统一截断策略
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute Bing search via MCP."""
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.RAW,
            )
        
        # Query预处理：去除"帮我搜一下"等前缀
        from domain.tools.query_preprocessor import preprocess_web_search_query
        preprocessed = preprocess_web_search_query(query)
        cleaned_query = preprocessed["normalized_query"]
        
        print(f"[Bing MCP] Original query: {query}")
        print(f"[Bing MCP] Cleaned query: {cleaned_query}")
        
        try:
            # Prepare MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": cleaned_query,  # 使用清洗后的query
                        "limit": self.max_results,
                        "engines": ["bing"],
                        "market": "zh-CN",  # 指定中文市场，提升中文搜索质量
                    }
                }
            }
            
            print(f"[Bing MCP] Request arguments: {request['params']['arguments']}")
            
            # Call MCP server via npx
            process = subprocess.Popen(
                ["npx", "open-websearch@latest"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={
                    "MODE": "stdio",
                    "DEFAULT_SEARCH_ENGINE": "bing",
                    "PATH": os.environ.get("PATH", "")
                }
            )
            
            stdout, stderr = process.communicate(
                input=json.dumps(request) + "\n",
                timeout=self.timeout
            )
            
            # Debug logging
            if stderr:
                print(f"[Bing MCP] stderr: {stderr[:200]}")
            
            # Parse response
            lines = stdout.strip().split("\n")
            response_line = None
            for line in lines:
                if line.startswith("{") and '"result"' in line:
                    response_line = line
                    break
            
            if not response_line:
                print(f"[Bing MCP] No valid response line found. stdout: {stdout[:500]}")
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_response",
                    result_type=ResultType.RAW,
                )
            
            response = json.loads(response_line)
            result_data = response.get("result", {})
            content = result_data.get("content", [])
            
            if not content:
                print(f"[Bing MCP] No content in response: {response}")
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                    result_type=ResultType.RAW,
                )
            
            # Extract results from MCP response
            text_content = content[0].get("text", "")
            if not text_content:
                print(f"[Bing MCP] Empty text content")
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="empty_content",
                    result_type=ResultType.RAW,
                )
            
            search_data = json.loads(text_content)
            results = search_data.get("results", [])
            
            if not results:
                print(f"[Bing MCP] No results in search_data: {search_data}")
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_results",
                    result_type=ResultType.RAW,
                )
            
            print(f"[Bing MCP] Got {len(results)} results for query: {cleaned_query}")
            
            # Process results
            from infra.tool_clients.search_result_processor import process_search_results
            
            # Convert to standard format with robust field extraction
            standard_results = []
            for r in results:
                # 健壮性处理：支持多种字段名
                title = r.get("title") or r.get("name") or ""
                url = r.get("url") or r.get("link") or ""
                snippet = r.get("description") or r.get("snippet") or r.get("content") or ""
                
                if not title and not url:
                    continue  # Skip invalid results
                
                standard_results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "score": 0.8,  # Default score for Bing results
                })
            
            if not standard_results:
                print(f"[Bing MCP] No valid results after conversion")
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_valid_results",
                    result_type=ResultType.RAW,
                )
            
            processed = process_search_results(
                standard_results,
                query=cleaned_query,  # 使用清洗后的query做相关性判断
                max_results=self.max_results,
                relevance_threshold=0.05,  # 进一步降低阈值，避免过度过滤
            )
            
            if not processed:
                # 如果过滤后为空，直接使用原始结果
                print(f"[Bing MCP] All results filtered out, using raw results")
                processed = standard_results[:self.max_results]
            
            # Format output
            lines = []
            for i, r in enumerate(processed, 1):
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")[:self.snippet_chars]
                credibility = r.get("credibility", 5)
                
                trust_mark = ""
                if credibility >= 9:
                    trust_mark = " [官方]"
                elif credibility >= 7:
                    trust_mark = " [可信]"
                
                lines.append(f"{i}. {title}{trust_mark} | {url} | {snippet}")
            
            text = f"已搜索{query}，结果如下：\n" + "\n".join(lines)  # 显示原始query给用户
            
            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "bing_mcp",
                    "query": query,  # 保留原始query
                    "cleaned_query": cleaned_query,  # 记录清洗后的query
                    "results": processed,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.RAW,
            )
            
        except subprocess.TimeoutExpired:
            print(f"[Bing MCP] Timeout after {self.timeout}s")
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.RAW,
            )
        except Exception as e:
            print(f"[Bing MCP] Error: {e}")
            import traceback
            traceback.print_exc()
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"bing_mcp_error:{e}",
                result_type=ResultType.RAW,
            )
    
    def health_check(self) -> bool:
        """Check if npx is available."""
        try:
            subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                timeout=2
            )
            return True
        except Exception:
            return False
