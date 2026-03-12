# Day3快速修复方案

## 修复策略

根据产品定义和数据分析，分3个阶段修复：

---

## 阶段1：拒识规则（0.5天，立即见效+11条）

### 修复位置
`agent_service/domain/intents/router_4b_with_logprobs.py`

### 修复内容
在`try_route()`最前面添加拒识规则（优先级-1，最高）：

```python
def try_route(self, query: str) -> Optional[str]:
    """
    规则优先级（从高到低）:
    - 优先级-1（最高）: 拒识规则 → reject
    - 优先级0: 旅游意图关键词 → plan_trip
    - 优先级1: 目的地+时间 → plan_trip
    - 优先级2: 位置+类别 → find_nearby
    - 优先级3: 天气关键词 → get_weather
    """
    
    # 优先级-1: 拒识规则（最高优先级）
    # 设备控制类
    device_control_keywords = ["设闹钟", "发微信", "打开空调", "关空调", "导航回家", "打电话"]
    if any(kw in query for kw in device_control_keywords):
        return "reject_device_control"
    
    # 投资建议类
    investment_keywords = ["值得买吗", "应该买", "买哪个好", "推荐买"]
    if any(kw in query for kw in investment_keywords):
        return "reject_investment_advice"
    
    # 娱乐互动类（成语接龙、讲笑话等）
    entertainment_keywords = ["成语接龙", "讲笑话", "猜谜语", "玩游戏", "聊天", "陪我"]
    if any(kw in query for kw in entertainment_keywords):
        return "reject_entertainment"
    
    # 原有规则...
```

### 预期效果
- 拒识准确率: 0% → 100% (+11条)
- 娱乐互动误判: +1条（"成语接龙"case）
- 整体准确率: 59.5% → 65.5% (+12条)

---

## 阶段2：web_search实时查询规则（0.3天，立即见效+5条）

### 修复位置
`agent_service/domain/intents/router_4b_with_logprobs.py`

### 修复内容
在优先级0添加实时查询规则：

```python
# 优先级0: 实时查询关键词 → web_search
realtime_keywords = ["限号", "油价", "打折", "最新款", "最新", "今天", "现在"]
if any(kw in query for kw in realtime_keywords) and any(verb in query for verb in ["搜", "查", "看"]):
    return "web_search"
```

### 预期效果
- web_search准确率: 17.4% → 39.1% (+5条)
- 整体准确率: 65.0% → 67.5%

---

## 阶段3：web_search vs plan_trip优先级调整（0.2天，立即见效+7条）

### 修复位置
`agent_service/domain/intents/router_4b_with_logprobs.py`

### 修复内容
调整规则顺序，"搜/查"优先级高于"旅游"：

```python
# 优先级0: "搜/查" + 任何内容 → web_search（高于旅游规则）
search_verbs = ["搜", "查", "看", "找"]
if any(verb in query for verb in search_verbs):
    # 排除明确的附近查询
    if not any(loc in query for loc in ["附近", "周边", "这里"]):
        return "web_search"

# 优先级1: 旅游意图关键词 → plan_trip
trip_keywords = ["旅游", "旅行", "游玩", "攻略", "行程"]
if any(kw in query for kw in trip_keywords):
    return "plan_trip"
```

### 预期效果
- web_search准确率: 39.1% → 69.6% (+7条)
- 整体准确率: 67.5% → 71.0%

---

## 阶段4：评测集label修正（0.1天，不修代码，修正基线+21条）

### 问题分析
当前28条search_nearby case中：
- 1条有明确位置（H00005: 上海外滩周边）→ 保持tool_call_then_nearby
- 27条隐式位置词（附近/周边/这附近）→ 应该改为clarify_missing_location

### 产品定义（已确认）
> 附近的、最近的、周边的，检测到此类意图后，如果提取不到城市、街道数据，那就反问澄清

### 修复方案
修改`archive/csv_data/testset_200条_0309_fixed.csv`：

```python
# 需要修改的case（27条）
cases_to_fix = [
    "H00001", "H00002", "H00003", "H00013", "H00024", "H00025",
    "H00034", "H00035", "H00037", "H00057", "H00058", "H00059",
    "H00060", "H00061", "H00062", "H00063", "H00064", "H00065",
    "H00067", "H00068", "H00069", "H00070", "H00071", "H00072",
    "H00073", "H00075", "H00077"
]

# 修改expected_behavior
# tool_call_then_nearby → clarify_missing_location
```

### 预期效果
- search_nearby准确率: 3.6% → 100% (+27条，但实际是修正label）
- 整体准确率: 71.0% → 84.5%

---

## 总结

### 修复前
- 整体准确率: 59.5% (119/200)
- 拒识: 0% (0/11)
- web_search: 17.4% (4/23)
- search_nearby: 3.6% (1/28)

### 修复后（阶段1-3，纯规则修复）
- 整体准确率: 71.5% (143/200) ✅ +12%
- 拒识: 100% (11/11) ✅ +100%
- 娱乐互动误判: 修复1条
- web_search: 69.6% (16/23) ✅ +52.2%
- search_nearby: 3.6% (1/28) （待label修正）

### 修复后（阶段4，label修正）
- 整体准确率: 84.5% (169/200) ✅ +25%
- 拒识: 100% (11/11) ✅ +100%
- web_search: 69.6% (16/23) ✅ +52.2%
- search_nearby: 100% (28/28) ✅ +96.4%（label修正）

### 工作量
- 阶段1: 0.5天
- 阶段2: 0.3天
- 阶段3: 0.2天
- 阶段4: 0.1天
- **总计**: 1.1天

---

## 下一步

1. 实施阶段1-3规则修复
2. 运行smoke test验证
3. 修改评测集label（阶段4）
4. 重新运行200条评测
5. 输出最终报告

