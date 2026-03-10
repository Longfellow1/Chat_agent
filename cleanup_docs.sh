#!/bin/bash

# 文档清理脚本
# 删除过程性、重复的 Markdown 文档

set -e

echo "开始清理文档..."
echo "==============================================="

# 创建归档目录
echo "创建归档目录..."
mkdir -p archive/milestones
mkdir -p archive/test_reports
mkdir -p archive/baidu_integration

# 移动重要的里程碑报告到归档
echo "归档重要文档..."
[ -f M4_FINAL_REPORT.md ] && mv M4_FINAL_REPORT.md archive/milestones/
[ -f M5_FINAL_COMPLETION_REPORT.md ] && mv M5_FINAL_COMPLETION_REPORT.md archive/milestones/

# 删除过程性里程碑文档
echo "删除过程性里程碑文档..."
rm -f M4_COMPLETION_SUMMARY.md
rm -f M4_P0_COMPLETION_REPORT.md
rm -f M4_REVIEW_RESPONSE.md
rm -f M5_1_REMEDIATION_REPORT.md
rm -f M5_2_FINAL_SUMMARY.md
rm -f M5_2_GET_WEATHER_COMPLETION.md
rm -f M5_2_TRUTH_REPORT.md
rm -f M5_2_WEATHER_IMPLEMENTATION_COMPLETE.md
rm -f M5_2_WEATHER_QUOTA_EVALUATION.md
rm -f M5_3_CONTENT_REWRITER_COMPLETION.md
rm -f M5_4_PLAN_TRIP_M1_FINAL_SUMMARY.md
rm -f M5_4_PLAN_TRIP_M2_COMPLETE.md
rm -f M5_4_PLAN_TRIP_M2_COMPLETION.md
rm -f M5_4_PLAN_TRIP_M2_FINAL_REPORT.md
rm -f M5_4_PLAN_TRIP_MILESTONE_1_COMPLETE.md
rm -f M5_CONTENT_REWRITER_CORRECTION.md
rm -f M5_FIND_NEARBY_COMPLETION.md
rm -f M5_REVIEW_FIXES.md
rm -f M5_STABILITY_FIX_COMPLETE.md
rm -f M5_VALIDATION_SUMMARY.md
rm -f M5_FINAL_VALIDATION_REPORT.md
rm -f spec/m4_provider_chain_completion.md
rm -f spec/routing_fixes_completion.md
rm -f spec/routing_fixes_final_completion.md
rm -f spec/parser_simplification_completion.md

# 删除百度相关重复文档
echo "删除百度集成重复文档..."
rm -f BAIDU_AI_SEARCH_COMPLETION.md
rm -f BAIDU_API_HELP_NEEDED.md
rm -f BAIDU_API_KEY_ISSUE.md
rm -f BAIDU_NEWS_DEPRECATION.md
rm -f BAIDU_SEARCH_STATUS.md
rm -f BAIDU_WEB_SEARCH_COMPLETION.md
rm -f docs/baidu_ai_search_integration.md
rm -f docs/baidu_integration_completion.md
rm -f docs/baidu_quick_start.md

# 删除项目状态重复文档
echo "删除项目状态重复文档..."
rm -f M5_PROJECT_STATUS_INVENTORY.md
rm -f PROJECT_STATUS_RECONCILIATION.md
rm -f TOOL_STATUS_INVENTORY.md
rm -f LOCATION_INTENT_PROJECT_STATUS.md
rm -f PROJECT_PROGRESS_SUMMARY.md
rm -f M5_1_CONTEXT_TRANSFER_STATUS.md

# 删除验证任务
echo "删除验证任务文档..."
rm -f M5_4_PLAN_TRIP_MILESTONE_1_REMEDIATION.md
rm -f M5_VERIFICATION_TASKS.md

# 删除其他临时文档
echo "删除临时分析文档..."
rm -f M5_STABILITY_ROOT_CAUSE_ANALYSIS.md
rm -f MODEL_UPGRADE_REPORT.md
rm -f SNIPPET_TRUNCATION_OPTIMIZATION.md
rm -f PROVIDER_CHAIN_CONFIGURATION.md
rm -f bing_mcp_evaluation_report.md
rm -f bing_mcp_performance_analysis.md
rm -f credibility_scoring_analysis.md
rm -f ARCHITECTURE_COMPARISON.md

# 删除旧的测试报告
echo "删除旧测试报告..."
rm -f tests/integration/user_satisfaction_50_report.md
rm -f tests/integration/real_dataset_test_report.md
rm -f tests/integration/test_100_queries_report.md
rm -f tests/integration/nearby_100_test_report.md
rm -f tests/integration/keyword_extraction_report.md
rm -f tests/integration/m1_task3_end_to_end_report.md
rm -f tests/integration/m2_query_preprocessing_report.md
rm -f tests/integration/m2_result_ranking_report.md
rm -f tests/integration/m2_routing_baseline_report.md
rm -f tests/integration/m2_task4_end_to_end_report.md
rm -f tests/integration/m2_task4_report.md
rm -f tests/integration/baidu_ai_search_30_queries_report.md
rm -f tests/integration/baidu_web_search_30_queries_report.md

# 删除过时的规范文档
echo "删除过时规范文档..."
rm -f spec/code_quality_analysis.md
rm -f spec/local_life_optimization_milestone.md
rm -f spec/m4_planning.md
rm -f spec/m4_provider_chain_implementation.md
rm -f spec/m4_test_design_review.md
rm -f spec/m5_4_plan_trip_tdd.md
rm -f spec/m5_auto_show_readiness.md
rm -f spec/m5_milestone_plan.md
rm -f spec/milestone_plan.md
rm -f spec/milestones_summary.md
rm -f spec/prd_eval_and_release.md
rm -f spec/product_requirements_review.md
rm -f spec/SPEC_MANAGEMENT_PLAN.md
rm -f spec/tool_accuracy_milestone_v2.md
rm -f spec/tool_contract_v1.md
rm -f spec/spec_v1_production.md
rm -f spec/评审.md

# 删除临时测试文件
echo "删除临时测试文件..."
rm -f testset_design_v2.md

# 统计
echo ""
echo "==============================================="
echo "清理完成！"
echo ""
echo "保留的核心文档:"
echo "  - PROJECT_STATUS.md (新建)"
echo "  - MANUAL_TEST_QUERIES.md"
echo "  - 项目架构文档.md"
echo "  - agent_service/README.md"
echo ""
echo "归档目录:"
echo "  - archive/milestones/"
echo ""
echo "剩余文档数:"
find . -name "*.md" -type f ! -path "./node_modules/*" ! -path "./.venv/*" ! -path "./.pytest_cache/*" ! -path "./Mcp_test/*" ! -path "./agent_service/.pytest_cache/*" | wc -l
echo ""
echo "建议下一步:"
echo "  1. 查看 PROJECT_STATUS.md"
echo "  2. 查看 DOC_CLEANUP_PLAN.md 了解详情"
echo "  3. 创建合并后的文档（见计划）"
