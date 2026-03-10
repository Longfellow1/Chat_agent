#!/bin/bash

# M2 端到端测试启动脚本
# 自动加载环境变量并运行测试

set -e

# 激活虚拟环境
source .venv/bin/activate

# 运行测试
python tests/integration/test_m2_task4_end_to_end.py

echo ""
echo "测试完成！查看报告: tests/integration/m2_task4_end_to_end_report.md"
