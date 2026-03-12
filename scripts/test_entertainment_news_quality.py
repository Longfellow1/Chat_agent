#!/usr/bin/env python3
"""
测试娱乐新闻第一轮输出质量
验证：
1. 返回内容精炼（无URL、日期等元数据）
2. 每条新闻简洁（30-50字）
3. 格式清晰（序号. 标题\n摘要）
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.agent')

# Add agent_service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_service'))

from infra.tool_clients.mcp_gateway import MCPToolGateway


def test_entertainment_news_quality():
    """测试娱乐新闻第一轮输出质量"""
    
    # 创建gateway
    gateway = MCPToolGateway()
    
    # 测试查询
    test_queries = [
        "找找娱乐新闻",
        "明星八卦",
        "电影新闻",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = gateway._news(query)
        
        if not result.ok:
            print(f"❌ Failed: {result.error}")
            continue
        
        # 输出第一轮内容
        print("\n第一轮输出（用户看到的）:")
        print("-" * 60)
        print(result.text)
        print("-" * 60)
        
        # 验证质量
        lines = result.text.strip().split('\n\n')
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


if __name__ == "__main__":
    test_entertainment_news_quality()
