# Project Structure（当前结构与落地目标）

## 1. 当前目录结构（as-is）
```text
evaluation/
├── Chatflow-Chat_2_0224-draft-1273/
│   └── Chatflow-Chat_2_0224-draft-1273/
│       └── workflow/
├── spec/
├── traces/
├── evaluation.py
├── testset_eval_1000_v3.csv
├── testset_eval_1000_v3_sample5p.csv
└── ...（历史评测产物 xlsx/csv/report）
```

## 2. 目标工程结构（to-be）
```text
evaluation/
├── agent_service/
│   ├── app/
│   │   ├── api/                # HTTP 路由与请求校验
│   │   ├── orchestrator/       # 主链路编排（pre -> llm -> tool -> post）
│   │   ├── policies/           # 安全、长度、拒答、降级策略
│   │   └── schemas/            # JSON 契约与数据模型
│   ├── domain/
│   │   ├── intents/            # 意图与决策模型
│   │   ├── tools/              # 工具协议定义
│   │   └── memory/             # V2 预留
│   ├── infra/
│   │   ├── llm_clients/        # LM Studio / Coze 适配
│   │   ├── tool_clients/       # weather/news/search/... 适配
│   │   ├── storage/            # Redis/Postgres
│   │   └── observability/      # trace/log/metrics
│   ├── skills/                 # 多skills扩展位（预留）
│   └── main.py                 # 服务启动入口
├── eval/
│   ├── evaluation.py           # 评测主脚本（现有脚本迁移）
│   ├── prompts/                # 裁判提示词版本
│   └── reports/                # 评测报告输出
├── datasets/
│   ├── single_turn/
│   └── multi_turn/
├── scripts/
│   ├── run_dev.sh
│   ├── run_eval_smoke.sh
│   └── run_eval_full.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── spec/
```

## 3. 开工顺序（第一批）
1. 搭建 `agent_service` 最小骨架与 `/chat` 接口。
2. 迁移 LLM 客户端（LM Studio、Coze）到统一 `llm_clients`。
3. 抽离工具调用协议与 6 类工具 adapter。
4. 接入 trace/log 与统一错误码。
5. 把 `evaluation.py` 移到 `eval/`，保留现有评测能力不回退。

## 4. 约束
- 前期不强切多skills执行器，只保留 `skills/` 接口与注册位。
- 所有新增能力必须走 schema 契约，不允许隐式字段漂移。
