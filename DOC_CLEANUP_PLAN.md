# 文档清理与合并计划

## 分析结果

总文档数: 140 个 Markdown 文件

### 文档分类统计

| 类型 | 数量 | 总大小 | 建议 |
|------|------|--------|------|
| other | 46 | 187KB | 保留核心文档 |
| specification | 29 | 217KB | 合并重复规范 |
| milestone_completion | 26 | 93KB | 删除过程文档 |
| baidu_integration | 14 | 102KB | 合并为单一文档 |
| documentation | 9 | 60KB | 整理到 docs/ |
| project_status | 7 | 36KB | 合并为单一状态 |
| test_report | 7 | 31KB | 保留最新的 |
| verification | 2 | 10KB | 已完成可删除 |

---

## 清理策略

### 1. 里程碑完成报告 (26个 → 5个)

**保留:**
- `M4_FINAL_REPORT.md` - M4 最终报告
- `M5_FINAL_COMPLETION_REPORT.md` - M5 最终报告
- `PROJECT_STATUS_SUMMARY.md` - 项目总体状态

**删除过程性文档 (21个):**
```
M4_COMPLETION_SUMMARY.md
M4_P0_COMPLETION_REPORT.md
M4_REVIEW_RESPONSE.md
M5_1_REMEDIATION_REPORT.md
M5_2_FINAL_SUMMARY.md
M5_2_GET_WEATHER_COMPLETION.md
M5_2_TRUTH_REPORT.md
M5_2_WEATHER_IMPLEMENTATION_COMPLETE.md
M5_3_CONTENT_REWRITER_COMPLETION.md
M5_4_PLAN_TRIP_M1_FINAL_SUMMARY.md
M5_4_PLAN_TRIP_M2_COMPLETE.md
M5_4_PLAN_TRIP_M2_COMPLETION.md
M5_4_PLAN_TRIP_M2_FINAL_REPORT.md
M5_4_PLAN_TRIP_MILESTONE_1_COMPLETE.md
M5_CONTENT_REWRITER_CORRECTION.md
M5_FIND_NEARBY_COMPLETION.md
M5_REVIEW_FIXES.md
M5_STABILITY_FIX_COMPLETE.md
M5_VALIDATION_SUMMARY.md
spec/m4_provider_chain_completion.md
spec/routing_fixes_completion.md
```

### 2. 百度集成文档 (14个 → 2个)

**合并为:**
- `docs/BAIDU_INTEGRATION_GUIDE.md` - 统一的百度集成指南

**删除重复文档 (12个):**
```
BAIDU_AI_SEARCH_COMPLETION.md
BAIDU_API_HELP_NEEDED.md
BAIDU_API_KEY_ISSUE.md
BAIDU_NEWS_DEPRECATION.md
BAIDU_SEARCH_STATUS.md
BAIDU_WEB_SEARCH_COMPLETION.md
docs/baidu_ai_search_integration.md
docs/baidu_integration_completion.md
docs/baidu_maps_mcp_integration.md
docs/baidu_mcp_integration.md
docs/baidu_qianfan_integration_guide.md
docs/baidu_quick_start.md
tests/integration/baidu_ai_search_30_queries_report.md
tests/integration/baidu_web_search_30_queries_report.md
```

### 3. 项目状态文档 (7个 → 1个)

**合并为:**
- `PROJECT_STATUS.md` - 统一的项目状态文档

**删除重复文档 (6个):**
```
M5_PROJECT_STATUS_INVENTORY.md
PROJECT_STATUS_RECONCILIATION.md
TOOL_STATUS_INVENTORY.md
PROJECT_STATUS_SUMMARY.md
LOCATION_INTENT_PROJECT_STATUS.md
PROJECT_PROGRESS_SUMMARY.md
M5_1_CONTEXT_TRANSFER_STATUS.md
```

### 4. 测试报告 (7个 → 2个)

