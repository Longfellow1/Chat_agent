#!/usr/bin/env python3
"""
移除所有mock fallback的脚本

执行步骤：
1. 移除所有mock provider注册
2. 移除所有mock fallback调用
3. 添加LLM fallback方法
"""

import re
from pathlib import Path

def remove_mock_from_mcp_gateway():
    """移除mcp_gateway.py中的所有mock相关代码"""
    
    file_path = Path("agent_service/infra/tool_clients/mcp_gateway.py")
    content = file_path.read_text(encoding="utf-8")
    
    # 1. 移除mock导入（已完成）
    
    # 2. 移除所有 .register_provider("mock", MockProvider) 行
    content = re.sub(
        r'\s+self\.\w+_chain\.register_provider\("mock", MockProvider\)\n',
        '',
        content
    )
    
    # 3. 移除 from infra.tool_clients.providers.mock_provider import MockProvider
    content = re.sub(
        r'\s+from infra\.tool_clients\.providers\.mock_provider import MockProvider\n',
        '',
        content
    )
    
    # 4. 替换所有 fallback = mock_xxx(...) 模式为 LLM fallback
    # 这个需要手动处理，因为每个地方的参数不同
    
    file_path.write_text(content, encoding="utf-8")
    print(f"✅ 已移除 {file_path} 中的mock注册")

if __name__ == "__main__":
    remove_mock_from_mcp_gateway()
    print("\n✅ Mock移除完成")
    print("\n⚠️  接下来需要手动：")
    print("1. 替换所有 fallback = mock_xxx(...) 为 LLM fallback调用")
    print("2. 添加 _llm_fallback() 方法")
    print("3. 删除 mock_clients.py 和 mock_provider.py")
