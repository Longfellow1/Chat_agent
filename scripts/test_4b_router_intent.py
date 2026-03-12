#!/usr/bin/env python3
"""
4B Router Intent Evaluation Script
===================================

直接测试 4B 模型的意图识别效果

使用方式：
python scripts/test_4b_router_intent.py --model qwen3-4b-2507 --endpoint http://localhost:1234/v1
"""

import json
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime


# 100 个评测数据 - 专注于 LLM 意图识别能力
# 移除规则能处理的简单查询，专注于需要 LLM 理解的复杂场景
EVALUATION_DATASET = [
    # === 参数缺失/不完整（需要 LLM 判断）- 35 个 ===
    {"id": "1", "query": "我想去北京", "expected_tool": "plan_trip", "category": "incomplete", "note": "缺少时间参数"},
    {"id": "2", "query": "北京附近", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少类别参数"},
    {"id": "3", "query": "天气", "expected_tool": "get_weather", "category": "incomplete", "note": "缺少位置参数"},
    {"id": "4", "query": "我想去旅游", "expected_tool": "plan_trip", "category": "incomplete", "note": "缺少目的地和时间"},
    {"id": "5", "query": "附近有什么", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置和类别"},
    {"id": "6", "query": "帮我查一下", "expected_tool": "web_search", "category": "incomplete", "note": "缺少查询内容"},
    {"id": "7", "query": "我想吃饭", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置，类别隐含为餐厅"},
    {"id": "8", "query": "明天", "expected_tool": "get_weather", "category": "incomplete", "note": "单字，隐含查天气"},
    {"id": "9", "query": "股票", "expected_tool": "get_stock", "category": "incomplete", "note": "缺少股票代码"},
    {"id": "10", "query": "新闻", "expected_tool": "get_news", "category": "incomplete", "note": "缺少新闻主题"},
    {"id": "11", "query": "上海", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名，意图不明"},
    {"id": "12", "query": "酒店", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置"},
    {"id": "13", "query": "餐厅", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置"},
    {"id": "14", "query": "景点", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置"},
    {"id": "15", "query": "我想住", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少位置"},
    {"id": "16", "query": "去哪玩", "expected_tool": "plan_trip", "category": "incomplete", "note": "缺少目的地"},
    {"id": "17", "query": "几点", "expected_tool": "web_search", "category": "incomplete", "note": "缺少上下文"},
    {"id": "18", "query": "多少钱", "expected_tool": "web_search", "category": "incomplete", "note": "缺少主语"},
    {"id": "19", "query": "怎么去", "expected_tool": "web_search", "category": "incomplete", "note": "缺少目的地"},
    {"id": "20", "query": "在哪", "expected_tool": "web_search", "category": "incomplete", "note": "缺少主语"},
    {"id": "21", "query": "我想买", "expected_tool": "web_search", "category": "incomplete", "note": "缺少购买对象"},
    {"id": "22", "query": "推荐", "expected_tool": "web_search", "category": "incomplete", "note": "缺少推荐内容"},
    {"id": "23", "query": "查询", "expected_tool": "web_search", "category": "incomplete", "note": "缺少查询内容"},
    {"id": "24", "query": "搜索", "expected_tool": "web_search", "category": "incomplete", "note": "缺少搜索内容"},
    {"id": "25", "query": "找", "expected_tool": "web_search", "category": "incomplete", "note": "缺少查找对象"},
    {"id": "26", "query": "北京天气", "expected_tool": "get_weather", "category": "incomplete", "note": "完整但简短"},
    {"id": "27", "query": "上海美食", "expected_tool": "find_nearby", "category": "incomplete", "note": "缺少具体类别"},
    {"id": "28", "query": "杭州景点", "expected_tool": "find_nearby", "category": "incomplete", "note": "完整但简短"},
    {"id": "29", "query": "深圳酒店", "expected_tool": "find_nearby", "category": "incomplete", "note": "完整但简短"},
    {"id": "30", "query": "广州旅游", "expected_tool": "plan_trip", "category": "incomplete", "note": "缺少时间"},
    {"id": "31", "query": "成都", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名"},
    {"id": "32", "query": "西安", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名"},
    {"id": "33", "query": "南京", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名"},
    {"id": "34", "query": "苏州", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名"},
    {"id": "35", "query": "武汉", "expected_tool": "web_search", "category": "incomplete", "note": "单字地名"},
    
    # === 意图模糊/多义（需要 LLM 推理）- 35 个 ===
    {"id": "36", "query": "我想去一个有山有水的地方", "expected_tool": "plan_trip", "category": "ambiguous", "note": "描述性目的地"},
    {"id": "37", "query": "帮我规划一下", "expected_tool": "plan_trip", "category": "ambiguous", "note": "有规划意图"},
    {"id": "38", "query": "北京或上海，3天", "expected_tool": "plan_trip", "category": "ambiguous", "note": "多个目的地"},
    {"id": "39", "query": "我想去旅游，但不知道去哪", "expected_tool": "plan_trip", "category": "ambiguous", "note": "旅游意图明确"},
    {"id": "40", "query": "查询一下", "expected_tool": "web_search", "category": "ambiguous", "note": "极度模糊"},
    {"id": "41", "query": "我想找个地方", "expected_tool": "find_nearby", "category": "ambiguous", "note": "找地方意图"},
    {"id": "42", "query": "今天怎么样", "expected_tool": "get_weather", "category": "ambiguous", "note": "可能是天气"},
    {"id": "43", "query": "最近的", "expected_tool": "find_nearby", "category": "ambiguous", "note": "缺主语"},
    {"id": "44", "query": "给我推荐一下", "expected_tool": "web_search", "category": "ambiguous", "note": "缺推荐内容"},
    {"id": "45", "query": "我想了解", "expected_tool": "web_search", "category": "ambiguous", "note": "缺了解内容"},
    {"id": "46", "query": "周末想出去玩", "expected_tool": "plan_trip", "category": "ambiguous", "note": "出去玩=旅游"},
    {"id": "47", "query": "有什么好的", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "48", "query": "帮我看看", "expected_tool": "web_search", "category": "ambiguous", "note": "缺看什么"},
    {"id": "49", "query": "告诉我", "expected_tool": "web_search", "category": "ambiguous", "note": "缺告诉什么"},
    {"id": "50", "query": "我想知道", "expected_tool": "web_search", "category": "ambiguous", "note": "缺知道什么"},
    {"id": "51", "query": "怎么样", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "52", "query": "可以吗", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "53", "query": "行不行", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "54", "query": "好不好", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "55", "query": "对不对", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "56", "query": "是什么", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "57", "query": "为什么", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "58", "query": "哪里", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "59", "query": "什么时候", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "60", "query": "谁", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "61", "query": "多久", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "62", "query": "多远", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "63", "query": "多大", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "64", "query": "多高", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "65", "query": "多重", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "66", "query": "几个", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "67", "query": "哪个", "expected_tool": "web_search", "category": "ambiguous", "note": "缺主语"},
    {"id": "68", "query": "这个", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "69", "query": "那个", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    {"id": "70", "query": "它", "expected_tool": "web_search", "category": "ambiguous", "note": "缺上下文"},
    
    # === 复杂语义/隐含意图（需要 LLM 理解）- 30 个 ===
    {"id": "71", "query": "我想吃饭，但不知道在哪", "expected_tool": "find_nearby", "category": "complex", "note": "隐含类别（餐厅）"},
    {"id": "72", "query": "周末想出去走走", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游意图"},
    {"id": "73", "query": "有什么好玩的地方吗", "expected_tool": "find_nearby", "category": "complex", "note": "隐含类别（景点）"},
    {"id": "74", "query": "我想休息一下", "expected_tool": "find_nearby", "category": "complex", "note": "可能是酒店/咖啡厅"},
    {"id": "75", "query": "明天要不要带伞", "expected_tool": "get_weather", "category": "complex", "note": "隐含查天气"},
    {"id": "76", "query": "最近有什么大事", "expected_tool": "get_news", "category": "complex", "note": "隐含查新闻"},
    {"id": "77", "query": "科技公司的表现", "expected_tool": "get_stock", "category": "complex", "note": "可能是股票"},
    {"id": "78", "query": "我想学点东西", "expected_tool": "web_search", "category": "complex", "note": "隐含搜索学习资源"},
    {"id": "79", "query": "有什么好看的", "expected_tool": "web_search", "category": "complex", "note": "可能是电影、书籍"},
    {"id": "80", "query": "帮我安排一下行程", "expected_tool": "plan_trip", "category": "complex", "note": "行程=旅游规划"},
    {"id": "81", "query": "我想找个安静的地方", "expected_tool": "find_nearby", "category": "complex", "note": "可能是咖啡厅/图书馆"},
    {"id": "82", "query": "晚上去哪吃", "expected_tool": "find_nearby", "category": "complex", "note": "隐含餐厅"},
    {"id": "83", "query": "周围有什么", "expected_tool": "find_nearby", "category": "complex", "note": "缺位置和类别"},
    {"id": "84", "query": "我想看看风景", "expected_tool": "find_nearby", "category": "complex", "note": "隐含景点"},
    {"id": "85", "query": "放松一下", "expected_tool": "find_nearby", "category": "complex", "note": "可能是spa/咖啡厅"},
    {"id": "86", "query": "出去转转", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游"},
    {"id": "87", "query": "散散心", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游"},
    {"id": "88", "query": "度假", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游"},
    {"id": "89", "query": "避暑", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游"},
    {"id": "90", "query": "避寒", "expected_tool": "plan_trip", "category": "complex", "note": "隐含旅游"},
    {"id": "91", "query": "会不会下雨", "expected_tool": "get_weather", "category": "complex", "note": "隐含查天气"},
    {"id": "92", "query": "冷不冷", "expected_tool": "get_weather", "category": "complex", "note": "隐含查天气"},
    {"id": "93", "query": "热不热", "expected_tool": "get_weather", "category": "complex", "note": "隐含查天气"},
    {"id": "94", "query": "需要穿什么", "expected_tool": "get_weather", "category": "complex", "note": "隐含查天气"},
    {"id": "95", "query": "最近股市怎么样", "expected_tool": "get_stock", "category": "complex", "note": "隐含查股票"},
    {"id": "96", "query": "有什么热点", "expected_tool": "get_news", "category": "complex", "note": "隐含查新闻"},
    {"id": "97", "query": "今天发生了什么", "expected_tool": "get_news", "category": "complex", "note": "隐含查新闻"},
    {"id": "98", "query": "最新消息", "expected_tool": "get_news", "category": "complex", "note": "隐含查新闻"},
    {"id": "99", "query": "市场行情", "expected_tool": "get_stock", "category": "complex", "note": "隐含查股票"},
    {"id": "100", "query": "经济形势", "expected_tool": "get_news", "category": "complex", "note": "可能是新闻或股票"},
]


class Router4BIntentEvaluator:
    """4B Router 意图识别评测器"""
    
    def __init__(self, endpoint: str, model: str):
        """初始化评测器"""
        self.endpoint = endpoint
        self.model = model
        self.llm_client = self._init_llm_client()
        
        if self.llm_client is None:
            raise RuntimeError(f"Failed to connect to LLM at {endpoint}")
    
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        try:
            from agent_service.infra.llm_clients.lm_studio_client import LMStudioClient
            
            client = LMStudioClient(
                base_url=self.endpoint,
                model=self.model
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
                print(f"✓ Connected to {self.model} at {self.endpoint}")
                return client
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
        
        return None
    
    def evaluate(self):
        """运行评测"""
        from agent_service.domain.intents.router_4b_with_logprobs import Router4BWithLogprobs
        
        router = Router4BWithLogprobs(llm_client=self.llm_client)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "endpoint": self.endpoint,
            "total": len(EVALUATION_DATASET),
            "correct": 0,
            "incorrect": 0,
            "latencies": [],
            "confidences": [],
            "by_category": {},
            "details": []
        }
        
        print(f"\n{'='*60}")
        print(f"4B Router Intent Evaluation")
        print(f"{'='*60}")
        print(f"Model: {self.model}")
        print(f"Endpoint: {self.endpoint}")
        print(f"Total Cases: {len(EVALUATION_DATASET)}")
        print(f"{'='*60}\n")
        
        for i, case in enumerate(EVALUATION_DATASET, 1):
            query = case["query"]
            expected_tool = case["expected_tool"]
            category = case["category"]
            
            # 初始化类别统计
            if category not in results["by_category"]:
                results["by_category"][category] = {"correct": 0, "total": 0, "latencies": []}
            
            # 调用路由器
            start = time.time()
            result = router.route(query)
            latency = (time.time() - start) * 1000  # ms
            
            # 记录结果
            results["latencies"].append(latency)
            results["confidences"].append(result.get("confidence", 0))
            results["by_category"][category]["latencies"].append(latency)
            results["by_category"][category]["total"] += 1
            
            is_correct = result["tool"] == expected_tool
            
            if is_correct:
                results["correct"] += 1
                results["by_category"][category]["correct"] += 1
                status = "✓"
            else:
                results["incorrect"] += 1
                status = "✗"
            
            # 记录详情
            detail = {
                "id": case["id"],
                "query": query,
                "expected": expected_tool,
                "got": result["tool"],
                "correct": is_correct,
                "confidence": result.get("confidence", 0),
                "latency_ms": latency,
                "needs_clarification": result.get("needs_clarification", False),
                "source": result.get("source", "unknown"),
            }
            
            if "note" in case:
                detail["note"] = case["note"]
            
            results["details"].append(detail)
            
            # 打印进度
            print(f"[{i:2d}/30] {status} {case['id']:3s} | {query[:40]:40s} | "
                  f"{result['tool']:12s} | {latency:6.1f}ms | conf={result.get('confidence', 0):.2f}")
        
        # 计算统计
        self._print_summary(results)
        
        # 保存结果
        self._save_results(results)
        
        return results
    
    def _print_summary(self, results):
        """打印总结"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        
        # 总体
        overall_accuracy = results["correct"] / results["total"]
        avg_latency = sum(results["latencies"]) / len(results["latencies"])
        p50_latency = sorted(results["latencies"])[len(results["latencies"]) // 2]
        p95_latency = sorted(results["latencies"])[int(len(results["latencies"]) * 0.95)]
        avg_confidence = sum(results["confidences"]) / len(results["confidences"])
        
        print(f"\nOverall:")
        print(f"  Accuracy: {overall_accuracy:.2%} ({results['correct']}/{results['total']})")
        print(f"  Avg Latency: {avg_latency:.1f}ms")
        print(f"  P50 Latency: {p50_latency:.1f}ms")
        print(f"  P95 Latency: {p95_latency:.1f}ms")
        print(f"  Avg Confidence: {avg_confidence:.2f}")
        
        # 按类别
        print(f"\nBy Category:")
        for category in ["incomplete", "ambiguous", "complex"]:
            if category in results["by_category"]:
                stats = results["by_category"][category]
                accuracy = stats["correct"] / stats["total"]
                avg_lat = sum(stats["latencies"]) / len(stats["latencies"])
                print(f"  {category:12s}: {accuracy:.2%} ({stats['correct']}/{stats['total']}) | "
                      f"avg_latency={avg_lat:.1f}ms")
        
        # 难例分析
        print(f"\nComplex Cases Analysis:")
        complex_cases = [d for d in results["details"] if d["id"] in ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]]
        complex_correct = sum(1 for c in complex_cases if c["correct"])
        complex_clarification = sum(1 for c in complex_cases if c["needs_clarification"])
        print(f"  Correct: {complex_correct}/{len(complex_cases)}")
        print(f"  Needs Clarification: {complex_clarification}/{len(complex_cases)}")
        
        # 失败案例
        failures = [d for d in results["details"] if not d["correct"]]
        if failures:
            print(f"\nFailures ({len(failures)}):")
            for f in failures[:5]:  # 只显示前 5 个
                print(f"  {f['id']}: {f['query'][:40]:40s} | "
                      f"expected={f['expected']:12s} got={f['got']:12s}")
            if len(failures) > 5:
                print(f"  ... and {len(failures) - 5} more")
        
        print(f"\n{'='*60}\n")
    
    def _save_results(self, results):
        """保存结果"""
        import os
        
        # 创建输出目录
        output_dir = "eval/reports"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存 JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/router_4b_intent_eval_{timestamp}.json"
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="4B Router Intent Evaluation")
    parser.add_argument("--endpoint", default="http://localhost:1234",
                        help="LLM endpoint (default: http://localhost:1234)")
    parser.add_argument("--model", default="qwen/qwen3-4b-2507",
                        help="Model name (default: qwen/qwen3-4b-2507)")
    
    args = parser.parse_args()
    
    try:
        evaluator = Router4BIntentEvaluator(
            endpoint=args.endpoint,
            model=args.model
        )
        
        results = evaluator.evaluate()
        
        # 返回状态码
        overall_accuracy = results["correct"] / results["total"]
        if overall_accuracy >= 0.85:
            print("✓ Evaluation passed!")
            return 0
        else:
            print("✗ Evaluation failed!")
            return 1
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
