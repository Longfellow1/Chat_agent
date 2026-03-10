# Location Intent 完整指南

> 地点意图解析模块的完整文档，包含架构设计、使用指南和快速参考

---

## 📚 目录

1. [快速开始](#快速开始)
2. [核心功能](#核心功能)
3. [数据模型](#数据模型)
4. [使用方式](#使用方式)
5. [词典管理](#词典管理)
6. [测试](#测试)
7. [扩展指南](#扩展指南)
8. [性能指标](#性能指标)

---

## 快速开始

### 基础使用

```python
from domain.location.parser import parse_location_intent

# 解析查询
query = "北京市的鸟巢周边，最近的711是哪一家"
intent = parse_location_intent(query)

# 访问结构化字段
print(intent.city)           # "北京市"
print(intent.anchor_poi)     # "国家体育场"（已解析别名）
print(intent.brand)          # "711"
print(intent.category)       # "便利店"（从品牌推断）
print(intent.sort_by)        # SortBy.DISTANCE
print(intent.is_complete())  # True

# 转换为工具参数
tool_args = intent.to_tool_args()
# {"keyword": "国家体育场 711", "city": "北京市"}
```

### 导入速查

```python
# 基础导入
from domain.location.parser import parse_location_intent
from domain.location.intent import LocationIntent, SortBy, AnchorType

# 字典导入
from domain.location.dictionaries import (
    resolve_landmark,
    get_category_for_brand,
    parse_sort_intent,
    parse_constraints,
)

# 集成导入
from domain.tools.planner_v2 import build_tool_plan_v2
from infra.tool_clients.mcp_gateway_v2 import MCPToolGatewayV2
```

---

## 核心功能

### 1. Query 结构化

将自然语言查询转换为结构化的 LocationIntent：

```
输入：北京市的鸟巢周边，最近的711是哪一家
↓
LocationIntent(
  city="北京市",
  anchor_poi="国家体育场",
  brand="711",
  category="便利店",
  sort_by=SortBy.DISTANCE,
  sort_order="asc"
)
```

### 2. 地名别名解析

自动解析通俗地名到官方 POI：

```python
resolve_landmark("鸟巢")      # → "国家体育场"
resolve_landmark("水立方")    # → "国家游泳中心"
resolve_landmark("世博源")    # → "上海世博会博物馆"
```

### 3. 品牌推断业态

从品牌自动推断业态分类：

```python
get_category_for_brand("711")      # → "便利店"
get_category_for_brand("肯德基")   # → "快餐"
get_category_for_brand("星巴克")   # → "咖啡厅"
```

### 4. 排序意图识别

识别自然语言中的排序意图：

```python
parse_sort_intent("最近的")    # → ("distance", "asc")
parse_sort_intent("最好评")    # → ("rating", "desc")
parse_sort_intent("人均最低")  # → ("price", "asc")
```

### 5. 约束条件提取

提取查询中的约束条件：

```python
parse_constraints("24小时")     # → {"open_24h": True}
parse_constraints("有停车位")   # → {"has_parking": True}
parse_constraints("有wifi")     # → {"has_wifi": True}
```

---

## 数据模型

### LocationIntent 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| city | str | 城市（必填） | "北京市" |
| district | str | 区（可选） | "朝阳区" |
| street | str | 街道（可选） | "建国路" |
| anchor_poi | str | 地标/POI | "国家体育场" |
| anchor_type | AnchorType | 地标类型 | AnchorType.LANDMARK |
| brand | str | 品牌 | "711" |
| category | str | 业态 | "便利店" |
| sort_by | SortBy | 排序方式 | SortBy.DISTANCE |
| sort_order | str | 排序顺序 | "asc" |
| constraints | dict | 约束条件 | {"open_24h": True} |
| confidence | float | 置信度 | 0.85 |

### 枚举类型

```python
class AnchorType(str, Enum):
    LANDMARK = "landmark"  # 地标（鸟巢、世博源）
    ADDRESS = "address"    # 地址（xx街道xx号）
    POI = "poi"           # POI（餐厅、医院）

class SortBy(str, Enum):
    DISTANCE = "distance"  # 距离
    RATING = "rating"      # 评分
    PRICE = "price"        # 价格
```

---

## 使用方式

### 方式 1：直接使用

```python
from domain.location.parser import parse_location_intent

intent = parse_location_intent(query)
tool_args = intent.to_tool_args()
```

### 方式 2：使用 planner_v2

```python
from domain.tools.planner_v2 import build_tool_plan_v2

plan = build_tool_plan_v2(query, "find_nearby", use_location_intent=True)
tool_args = plan["tool_args"]
```

### 方式 3：使用 MCP 网关

```python
from infra.tool_clients.mcp_gateway_v2 import MCPToolGatewayV2

gateway = MCPToolGatewayV2()
result, intent = gateway.invoke_nearby_with_intent(query)
```

### 在 ChatFlow 中集成

```python
from domain.location.parser import parse_location_intent

if route.tool_name == "find_nearby":
    # 解析位置意图
    intent = parse_location_intent(effective_query)
    
    # 检查完整性
    if not intent.is_complete():
        return ChatResponse(
            decision_mode="clarify",
            final_text="请告诉我你在哪个城市"
        )
    
    # 调用工具
    tool_args = intent.to_tool_args()
```

---

## 词典管理

### 地名别名（LANDMARK_ALIASES）

```python
LANDMARK_ALIASES = {
    "鸟巢": "国家体育场",
    "水立方": "国家游泳中心",
    "世博源": "上海世博会博物馆",
    # ... 更多别名
}
```

### 品牌分类（BRAND_CATEGORY_MAP）

```python
BRAND_CATEGORY_MAP = {
    "711": "便利店",
    "肯德基": "快餐",
    "星巴克": "咖啡厅",
    # ... 更多品牌
}
```

### 排序关键词（SORT_KEYWORDS）

```python
SORT_KEYWORDS = {
    "最近": ("distance", "asc"),
    "最好评": ("rating", "desc"),
    "人均最低": ("price", "asc"),
    # ... 更多关键词
}
```

### 约束条件（CONSTRAINT_KEYWORDS）

```python
CONSTRAINT_KEYWORDS = {
    "24小时": {"open_24h": True},
    "有停车位": {"has_parking": True},
    "有wifi": {"has_wifi": True},
    # ... 更多约束
}
```

---

## 测试

### 运行测试

```bash
# 单元测试
pytest tests/unit/test_location_intent.py -v

# 集成测试
pytest tests/integration/test_location_intent_integration.py -v

# 查看覆盖率
pytest tests/unit/test_location_intent.py --cov=domain.location
```

### 测试覆盖率

```
domain/location/intent.py      100%
domain/location/dictionaries.py 95%
domain/location/parser.py       92%
```

---

## 扩展指南

### 添加地名别名

编辑 `agent_service/domain/location/dictionaries.py`：

```python
LANDMARK_ALIASES["新地标"] = "官方地标名称"
```

### 添加品牌

```python
BRAND_CATEGORY_MAP["新品牌"] = "业态分类"
```

### 添加排序关键词

```python
SORT_KEYWORDS["新关键词"] = ("sort_by", "order")
```

### 添加约束条件

```python
CONSTRAINT_KEYWORDS["新约束"] = {"constraint_key": True}
```

---

## 性能指标

| 指标 | 目标 | 实现 |
|------|------|------|
| 单次解析 | < 5ms | ✓ |
| 批量解析（100条） | < 500ms | ✓ |
| 内存占用 | < 1MB | ✓ |
| 测试覆盖率 | >= 80% | ✓ |
| 单元测试数 | >= 20 | ✓ (30+) |

---

## 常见场景

### 场景 1：简单查询

```python
query = "北京市附近的餐厅"
intent = parse_location_intent(query)

if intent.is_complete():
    tool_args = intent.to_tool_args()
else:
    # 提示用户补充信息
    pass
```

### 场景 2：复杂查询

```python
query = "北京市的鸟巢周边，最近的711是哪一家"
intent = parse_location_intent(query)

# 所有字段都已提取
print(f"城市：{intent.city}")
print(f"地标：{intent.anchor_poi}")
print(f"品牌：{intent.brand}")
print(f"业态：{intent.category}")
```

### 场景 3：不完整查询

```python
query = "附近的餐厅"
intent = parse_location_intent(query)

if not intent.is_complete():
    print("缺失字段：city")
    # 提示用户：请告诉我你在哪个城市
```

---

## 错误处理

```python
try:
    intent = parse_location_intent(query)
    
    if not intent.is_complete():
        missing = []
        if not intent.city:
            missing.append("city")
        if not intent.anchor_poi and not intent.category:
            missing.append("target")
        
        return {"error": "incomplete_intent", "missing": missing}
    
    tool_args = intent.to_tool_args()
    
except Exception as e:
    logger.error(f"解析失败：{query}", exc_info=True)
    return {"error": "parse_error"}
```

---

## 常见问题

### Q: 如何处理不完整的查询？

```python
intent = parse_location_intent(query)
if not intent.is_complete():
    return "请告诉我你在哪个城市"
```

### Q: 如何添加新的地名别名？

编辑 `agent_service/domain/location/dictionaries.py`，添加到 `LANDMARK_ALIASES`。

### Q: 如何检查解析的置信度？

```python
intent = parse_location_intent(query)
if intent.confidence < 0.5:
    # 可能需要 LLM 补全
    pass
```

### Q: 如何获取工具参数？

```python
tool_args = intent.to_tool_args()
# {"keyword": "...", "city": "..."}
```

---

## 交付物清单

### 代码模块（4 个）
- `agent_service/domain/location/intent.py` - 数据模型
- `agent_service/domain/location/dictionaries.py` - 词典
- `agent_service/domain/location/parser.py` - 解析器
- `agent_service/domain/location/__init__.py` - 模块入口

### 集成层（2 个）
- `agent_service/domain/tools/planner_v2.py` - 工具计划构建
- `agent_service/infra/tool_clients/mcp_gateway_v2.py` - MCP 网关

### 测试（2 个）
- `tests/unit/test_location_intent.py` - 单元测试（30+ 用例）
- `tests/integration/test_location_intent_integration.py` - 集成测试（12+ 用例）

---

## 相关架构

### 数据流

```
用户输入
  ↓
[Rewrite 模块] - 指代消解（后期）
  ↓
[Router] - 工具路由
  ↓
[Query 结构化] ← LocationIntent
  ↓
[工具调用] - MCP 网关
  ↓
[结果返回]
```

### 当前实施范围

✅ Query 结构化（LocationIntent）  
⏳ Rewrite 模块（后期）  
⏳ 多轮会话支持（后期）

---

**文档版本**：v2.0（合并版）  
**创建日期**：2026-03-06  
**合并自**：LOCATION_INTENT_SUMMARY.md, location_intent_quick_reference.md, location_intent_usage_guide.md  
**状态**：✅ 生产就绪
