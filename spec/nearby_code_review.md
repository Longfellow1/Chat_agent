# Nearby 代码走查报告

**日期**: 2026-03-05  
**目的**: 确认 nearby 链路使用最新逻辑，无旧接口残留

---

## 一、验证结果总结

### ✅ 核心链路已打通

```
用户查询 → ChatFlow → Planner V2 → Executor → Gateway → Amap MCP → 真实 POI
```

**测试验证**:
- ✅ 路由到 find_nearby: 100%
- ✅ 使用 amap_mcp provider: 100%
- ✅ 返回真实数据: 100%
- ✅ 提取 LocationIntent: 100%

**测试案例**: "上海静安寺附近的咖啡厅"
- Tool Args: `{'location': '静安寺', 'keyword': '咖啡厅', 'city': '上海'}`
- Provider: `amap_mcp`
- 返回: M Stand、LAVAZZA、看得到风景的咖啡馆（真实 POI）

---

## 二、代码路径分析

### 2.1 正确的代码路径

| 层级 | 文件 | 方法/函数 | 状态 |
|------|------|----------|------|
| 1. 入口 | `chat_flow.py` | `run()` | ✅ 正确 |
| 2. 规划 | `planner_v2.py` | `build_tool_plan_v2()` | ✅ 使用 LocationIntent |
| 3. 执行 | `executor.py` | `execute()` | ✅ 调用 gateway.invoke() |
| 4. 网关 | `mcp_gateway.py` | `invoke()` → `_nearby()` | ✅ 优先 MCP |
| 5. MCP | `amap_mcp_client.py` | `find_nearby()` | ✅ 返回真实数据 |

### 2.2 关键代码片段

**Planner V2 使用 LocationIntent**:
```python
# planner_v2.py:28-45
if tool_name == "find_nearby" and use_location_intent:
    intent = parse_location_intent(query)
    if not intent.is_complete():
        return {"error": "incomplete_intent", ...}
    return {
        "tool_name": tool_name,
        "tool_args": intent.to_tool_args(),  # ✅ 使用 LocationIntent
        "intent": intent.to_dict(),
    }
```

**Gateway 优先使用 MCP**:
```python
# mcp_gateway.py:287-294
def _nearby(self, keyword: str, city: str | None, location: str | None = None):
    if self.amap_mcp:
        try:
            return self.amap_mcp.find_nearby(keyword=keyword, city=city, location=location)  # ✅ 优先 MCP
        except Exception as e:
            print(f"Amap MCP failed: {e}, falling back to mock")
```

---

## 三、发现的问题

### ❌ 问题 1: 旧 Amap API 逻辑残留

**位置**: `mcp_gateway.py:308-360`

**问题描述**:
- 当 MCP 失败后，会 fallback 到旧的 Amap API 直接调用
- 这段代码**不使用** LocationIntent、Result Processor、Template
- 使用旧的 `_parse_nearby_keyword()` 函数

**代码片段**:
```python
# mcp_gateway.py:308-360
if not keyword:
    keyword = "餐厅"

parsed = _parse_nearby_keyword(keyword)  # ❌ 旧逻辑
anchor = parsed.get("anchor") or ""
final_keyword = parsed.get("keyword") or keyword
types = parsed.get("types") or ""

params = {
    "key": self.amap_key,
    "keywords": final_keyword,
    # ... 直接调用高德 API
}
```

**影响**:
- 当前不影响（因为 MCP 正常工作）
- 但如果 MCP 失败，会走旧逻辑，导致：
  - 不使用 LocationIntent 解析
  - 不使用 Result Processor 重排序
  - 不使用 Template 格式化

**建议**: 删除第 308-360 行的旧 API 逻辑，MCP 失败直接 fallback 到 mock

---

### ⚠️ 问题 2: Provider Chain 代码未使用

**位置**: 
- `infra/tool_clients/provider_chain.py`
- `infra/tool_clients/providers/amap_providers.py`

