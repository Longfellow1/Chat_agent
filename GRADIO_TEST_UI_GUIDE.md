# Gradio测试界面使用指南

## 快速启动

### 启动服务
```bash
.venv/bin/python gradio_test_ui.py
```

### 访问地址
```
http://localhost:7870
```

### 停止服务
按 `Ctrl+C` 停止服务

---

## 服务说明

- **端口**: 7870 (独立端口，不与主线8000冲突)
- **后端**: 使用CLI模式调用agent_service
- **环境**: 自动加载 `.env.agent` 配置

---

## 测试用例分类

### 1. 天气查询 (get_weather)
- 预期: `tool_call/get_weather`
- 示例:
  - 北京今天天气怎么样
  - 请查一下长沙下周二气温大概多少

### 2. 股票查询 (get_stock)
- 预期: `tool_call/get_stock`
- 示例:
  - 帮我看招商银行实时行情
  - 请查看比亚迪今天股价
  - 茅台现在多少钱

### 3. 新闻查询 (get_news)
- 预期: `tool_call/get_news`
- 示例:
  - 我想看今天国际局势热点
  - 我想看今天医药热点

### 4. 地点查询 (find_nearby)
- 预期: `tool_call/find_nearby`
- 示例:
  - 帮我找合肥天河周边的加油站
  - 济南解放碑附近有什么商场
  - 帮我找成都东部新城周边的景点
  - 帮我找福州和平路周边的停车场

### 5. 旅游规划 (plan_trip)
- 预期: `tool_call/plan_trip`
- 示例:
  - 帮我规划青岛4天旅游行程

### 6. 搜索查询 (web_search)
- 预期: `tool_call/web_search`
- 示例:
  - 请检索品牌口碑

### 7. 闲聊/知识 (reply)
- 预期: `reply`
- 示例:
  - 我好难过，能陪我聊聊吗
  - 请简单解释十二生肖
  - 用一句话说说你的功能
  - 我有点无聊陪我聊会儿

---

## 调试信息说明

界面右侧显示的调试信息包括:
- **决策模式**: tool_call / reply / reject
- **工具名称**: 调用的工具名
- **工具参数**: 传递给工具的参数
- **工具状态**: ok / fallback_or_error
- **工具提供商**: 实际使用的provider
- **路由来源**: llm_router / rule_override / rule_fastpath
- **提取来源**: location_intent / rule_or_router / llm_fallback
- **延迟(ms)**: 各阶段耗时统计
- **意图概率**: 路由器的意图分类概率

---

## 常见问题

### Q: 服务启动失败？
A: 检查端口7870是否被占用，或查看终端错误信息

### Q: 调用超时？
A: 默认超时30秒，检查后端LLM服务是否正常

### Q: 工具调用错误？
A: 查看调试信息中的 `tool_error` 字段，检查环境变量配置

---

## 文件位置

- 界面文件: `gradio_test_ui.py`
- 环境配置: `.env.agent`
- 后端服务: `agent_service/main.py`
