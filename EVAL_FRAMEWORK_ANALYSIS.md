# 评测框架匹配度分析

**日期**: 2026-03-09  
**目标**: 使用800条评测数据进行完整端到端评测

---

## 一、现有评测框架概览

### 1.1 评测脚本

| 脚本 | 用途 | 数据量 | 状态 |
|------|------|--------|------|
| `scripts/run_eval_chatapi.py` | 通用评测（延迟+答案） | 可配置 | ✅ 可用 |
| `scripts/self_assess_agent.py` | 自评测（13个case） | 13条 | ✅ 可用 |
| `scripts/run_smoke_tools.py` | 冒烟测试（8个工具） | 8条 | ✅ 可用 |

### 1.2 评测数据集

| 数据集 | 路径 | 数据量 | 状态 |
|--------|------|--------|------|
| 完整评测集 | `archive/csv_data/testset_eval_1000_v3.csv` | 1000条 | ✅ 存在 |
| 5%采样集 | `archive/csv_data/testset_eval_1000_v3_sample5p.csv` | 50条 | ✅ 存在 |

### 1.3 数据集结构

**字段**:
- `sample_id`: 样本ID
- `query`: 用户查询
- `sample_type`: 正/负/难
- `scenario`: 场景类型
- `category`: 类别（闲聊/工具调用/拒识）
- `expected_tool`: 期望工具名
- `expected_behavior`: 期望行为
- `risk_tag`: 风险标签

**分布**:
```
类别分布:
- 闲聊: 410条 (41%)
- 工具调用: 390条 (39%)
- 拒识: 200条 (20%)

工具分布:
- get_weather: 60条
- search_nearby: 58条
- get_stock: 58条
- plan_trip: 58条
- get_news: 58条
- web_search: 58条
- terminate_chat: 40条
```

---

## 二、工具名称匹配度分析

### 2.1 数据集 vs 当前实现

| 数据集工具名 | 当前实现 | 匹配度 | 说明 |
|-------------|---------|--------|------|
| `get_weather` | ✅ `get_weather` | 100% | 完全匹配 |
| `get_stock` | ✅ `get_stock` | 100% | 完全匹配 |
| `get_news` | ✅ `get_news` | 100% | 完全匹配 |
| `web_search` | ✅ `web_search` | 100% | 完全匹配 |
| `plan_trip` | ✅ `plan_trip` | 100% | 完全匹配 |
| `search_nearby` | ⚠️ `find_nearby` | 0% | **名称不匹配** |
| `terminate_chat` | ❌ 无 | 0% | **未实现** |

**总体匹配度**: 71% (5/7工具匹配)

### 2.2 关键问题

#### 问题1: `search_nearby` vs `find_nearby`

**数据集期望**: `search_nearby`  
**当前实现**: `find_nearby`

**影响**:
- 58条测试用例会被判定为失败
- 占工具调用类别的14.9% (58/390)
- 占总数据集的5.8% (58/1000)

**解决方案**:
1. **方案A**: 修改评测脚本，映射`search_nearby` → `find_nearby`
2. **方案B**: 在代码中添加`search_nearby`别名
3. **方案C**: 更新数据集（不推荐，历史数据）

#### 问题2: `terminate_chat`未实现

**数据集期望**: `terminate_chat`  
**当前实现**: 无此工具

**影响**:
- 40条测试用例会被判定为失败
- 占总数据集的4% (40/1000)

**解决方案**:
1. **方案A**: 实现`terminate_chat`工具（结束对话）
2. **方案B**: 评测时跳过这些case
3. **方案C**: 映射到`decision_mode == "end_chat"`

---

## 三、评测脚本适配性分析

### 3.1 `run_eval_chatapi.py`

**功能**:
- 调用`/chat`接口
- 记录延迟和答案
- 生成CSV报告

**优点**:
- ✅ 支持大规模评测（可配置limit）
- ✅ 记录延迟指标
- ✅ 生成结构化报告

**缺点**:
- ❌ 不验证工具名称
- ❌ 不验证expected_behavior
- ❌ 不计算准确率

**适配需求**:
- 需要添加工具名称验证逻辑
- 需要添加准确率计算
- 需要支持工具名称映射

### 3.2 `self_assess_agent.py`

**功能**:
- 13个固定case
- 验证工具名称和decision_mode
- 计算准确率

**优点**:
- ✅ 验证工具名称
- ✅ 计算准确率
- ✅ 支持bucket统计

**缺点**:
- ❌ 数据量太小（13条）
- ❌ 不支持外部数据集
- ❌ 固定case，不灵活

**适配需求**:
- 需要支持从CSV加载数据
- 需要支持工具名称映射

### 3.3 `run_smoke_tools.py`

**功能**:
- 8个工具冒烟测试
- 验证工具名称和状态

**优点**:
- ✅ 快速验证工具可用性
- ✅ 支持fallback_chain检查

**缺点**:
- ❌ 数据量太小（8条）
- ❌ 不支持外部数据集

**适配需求**:
- 可以保持现状，用于快速验证

---

## 四、推荐方案

### 4.1 创建新的评测脚本

**文件**: `scripts/run_full_eval.py`

**功能**:
1. 从CSV加载评测数据（支持800条）
2. 调用`/chat`接口
3. 验证工具名称（支持映射）
4. 验证expected_behavior
5. 计算准确率（总体+分类别）
6. 生成详细报告

**工具名称映射**:
```python
TOOL_NAME_MAPPING = {
    "search_nearby": "find_nearby",  # 数据集 → 实现
    "terminate_chat": "end_chat",    # 映射到decision_mode
}
```

