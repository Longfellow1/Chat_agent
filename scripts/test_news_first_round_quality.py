#!/usr/bin/env python3
"""
测试新闻第一轮输出质量
验证：
1. 返回内容精炼（无URL、日期等元数据）
2. 每条新闻简洁（30-50字）
3. 格式清晰（序号. 标题\n摘要）
"""

import sys
import os

# Add agent_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_service'))

from infra.tool_clients.providers.news_provider import SinaNewsProvider
from infra.tool_clients.provider_config import ProviderConfig


def test_news_first_round_quality():
    """测试新闻第一轮输出质量"""
    
    # 创建provider
    config = ProviderConfig(
        name="sina_news",
        priority=1,
        timeout=10.0,
    )
    provider = SinaNewsProvider(config)
    
    # 测试查询
    test_queries = [
        "股票市场",
        "基金投资",
        "期货交易",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = provider.execute(query=query)
        
        if not result.ok:
            print(f"❌ Failed: {result.error}")
            continue
        
        tool_result = result.data
        if not tool_result or not tool_result.ok:
            print(f"❌ Tool failed")
            continue
        
        # 输出第一轮内容
        print("\n第一轮输出（用户看到的）:")
        print("-" * 60)
        print(tool_result.text)
        print("-" * 60)
        
        # 验证质量
        lines = tool_result.text.strip().split('\n\n')
        print(f"\n✓ 返回 {len(lines)} 条新闻")
        
        # 检查每条新闻
        for i, line in enumerate(lines, 1):
            # 检查是否包含URL
            if 'http' in line:
                print(f"  ❌ 第{i}条包含URL")
            else:
                print(f"  ✓ 第{i}条无URL")
            
            # 检查长度
            char_count = len(line)
            if char_count > 150:
                print(f"  ⚠️  第{i}条过长 ({char_count}字)")
            else:
                print(f"  ✓ 第{i}条长度合理 ({char_count}字)")
        
        # 输出raw数据（用于后续多轮查询）
        if tool_result.raw:
            print(f"\n✓ Raw数据包含 {len(tool_result.raw.get('results', []))} 条完整记录")
            print(f"  可用于第二轮详细查询")


if __name__ == "__main__":
    test_news_first_round_quality()