**问题描述**:
- Provider Chain 功能在 gateway 整合时被删除
- 但相关代码文件仍然存在
- `AmapMCPProvider` 和 `AmapDirectProvider` 未被使用

**影响**: 无（代码未被调用）

**建议**: 
- 如果确认不再使用 Provider Chain，删除相关文件
- 或者在文档中标注为"已废弃"

---

## 四、未使用的旧函数

### 4.1 `_parse_nearby_keyword()`

**位置**: `mcp_gateway.py:1000-1050`

**用途**: 旧的 keyword 解析逻辑（不使用 LocationIntent）

**状态**: 
- ✅ 主流程不使用
- ❌ 旧 API fallback 逻辑中使用（第 308 行）

**建议**: 删除（连同旧 API 逻辑一起）

### 4.2 `_amap_search_around()`

**位置**: `mcp_gateway.py:362-410`

**用途**: 旧的周边搜索逻辑

**状态**: 
- ❌ 旧 API fallback 逻辑中使用（第 328 行）

**建议**: 删除（连同旧 API 逻辑一起）

---

## 五、推荐清理方案

### 方案 1: 最小改动（推荐）

**只删除旧 API fallback 逻辑**:

```python
# mcp_gateway.py:287-303
def _nearby(self, keyword: str, city: str | None, location: str | None = None):
    # Use Amap MCP if available
    if self.amap_mcp:
        try:
            return self.amap_mcp.find_nearby(keyword=keyword, city=city, location=location)
        except Exception as e:
            print(f"Amap MCP failed: {e}, falling back to mock")
    
    # Fallback to mock
    loc = city or "当前位置"
    return self._network_fallback(
        original_tool="find_nearby",
        query=f"{loc} 附近 {keyword}",
        hard_fallback=lambda: mock_find_nearby(keyword=keyword, city=city),
    )
    
    # ❌ 删除第 308-360 行的旧 API 逻辑
```

**删除的函数**:
- `_parse_nearby_keyword()` (第 1000-1050 行)
- `_amap_search_around()` (第 362-410 行)
- `_normalize_anchor()` (第 1052-1065 行)

### 方案 2: 彻底清理

**额外删除 Provider Chain 相关文件**:
- `infra/tool_clients/provider_chain.py`
- `infra/tool_clients/provider_base.py`
- `infra/tool_clients/provider_config.py`
- `infra/tool_clients/providers/amap_providers.py`
- `infra/tool_clients/circuit_breaker.py`

**风险**: 如果未来需要 Provider Chain，需要重新实现

---

## 六、测试覆盖

### 6.1 已验证的测试

| 测试 | 文件 | 状态 |
|------|------|------|
| 端到端测试 | `test_nearby_code_path.py` | ✅ 通过 |
| MCP 直接调用 | `test_amap_mcp_direct.py` | ✅ 通过 |
| Gateway 调用 | `test_gateway_invoke.py` | ✅ 通过 |
| 完整流程 | `test_amap_mcp_status.py` | ✅ 通过 |

### 6.2 需要补充的测试

- [ ] MCP 失败时的 fallback 行为测试
- [ ] LocationIntent 不完整时的 clarify 测试
- [ ] Result Processor 重排序效果测试
- [ ] Template 格式化效果测试

---

## 七、结论

### ✅ 主流程正确

- 完整链路已打通
- 使用最新的 LocationIntent、Result Processor、Template
- 返回真实 POI 数据

### ❌ 存在旧代码残留

- 旧 Amap API 逻辑（第 308-360 行）
- 旧辅助函数（`_parse_nearby_keyword`、`_amap_search_around`）
- 未使用的 Provider Chain 代码

### 📋 下一步行动

1. **立即执行**: 删除旧 API fallback 逻辑（方案 1）
2. **可选**: 删除 Provider Chain 相关文件（方案 2）
3. **补充测试**: MCP 失败场景、LocationIntent 边界情况

---

**审核人**: Tech Lead  
**生效日期**: 2026-03-05
