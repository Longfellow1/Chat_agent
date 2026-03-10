#!/usr/bin/env python3
"""Fix line 420 in mcp_gateway.py."""

with open('agent_service/infra/tool_clients/mcp_gateway.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic lines around 420
for i in range(len(lines)):
    if i == 419:  # Line 420 (0-indexed)
        # Check if this line has the problem
        if 'text = f' in lines[i] and '相关新闻' in lines[i]:
            # Replace with correct line
            lines[i] = '            text = f""{topic}"相关新闻：\\n" + "\\n".join(lines)\n'
            print(f"Fixed line {i+1}")
            
            # Check if next line is garbage
            if i+1 < len(lines) and lines[i+1].strip().startswith('" + "'):
                lines[i+1] = ''  # Remove garbage line
                print(f"Removed garbage line {i+2}")

with open('agent_service/infra/tool_clients/mcp_gateway.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Fixed line 420")
