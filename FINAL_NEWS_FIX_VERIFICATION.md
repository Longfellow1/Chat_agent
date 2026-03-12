# 新闻查询修复 - 最终验证

## 问题
Query"最近有什么国际局势热点"被路由到reply（LLM直接回复），而不是get_news。

## 根本原因
规则路由中没有新闻关键词检测，导致这个query无法被规则处理，只能交给LLM。但4B模型可能无法正确识别。

## 修复方案
在规则路由中添加规则4：新闻关键词检测

```python
# ========== 规则 4：新闻关键词 ==========
if any(kw in query for kw in ["新闻", "热点", "热搜", "大事", "消息", "发生了什么", "国际局势"]):
    return ToolCall(
        tool=ToolType.GET_NEWS,
        params={"query": query},
        confidence=0.85
    )
```

## 验证结果
单元测试：3/3 通过 ✅

| Query | Expected | Actual | Status |
|-------|----------|--------|--------|
| 最近有什么国际局势热点 | get_news | get_news | ✅ |
| 最近有什么大事 | get_news | get_news | ✅ |
| 今天有什么新闻 | get_news | get_news | ✅ |

## 修改文件
- `agent_service/domain/intents/router_4b_with_logprobs.py`
  - 在`RuleBasedRouter.try_route()`中添加规则4

## 关键改进
- 新闻查询现在由规则路由直接处理，不再依赖LLM
- 提高了新闻查询的准确率和响应速度
- 避免了4B模型可能的误判

## 规则优先级（更新）
1. 排除法：纯闲聊检测
2. 规则0：旅游意图关键词
3. 规则1：目的地 + 时间
4. 规则2：位置 + 类别
5. 规则3：天气关键词
6. **规则4：新闻关键词** ← 新增
7. LLM兜底

## 下一步
- 运行200条评测，验证整体效果
- 检查是否有其他类似的问题
