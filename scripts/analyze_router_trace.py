#!/usr/bin/env python3
"""
Router Architecture Trace Analysis
===================================

为每个工具类别采集详细的处理 trace，用于架构优化分析
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List


# 每个工具类别 10 条测试（5 条规则 + 5 条 LLM）
TEST_CASES = {
    "plan_trip": [
        # 规则命中（5条）
        {"query": "北京3天旅游", "expected_source": "rule", "note": "目的地+时间"},
        {"query": "上海旅行5天", "expected_source": "rule", "note": "目的地+时间"},
        {"query": "广州旅游", "expected_source": "rule", "note": "旅游关键词"},
        {"query": "出去转转", "expected_source": "rule", "note": "口语化旅游"},
        {"query": "避暑", "expected_source": "rule", "note": "季节性旅游"},
        # LLM 处理（5条）
        {"query": "我想去一个有山有水的地方", "expected_source": "llm", "note": "描述性目的地"},
        {"query": "周末想出去走走", "expected_source": "llm", "note": "隐含旅游意图"},
        {"query": "帮我安排一下行程", "expected_source": "llm", "note": "缺少所有参数"},
        {"query": "我想去旅游，但不知道去哪", "expected_source": "llm", "note": "意图明确但缺参数"},
        {"query": "国庆假期有什么推荐", "expected_source": "llm", "note": "隐含旅游+推荐"},
    ],
    "find_nearby": [
        # 规则命中（5条）
        {"query": "北京附近的餐厅", "expected_source": "rule", "note": "位置+类别"},
        {"query": "上海好吃的", "expected_source": "rule", "note": "位置+美食"},
        {"query": "广州酒店", "expected_source": "rule", "note": "位置+酒店"},
        {"query": "深圳景点", "expected_source": "rule", "note": "位置+景点"},
        {"query": "杭州哪里有银行", "expected_source": "rule", "note": "位置+银行"},
        # LLM 处理（5条）
        {"query": "我想吃饭，但不知道在哪", "expected_source": "llm", "note": "隐含类别，缺位置"},
        {"query": "有什么好玩的地方吗", "expected_source": "llm", "note": "隐含景点，缺位置"},
        {"query": "我想找个安静的地方", "expected_source": "llm", "note": "描述性类别"},
        {"query": "晚上去哪吃", "expected_source": "llm", "note": "隐含餐厅，缺位置"},
        {"query": "周围有什么", "expected_source": "llm", "note": "缺位置和类别"},
    ],
    "get_weather": [
        # 规则命中（5条）
        {"query": "北京天气", "expected_source": "rule", "note": "位置+天气"},
        {"query": "上海温度", "expected_source": "rule", "note": "位置+温度"},
        {"query": "广州下雨吗", "expected_source": "rule", "note": "位置+下雨"},
        {"query": "深圳晴天", "expected_source": "rule", "note": "位置+晴天"},
        {"query": "杭州风大吗", "expected_source": "rule", "note": "位置+风"},
        # LLM 处理（5条）
        {"query": "明天要不要带伞", "expected_source": "llm", "note": "隐含天气，缺位置"},
        {"query": "冷不冷", "expected_source": "llm", "note": "隐含天气，缺位置"},
        {"query": "热不热", "expected_source": "llm", "note": "隐含天气，缺位置"},
        {"query": "需要穿什么", "expected_source": "llm", "note": "穿衣→天气"},
        {"query": "会不会下雨", "expected_source": "llm", "note": "隐含天气，缺位置"},
    ],
    "web_search": [
        # 规则命中（5条）- web_search 没有规则，全部走 LLM
        {"query": "什么是人工智能", "expected_source": "llm", "note": "知识查询"},
        {"query": "如何学习编程", "expected_source": "llm", "note": "方法查询"},
        {"query": "Python教程", "expected_source": "llm", "note": "教程查询"},
        {"query": "最新科技新闻", "expected_source": "llm", "note": "新闻查询"},
        {"query": "北京有什么好玩的", "expected_source": "llm", "note": "推荐查询"},
        # LLM 处理（5条）
        {"query": "帮我查一下", "expected_source": "llm", "note": "极度模糊"},
        {"query": "查询一下", "expected_source": "llm", "note": "极度模糊"},
        {"query": "我想了解", "expected_source": "llm", "note": "缺了解内容"},
        {"query": "给我推荐一下", "expected_source": "llm", "note": "缺推荐内容"},
        {"query": "是什么", "expected_source": "llm", "note": "缺主语"},
    ],
    "get_news": [
        # 规则命中（5条）- get_news 没有规则，全部走 LLM
        {"query": "最近有什么大事", "expected_source": "llm", "note": "隐含新闻"},
        {"query": "今天发生了什么", "expected_source": "llm", "note": "隐含新闻"},
        {"query": "有什么热点", "expected_source": "llm", "note": "隐含新闻"},
        {"query": "最新消息", "expected_source": "llm", "note": "隐含新闻"},
        {"query": "科技新闻", "expected_source": "llm", "note": "明确新闻"},
        # LLM 处理（5条）
        {"query": "新闻", "expected_source": "llm", "note": "单字，缺主题"},
        {"query": "今天的新闻", "expected_source": "llm", "note": "缺主题"},
        {"query": "国际新闻", "expected_source": "llm", "note": "明确类别"},
        {"query": "财经新闻", "expected_source": "llm", "note": "明确类别"},
        {"query": "体育新闻", "expected_source": "llm", "note": "明确类别"},
    ],
    "get_stock": [
        # 规则命中（5条）- get_stock 没有规则，全部走 LLM
        {"query": "科技公司的表现", "expected_source": "llm", "note": "隐含股票"},
        {"query": "最近股市怎么样", "expected_source": "llm", "note": "隐含股票"},
        {"query": "市场行情", "expected_source": "llm", "note": "隐含股票"},
        {"query": "苹果股价", "expected_source": "llm", "note": "明确股票"},
        {"query": "特斯拉股票", "expected_source": "llm", "note": "明确股票"},
        # LLM 处理（5条）
        {"query": "股票", "expected_source": "llm", "note": "单字，缺代码"},
        {"query": "股价", "expected_source": "llm", "note": "缺代码"},
        {"query": "A股", "expected_source": "llm", "note": "缺具体股票"},
        {"query": "港股", "expected_source": "llm", "note": "缺具体股票"},
        {"query": "美股", "expected_source": "llm", "note": "缺具体股票"},
    ],
}


def collect_trace(router, query: str) -> Dict[str, Any]:
    """采集单个 query 的完整 trace"""
    
    start_time = time.time()
    
    # 调用路由器
    result = router.route(query)
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    # 构建 trace
    trace = {
        "query": query,
        "tool": result.get("tool"),
        "params": result.get("params", {}),
        "confidence": result.get("confidence", 0),
        "source": result.get("source", "unknown"),
        "needs_clarification": result.get("needs_clarification", False),
        "success": result.get("success", False),
        "latency_ms": latency_ms,
        "error": result.get("error"),
    }
    
    return trace


def main():
    """主函数"""
    from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient
    from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs
    
    # 初始化路由器
    client = LMStudioClient(base_url='http://localhost:1234', model='qwen/qwen3-4b-2507')
    router = Router4BWithLogprobs(llm_client=client)
    
    print("Collecting router traces...")
    
    # 采集所有 trace
    all_traces = {}
    
    for tool_type, cases in TEST_CASES.items():
        print(f"\n{tool_type}: {len(cases)} cases")
        
        tool_traces = []
        
        for i, case in enumerate(cases, 1):
            query = case["query"]
            expected_source = case["expected_source"]
            note = case["note"]
            
            # 采集 trace
            trace = collect_trace(router, query)
            
            # 添加元数据
            trace["expected_source"] = expected_source
            trace["note"] = note
            trace["case_id"] = f"{tool_type}_{i}"
            
            tool_traces.append(trace)
            
            # 打印进度
            source_match = "✓" if trace["source"] == expected_source else "✗"
            print(f"  [{i:2d}/10] {source_match} {query[:30]:30s} → {trace['source']:5s} ({trace['latency_ms']:.0f}ms)")
        
        all_traces[tool_type] = tool_traces
    
    # 保存结果
    output = {
        "timestamp": datetime.now().isoformat(),
        "model": "qwen/qwen3-4b-2507",
        "total_cases": sum(len(cases) for cases in TEST_CASES.values()),
        "traces_by_tool": all_traces,
    }
    
    output_file = f"eval/reports/router_trace_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Traces saved to: {output_file}")
    
    # 打印统计
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for tool_type, traces in all_traces.items():
        rule_count = sum(1 for t in traces if t["source"] == "rule")
        llm_count = sum(1 for t in traces if t["source"] == "llm")
        avg_latency = sum(t["latency_ms"] for t in traces) / len(traces)
        
        print(f"\n{tool_type}:")
        print(f"  Rule: {rule_count}/10")
        print(f"  LLM: {llm_count}/10")
        print(f"  Avg Latency: {avg_latency:.1f}ms")


if __name__ == "__main__":
    main()
