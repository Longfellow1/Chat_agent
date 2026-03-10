# 评测数据集设计规范

**日期**: 2026-03-09  
**版本**: v1.0  
**目标**: 基于当前智能体功能设计800条评测数据集

---

## 一、智能体功能现状

### 1.1 Decision Modes (决策模式)

| Mode | 说明 | 触发条件 |
|------|------|---------|
| `tool_call` | 工具调用 | 识别到实时信息需求 |
| `reply` | 闲聊回复 | 知识问答、情感支持等 |
| `reject` | 拒识 | 违法/危险/无意义输入 |
| `end_chat` | 结束对话 | 用户明确表示结束 |
| `clarify` | 澄清询问 | 工具参数缺失 |

### 1.2 支持的工具

| 工具名 | 功能 | 参数 | 状态 |
|--------|------|------|------|
| `get_weather` | 天气查询 | city | ✅ 已实现 |
| `get_stock` | 股票查询 | target | ✅ 已实现 |
| `get_news` | 新闻查询 | topic | ✅ 已实现 |
| `web_search` | 网页搜索 | query | ✅ 已实现 |
| `find_nearby` | 附近搜索 | keyword, city, location | ✅ 已实现 |
| `plan_trip` | 行程规划 | destination, days, travel_mode | ✅ 已实现 |

### 1.3 安全策略

- 违法内容拒识 (illegal)
- 无意义输入拒识 (noise)
- 超出能力边界提示 (out_of_scope)
- 危机干预支持 (crisis)

---

## 二、CSV数据集格式

### 2.1 必需字段
