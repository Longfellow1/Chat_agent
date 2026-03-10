"""
对话记忆实现对比

展示：自己实现 vs LangChain Memory 的性能和成本对比
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum


# ============================================================================
# 方案1：自己实现（推荐）
# ============================================================================

class ToolType(str, Enum):
    PLAN_TRIP = "plan_trip"
    FIND_NEARBY = "find_nearby"
    WEB_SEARCH = "web_search"


@dataclass
class ConversationContext:
    """对话上下文"""
    conversation_id: str
    active_intent: Optional[ToolType] = None
    partial_params: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    last_error: Optional[str] = None
    intent_transitions: List[Dict] = field(default_factory=list)
    
    def merge_params(self, new_params: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        merged = self.partial_params.copy()
        merged.update(new_params)
        return merged
    
    def record_transition(self, from_tool: Optional[ToolType], to_tool: ToolType):
        """记录意图转移"""
        if from_tool != to_tool:
            self.intent_transitions.append({
                "from": from_tool.value if from_tool else None,
                "to": to_tool.value,
                "timestamp": time.time()
            })
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "conversation_id": self.conversation_id,
            "active_intent": self.active_intent.value if self.active_intent else None,
            "partial_params": self.partial_params,
            "turn_count": self.turn_count,
            "last_error": self.last_error,
            "intent_transitions": self.intent_transitions,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        """从字典构建"""
        ctx = cls(
            conversation_id=data["conversation_id"],
            active_intent=ToolType(data["active_intent"]) if data.get("active_intent") else None,
            partial_params=data.get("partial_params", {}),
            turn_count=data.get("turn_count", 0),
            last_error=data.get("last_error"),
            intent_transitions=data.get("intent_transitions", []),
        )
        return ctx


class ConversationMemoryV1:
    """
    方案1：自己实现（推荐）
    
    优点：
    - 轻量级（无外部依赖）
    - 快速（内存操作）
    - 完全可控
    - 成本低（无额外LLM调用）
    
    缺点：
    - 无持久化（需要自己实现）
    - 无自动总结
    """
    
    def __init__(self, max_turns: int = 10):
        self.contexts: Dict[str, ConversationContext] = {}
        self.max_turns = max_turns
        self.stats = {
            "get_context_calls": 0,
            "save_context_calls": 0,
            "total_time_ms": 0,
        }
    
    def get_context(self, conversation_id: str) -> ConversationContext:
        """获取对话上下文"""
        start = time.time()
        
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id)
        
        ctx = self.contexts[conversation_id]
        
        elapsed = (time.time() - start) * 1000
        self.stats["get_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
        
        return ctx
    
    def save_context(self, conversation_id: str, ctx: ConversationContext):
        """保存对话上下文"""
        start = time.time()
        
        self.contexts[conversation_id] = ctx
        
        elapsed = (time.time() - start) * 1000
        self.stats["save_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        # 计算内存占用
        contexts_dict = {k: v.to_dict() for k, v in self.contexts.items()}
        memory_size = len(json.dumps(contexts_dict)) / 1024 / 1024
        
        return {
            **self.stats,
            "avg_time_ms": self.stats["total_time_ms"] / max(1, self.stats["get_context_calls"] + self.stats["save_context_calls"]),
            "memory_size_mb": memory_size,
        }


# ============================================================================
# 方案2：LangChain Memory 模拟
# ============================================================================

class ConversationMemoryV2_LangChain:
    """
    方案2：LangChain Memory 模拟
    
    优点：
    - 开箱即用
    - 支持多种后端
    - 自动总结（但需要额外LLM调用）
    
    缺点：
    - 成本高（每次总结需要LLM调用）
    - 复杂度高
    - 总结质量不可控
    """
    
    def __init__(self, llm_client=None, max_turns: int = 10):
        self.contexts: Dict[str, ConversationContext] = {}
        self.llm_client = llm_client
        self.max_turns = max_turns
        self.stats = {
            "get_context_calls": 0,
            "save_context_calls": 0,
            "summarize_calls": 0,
            "total_time_ms": 0,
            "llm_calls": 0,
            "llm_time_ms": 0,
        }
    
    def get_context(self, conversation_id: str) -> ConversationContext:
        """获取对话上下文"""
        start = time.time()
        
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id)
        
        ctx = self.contexts[conversation_id]
        
        elapsed = (time.time() - start) * 1000
        self.stats["get_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
        
        return ctx
    
    def save_context(self, conversation_id: str, ctx: ConversationContext):
        """保存对话上下文"""
        start = time.time()
        
        self.contexts[conversation_id] = ctx
        
        # 如果对话太长，自动总结
        if ctx.turn_count > self.max_turns:
            self._summarize_context(conversation_id)
        
        elapsed = (time.time() - start) * 1000
        self.stats["save_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
    
    def _summarize_context(self, conversation_id: str):
        """总结对话（模拟LLM调用）"""
        start = time.time()
        
        # 模拟LLM调用（实际需要100-200ms）
        if self.llm_client:
            # 实际调用LLM进行总结
            # summary = self.llm_client.call(...)
            # 这里模拟成本
            time.sleep(0.1)  # 模拟100ms延迟
        
        elapsed = (time.time() - start) * 1000
        self.stats["summarize_calls"] += 1
        self.stats["llm_calls"] += 1
        self.stats["llm_time_ms"] += elapsed
        self.stats["total_time_ms"] += elapsed
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        # 计算内存占用
        contexts_dict = {k: v.to_dict() for k, v in self.contexts.items()}
        memory_size = len(json.dumps(contexts_dict)) / 1024 / 1024
        
        return {
            **self.stats,
            "avg_time_ms": self.stats["total_time_ms"] / max(1, self.stats["get_context_calls"] + self.stats["save_context_calls"]),
            "memory_size_mb": memory_size,
            "llm_cost_estimate": self.stats["llm_calls"] * 0.001,  # 假设每次LLM调用成本0.001元
        }


# ============================================================================
# 方案3：混合方案（推荐）
# ============================================================================

class ConversationMemoryV3_Hybrid:
    """
    方案3：混合方案（推荐）
    
    优点：
    - 轻量级（内存 + 可选Redis）
    - 支持持久化
    - 支持意图转移分析
    - 无额外LLM调用
    
    缺点：
    - 需要Redis（可选）
    """
    
    def __init__(self, redis_client=None, max_turns: int = 10):
        self.contexts: Dict[str, ConversationContext] = {}
        self.redis = redis_client
        self.max_turns = max_turns
        self.stats = {
            "get_context_calls": 0,
            "save_context_calls": 0,
            "redis_hits": 0,
            "redis_misses": 0,
            "total_time_ms": 0,
        }
    
    def get_context(self, conversation_id: str) -> ConversationContext:
        """获取对话上下文"""
        start = time.time()
        
        # 先从Redis加载（如果可用）
        if self.redis:
            try:
                cached = self.redis.get(f"conv:{conversation_id}")
                if cached:
                    ctx = ConversationContext.from_dict(json.loads(cached))
                    self.stats["redis_hits"] += 1
                    elapsed = (time.time() - start) * 1000
                    self.stats["get_context_calls"] += 1
                    self.stats["total_time_ms"] += elapsed
                    return ctx
            except Exception:
                pass
            
            self.stats["redis_misses"] += 1
        
        # 再从内存加载
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = ConversationContext(conversation_id)
        
        ctx = self.contexts[conversation_id]
        
        elapsed = (time.time() - start) * 1000
        self.stats["get_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
        
        return ctx
    
    def save_context(self, conversation_id: str, ctx: ConversationContext):
        """保存对话上下文"""
        start = time.time()
        
        # 保存到内存
        self.contexts[conversation_id] = ctx
        
        # 保存到Redis（可选）
        if self.redis:
            try:
                self.redis.set(
                    f"conv:{conversation_id}",
                    json.dumps(ctx.to_dict()),
                    ex=3600  # 1小时过期
                )
            except Exception:
                pass
        
        elapsed = (time.time() - start) * 1000
        self.stats["save_context_calls"] += 1
        self.stats["total_time_ms"] += elapsed
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        # 计算内存占用
        contexts_dict = {k: v.to_dict() for k, v in self.contexts.items()}
        memory_size = len(json.dumps(contexts_dict)) / 1024 / 1024
        
        return {
            **self.stats,
            "avg_time_ms": self.stats["total_time_ms"] / max(1, self.stats["get_context_calls"] + self.stats["save_context_calls"]),
            "memory_size_mb": memory_size,
            "redis_hit_rate": self.stats["redis_hits"] / max(1, self.stats["redis_hits"] + self.stats["redis_misses"]),
        }


# ============================================================================
# 性能对比测试
# ============================================================================

def benchmark_comparison():
    """性能对比测试"""
    
    print("=" * 80)
    print("对话记忆实现对比")
    print("=" * 80)
    
    # 模拟场景：100个用户，每个用户5轮对话
    num_users = 100
    turns_per_user = 5
    
    # 方案1：自己实现
    print("\n【方案1】自己实现（推荐）")
    memory_v1 = ConversationMemoryV1()
    
    for user_id in range(num_users):
        for turn in range(turns_per_user):
            ctx = memory_v1.get_context(f"user_{user_id}")
            ctx.turn_count += 1
            ctx.active_intent = ToolType.PLAN_TRIP
            ctx.partial_params = {"destination": "北京", "days": 3}
            memory_v1.save_context(f"user_{user_id}", ctx)
    
    stats_v1 = memory_v1.get_stats()
    print(f"  总耗时: {stats_v1['total_time_ms']:.2f}ms")
    print(f"  平均耗时: {stats_v1['avg_time_ms']:.4f}ms")
    print(f"  内存占用: {stats_v1['memory_size_mb']:.4f}MB")
    print(f"  LLM调用: 0次")
    print(f"  成本: 0元")
    
    # 方案2：LangChain Memory
    print("\n【方案2】LangChain Memory")
    memory_v2 = ConversationMemoryV2_LangChain(max_turns=10)
    
    for user_id in range(num_users):
        for turn in range(turns_per_user):
            ctx = memory_v2.get_context(f"user_{user_id}")
            ctx.turn_count += 1
            ctx.active_intent = ToolType.PLAN_TRIP
            ctx.partial_params = {"destination": "北京", "days": 3}
            memory_v2.save_context(f"user_{user_id}", ctx)
    
    stats_v2 = memory_v2.get_stats()
    print(f"  总耗时: {stats_v2['total_time_ms']:.2f}ms")
    print(f"  平均耗时: {stats_v2['avg_time_ms']:.4f}ms")
    print(f"  内存占用: {stats_v2['memory_size_mb']:.4f}MB")
    print(f"  LLM调用: {stats_v2['llm_calls']}次")
    print(f"  成本: {stats_v2['llm_cost_estimate']:.4f}元")
    
    # 方案3：混合方案
    print("\n【方案3】混合方案（推荐）")
    memory_v3 = ConversationMemoryV3_Hybrid()
    
    for user_id in range(num_users):
        for turn in range(turns_per_user):
            ctx = memory_v3.get_context(f"user_{user_id}")
            ctx.turn_count += 1
            ctx.active_intent = ToolType.PLAN_TRIP
            ctx.partial_params = {"destination": "北京", "days": 3}
            memory_v3.save_context(f"user_{user_id}", ctx)
    
    stats_v3 = memory_v3.get_stats()
    print(f"  总耗时: {stats_v3['total_time_ms']:.2f}ms")
    print(f"  平均耗时: {stats_v3['avg_time_ms']:.4f}ms")
    print(f"  内存占用: {stats_v3['memory_size_mb']:.4f}MB")
    print(f"  LLM调用: 0次")
    print(f"  成本: 0元")
    
    # 对比总结
    print("\n" + "=" * 80)
    print("对比总结")
    print("=" * 80)
    
    print(f"\n性能对比（总耗时）:")
    print(f"  方案1: {stats_v1['total_time_ms']:.2f}ms (基准)")
    print(f"  方案2: {stats_v2['total_time_ms']:.2f}ms ({stats_v2['total_time_ms']/stats_v1['total_time_ms']:.1f}x)")
    print(f"  方案3: {stats_v3['total_time_ms']:.2f}ms ({stats_v3['total_time_ms']/stats_v1['total_time_ms']:.1f}x)")
    
    print(f"\n成本对比（LLM调用）:")
    print(f"  方案1: 0次 (0元)")
    print(f"  方案2: {stats_v2['llm_calls']}次 ({stats_v2['llm_cost_estimate']:.4f}元)")
    print(f"  方案3: 0次 (0元)")
    
    print(f"\n推荐: 方案1（自己实现）或方案3（混合方案）")
    print(f"不推荐: 方案2（LangChain Memory）- 成本高，收益低")


if __name__ == "__main__":
    benchmark_comparison()