**保留:**
- `tests/integration/TEST_REPORTS.md` - 合并所有测试报告

**删除旧报告 (6个):**
```
tests/integration/user_satisfaction_50_report.md
tests/integration/real_dataset_test_report.md
tests/integration/test_100_queries_final_report.md
tests/integration/nearby_100_test_report.md
tests/integration/test_100_queries_report.md
tests/integration/keyword_extraction_report.md
tests/integration/m1_task3_end_to_end_report.md
tests/integration/m2_query_preprocessing_report.md
tests/integration/m2_result_ranking_report.md
tests/integration/m2_routing_baseline_report.md
tests/integration/m2_task4_end_to_end_report.md
tests/integration/m2_task4_report.md
```

### 5. 规范文档 (29个 → 10个)

**保留核心规范:**
- `spec/ARCHITECTURE.md` - 架构设计
- `spec/MILESTONE_PLAN.md` - 里程碑规划
- `spec/TOOL_OPTIMIZATION_GUIDE.md` - 工具优化指南
- `spec/TEST_STANDARD.md` - 测试标准
- `spec/PRD.md` - 产品需求

**删除过时/重复规范 (19个):**
```
spec/code_quality_analysis.md
spec/local_life_optimization_milestone.md
spec/m4_planning.md
spec/m4_provider_chain_implementation.md
spec/m4_test_design_review.md
spec/m5_4_plan_trip_tdd.md
spec/m5_auto_show_readiness.md
spec/m5_milestone_plan.md
spec/milestone_plan.md
spec/milestones_summary.md
spec/parser_simplification_completion.md
spec/prd_eval_and_release.md
spec/product_requirements_review.md
spec/routing_fixes_final_completion.md
spec/SPEC_MANAGEMENT_PLAN.md
spec/tool_accuracy_milestone_v2.md
spec/tool_contract_v1.md
spec/评审.md
```

### 6. 验证任务 (2个 → 0个)

**删除已完成验证:**
```
M5_4_PLAN_TRIP_MILESTONE_1_REMEDIATION.md
M5_VERIFICATION_TASKS.md
```

### 7. 其他临时文档

**删除:**
```
M5_STABILITY_ROOT_CAUSE_ANALYSIS.md
M5_FINAL_VALIDATION_REPORT.md
MODEL_UPGRADE_REPORT.md
SNIPPET_TRUNCATION_OPTIMIZATION.md
PROVIDER_CHAIN_CONFIGURATION.md
bing_mcp_evaluation_report.md
bing_mcp_performance_analysis.md
credibility_scoring_analysis.md
手动测试终端指令.md
工作流key.md
testset_design_v2.md
```

---

## 合并后的文档结构

```
项目根目录/
├── README.md                          # 项目总览
├── PROJECT_STATUS.md                  # 项目状态（合并）
├── ARCHITECTURE.md                    # 架构文档（合并）
│
├── docs/                              # 文档目录
│   ├── BAIDU_INTEGRATION_GUIDE.md    # 百度集成指南（合并）
│   ├── PROVIDER_CHAIN_GUIDE.md       # Provider Chain 使用指南
│   ├── AUTO_SHOW_GUIDE.md            # 车展演示指南
│   └── MANUAL_TEST_GUIDE.md          # 手动测试指南
│
├── spec/                              # 规范文档
│   ├── ARCHITECTURE.md               # 架构设计（合并）
│   ├── MILESTONE_PLAN.md             # 里程碑规划（合并）
│   ├── TOOL_OPTIMIZATION_GUIDE.md    # 工具优化指南（合并）
│   ├── TEST_STANDARD.md              # 测试标准
│   └── PRD.md                        # 产品需求（合并）
│
├── tests/integration/                 # 测试报告
│   └── TEST_REPORTS.md               # 测试报告汇总（合并）
│
└── archive/                           # 归档（可选）
    └── milestones/                    # 里程碑归档
        ├── M4_FINAL_REPORT.md
        └── M5_FINAL_COMPLETION_REPORT.md
```

