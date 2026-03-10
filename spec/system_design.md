# System Design（技术架构）

## 1. 目标
将 `Chat_2_0224` 能力生产化，满足：高可用、可观测、可评测、可灰度、可回滚。

## 2. 架构原则
- 单次调用优先：单次 LLM 决策 + 规则后处理
- Deterministic First：能规则化的逻辑优先规则化
- Observable by Default：全链路 trace + metrics + logs
- Evolvable：路由模型、工具层、记忆层可插拔

## 3. 在线主链路
1. 输入预处理（规则审查：敏感/乱码/结束会话）
2. 单次 LLM 决策（结构化 JSON）
3. 工具执行（如需）
4. 输出后处理（安全/长度/格式）
5. 返回响应

## 4. JSON 契约（建议最小集）
```json
{
  "query": "...",
  "effective_query": "...",
  "intent_probs": {"1":0.0,"2":0.0,"3":0.0,"4":0.0,"5":0.0,"6":0.0,"7":0.0},
  "decision_mode": "reply|tool_call|reject|clarify|end_chat",
  "tool_name": "get_weather|null",
  "tool_args": {},
  "missing_slots": [],
  "risk_level": "none|low|medium|high",
  "final_text": "...",
  "latency_ms": {"llm": 0, "tools": 0, "total": 0}
}
```

## 5. 模型与推理服务
- 主模型：`qwen2.5-7B-8bit`
- v1 不拆独立路由模型
- v2 视评测结果引入 1-2B 路由模型（前置）

### Model Server 设计
- Inference Gateway：统一鉴权、超时、重试、熔断
- Policy Engine：按场景设置推理参数（路由低温、闲聊中温）
- Tool Adapter：工具白名单 + 参数校验 + 超时治理

## 6. 数据与存储
- 热数据：会话态（Redis）
- 业务数据：会话与记忆（PostgreSQL）
- 冷数据：评测与 trace（对象存储/数据仓）

## 7. 并发与可靠性
- 异步 I/O + worker 池
- 限流（用户/租户级）
- 熔断与降级（工具失败回退模板）
- 目标：可用性 99.9%，错误率 <1%

## 8. 安全设计
- 输入安全前置 + 输出安全后置
- 高风险命中强制覆盖模型输出
- 秘钥走 KMS/环境变量，不明文落盘

## 9. 可观测性
- 请求级 trace_id
- 节点级 span（预处理/LLM/工具/后处理）
- 在线指标：P50/P95、错误率、工具命中率、拒答率

## 10. 接入策略（Coze / 本地）
- 本地后端：LM Studio（OpenAI 兼容）
- Coze 后端：Bot Chat API（黑盒工具不可观测）
- Coze 下工具指标可置中性，主看任务达成与安全

## 11. 多Skills扩展预留（现阶段不强切）
- 当前执行原则：前期以现有架构为准（单次调用 + 规则编排）。
- 预留扩展位：
  - `skill_registry`：技能元数据注册（id/schema/version/owner/slo）
  - `skill_adapter`：统一调用协议（invoke/timeout/retry/fallback）
  - `skill_router_hook`：路由后置钩子，可按需将特定场景切到skill
- 渐进迁移策略：
  1) 先将实时工具链技能化（weather/news/search/stock/travel/nearby）
  2) 再将记忆、偏好能力技能化
  3) 路由模型与技能路由最终解耦
- 约束：未达到评测门禁前，不扩大技能编排自由度。

