# agent_service

最小可运行的智能体服务骨架。

## 1) CLI 模式（单条）
```bash
cd /Users/Harland/Documents/evaluation
export AGENT_BACKEND=lmstudio
./scripts/run_agent_local.sh "今天天气怎么样"
```

## 2) HTTP 服务模式
```bash
cd /Users/Harland/Documents/evaluation
export AGENT_BACKEND=lmstudio
./scripts/run_agent_server.sh
```

默认监听 `0.0.0.0:8000`，可通过环境变量覆盖：
- `AGENT_HOST`
- `AGENT_PORT`

## 3) 接口
### 健康检查
```bash
curl -sS http://127.0.0.1:8000/health
```

### 对话接口
```bash
./scripts/call_chat_api.sh http://127.0.0.1:8000 "今天天气怎么样"
```

多轮（带上下文重写）示例：
```bash
./scripts/call_chat_api.sh http://127.0.0.1:8000 "郑州天气怎么样" demo-1
./scripts/call_chat_api.sh http://127.0.0.1:8000 "那边再查一下" demo-1
```

请求体：
```json
{
  "query": "今天天气怎么样",
  "session_id": "optional-but-recommended",
  "user_id": "optional"
}
```

`session_id` 用于上下文重写（指代消解、续问补全）。同一段对话请保持同一个 `session_id`。

响应体：
```json
{
  "code": "0",
  "message": "ok",
  "trace_id": "...",
  "data": { "decision_mode": "reply", "final_text": "..." }
}
```

## 4) 错误码（当前）
- `A0001`: invalid request
- `A0002`: invalid json body（预留）
- `A0003`: internal server error
- `A0004`: llm backend unavailable

## 5) Trace
- 每次请求生成或透传 `x-trace-id`
- 日志落在 `traces/agent_service_YYYYMMDD.jsonl`

## 6) 后端切换
### LM Studio
- `AGENT_BACKEND=lmstudio`
- `LM_STUDIO_BASE`（默认 `http://localhost:1234`）
- `LM_STUDIO_MODEL`（默认 `qwen2.5-7b-instruct-mlx`）

### Coze
- `AGENT_BACKEND=coze`
- `COZE_API_BASE`
- `COZE_BOT_ID`
- `COZE_API_TOKEN`

## 7) 工具 API（MCP 风格统一入口）
工具调用统一通过 `MCPToolGateway.invoke(name,args)`。
默认兜底顺序：
1. 主工具 API（如 AlphaVantage/和风/高德）
2. 联网搜索兜底（Tavily）
3. mock 最后兜底（避免主链路中断）

- 股票（Alpha Vantage）
  - `ALPHA_VANTAGE_API_KEY`
- Web 搜索 / 新闻（Tavily）
  - `TAVILY_API_KEY`
- 联网兜底开关
  - `ENABLE_NETWORK_FALLBACK=true|false`（默认 `true`）
- 天气（和风天气）
  - `QWEATHER_API_KEY`
  - `QWEATHER_API_HOST`（按和风控制台分配的 Host；未配置时默认 `devapi.qweather.com/geoapi.qweather.com`）
  - 未配置或失败时，优先走 Tavily 兜底，再退 mock
- 地图周边（高德地图）
  - `AMAP_API_KEY`
  - 未配置或失败时，优先走 Tavily 兜底，再退 mock


- 工具后续写开关
  - `TOOL_POST_LLM=true|false`（默认 `true`，表示工具结果返回后再经过一次 LLM 组织语言）
