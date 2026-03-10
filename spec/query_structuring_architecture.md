# Query 结构化架构设计

## 问题澄清

### 1. Rewrite 模块的输出格式

```json
{
  "query": "播放他的歌",
  "rewrite_query": "播放周杰伦的歌",
  "rewritten": 1,
  "source": "history_reference"
}
```

**关键点**：
- `query`：原始用户输入
- `rewrite_query`：重写后的查询（指代已消解）
- `rewritten`：是否进行了重写（0/1）
- `source`：重写来源（rule/llm/history_reference 等）

### 2. Query 结构化的作用域

**核心问题**：是为所有技能做通用结构化，还是只为 find_nearby/plan_trip 做专用结构化？

**答案**：**分层策略**

---

## 架构决策

### 总体原则

```
┌─────────────────────────────────────────────────────────┐
│                    ChatFlow.run()                        │
├─────────────────────────────────────────────────────────┤
│ 1. Rewrite 模块（通用）                                  │
│    输入：query                                           │
│    输出：rewrite_query（指代消解）                       │
│    职责：多轮省略指代 → 完整查询                         │
├─────────────────────────────────────────────────────────┤
│ 2. Router（通用）                                        │
│    输入：rewrite_query                                   │
│    输出：tool_name                                       │
│    职责：意图识别 → 工具路由                             │
├─────────────────────────────────────────────────────────┤
│ 3. Query 结构化（工具专用）                              │
│    输入：rewrite_query + tool_name                       │
│    输出：tool_args（结构化参数）                         │
│    职责：参数提取 → 工具调用                             │
└─────────────────────────────────────────────────────────┘
```

### 分层详解

#### 第 1 层：Rewrite（通用，多轮指代消解）

**职责**：处理多轮省略指代
- "那里" → 上次的锚点
- "第一家" → 上次搜索的第一个结果
- "他的歌" → 历史中提到的人名

**输入**：
```python
{
  "query": "那里最近的711",
  "session_id": "user_123",
  "history": [
    {"query": "北京市的鸟巢周边", "tool": "find_nearby", "results": [...]}
  ]
}
```

**输出**：
```python
{
  "query": "那里最近的711",
  "rewrite_query": "北京市的鸟巢周边最近的711",
  "rewritten": 1,
  "source": "location_reference"
}
```

**不做的事**：
- ❌ 不提取 city/anchor_poi/brand 等结构化字段
- ❌ 不做工具专用的参数提取
- ✅ 只做指代消解，输出完整的自然语言查询

#### 第 2 层：Router（通用，工具路由）

**职责**：识别意图，路由到工具
- 输入：`rewrite_query`（已消解的完整查询）
- 输出：`tool_name`（find_nearby / plan_trip / get_weather 等）

**现有实现**：`domain/intents/router.py`（保持不变）

#### 第 3 层：Query 结构化（工具专用，参数提取）

**职责**：根据工具类型，提取结构化参数

**分两类**：

##### 3A. 通用工具（get_weather / get_news / get_stock / web_search）

**现有实现**：`domain/tools/planner.py`（保持不变）

```python
# 简单参数提取
def extract_rule_tool_args(query: str, tool_name: str) -> dict[str, Any]:
    if tool_name == "get_weather":
        city = extract_city(query)
        return {"city": city} if city else {}
    # ...
```

**特点**：
- 参数少（1-2 个）
- 规则提取足够
- 无需复杂结构化

##### 3B. 复杂工具（find_nearby / plan_trip）

**新增实现**：`domain/location/intent.py`（LocationIntent 结构化）

```python
# 复杂参数提取
def parse_location_intent(query: str) -> LocationIntent:
    """
    结构化解析地理位置意图
    输入：rewrite_query（已消解的完整查询）
    输出：LocationIntent（结构化参数）
    """
    intent = LocationIntent()
    
    # 提取：city, district, anchor_poi, brand, category, sort_by, constraints
    intent.city = extract_city(query)
    intent.anchor_poi = extract_anchor_poi(query)
    intent.brand = extract_brand(query)
    intent.category = extract_category(query)
    intent.sort_by, intent.sort_order = parse_sort_intent(query)
    
    return intent
```

**特点**：
- 参数多（6-8 个）
- 需要复杂结构化
- 支持两跳检索

---

## 数据流示例

### Case 1：多轮指代 + 地理位置查询

