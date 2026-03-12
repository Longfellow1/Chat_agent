# 4B Router 真实测试指南

## 问题

之前的文档中声称 4B Router 性能指标（延迟 350ms，准确率 85%），但这些都是**理论值**，没有真实的 4B 模型测试数据支撑。

## 解决方案

现在提供了真实的 4B 模型测试框架，包含 30 个意图评测数据（10 个难例）。

## 前置条件

### 1. 安装 4B 模型

**选项 A：使用 LM Studio（推荐）**

```bash
# 下载 LM Studio
# https://lmstudio.ai/

# 启动 LM Studio 服务
# 1. 打开 LM Studio
# 2. 选择模型：Qwen3-4B-2507
# 3. 点击 "Start Server"
# 4. 服务会在 http://localhost:1234/v1 启动
```

**选项 B：使用 vLLM**

```bash
# 安装 vLLM
pip install vllm

# 启动 vLLM 服务
vllm serve Qwen/Qwen3-4B-2507 \
  --api-key token-abc123 \
  --port 8000
```

**选项 C：使用 Ollama**

```bash
# 安装 Ollama
# https://ollama.ai/

# 拉取模型
ollama pull qwen3-4b-2507

# 启动服务
ollama serve
```

### 2. 验证连接

```bash
# 测试 LM Studio 连接
curl http://localhost:1234/v1/models

# 应该返回类似：
# {
#   "object": "list",
#   "data": [
#     {
#       "id": "qwen3-4b-2507",
#       "object": "model",
#       ...
#     }
#   ]
# }
```

## 运行测试

### 方式 1：使用独立脚本（推荐）

```bash
# 基础用法（使用默认配置）
python scripts/test_4b_router_intent.py

# 自定义端点和模型
python scripts/test_4b_router_intent.py \
  --endpoint http://localhost:1234/v1 \
  --model qwen3-4b-2507

# 使用 vLLM
python scripts/test_4b_router_intent.py \
  --endpoint http://localhost:8000/v1 \
  --model qwen3-4b-2507
```

### 方式 2：使用 pytest

```bash
# 运行完整测试
pytest tests/integration/test_router_4b_intent_evaluation.py -v -s

# 只运行简单查询测试
pytest tests/integration/test_router_4b_intent_evaluation.py::TestRouter4BIntentEvaluation::test_simple_queries -v -s

# 只运行难例测试
pytest tests/integration/test_router_4b_intent_evaluation.py::TestRouter4BIntentEvaluation::test_hard_queries -v -s
```

## 评测数据集

### 设计原则

**专注于 LLM 意图识别能力**：
- 移除规则能处理的简单查询（如"我想去北京3天"）
- 专注于需要 LLM 理解和推理的复杂场景
- 测试 4B 模型在参数缺失、意图模糊、复杂语义下的表现

### 参数缺失/不完整（10 个）

测试 LLM 能否识别意图，即使关键参数缺失：

```
1:  "我想去北京" → plan_trip（缺少时间参数）
2:  "北京附近" → find_nearby（缺少类别参数）
3:  "天气" → get_weather（缺少位置参数）
4:  "我想去旅游" → plan_trip（缺少目的地和时间）
5:  "附近有什么" → find_nearby（缺少位置和类别）
6:  "帮我查一下" → web_search（缺少查询内容）
7:  "我想吃饭" → find_nearby（缺少位置，类别隐含为餐厅）
8:  "明天" → get_weather（缺少位置，隐含查天气）
9:  "股票" → get_stock（缺少股票代码）
10: "新闻" → get_news（缺少新闻主题）
```

**预期准确率**：70-80%（需要 LLM 理解隐含意图）

### 意图模糊/多义（10 个）

测试 LLM 在意图不明确时的判断能力：

```
11: "我想去一个有山有水的地方" → plan_trip（描述性目的地）
12: "帮我规划一下" → web_search（极度模糊）
13: "北京或上海，3天" → plan_trip（多个目的地）
14: "我想去旅游，但不知道去哪" → plan_trip（意图清晰但缺少关键信息）
15: "查询一下" → web_search（极度模糊）
16: "我想找个地方" → find_nearby（意图不明确）
17: "今天怎么样" → get_weather（可能是天气或其他）
18: "最近的" → find_nearby（缺少主语和位置）
19: "给我推荐一下" → web_search（缺少推荐内容）
20: "我想了解" → web_search（缺少了解内容）
```

**预期准确率**：60-70%（高度模糊，需要澄清）

### 复杂语义/隐含意图（10 个）

测试 LLM 理解复杂语义和隐含意图的能力：

```
21: "我想吃饭，但不知道在哪" → find_nearby（隐含类别：餐厅）
22: "周末想出去玩" → plan_trip（隐含时间：周末）
23: "有什么好玩的地方吗" → find_nearby（隐含类别：景点）
24: "我想休息一下" → find_nearby（可能是酒店或咖啡厅）
25: "明天要不要带伞" → get_weather（隐含查天气）
26: "最近有什么大事" → get_news（隐含查新闻）
27: "科技公司的表现" → get_stock（可能是股票或新闻）
28: "我想学点东西" → web_search（隐含搜索学习资源）
29: "有什么好看的" → web_search（可能是电影、书籍等）
30: "帮我安排一下行程" → plan_trip（缺少所有关键参数）
```

