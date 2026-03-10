# Query Rewrite 整合方案

## 文档概述

本文档分析 `query-rewrite-agents` 项目的整合方案，包括依赖评估、架构设计、代码规范和实施计划。

## 目录

1. [项目现状分析](#1-项目现状分析)
2. [代码规范总结](#2-代码规范总结)
3. [依赖分析](#3-依赖分析)
4. [架构整合方案](#4-架构整合方案)
5. [实施计划](#5-实施计划)
6. [风险评估](#6-风险评估)

---

## 1. 项目现状分析

### 1.1 当前项目结构

```
evaluation/
├── agent_service/          # 智能体服务（生产代码）
├── query-rewrite-agents/   # 重写模块（待整合）
├── Mcp_test/              # 高德MCP测试demo
├── evaluation.py          # 评测主脚本
├── datasets/              # 测试数据集
└── spec/                  # 项目文档
```

### 1.2 现有重写能力

**agent_service/app/orchestrator/rewrite.py**（简单规则）
- 指代消解：那边/那里 → 城市名
- 续问补全：继续/再查 → 补全上下文
- 泛化追问：帮我查 + 城市 → 具体查询

**query-rewrite-agents**（完整系统）
- LLM 语义重写
- 知识库检索增强（ES + BM25 + 向量）
- 规则 + LLM 混合策略
- 完整的评测体系

---

## 2. 代码规范总结

### 2.1 agent_service 代码规范

#### 类型注解规范
```python
# ✅ 推荐：使用 from __future__ import annotations
from __future__ import annotations

def execute(self, tool_name: str, tool_args: dict[str, Any]) -> ToolResult:
    pass

# ✅ 使用 Protocol 定义接口
from typing import Protocol

class LLMClient(Protocol):
    def generate(self, user_query: str, system_prompt: str) -> str:
        ...
```

#### 数据类规范
```python
# ✅ 使用 @dataclass 定义数据模型
from dataclasses import dataclass, field

@dataclass
class ChatResponse:
    query: str
    effective_query: str
    rewritten: int = 0
    tool_args: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

#### 错误处理规范
```python
# ✅ 捕获具体异常，使用 noqa 标记宽泛捕获
try:
    return self.gateway.invoke(tool_name=tool_name, tool_args=tool_args)
except Exception as e:  # noqa: BLE001
    return ToolResult(ok=False, text="工具调用失败", error=str(e))

# ✅ 业务异常使用 HTTPException
from fastapi import HTTPException

if not query:
    raise HTTPException(
        status_code=err.http_status,
        detail={"code": err.code, "message": err.message}
    )
```


#### 函数规范
```python
# ✅ 纯函数使用下划线前缀（私有辅助函数）
def _extract_json_object(text: str) -> dict[str, object] | None:
    pass

# ✅ 复杂逻辑拆分为小函数
def _build_merged_tool_plan(...) -> ToolPlan:
    # 1) fast path: rules + router llm args
    rule_args = extract_rule_tool_args(...)
    
    # 2) slow path: llm extractor fallback
    llm_extra = _extract_slots_with_llm(...)
    
    # 3) final fallback policy
    return ToolPlan(...)
```

#### 配置管理规范
```python
# ✅ 配置从环境变量读取，提供默认值
self.tool_post_llm = os.getenv("TOOL_POST_LLM", "true").strip().lower() == "true"
self.route_timeout_sec = float(os.getenv("ROUTE_LLM_TIMEOUT_SEC", "8"))

# ❌ 避免：配置硬编码在代码中
```

#### 日志规范
```python
# ✅ 避免使用 print，仅在 CLI 入口使用
# main.py
print(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))

# ❌ 业务代码中不使用 print
# ✅ 使用 trace 系统记录关键事件
```

### 2.2 evaluation.py 代码规范

#### 函数组织规范
```python
# ✅ 按阶段组织函数
def run_phase1(...) -> pd.DataFrame:
    """Phase 1: 批量推理"""
    pass

def run_phase2(...) -> pd.DataFrame:
    """Phase 2: 规则打分"""
    pass

def run_phase3(...) -> pd.DataFrame:
    """Phase 3: LLM Judge"""
    pass

# ✅ 辅助函数使用下划线前缀
def _safe_str(val, default=""):
    pass

def _rate(df: pd.DataFrame, col: str) -> str:
    pass
```

#### 类型提示规范
```python
# ✅ 使用类型提示（Dict, List, Any）
from typing import Dict, List, Any

def _mock_tool_execute(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    pass

# ✅ 使用 pd.DataFrame, pd.Series 类型
def score_row(row: pd.Series) -> Dict[str, Any]:
    pass
```

#### 错误处理规范
```python
# ✅ 使用 try-except 保护外部调用
try:
    resp = client.chat.completions.create(...)
except Exception as e:
    res["judge_error"] = str(e)
    return res
```

---

## 3. 依赖分析

### 3.1 核心依赖（必须）

#### LLM 推理
```txt
openai==1.78.1              # OpenAI 兼容接口
langchain==0.3.9            # LLM 编排框架
langchain-openai==0.3.16    # OpenAI 适配器
```

#### 检索增强（RAG）
```txt
elasticsearch==8.13.0       # 知识库存储（必须）
rank_bm25==0.2.2           # BM25 关键词检索
FlagEmbedding==1.2.9       # 嵌入模型（BGE系列）
faiss-cpu==1.8.0           # 向量检索（可选）
```

#### 基础设施
```txt
fastapi==0.110.2           # Web 服务
torch==2.7.0               # 深度学习框架
```

### 3.2 外部服务依赖

#### 🔴 强依赖（必须部署）

**1. Elasticsearch**
- 用途：知识库存储、BM25检索、历史对话索引
- 版本：8.x
- 配置：
  ```bash
  REWRITE_ES_HOST=http://localhost:9200
  REWRITE_ES_USER=elastic
  REWRITE_ES_PASSWORD=
  REWRITE_ES_INDEX=rewrite_knowledge
  ```
- 评估：**必须部署**，是核心检索引擎

**2. LLM 推理服务（微调模型）**
- 用途：语义重写、指代消解
- 接口：OpenAI 兼容（`/v1/chat/completions`）
- 部署方案：
  - **vLLM**（推荐）：高性能推理，支持 OpenAI 兼容接口
  - LM Studio：本地开发可用，生产不推荐
  - TGI（Text Generation Inference）：HuggingFace 官方方案
- 配置：
  ```bash
  REWRITE_LLM_BASE=http://localhost:8000/v1
  REWRITE_LLM_MODEL=rewrite-model
  REWRITE_LLM_TIMEOUT=5.0
  ```
- 评估：**必须部署**，微调模型需要通过 vLLM 暴露接口

**3. 嵌入模型服务**
- 用途：向量检索（如果启用）
- 模型：BGE 系列（`BAAI/bge-large-zh-v1.5`）
- 部署方案：
  - 本地加载（`FlagEmbedding`）
  - 远程服务（通过 `langchain_openai.OpenAIEmbeddings` 调用）
- 配置：
  ```bash
  REWRITE_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
  REWRITE_EMBEDDING_DEVICE=cpu  # cpu | cuda
  ```
- 评估：**可选**，如果只用 BM25 可以不部署


### 3.3 模型部署方案

#### 方案A：vLLM + 本地嵌入（推荐）

**部署步骤**：
```bash
# 1. 部署微调模型（vLLM）
docker run -d --gpus all \
  -p 8000:8000 \
  -v /path/to/your/model:/model \
  vllm/vllm-openai:latest \
  --model /model \
  --served-model-name rewrite-model \
  --max-model-len 4096

# 2. 嵌入模型（本地加载）
# 在 agent_service 中直接使用 FlagEmbedding
```

**优点**：
- vLLM 性能最优（PagedAttention、连续批处理）
- OpenAI 兼容接口，无需改代码
- 嵌入模型本地加载，无额外服务

**缺点**：
- 需要 GPU（至少 1 张 A10/V100）
- 首次加载模型较慢

#### 方案B：TGI + 远程嵌入

**部署步骤**：
```bash
# 1. 部署微调模型（TGI）
docker run -d --gpus all \
  -p 8080:80 \
  -v /path/to/your/model:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id /data \
  --max-input-length 2048 \
  --max-total-tokens 4096

# 2. 嵌入模型（远程服务）
# 需要单独部署嵌入服务（如 TEI）
```

**优点**：
- HuggingFace 官方支持
- 嵌入服务可独立扩展

**缺点**：
- 性能略低于 vLLM
- 需要部署两个服务

---

## 4. 架构整合方案

### 4.1 目标架构

```
evaluation/
├── agent_service/
│   ├── app/
│   │   ├── orchestrator/
│   │   │   ├── chat_flow.py          # 主流程（已有）
│   │   │   └── rewrite.py            # 简单规则重写（已有）
│   ├── domain/
│   │   ├── rewrite/                  # 新增：重写领域
│   │   │   ├── __init__.py
│   │   │   ├── rewriter.py           # 重写器接口
│   │   │   ├── rule_rewriter.py      # 规则重写（迁移现有）
│   │   │   ├── llm_rewriter.py       # LLM 重写（整合 query-rewrite-agents）
│   │   │   └── hybrid_rewriter.py    # 混合策略（规则优先 + LLM 兜底）
│   ├── infra/
│   │   ├── rewrite_clients/          # 新增：重写基础设施
│   │   │   ├── __init__.py
│   │   │   ├── es_knowledge.py       # ES 知识库适配
│   │   │   ├── embedding_service.py  # 嵌入服务
│   │   │   └── retriever.py          # 检索器（BM25 + 向量）
│   │   └── config.py                 # 统一配置（新增 rewrite 配置）
├── query-rewrite-agents/             # 保留：作为参考和资源
│   ├── data/                         # 评测数据
│   ├── docs/                         # PRD 文档
│   └── pilot/agents/query_rewrite_agent/
│       ├── prompts/                  # 提示词模板（复用）
│       └── utils/                    # 规则工具（复用）
```

### 4.2 接口设计

#### Rewriter 接口（遵循 agent_service 规范）

```python
# agent_service/domain/rewrite/rewriter.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

@dataclass
class RewriteContext:
    """重写上下文"""
    query: str
    history: list[dict[str, object]]
    session_id: str | None = None

@dataclass
class RewriteResult:
    """重写结果"""
    effective_query: str
    rewritten: bool
    source: str  # "rule" | "llm" | "hybrid"
    confidence: float = 1.0
    debug_info: dict[str, object] | None = None

class Rewriter(Protocol):
    """重写器接口"""
    def rewrite(self, ctx: RewriteContext) -> RewriteResult:
        ...
```

#### 规则重写器（迁移现有逻辑）

```python
# agent_service/domain/rewrite/rule_rewriter.py
from __future__ import annotations

from .rewriter import Rewriter, RewriteContext, RewriteResult

class RuleRewriter(Rewriter):
    """基于规则的快速重写（迁移自 app/orchestrator/rewrite.py）"""
    
    def rewrite(self, ctx: RewriteContext) -> RewriteResult:
        q = ctx.query.strip()
        if not q or not ctx.history:
            return RewriteResult(effective_query=q, rewritten=False, source="rule")
        
        # 从历史中提取上下文
        session_ctx = self._build_session_context(ctx.history)
        
        # 1. 指代消解（那边/那里 -> 城市名）
        city = session_ctx.get("last_city")
        if city and any(k in q for k in ("那边", "那里", "那儿", "这边", "这里")):
            rewritten = q
            for k in ("那边", "那里", "那儿", "这边", "这里"):
                rewritten = rewritten.replace(k, str(city))
            return RewriteResult(
                effective_query=rewritten,
                rewritten=True,
                source="rule",
                confidence=0.95
            )
        
        # 2. 续问补全（继续/再查 -> 补全上下文）
        if self._is_followup_short(q):
            last_tool = session_ctx.get("last_tool")
            if last_tool:
                rebuilt = self._rebuild_from_last_tool(last_tool, session_ctx)
                if rebuilt:
                    return RewriteResult(
                        effective_query=rebuilt,
                        rewritten=True,
                        source="rule",
                        confidence=0.9
                    )
        
        return RewriteResult(effective_query=q, rewritten=False, source="rule")
    
    def _build_session_context(self, history: list[dict[str, object]]) -> dict[str, object]:
        """从历史对话构建会话上下文"""
        if not history:
            return {}
        last = history[-1]
        return {
            "last_city": last.get("city"),
            "last_tool": last.get("tool_name"),
            "last_topic": last.get("topic"),
            "last_target": last.get("target"),
        }
    
    def _is_followup_short(self, q: str) -> bool:
        keys = ("继续", "再查", "再看", "再来", "帮我查查", "查查", "看下", "看看")
        return len(q) <= 12 and any(k in q for k in keys)
    
    def _rebuild_from_last_tool(
        self,
        last_tool: str,
        ctx: dict[str, object]
    ) -> str:
        """根据上一次工具调用重建查询"""
        city = ctx.get("last_city")
        topic = ctx.get("last_topic")
        target = ctx.get("last_target")
        
        if last_tool == "get_weather" and city:
            return f"{city}今天天气怎么样"
        if last_tool == "get_news":
            t = topic or "今日热点"
            return f"查一下{t}新闻"
        if last_tool == "get_stock":
            t = target or "上证指数"
            return f"查一下{t}最新行情"
        return ""
```


#### LLM 重写器（整合 query-rewrite-agents）

```python
# agent_service/domain/rewrite/llm_rewriter.py
from __future__ import annotations

from .rewriter import Rewriter, RewriteContext, RewriteResult
from infra.rewrite_clients.retriever import KnowledgeRetriever
from infra.llm_clients.base import LLMClient

class LLMRewriter(Rewriter):
    """基于 LLM 的语义重写（整合 query-rewrite-agents 核心逻辑）"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        retriever: KnowledgeRetriever | None = None,
        enable_knowledge: bool = False,
        timeout_sec: float = 5.0
    ) -> None:
        self.llm = llm_client
        self.retriever = retriever
        self.enable_knowledge = enable_knowledge
        self.timeout_sec = timeout_sec
    
    def rewrite(self, ctx: RewriteContext) -> RewriteResult:
        # 1. 检索相关知识（如果启用）
        knowledge = []
        if self.enable_knowledge and self.retriever:
            try:
                knowledge = self.retriever.retrieve(ctx.query, top_k=3)
            except Exception as e:  # noqa: BLE001
                # 检索失败不影响重写
                pass
        
        # 2. 构建提示词（复用 query-rewrite-agents 的 prompt）
        prompt = self._build_prompt(ctx, knowledge)
        
        # 3. 调用 LLM
        try:
            if hasattr(self.llm, "generate_with_timeout"):
                response = self.llm.generate_with_timeout(  # type: ignore[attr-defined]
                    user_query=prompt,
                    system_prompt=self._system_prompt(),
                    timeout_sec=self.timeout_sec
                )
            else:
                response = self.llm.generate(
                    user_query=prompt,
                    system_prompt=self._system_prompt()
                )
        except Exception as e:  # noqa: BLE001
            # LLM 失败返回原查询
            return RewriteResult(
                effective_query=ctx.query,
                rewritten=False,
                source="llm",
                confidence=0.0,
                debug_info={"error": str(e)}
            )
        
        # 4. 解析结果
        return self._parse_response(response, ctx.query)
    
    def _build_prompt(
        self,
        ctx: RewriteContext,
        knowledge: list[str]
    ) -> str:
        """构建 LLM 提示词"""
        history_text = ""
        if ctx.history:
            lines = []
            for i, turn in enumerate(ctx.history[-3:], 1):  # 最近3轮
                q = turn.get("query", "")
                a = turn.get("answer", "")
                lines.append(f"第{i}轮 - 用户: {q}")
                lines.append(f"第{i}轮 - 助手: {a}")
            history_text = "\n".join(lines)
        
        knowledge_text = ""
        if knowledge:
            knowledge_text = "\n相关知识：\n" + "\n".join(f"- {k}" for k in knowledge)
        
        return f"""当前用户输入：{ctx.query}

历史对话：
{history_text if history_text else "（无历史）"}
{knowledge_text}

请根据历史对话和相关知识，对当前用户输入进行重写，补全省略的信息。
如果不需要重写，直接返回原输入。

输出格式（JSON）：
{{"rewritten_query": "重写后的查询", "rewritten": true/false, "confidence": 0.0-1.0}}
"""
    
    def _system_prompt(self) -> str:
        """系统提示词（复用 query-rewrite-agents）"""
        return """你是查询重写助手。你的任务是：
1. 根据历史对话补全指代词（他/她/它/那边/这里等）
2. 补全省略的实体（城市、人名、主题等）
3. 保持原意，不要改变用户意图
4. 如果不需要重写，返回原查询

只输出 JSON，不要输出其他内容。"""
    
    def _parse_response(self, response: str, original_query: str) -> RewriteResult:
        """解析 LLM 响应"""
        import json
        import re
        
        # 尝试解析 JSON
        try:
            # 提取 JSON 对象
            match = re.search(r'\{[^}]+\}', response)
            if match:
                obj = json.loads(match.group(0))
                rewritten_query = obj.get("rewritten_query", original_query)
                rewritten = bool(obj.get("rewritten", False))
                confidence = float(obj.get("confidence", 0.8))
                
                return RewriteResult(
                    effective_query=rewritten_query,
                    rewritten=rewritten,
                    source="llm",
                    confidence=confidence
                )
        except Exception:  # noqa: BLE001
            pass
        
        # 解析失败，返回原查询
        return RewriteResult(
            effective_query=original_query,
            rewritten=False,
            source="llm",
            confidence=0.0,
            debug_info={"parse_error": "failed to parse LLM response"}
        )
```

#### 混合策略重写器（生产推荐）

```python
# agent_service/domain/rewrite/hybrid_rewriter.py
from __future__ import annotations

from .rewriter import Rewriter, RewriteContext, RewriteResult
from .rule_rewriter import RuleRewriter
from .llm_rewriter import LLMRewriter

class HybridRewriter(Rewriter):
    """混合策略：规则优先 + LLM 兜底"""
    
    def __init__(
        self,
        rule_rewriter: RuleRewriter,
        llm_rewriter: LLMRewriter,
        rule_confidence_threshold: float = 0.8
    ) -> None:
        self.rule = rule_rewriter
        self.llm = llm_rewriter
        self.threshold = rule_confidence_threshold
    
    def rewrite(self, ctx: RewriteContext) -> RewriteResult:
        # 1. 先尝试规则重写（快速路径）
        rule_result = self.rule.rewrite(ctx)
        if rule_result.rewritten and rule_result.confidence >= self.threshold:
            return rule_result
        
        # 2. 规则不适用或置信度低，走 LLM
        llm_result = self.llm.rewrite(ctx)
        
        # 3. 如果 LLM 也失败，返回规则结果（降级）
        if not llm_result.rewritten or llm_result.confidence < 0.5:
            return rule_result if rule_result.rewritten else llm_result
        
        # 4. 返回 LLM 结果，标记为混合策略
        llm_result.source = "hybrid"
        return llm_result
```

### 4.3 配置管理（遵循 agent_service 规范）

```python
# agent_service/infra/config.py
from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass
class RewriteConfig:
    """重写模块配置"""
    
    # 重写策略
    strategy: str  # "rule" | "llm" | "hybrid"
    rule_confidence_threshold: float
    
    # LLM 配置（微调模型）
    llm_base: str
    llm_model: str
    llm_timeout: float
    
    # 知识库配置
    enable_knowledge: bool
    es_host: str
    es_user: str
    es_password: str
    es_index: str
    
    # 嵌入模型配置
    embedding_model: str
    embedding_device: str  # "cpu" | "cuda"
    
    # 检索配置
    retrieval_top_k: int
    enable_rerank: bool
    
    @classmethod
    def from_env(cls) -> RewriteConfig:
        """从环境变量加载配置"""
        return cls(
            strategy=os.getenv("REWRITE_STRATEGY", "hybrid"),
            rule_confidence_threshold=float(os.getenv("REWRITE_RULE_THRESHOLD", "0.8")),
            llm_base=os.getenv("REWRITE_LLM_BASE", "http://localhost:8000/v1"),
            llm_model=os.getenv("REWRITE_LLM_MODEL", "rewrite-model"),
            llm_timeout=float(os.getenv("REWRITE_LLM_TIMEOUT", "5.0")),
            enable_knowledge=os.getenv("REWRITE_ENABLE_KNOWLEDGE", "false").lower() == "true",
            es_host=os.getenv("REWRITE_ES_HOST", "http://localhost:9200"),
            es_user=os.getenv("REWRITE_ES_USER", "elastic"),
            es_password=os.getenv("REWRITE_ES_PASSWORD", ""),
            es_index=os.getenv("REWRITE_ES_INDEX", "rewrite_knowledge"),
            embedding_model=os.getenv("REWRITE_EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"),
            embedding_device=os.getenv("REWRITE_EMBEDDING_DEVICE", "cpu"),
            retrieval_top_k=int(os.getenv("REWRITE_RETRIEVAL_TOP_K", "5")),
            enable_rerank=os.getenv("REWRITE_ENABLE_RERANK", "false").lower() == "true",
        )
```


### 4.4 工厂模式改造

```python
# agent_service/app/factory.py
from __future__ import annotations

import os
from functools import lru_cache

from app.orchestrator.chat_flow import ChatFlow
from domain.tools.executor import ToolExecutor
from domain.rewrite.rewriter import Rewriter
from domain.rewrite.rule_rewriter import RuleRewriter
from domain.rewrite.llm_rewriter import LLMRewriter
from domain.rewrite.hybrid_rewriter import HybridRewriter
from infra.llm_clients.coze_client import CozeClient
from infra.llm_clients.lm_studio_client import LMStudioClient
from infra.llm_clients.base import LLMClient
from infra.storage.session_store import InMemorySessionStore
from infra.config import RewriteConfig

@lru_cache(maxsize=1)
def build_flow() -> ChatFlow:
    """构建 ChatFlow（单例）"""
    tool_executor = ToolExecutor()
    session_store = InMemorySessionStore(
        ttl_seconds=int(os.getenv("SESSION_TTL_SEC", "1800"))
    )
    
    # 构建主 LLM 客户端
    llm_client = _build_llm_client()
    
    # 构建重写器（可选）
    rewriter = _build_rewriter(llm_client)
    
    return ChatFlow(
        llm_client=llm_client,
        tool_executor=tool_executor,
        session_store=session_store,
        rewriter=rewriter
    )

def _build_llm_client() -> LLMClient:
    """构建 LLM 客户端"""
    backend = os.getenv("AGENT_BACKEND", "lmstudio").strip().lower()
    if backend == "coze":
        return CozeClient()
    return LMStudioClient()

def _build_rewriter(llm_client: LLMClient) -> Rewriter | None:
    """构建重写器"""
    config = RewriteConfig.from_env()
    
    if config.strategy == "rule":
        return RuleRewriter()
    
    if config.strategy == "llm":
        # 构建 LLM 重写器（需要单独的 LLM 客户端）
        rewrite_llm = _build_rewrite_llm_client(config)
        retriever = _build_retriever(config) if config.enable_knowledge else None
        return LLMRewriter(
            llm_client=rewrite_llm,
            retriever=retriever,
            enable_knowledge=config.enable_knowledge,
            timeout_sec=config.llm_timeout
        )
    
    if config.strategy == "hybrid":
        rule_rewriter = RuleRewriter()
        rewrite_llm = _build_rewrite_llm_client(config)
        retriever = _build_retriever(config) if config.enable_knowledge else None
        llm_rewriter = LLMRewriter(
            llm_client=rewrite_llm,
            retriever=retriever,
            enable_knowledge=config.enable_knowledge,
            timeout_sec=config.llm_timeout
        )
        return HybridRewriter(
            rule_rewriter=rule_rewriter,
            llm_rewriter=llm_rewriter,
            rule_confidence_threshold=config.rule_confidence_threshold
        )
    
    # 默认不启用重写
    return None

def _build_rewrite_llm_client(config: RewriteConfig) -> LLMClient:
    """构建重写专用 LLM 客户端"""
    # 使用 LMStudioClient 连接 vLLM
    from infra.llm_clients.lm_studio_client import LMStudioClient
    return LMStudioClient(
        base_url=config.llm_base,
        model=config.llm_model
    )

def _build_retriever(config: RewriteConfig):
    """构建知识库检索器"""
    from infra.rewrite_clients.retriever import KnowledgeRetriever
    from infra.rewrite_clients.es_knowledge import ESKnowledgeStore
    from infra.rewrite_clients.embedding_service import EmbeddingService
    
    # ES 知识库
    es_store = ESKnowledgeStore(
        host=config.es_host,
        user=config.es_user,
        password=config.es_password,
        index=config.es_index
    )
    
    # 嵌入服务
    embedding = EmbeddingService(
        model=config.embedding_model,
        device=config.embedding_device
    )
    
    return KnowledgeRetriever(
        knowledge_store=es_store,
        embedding_service=embedding,
        top_k=config.retrieval_top_k,
        enable_rerank=config.enable_rerank
    )
```

### 4.5 ChatFlow 集成

```python
# agent_service/app/orchestrator/chat_flow.py（修改）
from __future__ import annotations

from domain.rewrite.rewriter import Rewriter, RewriteContext

class ChatFlow:
    def __init__(
        self,
        llm_client: LLMClient,
        tool_executor: ToolExecutor,
        session_store: InMemorySessionStore,
        rewriter: Rewriter | None = None  # 新增
    ) -> None:
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.session_store = session_store
        self.rewriter = rewriter  # 新增
        # ... 其他配置 ...
    
    def run(self, req: ChatRequest) -> ChatResponse:
        t0 = time.perf_counter()
        query = req.query.strip()
        
        # 0) rewrite with session context
        effective_query = query
        rewrite_source = "none"
        rewritten = 0
        
        if self.rewriter and req.session_id:
            # 获取历史对话
            history = self._get_history(req.session_id)
            
            # 调用重写器
            ctx = RewriteContext(
                query=query,
                history=history,
                session_id=req.session_id
            )
            result = self.rewriter.rewrite(ctx)
            
            effective_query = result.effective_query
            rewritten = int(result.rewritten)
            rewrite_source = result.source
        
        # ... 后续逻辑保持不变 ...
    
    def _get_history(self, session_id: str) -> list[dict[str, object]]:
        """获取历史对话"""
        session_ctx = self.session_store.get(session_id)
        # 从 session_ctx 构建历史对话列表
        # 这里需要根据实际存储结构调整
        return []
```

---

## 5. 实施计划

### 5.1 Phase 1：接口抽象 + 规则迁移（1-2天）

**目标**：建立重写模块基础架构，迁移现有规则重写

**任务清单**：
- [ ] 创建 `domain/rewrite/` 模块结构
- [ ] 定义 `Rewriter` 接口（`rewriter.py`）
- [ ] 实现 `RuleRewriter`（迁移 `app/orchestrator/rewrite.py`）
- [ ] 添加单元测试（`tests/unit/test_rule_rewriter.py`）
- [ ] 在 `ChatFlow` 中集成 `RuleRewriter`
- [ ] 验证现有功能不回退

**验收标准**：
- 所有现有重写测试用例通过
- 新增至少 5 个单元测试
- 代码覆盖率 >= 80%

### 5.2 Phase 2：LLM 重写器（3-5天）

**目标**：整合 query-rewrite-agents 的 LLM 重写能力

**前置条件**：
- vLLM 部署完成（微调模型可访问）

**任务清单**：
- [ ] 部署 vLLM（微调模型）
- [ ] 创建 `RewriteConfig` 配置类
- [ ] 实现 `LLMRewriter`（复用 query-rewrite-agents 的 prompt）
- [ ] 添加集成测试（`tests/integration/test_llm_rewriter.py`）
- [ ] 配置环境变量（`.env.agent`）
- [ ] 对比评测（规则 vs LLM）

**验收标准**：
- LLM 重写器可独立运行
- 重写准确率 >= 85%（基于评测集）
- 平均时延 <= 500ms

### 5.3 Phase 3：混合策略（2天）

**目标**：实现生产级混合策略

**任务清单**：
- [ ] 实现 `HybridRewriter`
- [ ] 添加策略切换配置（`REWRITE_STRATEGY`）
- [ ] 改造 `factory.py`（支持策略选择）
- [ ] 添加 E2E 测试（`tests/e2e/test_rewrite_strategies.py`）
- [ ] 性能对比评测（规则 vs LLM vs 混合）

**验收标准**：
- 混合策略准确率 >= 90%
- 80% 请求走规则快速路径（<10ms）
- 20% 复杂请求走 LLM（<500ms）

### 5.4 Phase 4：知识库增强（可选，2-3周）

**目标**：集成 ES 知识库检索

**前置条件**：
- Elasticsearch 部署完成

**任务清单**：
- [ ] 部署 Elasticsearch
- [ ] 实现 `ESKnowledgeStore`（ES 适配器）
- [ ] 实现 `EmbeddingService`（嵌入模型）
- [ ] 实现 `KnowledgeRetriever`（BM25 + 向量检索）
- [ ] 导入知识库数据（复用 query-rewrite-agents 的数据）
- [ ] 添加检索评测

**验收标准**：
- 检索召回率 >= 80%
- 检索时延 <= 200ms
- 重写准确率提升 >= 5%

---

## 6. 风险评估

### 6.1 技术风险

| 风险项 | 影响 | 概率 | 缓解措施 |
|--------|------|------|----------|
| vLLM 部署失败 | 高 | 中 | 先用 LM Studio 开发，生产再切 vLLM |
| 微调模型效果不佳 | 高 | 中 | 保留规则重写作为兜底 |
| ES 依赖过重 | 中 | 低 | Phase 1-3 不启用知识库，先验证 LLM 效果 |
| 性能开销（LLM 推理） | 中 | 高 | 混合策略：规则快速路径 + LLM 兜底 |
| 配置管理复杂 | 低 | 中 | 使用 Pydantic 统一配置，启动时校验 |

### 6.2 项目风险

| 风险项 | 影响 | 概率 | 缓解措施 |
|--------|------|------|----------|
| 时间估算不准 | 中 | 中 | 渐进式交付，Phase 1-2 为核心，Phase 4 可延后 |
| 代码规范不一致 | 低 | 低 | 严格遵循 agent_service 规范，Code Review |
| 测试覆盖不足 | 中 | 中 | 每个 Phase 强制要求测试，覆盖率 >= 80% |
| 依赖冲突 | 低 | 低 | 使用虚拟环境隔离，requirements.txt 锁定版本 |

---

## 7. 部署清单

### 7.1 最小部署（规则重写）

```bash
# 无需额外服务，直接使用现有规则
export REWRITE_STRATEGY=rule
```

### 7.2 标准部署（LLM 重写，无知识库）

```bash
# 1. 部署微调模型（vLLM）
docker run -d --name rewrite-llm --gpus all \
  -p 8000:8000 \
  -v /path/to/model:/model \
  vllm/vllm-openai:latest \
  --model /model --served-model-name rewrite-model

# 2. 配置环境变量
export REWRITE_STRATEGY=llm
export REWRITE_LLM_BASE=http://localhost:8000/v1
export REWRITE_LLM_MODEL=rewrite-model
export REWRITE_ENABLE_KNOWLEDGE=false
```

### 7.3 完整部署（LLM + 知识库）

```bash
# 1. 部署 Elasticsearch
docker run -d --name rewrite-es \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.13.0

# 2. 部署微调模型（vLLM）
docker run -d --name rewrite-llm --gpus all \
  -p 8000:8000 \
  -v /path/to/model:/model \
  vllm/vllm-openai:latest \
  --model /model --served-model-name rewrite-model

# 3. 配置环境变量
export REWRITE_STRATEGY=hybrid
export REWRITE_LLM_BASE=http://localhost:8000/v1
export REWRITE_ENABLE_KNOWLEDGE=true
export REWRITE_ES_HOST=http://localhost:9200
export REWRITE_EMBEDDING_DEVICE=cuda  # 如果有 GPU
```

---

## 8. 评测方案

### 8.1 评测指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| 重写准确率 | 重写后查询符合预期的比例 | >= 90% |
| 规则覆盖率 | 规则重写命中的比例 | >= 80% |
| LLM 准确率 | LLM 重写准确的比例 | >= 85% |
| 平均时延 | 重写模块平均耗时 | <= 100ms（规则）<br><= 500ms（LLM） |
| P95 时延 | 95% 请求的时延 | <= 200ms（规则）<br><= 800ms（LLM） |

### 8.2 评测数据集

复用 `query-rewrite-agents/data/` 中的评测数据：
- 指代消解：100 条
- 续问补全：100 条
- 实体补全：100 条
- 负例（不需要重写）：50 条

### 8.3 评测脚本

```python
# scripts/eval_rewrite.py
"""重写模块评测脚本"""

import pandas as pd
from agent_service.domain.rewrite.rule_rewriter import RuleRewriter
from agent_service.domain.rewrite.llm_rewriter import LLMRewriter
from agent_service.domain.rewrite.hybrid_rewriter import HybridRewriter

def eval_rewriter(rewriter, testset_path: str):
    df = pd.read_csv(testset_path)
    results = []
    
    for _, row in df.iterrows():
        ctx = RewriteContext(
            query=row["query"],
            history=eval(row["history"]),  # JSON string to list
            session_id=row.get("session_id")
        )
        
        result = rewriter.rewrite(ctx)
        
        # 判断准确性
        expected = row["expected_rewrite"]
        correct = result.effective_query == expected
        
        results.append({
            "sample_id": row["sample_id"],
            "query": row["query"],
            "expected": expected,
            "actual": result.effective_query,
            "correct": correct,
            "source": result.source,
            "confidence": result.confidence
        })
    
    # 计算指标
    df_result = pd.DataFrame(results)
    accuracy = df_result["correct"].mean()
    
    print(f"准确率: {accuracy:.2%}")
    print(f"重写率: {df_result['actual'].ne(df_result['query']).mean():.2%}")
    
    return df_result

if __name__ == "__main__":
    # 评测规则重写器
    rule_rewriter = RuleRewriter()
    eval_rewriter(rule_rewriter, "datasets/rewrite_test.csv")
```

---

## 9. 总结

### 9.1 核心价值

1. **渐进式整合**：不破坏现有功能，逐步增强重写能力
2. **灵活配置**：支持规则/LLM/混合三种策略，按需选择
3. **生产就绪**：混合策略兼顾性能和准确性
4. **可观测性**：完整的 trace 和评测体系

### 9.2 关键决策

1. **保留 query-rewrite-agents**：作为参考和资源库，不删除
2. **遵循 agent_service 规范**：类型注解、错误处理、配置管理
3. **优先规则重写**：80% 场景走规则快速路径
4. **LLM 作为兜底**：20% 复杂场景走 LLM
5. **知识库可选**：Phase 4 按需启用

### 9.3 下一步行动

1. Review 本文档，确认技术方案
2. 部署 vLLM（微调模型）
3. 开始 Phase 1 实施（接口抽象 + 规则迁移）

---

**文档版本**：v1.0  
**创建日期**：2026-03-03  
**作者**：Kiro AI Assistant  
**审核状态**：待审核