```
用户第1轮：
  query: "北京市的鸟巢周边，最近的711是哪一家"
  
  ↓ Rewrite（无需重写）
  rewrite_query: "北京市的鸟巢周边，最近的711是哪一家"
  
  ↓ Router
  tool_name: "find_nearby"
  
  ↓ Query 结构化（LocationIntent）
  LocationIntent(
    city="北京市",
    anchor_poi="鸟巢",
    brand="711",
    category="便利店",
    sort_by="distance"
  )
  
  ↓ 两跳检索
  结果：[711便利店1, 711便利店2, ...]

用户第2轮：
  query: "那里最近的便利店呢"
  
  ↓ Rewrite（消解指代）
  rewrite_query: "北京市的鸟巢周边最近的便利店"
  rewritten: 1
  source: "location_reference"
  
  ↓ Router
  tool_name: "find_nearby"
  
  ↓ Query 结构化（LocationIntent）
  LocationIntent(
    city="北京市",
    anchor_poi="鸟巢",
    brand="",
    category="便利店",
    sort_by="distance"
  )
  
  ↓ 两跳检索
  结果：[便利店1, 便利店2, ...]
```

### Case 2：简单天气查询

```
用户：
  query: "北京明天天气怎么样"
  
  ↓ Rewrite（无需重写）
  rewrite_query: "北京明天天气怎么样"
  
  ↓ Router
  tool_name: "get_weather"
  
  ↓ Query 结构化（简单提取）
  tool_args: {"city": "北京"}
  
  ↓ 工具调用
  结果：晴天，气温 15-25°C
```

---

## 架构图

```
┌──────────────────────────────────────────────────────────────┐
│                      ChatFlow.run()                           │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ 第1层：Rewrite 模块（通用）                                   │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 输入：query + session_id + history                     │   │
│ │ 处理：多轮省略指代消解                                 │   │
│ │ 输出：rewrite_query（完整查询）                        │   │
│ │ 例：那里 → 北京市的鸟巢周边                            │   │
│ └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│ 第2层：Router（通用）                                         │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ 输入：rewrite_query                                    │   │
│ │ 处理：规则 + LLM 混合路由                              │   │
│ │ 输出：tool_name                                        │   │
│ │ 例：find_nearby / get_weather / plan_trip              │   │
│ └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────────────┐          ┌──────────────────────────┐
│ 第3A层：简单工具参数提取  │          │ 第3B层：复杂工具参数提取  │
│ (planner.py)             │          │ (location/intent.py)     │
├──────────────────────────┤          ├──────────────────────────┤
│ get_weather              │          │ find_nearby              │
│ get_news                 │          │ plan_trip                │
│ get_stock                │          │                          │
│ web_search               │          │ LocationIntent:          │
│                          │          │ - city                   │
│ tool_args: {             │          │ - district               │
│   "city": "北京"         │          │ - anchor_poi             │
│ }                        │          │ - brand                  │
│                          │          │ - category               │
│                          │          │ - sort_by                │
│                          │          │ - constraints            │
└──────────────────────────┘          └──────────────────────────┘
        ↓                                           ↓
┌──────────────────────────┐          ┌──────────────────────────┐
│ 工具调用（单跳）         │          │ 工具调用（两跳）         │
│ 1. 直接调用高德/天气API  │          │ 1. 定位锚点              │
│ 2. 返回结果              │          │ 2. 周边搜索              │
│                          │          │ 3. 过滤重排              │
│                          │          │ 4. 返回结果              │
└──────────────────────────┘          └──────────────────────────┘
```

---

## 实施方案

### 第 1 步：Rewrite 模块（已规划）

**文件**：`spec/rewrite_integration_plan.md`

**职责**：
- 指代消解（那里/第一家/这家）
- 输出：`rewrite_query`（完整查询）

**不做**：
- ❌ 不做工具专用的参数提取

### 第 2 步：Router（保持不变）

**文件**：`domain/intents/router.py`

**职责**：
- 工具路由
- 输出：`tool_name`

### 第 3 步：Query 结构化（分工具类型）

#### 3A. 简单工具（保持不变）

**文件**：`domain/tools/planner.py`

**职责**：
- 简单参数提取
- 输出：`tool_args`

#### 3B. 复杂工具（新增）

**文件**：`domain/location/intent.py`

**职责**：
- 复杂参数结构化
- 输出：`LocationIntent`

