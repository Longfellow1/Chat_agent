# 测试脚本标准规范

**制定日期**: 2026-03-05  
**适用范围**: 所有集成测试和端到端测试脚本

---

## 一、核心要求

所有测试脚本必须做到以下三点：

### 1. 记录问答对原始内容

**要求**: 完整记录每个测试用例的输入和输出

**格式**:
```json
{
  "query_id": 1,
  "query": "用户查询内容",
  "timestamp": "2026-03-05 14:30:00",
  "response": {
    "tool_name": "web_search",
    "tool_args": {"query": "处理后的查询"},
    "tool_result": {
      "ok": true,
      "text": "工具返回的文本",
      "raw": {...}
    }
  },
  "llm_response": "LLM 最终生成的回答（如果有）"
}
```

**存储位置**: `tests/integration/data/{test_name}_raw_data.json`

### 2. 记录过程分数

**要求**: 记录每个评估维度的分数和判断依据

**格式**:
```json
{
  "query_id": 1,
  "query": "用户查询内容",
  "scores": {
    "relevance": {
      "score": 0.8,
      "reason": "Top 3 结果中有 2 条相关",
      "details": {
        "result_1": {"relevant": true, "reason": "标题匹配"},
        "result_2": {"relevant": true, "reason": "内容匹配"},
        "result_3": {"relevant": false, "reason": "不相关"}
      }
    },
    "satisfaction": {
      "score": 1.0,
      "reason": "结果能回答问题，格式清晰"
    },
    "technical_validity": {
      "score": 1.0,
      "reason": "工具返回非空结果"
    }
  },
  "final_judgment": "pass"
}
```

**存储位置**: `tests/integration/data/{test_name}_scores.json`

### 3. 产出结果报告

**要求**: 生成 Markdown 格式的可读报告，包含：
- 测试概览（总数、通过率、失败率）
- 分维度统计（相关性、满意度、技术有效率等）
- 失败案例详细分析
- 改进建议

**格式**: 见下方模板

**存储位置**: `tests/integration/{test_name}_report.md`

---

## 二、报告模板

```markdown
# {测试名称} 测试报告

**测试日期**: YYYY-MM-DD  
**测试人**: [自动化/人工]  
**测试集**: N 条查询

---

## 一、测试概览

| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 总查询数 | N | - | - |
| 通过数 | X | - | - |
| 失败数 | Y | - | - |
| 通过率 | Z% | ≥ 85% | ✅/❌ |

---

## 二、分维度统计

### 2.1 相关性有效率

| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 相关查询数 | X/N | ≥ 26/30 (85%) | ✅/❌ |
| 相关性有效率 | X% | ≥ 85% | ✅/❌ |

### 2.2 用户满意度

| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 满意查询数 | X/N | ≥ 23/30 (75%) | ✅/❌ |
| 用户满意度 | X% | ≥ 75% | ✅/❌ |

### 2.3 技术有效率

| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 有效查询数 | X/N | ≥ 27/30 (90%) | ✅/❌ |
| 技术有效率 | X% | ≥ 90% | ✅/❌ |

---

## 三、失败案例分析

### 案例1: {查询内容}

**问题**: {问题描述}

**原始数据**:
- Query: {查询}
- Response: {响应}

**分数**:
- 相关性: {分数} - {原因}
- 满意度: {分数} - {原因}

**改进建议**: {建议}

---

## 四、改进建议

1. {建议1}
2. {建议2}
3. {建议3}

---

## 五、原始数据

完整原始数据见: `tests/integration/data/{test_name}_raw_data.json`  
完整评分数据见: `tests/integration/data/{test_name}_scores.json`

---

**生成时间**: YYYY-MM-DD HH:MM:SS  
**测试脚本**: `tests/integration/{test_name}.py`
```

---

## 三、代码模板

### 3.1 测试脚本结构