**验证逻辑**:
```python
def validate_result(expected, actual):
    # 1. 工具名称验证（支持映射）
    expected_tool = TOOL_NAME_MAPPING.get(expected["tool"], expected["tool"])
    tool_match = actual["tool_name"] == expected_tool
    
    # 2. 行为验证
    if expected["behavior"] == "tool_call_then_*":
        behavior_match = actual["decision_mode"] == "tool_call"
    elif expected["behavior"] == "reject_*":
        behavior_match = actual["decision_mode"] == "reject"
    # ...
    
    return tool_match and behavior_match
```

### 4.2 修复工具名称不匹配

#### 方案A: 添加别名（推荐）

在`mcp_gateway.py`中添加：

```python
def invoke(self, tool_name: str, tool_args: dict[str, Any]) -> ToolResult:
    # 工具名称别名映射
    TOOL_ALIASES = {
        "search_nearby": "find_nearby",
    }
    tool_name = TOOL_ALIASES.get(tool_name, tool_name)
    
    if tool_name == "get_weather":
        # ...
```

#### 方案B: 实现terminate_chat

在`mcp_gateway.py`中添加：

```python
if tool_name == "terminate_chat":
    return ToolResult(
        ok=True,
        text="好的，再见！",
        raw={"action": "end_chat"}
    )
```

### 4.3 评测流程

```
1. 准备阶段
   ├─ 启动agent服务 (scripts/run_agent_server.sh)
   ├─ 验证服务可用 (scripts/run_smoke_tools.py)
   └─ 确认数据集路径

2. 执行评测
   ├─ 运行完整评测 (scripts/run_full_eval.py --limit 800)
   ├─ 记录每条query的结果
   └─ 实时显示进度

3. 生成报告
   ├─ 总体准确率
   ├─ 分类别准确率（闲聊/工具调用/拒识）
   ├─ 分工具准确率
   ├─ 延迟统计（avg/p95/p99）
   ├─ 失败case分析
   └─ 导出CSV和JSON报告

4. 问题分析
   ├─ 识别高频失败模式
   ├─ 分析工具调用失败原因
   └─ 生成改进建议
```

---

## 五、实施计划

### 5.1 立即执行（今天）

1. ✅ **创建评测框架分析文档**（本文档）
2. ⏳ **创建`run_full_eval.py`脚本**
   - 支持CSV加载
   - 支持工具名称映射
   - 支持准确率计算
3. ⏳ **添加工具名称别名**
   - `search_nearby` → `find_nearby`
4. ⏳ **运行小规模测试**
   - 使用50条数据验证脚本

### 5.2 后续执行（明天）

1. **运行完整评测**
   - 800条数据
   - 生成详细报告
2. **问题分析**
   - 识别失败模式
   - 生成改进建议
3. **优化迭代**
   - 修复高频问题
   - 重新评测验证

---

## 六、预期结果

### 6.1 评测指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 总体准确率 | ≥ 85% | 所有case的准确率 |
| 工具调用准确率 | ≥ 90% | 工具名称+参数正确 |
| 闲聊准确率 | ≥ 80% | 回复合理性 |
| 拒识准确率 | ≥ 95% | 安全性要求高 |
| 平均延迟 | ≤ 3s | 用户体验 |
| P95延迟 | ≤ 5s | 长尾性能 |

### 6.2 报告内容

```
评测报告
├─ 总体统计
│  ├─ 总数: 800
│  ├─ 通过: 680 (85%)
│  ├─ 失败: 120 (15%)
│  └─ 错误: 0 (0%)
│
├─ 分类别统计
│  ├─ 闲聊: 328/410 (80%)
│  ├─ 工具调用: 351/390 (90%)
│  └─ 拒识: 190/200 (95%)
│
├─ 分工具统计
│  ├─ get_weather: 54/60 (90%)
│  ├─ find_nearby: 52/58 (90%)
│  ├─ get_stock: 55/58 (95%)
│  ├─ plan_trip: 52/58 (90%)
│  ├─ get_news: 56/58 (97%)
│  └─ web_search: 55/58 (95%)
│
├─ 延迟统计
│  ├─ 平均: 2.5s
│  ├─ P95: 4.2s
│  └─ P99: 6.8s
│
└─ 失败分析
   ├─ 工具识别错误: 45 (37.5%)
   ├─ 参数提取错误: 30 (25%)
   ├─ 工具执行失败: 25 (20.8%)
   └─ 其他: 20 (16.7%)
```

---

## 七、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| 工具名称不匹配导致低准确率 | 高 | 高 | 添加别名映射 |
| 数据集标注不准确 | 中 | 中 | 人工抽查验证 |
| 评测时间过长（800条） | 中 | 低 | 支持并发调用 |
| API限流 | 低 | 中 | 添加重试机制 |

---

## 八、总结

### 8.1 当前状态

- ✅ 评测数据集完整（1000条）
- ✅ 基础评测脚本可用
- ⚠️ 工具名称匹配度71%（需要修复）
- ⚠️ 缺少完整评测脚本（需要创建）

### 8.2 下一步行动

1. **立即**: 创建`run_full_eval.py`脚本
2. **立即**: 添加工具名称别名
3. **今天**: 运行50条小规模测试
4. **明天**: 运行800条完整评测
5. **明天**: 分析结果并优化

### 8.3 预期时间

- 脚本开发: 2小时
- 小规模测试: 30分钟
- 完整评测: 1小时（800条 × 3s/条 ≈ 40分钟）
- 结果分析: 1小时
- **总计**: 4.5小时

---

**文档状态**: ✅ 完成  
**下一步**: 创建`run_full_eval.py`脚本

**最后更新**: 2026-03-09 by AI Assistant