**预期准确率**：65-75%（需要理解隐含意图）

## 预期结果

### 理论值 vs 实际值

| 指标 | 理论值 | 实际值（待测） |
|------|--------|---|
| 参数缺失准确率 | 70-80% | ? |
| 意图模糊准确率 | 60-70% | ? |
| 复杂语义准确率 | 65-75% | ? |
| 总体准确率 | 65-75% | ? |
| 平均延迟 | 350ms | ? |
| P50 延迟 | 350ms | ? |
| P95 延迟 | 500ms | ? |
| 澄清率 | 30-40% | ? |

## 输出结果

测试完成后，结果会保存到：

```
eval/reports/router_4b_intent_eval_YYYYMMDD_HHMMSS.json
```

### 结果格式

```json
{
  "timestamp": "2026-03-10T21:00:00",
  "model": "qwen3-4b-2507",
  "endpoint": "http://localhost:1234/v1",
  "total": 30,
  "correct": 25,
  "incorrect": 5,
  "latencies": [120, 150, 180, ...],
  "confidences": [0.85, 0.92, 0.78, ...],
  "by_category": {
    "simple": {
      "correct": 10,
      "total": 10,
      "latencies": [...]
    },
    "medium": {
      "correct": 8,
      "total": 10,
      "latencies": [...]
    },
    "hard": {
      "correct": 7,
      "total": 10,
      "latencies": [...]
    }
  },
  "details": [
    {
      "id": "s1",
      "query": "我想去北京3天",
      "expected": "plan_trip",
      "got": "plan_trip",
      "correct": true,
      "confidence": 0.92,
      "latency_ms": 120,
      "source": "rule"
    },
    ...
  ]
}
```

## 分析结果

### 1. 检查准确率

```bash
# 查看总体准确率
cat eval/reports/router_4b_intent_eval_*.json | jq '.correct / .total'

# 查看按类别的准确率
cat eval/reports/router_4b_intent_eval_*.json | jq '.by_category'
```

### 2. 检查延迟

```bash
# 计算平均延迟
cat eval/reports/router_4b_intent_eval_*.json | jq 'add(.latencies) / (.latencies | length)'

# 计算 P95 延迟
cat eval/reports/router_4b_intent_eval_*.json | jq '.latencies | sort | .[length * 0.95 | floor]'
```

### 3. 分析失败案例

```bash
# 查看所有失败的案例
cat eval/reports/router_4b_intent_eval_*.json | jq '.details[] | select(.correct == false)'
```

## 常见问题

### Q1: 连接失败怎么办？

**A:** 检查以下几点：

1. LM Studio 是否启动？
   ```bash
   curl http://localhost:1234/v1/models
   ```

2. 模型是否已加载？
   - 在 LM Studio 中检查模型列表

3. 防火墙是否阻止了连接？
   ```bash
   telnet localhost 1234
   ```

### Q2: 测试很慢怎么办？

**A:** 这是正常的。4B 模型在 CPU 上运行会很慢。

- 使用 GPU 加速（如果可用）
- 减少测试数据量
- 增加 timeout

### Q3: 准确率低于预期怎么办？

**A:** 可能的原因：

1. 提示词需要优化
2. 模型版本不同
3. 温度设置不同
4. 规则覆盖不足

**解决方案**：

1. 检查提示词（`router_4b_with_logprobs.py` 中的 `SYSTEM_PROMPT`）
2. 尝试调整温度（0.1-0.3）
3. 添加更多规则
4. 增加 few-shot 示例

### Q4: 如何改进准确率？

**A:** 几个方向：

1. **优化提示词**
   - 添加更多示例
   - 简化指令
   - 明确约束

2. **改进规则**
   - 添加更多关键词
   - 改进参数提取逻辑
   - 处理边界情况

3. **调整置信度阈值**
   - 降低阈值以减少澄清
   - 提高阈值以提高准确率

4. **模型微调**
   - 使用 LoRA 微调
   - 特定领域优化

## 下一步

1. **运行测试**
   ```bash
   python scripts/test_4b_router_intent.py
   ```

2. **分析结果**
   - 检查准确率是否达到预期
   - 分析失败案例
   - 识别改进方向

3. **优化提示词**
   - 根据失败案例调整
   - 添加新的规则
   - 测试新的提示词

4. **迭代改进**
   - 重复测试
   - 持续优化
   - 监控性能指标

## 参考资源

- [LM Studio 文档](https://lmstudio.ai/)
- [vLLM 文档](https://docs.vllm.ai/)
- [Qwen3-4B 模型卡](https://huggingface.co/Qwen/Qwen3-4B-2507)
- [Router 4B 实现](../agent_service/domain/intents/router_4b_with_logprobs.py)

---

**重要**：这是真实的 4B 模型测试框架。请实际运行测试，而不是依赖理论值。