**实现**：
```python
# agent_service/domain/location/intent.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

class SortBy(str, Enum):
    DISTANCE = "distance"
    RATING = "rating"
    PRICE = "price"

@dataclass
class LocationIntent:
    """地理位置意图（find_nearby / plan_trip 专用）"""
    
    # 地理层级
    city: str = ""
    district: str = ""
    street: str = ""
    
    # 锚点信息
    anchor_poi: str = ""
    
    # 目标信息
    brand: str = ""
    category: str = ""
    
    # 约束条件
    sort_by: SortBy = SortBy.DISTANCE
    sort_order: str = "asc"
    
    # 元数据
    raw_query: str = ""
    confidence: float = 1.0
    
    def is_complete(self) -> bool:
        """判断意图是否完整"""
        return bool(self.city and (self.anchor_poi or self.category))
```

---

## 关键决策

### Q1：Query 结构化是否需要通用？

**A：不需要通用，按工具类型分层**

**理由**：
1. 不同工具的参数差异大
   - get_weather：只需 city
   - find_nearby：需要 city/anchor_poi/brand/category/sort_by
   - plan_trip：需要 destination/days

2. 通用结构化会过度设计
   - 大多数工具不需要复杂结构化
   - 只有 find_nearby/plan_trip 需要

3. 分层更清晰
   - 简单工具用 planner.py（现有）
   - 复杂工具用 LocationIntent（新增）

### Q2：Rewrite 模块是否需要知道工具类型？

**A：不需要，Rewrite 是通用的**

**理由**：
1. Rewrite 的职责是指代消解
   - "那里" → 上次的锚点（通用）
   - "第一家" → 上次的第一个结果（通用）
   - 与工具类型无关

2. 工具类型由 Router 决定
   - Rewrite 输出完整查询
   - Router 识别工具
   - Query 结构化根据工具类型处理

3. 解耦更好
   - Rewrite 不需要关心下游工具
   - 新增工具时无需改 Rewrite

### Q3：LocationIntent 是否需要在 Rewrite 中使用？

**A：不需要，在 Query 结构化阶段使用**

**流程**：
```
Rewrite 输出：rewrite_query（字符串）
  ↓
Router 识别：tool_name
  ↓
Query 结构化：
  if tool_name == "find_nearby":
    intent = parse_location_intent(rewrite_query)
  else:
    tool_args = extract_rule_tool_args(rewrite_query, tool_name)
```

---

## 集成点

### ChatFlow 中的集成

```python
# agent_service/app/orchestrator/chat_flow.py
def run(self, req: ChatRequest) -> ChatResponse:
    # 1. Rewrite（通用）
    rw = rewrite_query(query=req.query, session_ctx=session_ctx)
    effective_query = rw.effective_query
    
    # 2. Router（通用）
    route = route_query(effective_query)
    
    # 3. Query 结构化（工具专用）
    if route.tool_name == "find_nearby":
        # 复杂工具：使用 LocationIntent
        from domain.location.intent import parse_location_intent
        intent = parse_location_intent(effective_query)
        plan = ToolPlan(
            tool_name="find_nearby",
            tool_args=intent.to_dict()
        )
    else:
        # 简单工具：使用现有 planner
        plan = _build_merged_tool_plan(
            query=effective_query,
            tool_name=route.tool_name,
            ...
        )
    
    # 4. 工具调用
    result = self.tool_executor.execute(plan.tool_name, plan.tool_args)
```

---

## 总结

### 分层职责

| 层级 | 模块 | 职责 | 输入 | 输出 | 作用域 |
|------|------|------|------|------|--------|
| 1 | Rewrite | 多轮指代消解 | query + history | rewrite_query | 通用 |
| 2 | Router | 工具路由 | rewrite_query | tool_name | 通用 |
| 3A | Planner | 简单参数提取 | rewrite_query + tool_name | tool_args | 简单工具 |
| 3B | LocationIntent | 复杂参数结构化 | rewrite_query | LocationIntent | find_nearby/plan_trip |

### 不做的事

- ❌ Rewrite 不做工具专用参数提取
- ❌ LocationIntent 不做多轮指代消解
- ❌ Query 结构化不做工具路由

### 做的事

- ✅ Rewrite：指代消解 → 完整查询
- ✅ Router：意图识别 → 工具路由
- ✅ Query 结构化：参数提取 → 工具调用

---

**文档版本**：v1.0  
**创建日期**：2026-03-03  
**作者**：Kiro AI Assistant  
**审核状态**：待审核
