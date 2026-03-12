#!/usr/bin/env python3
"""
运行200条评测，验证新提示词的效果
"""

import subprocess
import sys
import os

# 确保在正确的目录
os.chdir('agent_service')

# 运行评测
print("=" * 80)
print("运行200条评测，验证新提示词效果")
print("=" * 80)

result = subprocess.run(
    [sys.executable, '../scripts/run_full_eval.py', '--count', '200'],
    capture_output=False,
    text=True
)

sys.exit(result.returncode)
