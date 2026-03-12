# 7B 模型优化实施清单

## 📋 实施步骤

### 第1阶段：结构化输出优化

- [ ] **1.1 更新 ToolCall 数据结构**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：将 `reasoning` 字段移到第一个
  ```python
  @dataclass
  class ToolCall:
      reasoning: str  # ← 第一个字段
      tool: ToolType
      params: Dict[str, Any]
  ```

- [ ] **1.2 更新 JSON 解析逻辑**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：确保 `reasoning` 被正确解析
  ```python
  def _parse_response(self, response: str) -> Optional[ToolCall]:
      data = json.loads(response)
      return ToolCall(
          reasoning=data.get("reasoning", ""),  # ← 第一个
          tool=ToolType(data["tool"]),
          params=data.get("params", {})
      )
  ```

- [ ] **1.3 更新 Prompt 中的返回格式说明**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：在 SYSTEM_PROMPT 中明确说明
  ```
  【返回格式】
  {
    "reasoning": "你的分析过程",
    "tool": "选择的工具名称",
    "params": {参数字典}
  }
  
  【重要】reasoning 字段必须放在第一个！
  ```

- [ ] **1.4 测试 JSON 解析**
  - 命令：`pytest tests/unit/test_7b_optimization.py -v`
  - 验证：reasoning 字段被正确解析

---

### 第2阶段：工具描述排他性设计

- [ ] **2.1 创建 ToolDefinition 数据结构**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：添加 `boundary_description` 字段
  ```python
  @dataclass
  class ToolDefinition:
      name: ToolType
      description: str
      boundary_description: str  # ← 何时不该用
      required_params: List[str]
      optional_params: List[str]
  ```

- [ ] **2.2 编写工具描述**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：为每个工具编写详细的边界描述
  - 检查清单：
    - [ ] plan_trip：明确与 find_nearby 的区别
    - [ ] find_nearby：明确与 plan_trip 的区别
    - [ ] web_search：明确何时是最后的 fallback
    - [ ] get_weather：明确与 web_search 的区别
    - [ ] get_news：明确与 web_search 的区别
    - [ ] get_stock：明确与 web_search 的区别
    - [ ] encyclopedia：明确与 web_search 的区别

- [ ] **2.3 创建 ToolRegistry**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：集中管理所有工具定义
  ```python
  class ToolRegistry:
      TOOLS = {
          ToolType.PLAN_TRIP: ToolDefinition(...),
          ToolType.FIND_NEARBY: ToolDefinition(...),
          # ...
      }
  ```

- [ ] **2.4 在 Prompt 中使用工具描述**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：动态生成工具描述部分
  ```python
  SYSTEM_PROMPT = """
  ...
  【支持的工具】
  {tool_descriptions}
  ...
  """
  
  system_prompt = SYSTEM_PROMPT.format(
      tool_descriptions=ToolRegistry.get_all_tool_descriptions()
  )
  ```

- [ ] **2.5 测试工具描述**
  - 命令：`pytest tests/unit/test_7b_optimization.py::test_tool_descriptions -v`
  - 验证：所有工具都有明确的边界描述

---

### 第3阶段：边缘场景 Few-Shot 提示

- [ ] **3.1 编写 Few-Shot 示例**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：编写 2-3 个代表性的易混淆示例
  - 示例清单：
    - [ ] 示例1：意图不明确（用户只说城市名）
    - [ ] 示例2：跨界查询（天气+穿搭）
    - [ ] 示例3：边界模糊（find_nearby vs web_search）

- [ ] **3.2 在 Prompt 中使用 Few-Shot**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：将 Few-Shot 示例嵌入 SYSTEM_PROMPT
  ```python
  SYSTEM_PROMPT = """
  ...
  【边缘场景示例】
  {few_shot_examples}
  ...
  """
  ```

- [ ] **3.3 测试 Few-Shot 效果**
  - 命令：`pytest tests/unit/test_7b_optimization.py::test_edge_cases -v`
  - 验证：边缘场景的准确率提升

---

### 第4阶段：参数提取减负

- [ ] **4.1 定义决定性参数**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：为每个工具定义 `required_params` 和 `optional_params`
  ```python
  ToolType.PLAN_TRIP: ToolDefinition(
      required_params=["destination", "days"],  # ← 路由阶段
      optional_params=["travel_mode", "preferences", ...]  # ← 执行阶段
  )
  ```

- [ ] **4.2 创建 ParameterExtractor**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：实现分阶段参数提取
  ```python
  class ParameterExtractor:
      @staticmethod
      def extract_routing_params(tool_type, query):
          # 第1阶段：只提取决定性参数
          pass
      
      @staticmethod
      def extract_execution_params(tool_type, query, routing_params):
          # 第2阶段：提取可选参数
          pass
  ```

- [ ] **4.3 更新路由器**
  - 文件：`agent_service/domain/intents/unified_router_7b_optimized.py`
  - 操作：在路由阶段只提取决定性参数
  ```python
  def route(self, query: str):
      # 只提取决定性参数
      tool_def = ToolRegistry.get_tool_definition(tool_type)
      required_params = tool_def.required_params
      # ...
  ```