```python
"""
{测试名称}

目标：{测试目标}
验收标准：{验收标准}
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env.agent')

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

RAW_DATA_FILE = DATA_DIR / "{test_name}_raw_data.json"
SCORES_FILE = DATA_DIR / "{test_name}_scores.json"
REPORT_FILE = Path(__file__).parent / "{test_name}_report.md"


class TestRecorder:
    """测试记录器：记录原始数据和评分"""
    
    def __init__(self):
        self.raw_data = []
        self.scores = []
    
    def record_query(self, query_id, query, response, llm_response=None):
        """记录问答对原始内容"""
        self.raw_data.append({
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "response": response,
            "llm_response": llm_response,
        })
    
    def record_score(self, query_id, query, scores, final_judgment):
        """记录过程分数"""
        self.scores.append({
            "query_id": query_id,
            "query": query,
            "scores": scores,
            "final_judgment": final_judgment,
        })
    
    def save(self):
        """保存数据到文件"""
        with open(RAW_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, ensure_ascii=False, indent=2)
        
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)


class ReportGenerator:
    """报告生成器：生成 Markdown 报告"""
    
    def __init__(self, raw_data, scores):
        self.raw_data = raw_data
        self.scores = scores
    
    def generate(self):
        """生成报告"""
        report = []
        
        # 标题
        report.append(f"# {{测试名称}} 测试报告\n")
        report.append(f"**测试日期**: {datetime.now().strftime('%Y-%m-%d')}\n")
        report.append(f"**测试集**: {len(self.scores)} 条查询\n")
        report.append("\n---\n\n")
        
        # 测试概览
        report.append("## 一、测试概览\n\n")
        report.append(self._generate_overview())
        report.append("\n---\n\n")
        
        # 分维度统计
        report.append("## 二、分维度统计\n\n")
        report.append(self._generate_dimension_stats())
        report.append("\n---\n\n")
        
        # 失败案例分析
        report.append("## 三、失败案例分析\n\n")
        report.append(self._generate_failure_analysis())
        report.append("\n---\n\n")
        
        # 改进建议
        report.append("## 四、改进建议\n\n")
        report.append(self._generate_suggestions())
        report.append("\n---\n\n")
        
        # 原始数据链接
        report.append("## 五、原始数据\n\n")
        report.append(f"完整原始数据见: `{RAW_DATA_FILE.relative_to(Path.cwd())}`\n")
        report.append(f"完整评分数据见: `{SCORES_FILE.relative_to(Path.cwd())}`\n")
        
        return "".join(report)
    
    def _generate_overview(self):
        """生成概览"""
        total = len(self.scores)
        passed = sum(1 for s in self.scores if s['final_judgment'] == 'pass')
        failed = total - passed
        pass_rate = passed / total * 100 if total > 0 else 0
        
        return f"""| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 总查询数 | {total} | - | - |
| 通过数 | {passed} | - | - |
| 失败数 | {failed} | - | - |
| 通过率 | {pass_rate:.1f}% | ≥ 85% | {'✅' if pass_rate >= 85 else '❌'} |
"""
    
    def _generate_dimension_stats(self):
        """生成分维度统计"""
        # 实现具体的统计逻辑
        return "（根据具体测试维度实现）\n"
    
    def _generate_failure_analysis(self):
        """生成失败案例分析"""
        failures = [s for s in self.scores if s['final_judgment'] == 'fail']
        
        if not failures:
            return "无失败案例\n"
        
        analysis = []
        for i, failure in enumerate(failures, 1):
            analysis.append(f"### 案例{i}: {failure['query']}\n\n")
            analysis.append(f"**问题**: {failure['scores'].get('reason', 'N/A')}\n\n")
            analysis.append("**分数**:\n")
            for dim, score_data in failure['scores'].items():
                if isinstance(score_data, dict):
                    analysis.append(f"- {dim}: {score_data.get('score', 'N/A')} - {score_data.get('reason', 'N/A')}\n")
            analysis.append("\n")
        
        return "".join(analysis)
    
    def _generate_suggestions(self):
        """生成改进建议"""
        return "（根据失败案例分析生成）\n"
    
    def save(self):
        """保存报告到文件"""
        report = self.generate()
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n报告已生成: {REPORT_FILE}")


def main():
    """主函数"""
    recorder = TestRecorder()
    
    # 执行测试
    for i, test_case in enumerate(TEST_CASES, 1):
        query = test_case['query']
        
        # 1. 执行查询
        response = execute_query(query)
        
        # 2. 记录原始数据
        recorder.record_query(i, query, response)
        
        # 3. 评分
        scores = evaluate(query, response)
        final_judgment = "pass" if all_pass(scores) else "fail"
        
        # 4. 记录分数
        recorder.record_score(i, query, scores, final_judgment)
    
    # 5. 保存数据
    recorder.save()
    
    # 6. 生成报告
    generator = ReportGenerator(recorder.raw_data, recorder.scores)
    generator.save()
    
    print("\n测试完成！请查看报告进行人工复核。")


if __name__ == "__main__":
    main()
```

---

## 四、人工复核流程

### 4.1 复核内容

1. **查看报告**: 阅读 `{test_name}_report.md`
2. **检查失败案例**: 重点关注失败案例分析
3. **抽查原始数据**: 从 `{test_name}_raw_data.json` 中抽查 5-10 条
4. **验证评分**: 检查 `{test_name}_scores.json` 中的评分是否合理

### 4.2 复核标准

- 评分是否客观公正
- 失败案例分析是否准确
- 改进建议是否可行
- 原始数据是否完整

### 4.3 复核结果

在报告末尾添加复核意见：

```markdown
---

## 人工复核

**复核人**: [姓名]  
**复核日期**: YYYY-MM-DD  
**复核结果**: ✅ 通过 / ❌ 需要修正

**复核意见**:
1. {意见1}
2. {意见2}
```

---

## 五、检查清单

在提交测试脚本前，确保：

- [ ] 记录了所有问答对原始内容（JSON 格式）
- [ ] 记录了所有过程分数（JSON 格式）
- [ ] 生成了 Markdown 格式的报告
- [ ] 报告包含测试概览、分维度统计、失败案例分析、改进建议
- [ ] 原始数据和评分数据可追溯
- [ ] 报告末尾提示人工复核

---

**制定人**: Tech Lead  
**生效日期**: 2026-03-05  
**适用范围**: 所有集成测试和端到端测试

