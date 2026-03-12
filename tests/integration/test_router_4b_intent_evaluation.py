"""
4B Router Intent Evaluation - 30 Test Cases
============================================

30 个意图评测数据，包含 10 个模糊边界的难例

测试流程：
1. 调用 4B 模型进行意图识别
2. 记录延迟、准确率、置信度
3. 分析规则命中率 vs LLM 兜底率
4. 评估难例处理效果
"""

import json
import time
from typing import Dict, Any, List
import pytest


# 评测数据集：30 个查询
EVALUATION_DATASET = [
    # ===== 简单查询（规则能处理）- 10 个 =====
    {
        "id": "simple_1",
        "query": "我想去北京3天",
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "北京"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_2",
        "query": "北京附近有什么好吃的",
        "expected_tool": "find_nearby",
        "expected_params": {"city": "北京", "category": "餐厅"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_3",
        "query": "上海一周旅游",
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "上海"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_4",
        "query": "深圳附近的酒店",
        "expected_tool": "find_nearby",
        "expected_params": {"city": "深圳", "category": "酒店"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_5",
        "query": "广州5天行程",
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "广州"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_6",
        "query": "杭州附近的景点",
        "expected_tool": "find_nearby",
        "expected_params": {"city": "杭州", "category": "景点"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_7",
        "query": "北京的天气怎么样",
        "expected_tool": "get_weather",
        "expected_params": {"location": "北京"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_8",
        "query": "西安2天旅行",
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "西安"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_9",
        "query": "成都附近有什么医院",
        "expected_tool": "find_nearby",
        "expected_params": {"city": "成都", "category": "医院"},
        "category": "simple",
        "difficulty": "easy"
    },
    {
        "id": "simple_10",
        "query": "上海今天会下雨吗",
        "expected_tool": "get_weather",
        "expected_params": {"location": "上海"},
        "category": "simple",
        "difficulty": "easy"
    },
    
    # ===== 中等复杂查询（需要 LLM 兜底）- 10 个 =====
    {
        "id": "medium_1",
        "query": "什么是人工智能",
        "expected_tool": "web_search",
        "expected_params": {"query": "什么是人工智能"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_2",
        "query": "最新的新闻",
        "expected_tool": "get_news",
        "expected_params": {"query": "最新的新闻"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_3",
        "query": "查询苹果股票",
        "expected_tool": "get_stock",
        "expected_params": {"symbol": "AAPL"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_4",
        "query": "如何学习编程",
        "expected_tool": "web_search",
        "expected_params": {"query": "如何学习编程"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_5",
        "query": "今天的股市行情",
        "expected_tool": "get_news",
        "expected_params": {"query": "股市行情"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_6",
        "query": "Python 有什么优势",
        "expected_tool": "web_search",
        "expected_params": {"query": "Python 优势"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_7",
        "query": "查询微软股票价格",
        "expected_tool": "get_stock",
        "expected_params": {"symbol": "MSFT"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_8",
        "query": "最新的科技新闻",
        "expected_tool": "get_news",
        "expected_params": {"query": "科技新闻"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_9",
        "query": "机器学习是什么",
        "expected_tool": "web_search",
        "expected_params": {"query": "机器学习"},
        "category": "medium",
        "difficulty": "medium"
    },
    {
        "id": "medium_10",
        "query": "查询特斯拉股票",
        "expected_tool": "get_stock",
        "expected_params": {"symbol": "TSLA"},
        "category": "medium",
        "difficulty": "medium"
    },
    
    # ===== 难例：模糊边界 - 10 个 =====
    {
        "id": "hard_1",
        "query": "我想去北京",  # 缺少时间
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "北京"},
        "category": "hard",
        "difficulty": "hard",
        "note": "缺少时间参数，需要澄清"
    },
    {
        "id": "hard_2",
        "query": "北京附近",  # 缺少类别
        "expected_tool": "find_nearby",
        "expected_params": {"city": "北京"},
        "category": "hard",
        "difficulty": "hard",
        "note": "缺少类别参数，需要澄清"
    },
    {
        "id": "hard_3",
        "query": "我想去一个有山有水的地方",  # 没有明确目的地
        "expected_tool": "plan_trip",
        "expected_params": {},
        "category": "hard",
        "difficulty": "hard",
        "note": "没有明确目的地，需要澄清"
    },
    {
        "id": "hard_4",
        "query": "帮我规划一下",  # 极度模糊
        "expected_tool": "web_search",
        "expected_params": {"query": "帮我规划一下"},
        "category": "hard",
        "difficulty": "hard",
        "note": "极度模糊，无法确定意图"
    },
    {
        "id": "hard_5",
        "query": "附近有什么",  # 缺少位置和类别
        "expected_tool": "find_nearby",
        "expected_params": {},
        "category": "hard",
        "difficulty": "hard",
        "note": "缺少位置和类别，需要澄清"
    },
    {
        "id": "hard_6",
        "query": "天气",  # 缺少位置
        "expected_tool": "get_weather",
        "expected_params": {},
        "category": "hard",
        "difficulty": "hard",
        "note": "缺少位置参数，需要澄清"
    },
    {
        "id": "hard_7",
        "query": "我想去旅游，但不知道去哪",  # 意图清晰但参数缺失
        "expected_tool": "plan_trip",
        "expected_params": {},
        "category": "hard",
        "difficulty": "hard",
        "note": "意图清晰但参数缺失，需要澄清"
    },
    {
        "id": "hard_8",
        "query": "北京或上海，3天",  # 多个目的地
        "expected_tool": "plan_trip",
        "expected_params": {"destination": "北京"},  # 应该选择第一个
        "category": "hard",
        "difficulty": "hard",
        "note": "多个目的地，需要澄清"
    },
    {
        "id": "hard_9",
        "query": "我想吃饭，但不知道在哪",  # 意图是 find_nearby 但缺少位置
        "expected_tool": "find_nearby",
        "expected_params": {"category": "餐厅"},
        "category": "hard",
        "difficulty": "hard",
        "note": "意图清晰但缺少位置，需要澄清"
    },
    {
        "id": "hard_10",
        "query": "查询一下",  # 极度模糊
        "expected_tool": "web_search",
        "expected_params": {"query": "查询一下"},
        "category": "hard",
        "difficulty": "hard",
        "note": "极度模糊，无法确定意图"
    },
]


class TestRouter4BIntentEvaluation:
    """4B Router 意图识别评测"""
    
    @pytest.fixture
    def router(self):
        """初始化 router（需要真实的 4B 模型）"""
        from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs
        
        # 这里需要配置真实的 4B LLM 客户端
        # 例如：Qwen3-4B-2507 via vLLM 或 LM Studio
        llm_client = self._get_4b_llm_client()
        
        if llm_client is None:
            pytest.skip("4B LLM client not available")
        
        return Router4BWithLogprobs(llm_client=llm_client)
    
    def _get_4b_llm_client(self):
        """获取 4B LLM 客户端"""
        # 尝试连接到本地 LM Studio 或 vLLM
        try:
            from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient
            
            client = LMStudioClient(
                base_url="http://localhost:1234/v1",
                model="qwen3-4b-2507"
            )
            
            # 测试连接
            response = client.call(
                system_prompt="你是一个助手",
                user_message="测试",
                response_format="text",
                temperature=0.3,
                max_tokens=10
            )
            
            if response:
                return client
        except Exception as e:
            print(f"Failed to connect to LM Studio: {e}")
        
        return None
    
    def test_simple_queries(self, router):
        """测试简单查询（规则能处理）"""
        simple_cases = [case for case in EVALUATION_DATASET if case["category"] == "simple"]
        
        results = {
            "total": len(simple_cases),
            "correct": 0,
            "incorrect": 0,
            "latencies": [],
            "confidences": [],
        }
        
        for case in simple_cases:
            start = time.time()
            result = router.route(case["query"])
            latency = (time.time() - start) * 1000  # ms
            
            results["latencies"].append(latency)
            results["confidences"].append(result.get("confidence", 0))
            
            if result["tool"] == case["expected_tool"]:
                results["correct"] += 1
            else:
                results["incorrect"] += 1
                print(f"FAIL: {case['id']} - Expected {case['expected_tool']}, got {result['tool']}")
        
        # 统计
        accuracy = results["correct"] / results["total"]
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        avg_confidence = sum(results["confidences"]) / len(results["confidences"])
        
        print(f"\n=== Simple Queries Results ===")
        print(f"Accuracy: {accuracy:.2%} ({results['correct']}/{results['total']})")
        print(f"Avg Latency: {avg_latency:.1f}ms")
        print(f"Avg Confidence: {avg_confidence:.2f}")
        
        assert accuracy >= 0.9, f"Simple query accuracy too low: {accuracy:.2%}"
    
    def test_medium_queries(self, router):
        """测试中等复杂查询（需要 LLM 兜底）"""
        medium_cases = [case for case in EVALUATION_DATASET if case["category"] == "medium"]
        
        results = {
            "total": len(medium_cases),
            "correct": 0,
            "incorrect": 0,
            "latencies": [],
            "confidences": [],
        }
        
        for case in medium_cases:
            start = time.time()
            result = router.route(case["query"])
            latency = (time.time() - start) * 1000  # ms
            
            results["latencies"].append(latency)
            results["confidences"].append(result.get("confidence", 0))
            
            if result["tool"] == case["expected_tool"]:
                results["correct"] += 1
            else:
                results["incorrect"] += 1
                print(f"FAIL: {case['id']} - Expected {case['expected_tool']}, got {result['tool']}")
        
        # 统计
        accuracy = results["correct"] / results["total"]
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        avg_confidence = sum(results["confidences"]) / len(results["confidences"])
        
        print(f"\n=== Medium Queries Results ===")
        print(f"Accuracy: {accuracy:.2%} ({results['correct']}/{results['total']})")
        print(f"Avg Latency: {avg_latency:.1f}ms")
        print(f"Avg Confidence: {avg_confidence:.2f}")
        
        assert accuracy >= 0.8, f"Medium query accuracy too low: {accuracy:.2%}"
    
    def test_hard_queries(self, router):
        """测试难例（模糊边界）"""
        hard_cases = [case for case in EVALUATION_DATASET if case["category"] == "hard"]
        
        results = {
            "total": len(hard_cases),
            "correct": 0,
            "incorrect": 0,
            "needs_clarification": 0,
            "latencies": [],
            "confidences": [],
        }
        
        for case in hard_cases:
            start = time.time()
            result = router.route(case["query"])
            latency = (time.time() - start) * 1000  # ms
            
            results["latencies"].append(latency)
            results["confidences"].append(result.get("confidence", 0))
            
            if result["needs_clarification"]:
                results["needs_clarification"] += 1
            
            if result["tool"] == case["expected_tool"]:
                results["correct"] += 1
            else:
                results["incorrect"] += 1
                print(f"FAIL: {case['id']} - Expected {case['expected_tool']}, got {result['tool']}")
                print(f"  Note: {case.get('note', 'N/A')}")
        
        # 统计
        accuracy = results["correct"] / results["total"]
        clarification_rate = results["needs_clarification"] / results["total"]
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        avg_confidence = sum(results["confidences"]) / len(results["confidences"])
        
        print(f"\n=== Hard Queries Results ===")
        print(f"Accuracy: {accuracy:.2%} ({results['correct']}/{results['total']})")
        print(f"Clarification Rate: {clarification_rate:.2%}")
        print(f"Avg Latency: {avg_latency:.1f}ms")
        print(f"Avg Confidence: {avg_confidence:.2f}")
        
        # 难例的准确率可以较低，但澄清率应该较高
        assert clarification_rate >= 0.5, f"Hard query clarification rate too low: {clarification_rate:.2%}"
    
    def test_all_queries_performance(self, router):
        """测试所有查询的性能"""
        results = {
            "total": len(EVALUATION_DATASET),
            "correct": 0,
            "incorrect": 0,
            "latencies": [],
            "confidences": [],
            "by_category": {}
        }
        
        for case in EVALUATION_DATASET:
            start = time.time()
            result = router.route(case["query"])
            latency = (time.time() - start) * 1000  # ms
            
            results["latencies"].append(latency)
            results["confidences"].append(result.get("confidence", 0))
            
            category = case["category"]
            if category not in results["by_category"]:
                results["by_category"][category] = {"correct": 0, "total": 0}
            
            results["by_category"][category]["total"] += 1
            
            if result["tool"] == case["expected_tool"]:
                results["correct"] += 1
                results["by_category"][category]["correct"] += 1
            else:
                results["incorrect"] += 1
        
        # 总体统计
        overall_accuracy = results["correct"] / results["total"]
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        p50_latency = sorted(results["latencies"])[len(results["latencies"]) // 2]
        p95_latency = sorted(results["latencies"])[int(len(results["latencies"]) * 0.95)]
        avg_confidence = sum(results["confidences"]) / len(results["confidences"])
        
        print(f"\n=== Overall Performance ===")
        print(f"Total Queries: {results['total']}")
        print(f"Overall Accuracy: {overall_accuracy:.2%}")
        print(f"Avg Latency: {avg_latency:.1f}ms")
        print(f"P50 Latency: {p50_latency:.1f}ms")
        print(f"P95 Latency: {p95_latency:.1f}ms")
        print(f"Avg Confidence: {avg_confidence:.2f}")
        
        # 按类别统计
        print(f"\n=== By Category ===")
        for category, stats in results["by_category"].items():
            accuracy = stats["correct"] / stats["total"]
            print(f"{category}: {accuracy:.2%} ({stats['correct']}/{stats['total']})")
        
        # 保存结果
        self._save_results(results)
    
    def _save_results(self, results):
        """保存评测结果"""
        import json
        from datetime import datetime
        
        output_file = f"eval/reports/router_4b_intent_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
