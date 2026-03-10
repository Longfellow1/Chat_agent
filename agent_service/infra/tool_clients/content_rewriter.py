"""
内容重写模块

用于清理和重写工具返回的内容，去除噪声，提取核心信息
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from infra.llm_clients.base import LLMClient


@dataclass
class RewriteConfig:
    """重写配置"""
    
    enable_llm: bool = True  # 是否启用 LLM 重写
    max_length: int = 500  # 最大输出长度
    temperature: float = 0.3  # LLM 温度
    timeout_sec: float = 5.0  # 超时时间


class ContentRewriter:
    """内容重写器"""
    
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        config: RewriteConfig | None = None
    ) -> None:
        self.llm = llm_client
        self.config = config or RewriteConfig()
    
    def rewrite_news(self, raw_content: str) -> str:
        """
        重写新闻内容
        
        Args:
            raw_content: 原始新闻内容（包含噪声）
            
        Returns:
            清理后的新闻摘要
        """
        # 1. 清理噪声
        cleaned = self._clean_noise(raw_content)
        
        # 2. 如果启用 LLM，使用 LLM 重写
        if self.config.enable_llm and self.llm:
            try:
                return self._llm_rewrite_news(cleaned)
            except Exception:  # noqa: BLE001
                # LLM 失败，返回清理后的内容
                pass
        
        # 3. 规则提取摘要
        return self._extract_summary(cleaned)
    
    def _clean_noise(self, text: str) -> str:
        """
        清理噪声：URL、格式标记、多余空白等
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 1. 移除 URL
        # 匹配 [查看原文](url) 或 [text](url) 格式
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 移除独立的 URL
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # 2. 移除转义字符
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', ' ')
        
        # 3. 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # 4. 移除常见噪声词
        noise_patterns = [
            r'查看原文',
            r'点击查看',
            r'更多详情',
            r'阅读全文',
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _extract_summary(self, text: str) -> str:
        """
        规则提取摘要（不使用 LLM）
        
        Args:
            text: 清理后的文本
            
        Returns:
            摘要
        """
        # 按句子分割
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 提取前 3 句作为摘要
        summary_sentences = sentences[:3]
        summary = '。'.join(summary_sentences)
        
        # 限制长度
        if len(summary) > self.config.max_length:
            summary = summary[:self.config.max_length] + '...'
        
        return summary
    
    def _llm_rewrite_news(self, cleaned_text: str) -> str:
        """
        使用 LLM 重写新闻内容
        
        Args:
            cleaned_text: 清理后的文本
            
        Returns:
            LLM 重写后的摘要
        """
        if not self.llm:
            return cleaned_text
        
        prompt = self._build_news_prompt(cleaned_text)
        system_prompt = self._news_system_prompt()
        
        # 调用 LLM
        if hasattr(self.llm, "generate_with_timeout"):
            response = self.llm.generate_with_timeout(  # type: ignore[attr-defined]
                user_query=prompt,
                system_prompt=system_prompt,
                timeout_sec=self.config.timeout_sec
            )
        else:
            response = self.llm.generate(
                user_query=prompt,
                system_prompt=system_prompt
            )
        
        return response.strip()
    
    def _build_news_prompt(self, text: str) -> str:
        """构建新闻重写提示词"""
        return f"""请将以下财经新闻内容重写为简洁的摘要，要求：
1. 提取核心信息（市场趋势、关键数据、重要事件）
2. 去除冗余信息和噪声
3. 使用清晰、专业的语言
4. 控制在 200 字以内

原始内容：
{text}

重写后的摘要："""
    
    def _news_system_prompt(self) -> str:
        """新闻重写系统提示词"""
        return """你是一个专业的财经新闻编辑。你的任务是：
1. 提取新闻的核心信息（市场趋势、关键数据、重要事件）
2. 去除冗余信息和噪声（URL、格式标记等）
3. 使用清晰、专业的语言重写
4. 保持客观中立，不添加主观评论
5. 控制输出长度在 200 字以内

只输出重写后的摘要，不要输出其他内容。"""


def rewrite_news_batch(
    news_items: list[dict[str, Any]],
    llm_client: LLMClient | None = None,
    config: RewriteConfig | None = None
) -> list[dict[str, Any]]:
    """
    批量重写新闻内容
    
    Args:
        news_items: 新闻列表，每条新闻包含 title, content 等字段
        llm_client: LLM 客户端
        config: 重写配置
        
    Returns:
        重写后的新闻列表
    """
    rewriter = ContentRewriter(llm_client=llm_client, config=config)
    
    rewritten_items = []
    for item in news_items:
        # 提取原始内容
        raw_content = item.get("content", "")
        if not raw_content:
            # 如果没有 content，尝试使用 title + snippet
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            raw_content = f"{title}。{snippet}"
        
        # 重写内容
        rewritten_content = rewriter.rewrite_news(raw_content)
        
        # 构建新的 item
        rewritten_item = {
            **item,
            "content": rewritten_content,
            "original_content": raw_content,  # 保留原始内容
        }
        rewritten_items.append(rewritten_item)
    
    return rewritten_items
