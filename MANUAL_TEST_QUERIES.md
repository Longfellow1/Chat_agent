# 手动测试Query列表

## 测试说明
以下是5个精心挑选的测试query，覆盖不同场景。请在实际环境中测试这些query，验证：
1. Intent解析是否正确
2. 结果Rerank是否生效
3. 模板输出是否自然流畅

---

## Query 1: 基础场景 - 品牌 + 距离排序
```
北京市的鸟巢周边，最近的711是哪一家
```

**预期解析**：
- City: 北京市
- Anchor: 国家体育场（鸟巢别名解析）
- Brand: 711
- Category: 便利店
- Sort: distance (asc)

**预期行为**：
1. 调用高德MCP搜索"北京市 国家体育场 711"
2. 过滤结果：只保留名称包含"711"或"7-11"的POI
3. 按距离排序（升序）
4. 使用模板输出，例如："离您最近的是7-11便利店(鸟巢店)，距离200米"

---

## Query 2: 复杂场景 - 多层级 + 评分排序
```
上海静安寺周边评分最高的咖啡厅
```

**预期解析**：
- City: 上海
- District: 静安区
- Anchor: 上海静安寺（地标）
- Category: 咖啡厅
- Sort: rating (desc)

**预期行为**：
1. 调用高德MCP搜索"上海 静安区 上海静安寺 咖啡厅"
2. 过滤结果：只保留类型包含"咖啡"的POI
3. 按评分排序（降序）
4. 使用模板输出，例如："找到3个咖啡厅：\n1. 星巴克(静安寺店)（4.8分）\n2. ..."

---

## Query 3: 简单场景 - 城市 + 类别
```
深圳南山区的便利店
```

**预期解析**：
- City: 深圳
- District: 深圳南山区
- Category: 便利店
- Sort: distance (asc)

**预期行为**：
1. 调用高德MCP搜索"深圳 深圳南山区 便利店"
2. 过滤结果：只保留类型包含"便利店"的POI
3. 按距离排序（默认）
4. 使用模板输出，例如："为您找到5个便利店：\n1. 7-11便利店\n2. 全家便利店\n..."

---

## Query 4: 边缘场景 - 缺少城市
```
三里屯附近的肯德基
```

**预期解析**：
- City: (空)
- Anchor: 三里屯太古里
- Brand: 肯德基
- Category: 快餐
- Sort: distance (asc)
- Complete: False（缺少城市）

**预期行为**：
1. 返回错误："信息不完整，请提供地点和搜索目标"
2. 或者：如果高德MCP支持无城市搜索，则直接搜索"三里屯太古里 肯德基"

---

## Query 5: 价格排序场景
```
深圳福田区华强北最便宜的餐厅
```

**预期解析**：
- City: 深圳
- District: 深圳福田区
- Anchor: 华强北商业街
- Category: 餐厅
- Sort: price (asc)

**预期行为**：
1. 调用高德MCP搜索"深圳 深圳福田区 华强北商业街 餐厅"
2. 过滤结果：只保留类型包含"餐厅"的POI
3. 按价格排序（升序）
4. 使用模板输出，例如："找到5个餐厅：\n1. 沙县小吃（人均15元）\n2. ..."

---

## 测试检查点

### 1. Intent解析准确性
- [ ] 城市提取正确
- [ ] 地标别名解析正确（鸟巢→国家体育场）
- [ ] 品牌识别正确
- [ ] 类别识别正确
- [ ] 排序意图识别正确

### 2. Result Rerank效果
- [ ] 品牌过滤生效（只返回指定品牌）
- [ ] 距离排序生效（最近的在前）
- [ ] 评分排序生效（最高分在前）
- [ ] 价格排序生效（最便宜在前）
- [ ] Top N限制生效（默认5个）

### 3. 模板输出质量
- [ ] 输出自然流畅，无机械感
- [ ] 多次查询有不同的表达方式
- [ ] 包含关键信息（名称、地址、距离/评分/价格）
- [ ] 格式清晰易读

### 4. 性能指标
- [ ] 规则处理延迟 < 100ms
- [ ] 总延迟（含API调用）< 2000ms
- [ ] 无明显卡顿

---

## 测试方法

### 方式1：通过API测试
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "北京市的鸟巢周边，最近的711是哪一家", "session_id": "test-001"}'
```

### 方式2：通过Python测试
```python
from agent_service.domain.location.parser import parse_location_intent
from agent_service.infra.tool_clients.mcp_gateway_v2 import MCPToolGatewayV2

# Parse intent
query = "北京市的鸟巢周边，最近的711是哪一家"
intent = parse_location_intent(query)
print(f"Intent: {intent.to_dict()}")

# Invoke with MCP
gateway = MCPToolGatewayV2()
result, intent = gateway.invoke_with_intent("find_nearby", query)
print(f"Result: {result.text}")
print(f"POIs: {len(result.raw.get('pois', []))}")
```

---

**测试时间**：2026-03-03  
**测试人**：待填写  
**测试结果**：待填写
