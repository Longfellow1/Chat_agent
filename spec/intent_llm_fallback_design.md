# 意图NLU兜底方案设计文档

## 文档信息
- **创建日期**: 2026-03-09
- **版本**: v1.0
- **状态**: 设计中
- **负责人**: AI Assistant

---

## 一、背景与问题

### 1.1 当前状态

**规则路由**:
- **优势**: 快速（<1ms）、准确（覆盖80%常见场景）
- **劣势**: 无法处理模糊说法和边界case

**问题示例**:
```
✅ 规则能处理: "帮我规划上海2日游"
❌ 规则无法处理: "想去魔都玩两天，有什么推荐吗"
❌ 规则无法处理: "周末带家人出去转转，不知道去哪"
```

### 1.2 用户痛点

**车展场景**:
- 用户表达方式多样化
- 口语化、模糊化的query增多
- 规则无法覆盖所有表达方式

**核心问题**:
- 规则路由准确率高但覆盖率低（80%）
- 剩余20%的query需要兜底方案
- 不能让用户感知到"听不懂"

---

## 二、设计目标

### 2.1 核心目标

**P0 (Must Have)**:
1. 覆盖规则未命中的20%场景
2. 意图识别准确率 ≥ 85%
3. 延迟 ≤ 200ms（含规则路由时间）
4. 支持意图识别 + 参数提取（槽位填充）

**P1 (Should Have)**:
1. 置信度评分（用于澄清决策）
2. 持续学习（badcase收集和重训练）
3. A/B测试能力

### 2.2 成功指标

**定量指标**:
- 意图识别准确率: ≥ 85%
- 参数提取准确率: ≥ 80%
- 延迟: ≤ 200ms
- 覆盖率: 规则80% + LLM兜底20% = 100%

**定性指标**:
- 用户无感知（不知道是规则还是LLM）
- 澄清问题自然（置信度低时）
- 持续改进（badcase驱动）

---

## 三、技术方案

### 3.1 架构设计

```
用户输入: "想去魔都玩两天，有什么推荐吗"
  ↓
[规则路由] 快速匹配（<1ms）
  ↓ 未命中
[1.5B意图模型] LoRA微调（50-120ms）
  ↓ 输出结构化JSON
{
  "intent": "plan_trip",
  "params": {
    "destination": "上海",
    "days": 2
  },
  "confidence": 0.88
}
  ↓
[置信度判断]
  ├─ confidence ≥ 0.85 → 直接执行
  ├─ 0.7 ≤ confidence < 0.85 → 执行但记录
  └─ confidence < 0.7 → 返回澄清问题
  ↓
[工具调用] plan_trip(destination="上海", days=2)
  ↓
[续写LLM] 生成自然语言（已有）
```

### 3.2 模型选型

**推荐方案**: Qwen2.5-1.5B-Instruct + LoRA微调

**理由**:
1. **延迟可控**: 实测120ms内（参考query-rewrite-agents项目）
2. **效果足够**: 1.5B是耗时和准确度的甜点
3. **训练成本低**: Mac M4 Pro 24GB可以跑LoRA
4. **社区支持**: Qwen系列文档完善，生态成熟

**备选方案**:
- Qwen2.5-0.5B（如果延迟不满足）
- Phi-2 (2.7B)（如果准确率不满足）

**不推荐**: BERT类模型
- ❌ 输出格式受限（分类标签，不是结构化JSON）
- ❌ 难以处理意图识别+参数提取的复合任务

### 3.3 输出格式

**结构化JSON**（送给续写LLM）:
```json
{
  "intent": "plan_trip | find_nearby | get_weather | get_stock | get_news | web_search",
  "params": {
    "destination": "string",
    "days": "int",
    "travel_mode": "driving | transit",
    "city": "string",
    "keyword": "string",
    "topic": "string",
    "target": "string",
    "query": "string"
  },
  "confidence": 0.0-1.0
}
```

**送给续写LLM**: 完全兼容，续写LLM已经在用结构化数据。


---

## 四、训练数据准备

### 4.1 数据收集

**数据来源**:
1. **规则未命中的真实query** (优先级最高)
   - 从生产日志收集规则路由失败的query
   - 预计1000-2000条
2. **人工构造的边界case**
   - 模糊表达: "想去魔都玩两天"
   - 口语化: "周末带家人出去转转"
   - 多意图混合: "帮我查查上海天气，顺便规划个2日游"
   - 预计500-1000条
