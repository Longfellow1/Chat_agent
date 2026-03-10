#!/usr/bin/env python3
"""Fix Chinese quotes in mcp_gateway.py."""

with open('agent_service/infra/tool_clients/mcp_gateway.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_count = 0

for i in range(len(lines)):
    line = lines[i]
    
    # Fix line 416: 未检索到"{topic}"相关新闻
    if i == 415 and '未检索到' in line and '"相关新闻"' in line:
        # Use single quotes for f-string to avoid conflict with Chinese quotes
        lines[i] = '                return ToolResult(ok=False, text=f\'未检索到"{topic}"相关新闻\', error="no_news_results")\n'
        print(f"Fixed line {i+1}")
        fixed_count += 1
    
    # Fix line 420: "{topic}"相关新闻：
    if i == 419 and '"相关新闻：' in line:
        lines[i] = '            text = f\'"{topic}"相关新闻：\\n\' + "\\n".join(lines)\n'
        print(f"Fixed line {i+1}")
        fixed_count += 1

with open('agent_service/infra/tool_clients/mcp_gateway.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"✅ Fixed {fixed_count} lines")