---

## 执行计划

### 阶段1: 创建合并文档 (优先)

1. **PROJECT_STATUS.md** - 合并所有项目状态
2. **docs/BAIDU_INTEGRATION_GUIDE.md** - 合并百度集成文档
3. **spec/ARCHITECTURE.md** - 合并架构相关文档
4. **spec/MILESTONE_PLAN.md** - 合并里程碑规划
5. **tests/integration/TEST_REPORTS.md** - 合并测试报告

### 阶段2: 删除冗余文档

执行批量删除命令（见下方脚本）

### 阶段3: 验证

1. 检查合并文档的完整性
2. 确保没有遗漏重要信息
3. 更新 README.md 中的文档索引

---

## 预期效果

- **文档数量**: 140 → 约 20 个核心文档
- **减少**: 约 85% 的文档数量
- **提升**: 文档可维护性和可读性
- **保留**: 所有关键信息和历史记录

---

## 执行脚本

```bash
# 创建归档目录
mkdir -p archive/milestones

# 移动重要的里程碑报告到归档
mv M4_FINAL_REPORT.md archive/milestones/
mv M5_FINAL_COMPLETION_REPORT.md archive/milestones/

# 删除过程性里程碑文档
rm M4_COMPLETION_SUMMARY.md M4_P0_COMPLETION_REPORT.md M4_REVIEW_RESPONSE.md
rm M5_1_REMEDIATION_REPORT.md M5_2_FINAL_SUMMARY.md M5_2_GET_WEATHER_COMPLETION.md
rm M5_2_TRUTH_REPORT.md M5_2_WEATHER_IMPLEMENTATION_COMPLETE.md
rm M5_3_CONTENT_REWRITER_COMPLETION.md M5_4_PLAN_TRIP_M1_FINAL_SUMMARY.md
rm M5_4_PLAN_TRIP_M2_COMPLETE.md M5_4_PLAN_TRIP_M2_COMPLETION.md
rm M5_4_PLAN_TRIP_M2_FINAL_REPORT.md M5_4_PLAN_TRIP_MILESTONE_1_COMPLETE.md
rm M5_CONTENT_REWRITER_CORRECTION.md M5_FIND_NEARBY_COMPLETION.md
rm M5_REVIEW_FIXES.md M5_STABILITY_FIX_COMPLETE.md M5_VALIDATION_SUMMARY.md

# 删除百度相关重复文档
rm BAIDU_AI_SEARCH_COMPLETION.md BAIDU_API_HELP_NEEDED.md BAIDU_API_KEY_ISSUE.md
rm BAIDU_NEWS_DEPRECATION.md BAIDU_SEARCH_STATUS.md BAIDU_WEB_SEARCH_COMPLETION.md

# 删除项目状态重复文档
rm M5_PROJECT_STATUS_INVENTORY.md PROJECT_STATUS_RECONCILIATION.md
rm TOOL_STATUS_INVENTORY.md LOCATION_INTENT_PROJECT_STATUS.md
rm PROJECT_PROGRESS_SUMMARY.md M5_1_CONTEXT_TRANSFER_STATUS.md

# 删除验证任务
rm M5_4_PLAN_TRIP_MILESTONE_1_REMEDIATION.md M5_VERIFICATION_TASKS.md

# 删除其他临时文档
rm M5_STABILITY_ROOT_CAUSE_ANALYSIS.md M5_FINAL_VALIDATION_REPORT.md
rm MODEL_UPGRADE_REPORT.md SNIPPET_TRUNCATION_OPTIMIZATION.md
rm PROVIDER_CHAIN_CONFIGURATION.md bing_mcp_evaluation_report.md
rm bing_mcp_performance_analysis.md credibility_scoring_analysis.md

echo "清理完成！"
```

---

**注意**: 执行前请先创建合并文档，确保重要信息不丢失！