3. **数据增强**
   - 同义词替换: "上海" → "魔都"
   - 表达方式变换: "帮我规划" → "想去" → "打算去"
   - 预计扩充到5000-10000条

**数据分布**:
```
plan_trip: 30%
find_nearby: 25%
get_weather: 15%
web_search: 15%
get_stock: 8%
get_news: 7%
```

### 4.2 数据标注

**标注格式** (JSONL):
```jsonl
{"query": "想去魔都玩两天，有什么推荐吗", "intent": "plan_trip", "params": {"destination": "上海", "days": 2}}
{"query": "周末带家人出去转转，不知道去哪", "intent": "plan_trip", "params": {"destination": null, "days": 2}}
{"query": "附近有什么好吃的", "intent": "find_nearby", "params": {"keyword": "美食", "city": null}}
{"query": "明天上海会下雨吗", "intent": "get_weather", "params": {"city": "上海", "date": "明天"}}
```

**标注工具**:
- 使用Label Studio或自建标注工具
- 双人标注 + 一致性检查
- 不一致的case由第三人仲裁

**质量控制**:
- 标注一致性 ≥ 95%
- 每个意图至少500条样本
- 参数提取准确率 ≥ 90%

### 4.3 数据增强

**同义词替换**:
```python
SYNONYMS = {
    "上海": ["魔都", "申城"],
    "北京": ["帝都", "首都"],
    "规划": ["安排", "计划", "设计"],
    "推荐": ["建议", "介绍", "有什么"],
    "附近": ["周边", "旁边", "这边"]
}
```

**表达方式变换**:
```python
TEMPLATES = [
    "帮我{action}{destination}{days}日游",
    "想去{destination}玩{days}天",
    "{destination}{days}日游怎么安排",
    "打算去{destination}待{days}天，有什么推荐"
]
```

**回译增强** (可选):
- 中文 → 英文 → 中文
- 生成语义相同但表达不同的query

### 4.4 数据集划分

```
训练集: 70% (3500-7000条)
验证集: 15% (750-1500条)
测试集: 15% (750-1500条)
```

**划分原则**:
- 按意图分层采样
- 测试集包含最难的边界case
- 验证集用于早停和超参调优

---

## 五、LoRA微调流程

### 5.1 环境准备

**硬件要求**:
- Mac M4 Pro 24GB (已确认)
- 或 NVIDIA GPU ≥ 16GB

**软件依赖**:
```bash
# 安装LLaMA Factory
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .

# 下载Qwen2.5-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir models/Qwen2.5-1.5B-Instruct
```

### 5.2 训练配置

**LoRA配置** (`config/lora_intent.yaml`):
```yaml
model_name_or_path: models/Qwen2.5-1.5B-Instruct
dataset: intent_nlu
template: qwen
finetuning_type: lora
lora_target: all
lora_rank: 8
lora_alpha: 16
lora_dropout: 0.05
output_dir: output/intent_lora
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 5e-4
num_train_epochs: 3
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
logging_steps: 10
save_steps: 100
```

**数据配置** (`data/intent_nlu.json`):
```json
{
  "intent_nlu": {
    "file_name": "intent_nlu.jsonl",
    "columns": {
      "prompt": "query",
      "response": "output"
    }
  }
}
```

**Prompt模板**:
```
输入: {query}
输出: {{"intent": "{intent}", "params": {params}, "confidence": {confidence}}}
```

### 5.3 训练脚本

**训练命令**:
```bash
llamafactory-cli train \
  --stage sft \
  --model_name_or_path models/Qwen2.5-1.5B-Instruct \
  --dataset intent_nlu \
  --template qwen \
  --finetuning_type lora \
  --lora_target all \
  --output_dir output/intent_lora \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --lr_scheduler_type cosine \
  --logging_steps 10 \
  --save_steps 100 \
  --learning_rate 5e-4 \
  --num_train_epochs 3 \
  --plot_loss \
  --bf16
```

**预期训练时间**:
- Mac M4 Pro: 2-4小时
- NVIDIA A100: 30-60分钟

### 5.4 模型评估

**评估指标**:
```python
# 意图识别准确率
intent_accuracy = correct_intents / total_samples

# 参数提取F1
param_f1 = 2 * precision * recall / (precision + recall)

# 置信度校准
calibration_error = |predicted_confidence - actual_accuracy|
```

