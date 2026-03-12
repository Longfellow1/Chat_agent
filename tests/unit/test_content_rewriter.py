"""
测试内容重写模块
"""

from __future__ import annotations

import pytest

from agent_service.infra.tool_clients.content_rewriter import (
    ContentRewriter,
    RewriteConfig,
    rewrite_news_batch,
)


class TestContentRewriter:
    """测试 ContentRewriter"""
    
    def test_clean_noise_removes_urls(self):
        """测试清理 URL"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False))
        
        raw = "CNBC的《市场收盘后》报道：提供快速、准确和实用的市场更新。[查看原文](https://www.cnbc.com/video/2026/03/03/the-post-market-wrap-march-3-2026.html)"
        
        cleaned = rewriter._clean_noise(raw)
        
        assert "https://" not in cleaned
        assert "查看原文" not in cleaned
        assert "CNBC的《市场收盘后》报道" in cleaned
    
    def test_clean_noise_removes_escape_chars(self):
        """测试清理转义字符"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False))
        
        raw = "以下是今天的部分财经新闻：\\n\\n1. CNBC的《市场收盘后》报道"
        
        cleaned = rewriter._clean_noise(raw)
        
        assert "\\n" not in cleaned
        assert "CNBC的《市场收盘后》报道" in cleaned
    
    def test_clean_noise_removes_multiple_whitespace(self):
        """测试清理多余空白"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False))
        
        raw = "道指期货    小幅下跌；   投资者关注英伟达业绩"
        
        cleaned = rewriter._clean_noise(raw)
        
        assert "  " not in cleaned
        assert "道指期货 小幅下跌" in cleaned
    
    def test_extract_summary_limits_length(self):
        """测试摘要长度限制"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False, max_length=50))
        
        text = "这是一个非常长的第一句话，包含很多信息，超过了50个字的限制。这是第二句话。这是第三句话。"
        
        summary = rewriter._extract_summary(text)
        
        # 新策略：只取第一句，限制到50字
        assert len(summary) <= 53  # 50 + "..."
        assert "这是一个非常长的第一句话" in summary
    
    def test_extract_summary_takes_first_sentences(self):
        """测试提取第一句"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False, max_length=500))
        
        text = "第一句。第二句。第三句。第四句。"
        
        summary = rewriter._extract_summary(text)
        
        # 新策略：只取第一句
        assert "第一句" in summary
        assert "第二句" not in summary
        assert "第三句" not in summary
        assert "第四句" not in summary
    
    def test_rewrite_news_without_llm(self):
        """测试不使用 LLM 的新闻重写"""
        rewriter = ContentRewriter(config=RewriteConfig(enable_llm=False))
        
        raw = """以下是今天的部分财经新闻：\\n\\n1. CNBC的《市场收盘后》报道：提供快速、准确和实用的市场更新。[查看原文](https://www.cnbc.com/video/2026/03/03/the-post-market-wrap-march-3-2026.html)\\n\\n2. 芯片巨头英伟达财报公布后，道指期货小幅下跌；投资者关注英伟达业绩——[查看原文](https://www.wsj.com/livecoverage/stock-market-today-dow-sp-500-nasdaq-02-26-2026)"""
        
        result = rewriter.rewrite_news(raw)
        
        # 验证清理效果
        assert "https://" not in result
        assert "查看原文" not in result
        assert "\\n" not in result
        
        # 验证保留核心信息
        assert "CNBC" in result or "市场收盘后" in result or "英伟达" in result
    
    def test_rewrite_news_batch(self):
        """测试批量重写新闻"""
        news_items = [
            {
                "title": "道指下跌700点",
                "content": "科技股表现不佳，美国通胀报告火热，道指下跌700点——[查看原文](https://www.cnbc.com/2026/02/26/stock-market-today-live-updates.html)",
            },
            {
                "title": "英伟达财报",
                "snippet": "芯片巨头英伟达财报公布后，道指期货小幅下跌",
            },
        ]
        
        result = rewrite_news_batch(
            news_items,
            llm_client=None,
            config=RewriteConfig(enable_llm=False)
        )
        
        assert len(result) == 2
        
        # 第一条：使用 content
        assert "https://" not in result[0]["content"]
        assert "查看原文" not in result[0]["content"]
        assert "道指下跌" in result[0]["content"]
        
        # 第二条：使用 title + snippet，提取第一句
        assert "英伟达" in result[1]["content"]
        # 新策略：只取第一句，所以可能只有标题或第一句
        
        # 验证保留原始内容
        assert "original_content" in result[0]
        assert "original_content" in result[1]


class MockLLMClient:
    """Mock LLM 客户端"""
    
    def generate(self, user_query: str, system_prompt: str) -> str:
        """模拟 LLM 生成"""
        return "今日财经市场概要：道指下跌700点，科技股表现不佳，英伟达财报引发市场关注。"


class TestContentRewriterWithLLM:
    """测试使用 LLM 的内容重写"""
    
    def test_rewrite_news_with_llm(self):
        """测试使用 LLM 重写新闻"""
        mock_llm = MockLLMClient()
        rewriter = ContentRewriter(
            llm_client=mock_llm,
            config=RewriteConfig(enable_llm=True)
        )
        
        raw = """以下是今天的部分财经新闻：\\n\\n1. CNBC的《市场收盘后》报道：提供快速、准确和实用的市场更新。[查看原文](https://www.cnbc.com/video/2026/03/03/the-post-market-wrap-march-3-2026.html)"""
        
        result = rewriter.rewrite_news(raw)
        
        # 验证 LLM 重写结果
        assert "今日财经市场概要" in result
        assert "道指下跌" in result
    
    def test_rewrite_news_llm_fallback(self):
        """测试 LLM 失败时的降级"""
        
        class FailingLLMClient:
            def generate(self, user_query: str, system_prompt: str) -> str:
                raise RuntimeError("LLM 服务不可用")
        
        failing_llm = FailingLLMClient()
        rewriter = ContentRewriter(
            llm_client=failing_llm,
            config=RewriteConfig(enable_llm=True)
        )
        
        raw = "CNBC的《市场收盘后》报道：提供快速、准确和实用的市场更新。"
        
        # 应该降级到规则提取
        result = rewriter.rewrite_news(raw)
        
        assert "CNBC" in result or "市场收盘后" in result
