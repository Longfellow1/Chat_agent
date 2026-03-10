#!/bin/bash

# 清理根目录下的临时文件和测试脚本

set -e

echo "清理根目录文件..."
echo "==============================================="

# 创建归档目录
mkdir -p archive/test_scripts
mkdir -p archive/temp_files
mkdir -p archive/csv_data

# 移动临时测试脚本到归档
echo "归档测试脚本..."
mv test_*.py archive/test_scripts/ 2>/dev/null || true
mv fix_*.py archive/temp_files/ 2>/dev/null || true
mv verify_*.py archive/test_scripts/ 2>/dev/null || true
mv analyze_*.py archive/temp_files/ 2>/dev/null || true
mv extract_*.py archive/temp_files/ 2>/dev/null || true
mv evaluation.py archive/temp_files/ 2>/dev/null || true

# 移动 CSV 数据文件
echo "归档 CSV 数据..."
mv *.csv archive/csv_data/ 2>/dev/null || true

# 移动临时 shell 脚本
echo "归档临时脚本..."
mv run_*.sh archive/temp_files/ 2>/dev/null || true

# 删除重复的项目状态文档
echo "删除重复状态文档..."
rm -f PROJECT_STATUS_SUMMARY.md

# 删除空文档
echo "删除空文档..."
rm -f AGENT_ARCHITECTURE_ANALYSIS.md
rm -f M5_4_PLAN_TRIP_DESIGN.md

# 移动其他临时文档
echo "归档其他临时文档..."
mv agent-reach-integration-plan.md archive/temp_files/ 2>/dev/null || true
mv chatflow-alternatives-analysis.md archive/temp_files/ 2>/dev/null || true
mv open-source-chat-assistants.md archive/temp_files/ 2>/dev/null || true

# 保留的核心文档
echo ""
echo "==============================================="
echo "保留的核心文档:"
echo "  - PROJECT_STATUS.md"
echo "  - MANUAL_TEST_QUERIES.md"
echo "  - M5_4_PLAN_TRIP_PRD.md"
echo "  - M5_4_PLAN_TRIP_M3_PLAN.md"
echo "  - M5_4_PLAN_TRIP_M3_STATUS.md"
echo "  - 项目架构文档.md"
echo "  - 手动测试终端指令.md"
echo "  - 工作流key.md"
echo ""
echo "清理工具:"
echo "  - DOC_CLEANUP_PLAN.md"
echo "  - DOC_CLEANUP_SUMMARY.md"
echo "  - cleanup_docs.sh"
echo "  - cleanup_root_files.sh (本脚本)"
echo ""

# 统计
echo "根目录剩余文件:"
ls -1 *.md *.py *.sh 2>/dev/null | wc -l

echo ""
echo "归档目录:"
echo "  - archive/test_scripts/ (测试脚本)"
echo "  - archive/temp_files/ (临时文件)"
echo "  - archive/csv_data/ (CSV 数据)"
echo ""
echo "清理完成！"