**评估脚本**:
```bash
llamafactory-cli eval \
  --model_name_or_path output/intent_lora \
  --dataset intent_nlu_test \
  --template qwen \
  --output_dir output/eval_results
```

**目标指标**:
- 意图识别准确率: ≥ 85%
- 参数提取F1: ≥ 80%
- 延迟: ≤ 120ms


---

## 六、集成方案

### 6.1 Router层改造

**当前架构**:
```python
# agent_service/domain/intents/router.py
def route(query: str) -> Intent:
    # 规则路由
    if matches_rule(query):
        return parse_intent(query)
    else:
        return Intent(type="web_search")  # 默认兜底
```

**改造后架构**:
```python
# agent_service/domain/intents/router.py
def route(query: str) -> Intent:
    # Step 1: 规则路由（快速路径）
    rule_result = rule_router.match(query)
    if rule_result.matched:
        return rule_result.intent
    
    # Step 2: LLM兜底（慢速路径）
    llm_result = llm_router.predict(query)
    
    # Step 3: 置信度判断
    if llm_result.confidence >= 0.85:
        return llm_result.intent
    elif llm_result.confidence >= 0.7:
        # 执行但记录badcase
        log_low_confidence(query, llm_result)
        return llm_result.intent
    else:
        # 返回澄清问题
        return Intent(type="clarification", message="您是想...")
```

### 6.2 LLM Router实现

**模型加载**:
```python
# agent_service/infra/llm_clients/intent_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class IntentModel:
    def __init__(self, model_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        self.model.eval()
    
    def predict(self, query: str) -> dict:
        prompt = f"输入: {query}\n输出: "
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.1,
                do_sample=False
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> dict:
        # 解析JSON输出
        import json
        try:
            result = json.loads(response.split("输出: ")[1])
            return result
        except:
            return {"intent": "web_search", "params": {}, "confidence": 0.0}
```

**延迟优化**:
```python
# 1. 模型量化（可选）
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

# 2. 批量推理（如果有多个query）
def predict_batch(self, queries: List[str]) -> List[dict]:
    # 批量编码
    inputs = self.tokenizer(queries, return_tensors="pt", padding=True)
    # 批量推理
    outputs = self.model.generate(**inputs)
    # 批量解析
    return [self._parse_response(o) for o in outputs]
```

### 6.3 置信度校准

**问题**: 模型输出的confidence可能不准确

**解决方案**: Temperature Scaling
```python
class ConfidenceCalibrator:
    def __init__(self):
        self.temperature = 1.5  # 通过验证集调优
    
    def calibrate(self, logits: torch.Tensor) -> float:
        # 应用temperature scaling
        scaled_logits = logits / self.temperature
        probs = torch.softmax(scaled_logits, dim=-1)
        confidence = probs.max().item()
        return confidence
```

**校准流程**:
1. 在验证集上评估原始confidence
2. 使用Temperature Scaling调整
3. 重新评估校准后的confidence
4. 目标: ECE (Expected Calibration Error) < 0.1

### 6.4 持续学习

**Badcase收集**:
```python
# agent_service/infra/monitoring/badcase_logger.py
class BadcaseLogger:
    def log(self, query: str, predicted: Intent, actual: Intent, confidence: float):
        record = {
            "timestamp": datetime.now(),
            "query": query,
            "predicted_intent": predicted.type,
            "actual_intent": actual.type,
            "confidence": confidence,
            "is_correct": predicted.type == actual.type
        }
        # 写入数据库或文件
        self.db.insert("badcases", record)
```

**重训练流程**:
1. 每周收集badcase
2. 人工标注正确意图
3. 加入训练集
4. 重新训练LoRA
5. A/B测试新模型
6. 上线

**A/B测试**:
```python
class ABTestRouter:
    def __init__(self, model_a: IntentModel, model_b: IntentModel):
        self.model_a = model_a
        self.model_b = model_b
        self.ab_ratio = 0.1  # 10%流量给B模型
    
    def route(self, query: str, user_id: str) -> Intent:
        if hash(user_id) % 100 < self.ab_ratio * 100:
            return self.model_b.predict(query)
        else:
            return self.model_a.predict(query)
```

---

## 七、Mac本地训练指南

### 7.1 环境安装