- [ ] **4.4 创建执行器**
  - 文件：`agent_service/domain/tools/executor_v4_7b_optimized.py`
  - 操作：在执行阶段提取可选参数
  ```python
  class ToolExecutorV4:
      def execute(self, tool_call):
          # 第2阶段：提取可选参数
          execution_params = ParameterExtractor.extract_execution_params(...)
          # ...
  ```

- [ ] **4.5 测试参数提取**
  - 命令：`pytest tests/unit/test_7b_optimization.py::test_parameter_extraction -v`
  - 验证：参数提取准确率提升

---

## 🧪 测试和验证

### 单元测试

- [ ] **5.1 运行基础测试**
  ```bash
  pytest tests/unit/test_7b_optimization.py -v
  ```

- [ ] **5.2 运行集成测试**
  ```bash
  pytest tests/integration/test_7b_router.py -v
  ```

- [ ] **5.3 性能测试**
  ```bash
  pytest tests/performance/test_7b_latency.py -v
  ```

### 对比测试

- [ ] **5.4 准备测试数据集**
  - 文件：`tests/unit/test_7b_optimization.py`
  - 操作：准备 100 个测试用例（包括边缘场景）

- [ ] **5.5 运行对比测试**
  ```bash
  python tests/unit/test_7b_optimization.py
  ```

- [ ] **5.6 验证性能提升**
  - 工具选择准确率：75% → 92%（+17%）
  - 参数提取准确率：68% → 88%（+20%）
  - 边界判断准确率：60% → 85%（+25%）

---

## 📊 监控和指标

### 关键指标

- [ ] **6.1 设置监控**
  - 工具选择准确率
  - 参数提取准确率
  - 边界判断准确率
  - 平均延迟
  - 错误率

- [ ] **6.2 创建仪表板**
  - 文件：`docs/7b_optimization_metrics.md`
  - 操作：记录每日的性能指标

- [ ] **6.3 设置告警**
  - 准确率下降 > 5%
  - 延迟增加 > 50ms
  - 错误率上升 > 2%

---

## 🚀 灰度发布

### 第1阶段：内部测试（10%）

- [ ] **7.1 部署到测试环境**
  - 分支：`feature/7b-optimization`
  - 环境：`staging`

- [ ] **7.2 运行 1 周测试**
  - 监控指标
  - 收集反馈
  - 修复问题

### 第2阶段：小范围发布（25%）

- [ ] **7.3 发布到 25% 用户**
  - 环境：`production`
  - 用户：随机 25%
  - 监控：实时

- [ ] **7.4 运行 3 天**
  - 监控指标
  - 收集反馈
  - 修复问题

### 第3阶段：全量发布（100%）

- [ ] **7.5 发布到所有用户**
  - 环境：`production`
  - 用户：100%
  - 监控：持续

- [ ] **7.6 运行 1 周**
  - 监控指标
  - 收集反馈
  - 优化调整

---

## 📝 文档和培训

- [ ] **8.1 编写技术文档**
  - 文件：`7B_MODEL_OPTIMIZATION_GUIDE.md`
  - 内容：4 个优化动作的详细说明

- [ ] **8.2 编写实施指南**
  - 文件：`7B_OPTIMIZATION_IMPLEMENTATION_CHECKLIST.md`
  - 内容：逐步实施步骤

- [ ] **8.3 编写 API 文档**
  - 文件：`docs/unified_router_v3_api.md`
  - 内容：新路由器的 API 说明

- [ ] **8.4 进行团队培训**
  - 时间：1 小时
  - 内容：4 个优化动作的原理和效果

---

## ✅ 完成检查

- [ ] 所有代码已实现
- [ ] 所有测试已通过
- [ ] 性能指标已达到预期
- [ ] 文档已完成
- [ ] 团队已培训
- [ ] 灰度发布已完成
- [ ] 监控已设置

---

## 📈 预期收益

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 工具选择准确率 | 75% | 92% | +17% |
| 参数提取准确率 | 68% | 88% | +20% |
| 边界判断准确率 | 60% | 85% | +25% |
| 总体成功率 | 75% | 92% | +17% |
| 平均延迟 | 400ms | 380ms | -5% |
| 用户满意度 | 基准 | +15% | +15% |

---

## 🎯 关键里程碑

- **第1周**：完成第1-2阶段（结构化输出 + 工具描述）
- **第2周**：完成第3-4阶段（Few-Shot + 参数减负）
- **第3周**：完成测试和验证
- **第4周**：灰度发布和监控

---

## 📞 联系方式

- 技术负责人：[name]
- 产品负责人：[name]
- 运维负责人：[name]

---

## 附录

### A. 工具描述模板

```
【工具名】
用于[功能描述]。
必须包含[必需参数]。
系统会[系统行为]。

何时不该用：
- [反向示例1] → 使用[其他工具]
- [反向示例2] → 使用[其他工具]
只有当用户[明确信号]时，才使用本工具。
```

### B. Few-Shot 示例模板

```
【示例N】[场景描述]
用户说："[用户查询]"
分析：[分析过程]
正确做法：
{
  "reasoning": "[推理过程]",
  "tool": "[工具名]",
  "params": {[参数]}
}
```

### C. 测试用例模板

```python
TestCase(
    query="[用户查询]",
    expected_tool="[期望工具]",
    expected_params={[期望参数]},
    category="[类别]"  # normal, edge_case, boundary
)
```