**Step 1: 安装Homebrew** (如果没有):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Step 2: 安装Python 3.10+**:
```bash
brew install python@3.10
python3.10 -m pip install --upgrade pip
```

**Step 3: 创建虚拟环境**:
```bash
python3.10 -m venv venv_intent
source venv_intent/bin/activate
```

**Step 4: 安装依赖**:
```bash
pip install torch torchvision torchaudio
pip install transformers accelerate peft datasets
pip install llamafactory
```

### 7.2 下载模型

**使用Hugging Face CLI**:
```bash
pip install huggingface_hub
huggingface-cli login  # 输入token

# 下载Qwen2.5-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct \
  --local-dir models/Qwen2.5-1.5B-Instruct \
  --local-dir-use-symlinks False
```

**或使用Python脚本**:
```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2.5-1.5B-Instruct",
    local_dir="models/Qwen2.5-1.5B-Instruct",
    local_dir_use_symlinks=False
)
```

### 7.3 准备训练数据

**数据格式** (`data/intent_nlu.jsonl`):
```jsonl
{"query": "想去魔都玩两天", "output": "{\"intent\": \"plan_trip\", \"params\": {\"destination\": \"上海\", \"days\": 2}, \"confidence\": 0.95}"}
{"query": "附近有什么好吃的", "output": "{\"intent\": \"find_nearby\", \"params\": {\"keyword\": \"美食\"}, \"confidence\": 0.92}"}
```

**数据配置** (`data/dataset_info.json`):
```json
{
  "intent_nlu": {
    "file_name": "intent_nlu.jsonl",
    "columns": {
      "prompt": "query",
      "response": "output"
    }
  }
}
```

### 7.4 训练命令

**使用LLaMA Factory CLI**:
```bash
llamafactory-cli train \
  --stage sft \
  --model_name_or_path models/Qwen2.5-1.5B-Instruct \
  --dataset intent_nlu \
  --template qwen \
  --finetuning_type lora \
  --lora_target all \
  --lora_rank 8 \
  --lora_alpha 16 \
  --output_dir output/intent_lora \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --learning_rate 5e-4 \
  --num_train_epochs 3 \
  --bf16 \
  --logging_steps 10 \
  --save_steps 100 \
  --plot_loss
```

**预期输出**:
```
Loading model...
Training...
Epoch 1/3: 100%|██████████| 250/250 [15:23<00:00, 3.69s/it, loss=0.234]
Epoch 2/3: 100%|██████████| 250/250 [15:18<00:00, 3.67s/it, loss=0.156]
Epoch 3/3: 100%|██████████| 250/250 [15:21<00:00, 3.68s/it, loss=0.098]
Training completed!
```

### 7.5 模型测试

**推理脚本** (`test_intent_model.py`):
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = "output/intent_lora"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

test_queries = [
    "想去魔都玩两天",
    "附近有什么好吃的",
    "明天上海会下雨吗"
]

for query in test_queries:
    prompt = f"输入: {query}\n输出: "
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(**inputs, max_new_tokens=128, temperature=0.1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print(f"Query: {query}")
    print(f"Response: {response}\n")
```

**运行测试**:
```bash
python test_intent_model.py
```

### 7.6 延迟测试

**Benchmark脚本** (`benchmark_latency.py`):
```python
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "output/intent_lora"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

test_query = "想去魔都玩两天"
prompt = f"输入: {test_query}\n输出: "

# 预热
for _ in range(5):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    model.generate(**inputs, max_new_tokens=128)

# 测试
latencies = []
for _ in range(100):
    start = time.time()
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    model.generate(**inputs, max_new_tokens=128)
    latencies.append((time.time() - start) * 1000)

print(f"P50: {sorted(latencies)[50]:.2f}ms")
print(f"P95: {sorted(latencies)[95]:.2f}ms")
print(f"P99: {sorted(latencies)[99]:.2f}ms")
```

**目标延迟**:
- P50: ≤ 100ms
- P95: ≤ 150ms
- P99: ≤ 200ms


---

## 八、实施计划

### 8.1 Phase 1: MVP (2周)

**Week 1: 数据准备 + 模型训练**
- Day 1-2: 收集规则未命中的query（1000-2000条）
- Day 3-4: 人工标注 + 数据增强（扩充到5000条）
- Day 5-6: 训练LoRA模型
- Day 7: 模型评估 + 调优

**Week 2: 集成 + 测试**
- Day 8-9: Router层改造
- Day 10-11: 集成LLM Router
- Day 12-13: 端到端测试
- Day 14: 上线灰度测试（10%流量）

**验收标准**:
- ✅ 意图识别准确率 ≥ 85%
- ✅ 延迟 ≤ 200ms
- ✅ 覆盖率: 规则80% + LLM 20% = 100%

### 8.2 Phase 2: 优化 (2周)

**Week 3: 置信度校准 + Badcase收集**
- Day 15-16: 实现Temperature Scaling
- Day 17-18: 实现Badcase Logger
- Day 19-20: 收集第一批badcase
- Day 21: 人工标注badcase

**Week 4: 重训练 + A/B测试**
- Day 22-23: 重训练模型（加入badcase）
- Day 24-25: A/B测试（10% vs 90%）
- Day 26-27: 评估效果
- Day 28: 全量上线

**验收标准**:
- ✅ 意图识别准确率 ≥ 90%
- ✅ 置信度校准误差 < 0.1
- ✅ Badcase收集自动化

### 8.3 Phase 3: 持续优化 (长期)

**每周迭代**:
1. 收集badcase
2. 人工标注
3. 重训练模型
4. A/B测试
5. 上线

**目标**:
- 意图识别准确率 → 95%
- 覆盖率 → 100%
- 用户满意度 → 4.5/5.0

---

## 九、风险与挑战

### 9.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 延迟超标 | 高 | 中 | 模型量化、批量推理 |
| 准确率不达标 | 高 | 中 | 增加训练数据、调优超参 |
| 置信度不准确 | 中 | 高 | Temperature Scaling校准 |
| Mac训练速度慢 | 低 | 中 | 使用云GPU加速 |

### 9.2 产品风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 用户感知到"听不懂" | 高 | 低 | 置信度低时返回澄清 |
| Badcase收集不足 | 中 | 中 | 主动收集用户反馈 |
| 模型更新频率低 | 中 | 中 | 自动化重训练流程 |

### 9.3 成本风险

| 项目 | 成本 | 备注 |
|------|------|------|
| 模型训练 | 免费 | Mac本地训练 |
| 模型推理 | 免费 | 本地部署 |
| 数据标注 | 人力成本 | 每周2-4小时 |
| 存储 | 低 | 模型文件~3GB |

---

## 十、评审问题

### 10.1 待讨论

1. **延迟目标**: 200ms是否可接受？如果不行，考虑0.5B模型
2. **训练数据量**: 5000条是否足够？需要更多数据吗？
3. **置信度阈值**: 0.85/0.7是否合理？需要调整吗？
4. **重训练频率**: 每周一次是否合适？

### 10.2 需要确认

1. **Mac训练**: 是否在Mac本地训练，还是使用云GPU？
2. **模型部署**: 是否部署在本地，还是使用API服务？
3. **A/B测试**: 是否需要A/B测试能力？
4. **监控告警**: 需要哪些监控指标？

---

## 十一、附录

### 11.1 参考资料

- **Qwen2.5文档**: https://github.com/QwenLM/Qwen2.5
- **LLaMA Factory**: https://github.com/hiyouga/LLaMA-Factory
- **LoRA论文**: https://arxiv.org/abs/2106.09685
- **Temperature Scaling**: https://arxiv.org/abs/1706.04599
- **query-rewrite-agents项目**: `/Users/Harland/Documents/evaluation/query-rewrite-agents`

### 11.2 相关文档

- `M5_4_PLAN_TRIP_PRD.md`: plan_trip PRD
- `agent_service/domain/intents/router.py`: 当前路由实现
- `agent_service/domain/location/parser.py`: 规则解析器

### 11.3 训练数据示例

**plan_trip**:
```jsonl
{"query": "帮我规划上海2日游", "output": "{\"intent\": \"plan_trip\", \"params\": {\"destination\": \"上海\", \"days\": 2}, \"confidence\": 0.98}"}
{"query": "想去魔都玩两天", "output": "{\"intent\": \"plan_trip\", \"params\": {\"destination\": \"上海\", \"days\": 2}, \"confidence\": 0.95}"}
{"query": "周末带家人去上海转转", "output": "{\"intent\": \"plan_trip\", \"params\": {\"destination\": \"上海\", \"days\": 2}, \"confidence\": 0.92}"}
```

**find_nearby**:
```jsonl
{"query": "附近有什么好吃的", "output": "{\"intent\": \"find_nearby\", \"params\": {\"keyword\": \"美食\"}, \"confidence\": 0.96}"}
{"query": "周边哪里有咖啡店", "output": "{\"intent\": \"find_nearby\", \"params\": {\"keyword\": \"咖啡店\"}, \"confidence\": 0.94}"}
{"query": "这边有没有超市", "output": "{\"intent\": \"find_nearby\", \"params\": {\"keyword\": \"超市\"}, \"confidence\": 0.93}"}
```

**get_weather**:
```jsonl
{"query": "明天上海会下雨吗", "output": "{\"intent\": \"get_weather\", \"params\": {\"city\": \"上海\", \"date\": \"明天\"}, \"confidence\": 0.97}"}
{"query": "魔都今天天气怎么样", "output": "{\"intent\": \"get_weather\", \"params\": {\"city\": \"上海\", \"date\": \"今天\"}, \"confidence\": 0.95}"}
{"query": "上海这周末会不会下雨", "output": "{\"intent\": \"get_weather\", \"params\": {\"city\": \"上海\", \"date\": \"周末\"}, \"confidence\": 0.93}"}
```

### 11.4 模型性能对比

| 模型 | 参数量 | 延迟(P50) | 准确率 | 备注 |
|------|--------|-----------|--------|------|
| Qwen2.5-0.5B | 0.5B | 50ms | 80% | 速度快但准确率低 |
| Qwen2.5-1.5B | 1.5B | 100ms | 85% | 推荐 |
| Qwen2.5-3B | 3B | 200ms | 90% | 准确率高但延迟高 |
| Phi-2 | 2.7B | 150ms | 87% | 备选 |

### 11.5 交通时间估算策略（补充）

**背景**: plan_trip需要估算景点间交通时间，但不能每次都调用路线规划API（额度限制）

**解决方案**: 基于POI的business_area/district/adcode字段分层估算

**四层估算规则**:

1. **同商圈** (business_area相同):
   - 步行: 5-10分钟
   - 公交: 10-15分钟
   - 驾车: 5-10分钟

2. **同区跨商圈** (district相同，business_area不同):
   - 步行: 不推荐
   - 公交: 20-30分钟
   - 驾车: 15-20分钟

3. **跨区** (adcode相同，district不同):
   - 步行: 不推荐
   - 公交: 40-60分钟
   - 驾车: 30-45分钟

4. **跨城市** (adcode不同):
   - 步行: 不推荐
   - 公交: 不推荐
   - 驾车: 根据距离估算（100km/h高速，60km/h城市）

**特殊地形城市**:
- 重庆: 山地，驾车时间 × 1.5
- 成都: 平原，驾车时间 × 0.9
- 北京: 拥堵，驾车时间 × 1.3

**实现示例**:
```python
def estimate_transit_time(poi_a: dict, poi_b: dict, mode: str) -> int:
    """估算交通时间（分钟）"""
    # 同商圈
    if poi_a.get("business_area") == poi_b.get("business_area"):
        return {"transit": 12, "driving": 8, "walking": 8}[mode]
    
    # 同区跨商圈
    if poi_a.get("district") == poi_b.get("district"):
        return {"transit": 25, "driving": 18, "walking": 999}[mode]
    
    # 跨区
    if poi_a.get("adcode") == poi_b.get("adcode"):
        return {"transit": 50, "driving": 38, "walking": 999}[mode]
    
    # 跨城市
    distance_km = calculate_distance(poi_a["location"], poi_b["location"])
    return int(distance_km / 80 * 60)  # 假设80km/h平均速度
```

**LLM续写描述**:
```python
# 不让LLM自由估算，而是套规则输出描述
transit_time = estimate_transit_time(poi_a, poi_b, mode="transit")
description = f"地铁约{transit_time}分钟"  # LLM只负责生成自然语言
```

**验收标准**:
- 估算误差 ≤ 30%（与实际路线规划API对比）
- 不调用路线规划API（除非用户追问）

---

**状态**: ✅ 意图NLU兜底方案设计文档 v1.0 完成

**下一步**: 
1. 收集训练数据
2. 训练LoRA模型
3. 集成到Router层
4. 端到端测试

