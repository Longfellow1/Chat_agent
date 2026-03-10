"""
7B 模型优化效果测试

对比优化前后的准确率
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TestCase:
    """测试用例"""
    query: str
    expected_tool: str
    expected_params: Dict
    category: str  # "normal", "edge_case", "boundary"


class TestDataset:
    """测试数据集"""
    
    CASES = [
        # 正常场景（应该容易）
        TestCase("帮我规划一个北京3天的行程", "plan_trip", {"destination": "北京", "days": 3}, "normal"),
        TestCase("北京附近有什么好吃的", "find_nearby", {"city": "北京", "category": "餐厅"}, "normal"),
        TestCase("北京天气怎么样", "get_weather", {"city": "北京"}, "normal"),
        TestCase("搜索北京的历史", "web_search", {"query": "北京的历史"}, "normal"),
        
        # 边缘场景（7B 容易出错）
        TestCase("上海", "need_clarification", {}, "edge_case"),
        TestCase("北京", "need_clarification", {}, "edge_case"),
        TestCase("去北京出差穿什么", "web_search", {"query": "北京出差穿什么 天气"}, "edge_case"),
        TestCase("北京有什么", "need_clarification", {}, "edge_case"),
        TestCase("怎么去北京", "web_search", {"query": "怎么去北京"}, "edge_case"),
        
        # 边界模糊（需要精细判断）
        TestCase("北京有什么景点", "find_nearby", {"city": "北京", "category": "景点"}, "boundary"),
        TestCase("北京景点介绍", "web_search", {"query": "北京景点介绍"}, "boundary"),
        TestCase("北京3天行程推荐", "plan_trip", {"destination": "北京", "days": 3}, "boundary"),
        TestCase("北京3天有什么推荐", "need_clarification", {}, "boundary"),
        TestCase("北京附近的酒店", "find_nearby", {"city": "北京", "category": "酒店"}, "boundary"),
        TestCase("北京酒店推荐", "web_search", {"query": "北京酒店推荐"}, "boundary"),
        
        # 更多边缘场景
        TestCase("去北京", "need_clarification", {}, "edge_case"),
        TestCase("北京怎么样", "need_clarification", {}, "edge_case"),
        TestCase("北京好玩吗", "web_search", {"query": "北京好玩吗"}, "edge_case"),
        TestCase("北京值得去吗", "web_search", {"query": "北京值得去吗"}, "edge_case"),
        TestCase("北京2天行程", "plan_trip", {"destination": "北京", "days": 2}, "normal"),
        TestCase("北京5天自驾行程", "plan_trip", {"destination": "北京", "days": 5}, "normal"),
    ]


@dataclass
class EvaluationResult:
    """评估结果"""
    total: int
    correct: int
    accuracy: float
    by_category: Dict[str, Dict]  # {category: {total, correct, accuracy}}
    errors: List[Dict]  # 错误详情


class RouterEvaluator:
    """路由器评估器"""
    
    def __init__(self, router):
        """
        Args:
            router: 路由器实例
        """
        self.router = router
    
    def evaluate(self, test_cases: List[TestCase]) -> EvaluationResult:
        """
        评估路由器
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            评估结果
        """
        results = {
            "total": 0,
            "correct": 0,
            "by_category": {},
            "errors": []
        }
        
        for case in test_cases:
            # 路由
            route_result = self.router.route(case.query)
            
            # 检查结果
            if not route_result.get("success"):
                results["errors"].append({
                    "query": case.query,
                    "expected_tool": case.expected_tool,
                    "error": route_result.get("error")
                })
                results["total"] += 1
                continue
            
            tool_call = route_result.get("tool_call")
            if not tool_call:
                results["errors"].append({
                    "query": case.query,
                    "expected_tool": case.expected_tool,
                    "error": "No tool_call returned"
                })
                results["total"] += 1
                continue
            
            # 检查工具是否正确
            tool_correct = tool_call.tool.value == case.expected_tool
            
            # 检查参数是否正确（如果有）
            params_correct = True
            if case.expected_params:
                for key, value in case.expected_params.items():
                    if tool_call.params.get(key) != value:
                        params_correct = False
                        break
            
            # 更新统计
            results["total"] += 1
            if tool_correct and params_correct:
                results["correct"] += 1
            else:
                results["errors"].append({
                    "query": case.query,
                    "expected_tool": case.expected_tool,
                    "expected_params": case.expected_params,
                    "actual_tool": tool_call.tool.value,
                    "actual_params": tool_call.params,
                    "reasoning": tool_call.reasoning
                })
            
            # 按类别统计
            category = case.category
            if category not in results["by_category"]:
                results["by_category"][category] = {"total": 0, "correct": 0}
            
            results["by_category"][category]["total"] += 1
            if tool_correct and params_correct:
                results["by_category"][category]["correct"] += 1
        
        # 计算准确率
        accuracy = results["correct"] / results["total"] if results["total"] > 0 else 0
        
        # 计算各类别准确率
        for category in results["by_category"]:
            cat_data = results["by_category"][category]
            cat_data["accuracy"] = cat_data["correct"] / cat_data["total"] if cat_data["total"] > 0 else 0
        
        return EvaluationResult(
            total=results["total"],
            correct=results["correct"],
            accuracy=accuracy,
            by_category=results["by_category"],
            errors=results["errors"]
        )
    
    def print_report(self, result: EvaluationResult):
        """打印评估报告"""
        print("=" * 80)
        print("7B 模型优化效果评估")
        print("=" * 80)
        
        print(f"\n【总体结果】")
        print(f"  总测试数：{result.total}")
        print(f"  正确数：{result.correct}")
        print(f"  准确率：{result.accuracy:.1%}")
        
        print(f"\n【按类别统计】")
        for category, data in result.by_category.items():
            print(f"  {category}:")
            print(f"    总数：{data['total']}")
            print(f"    正确：{data['correct']}")
            print(f"    准确率：{data['accuracy']:.1%}")
        
        if result.errors:
            print(f"\n【错误详情】（共 {len(result.errors)} 个）")
            for i, error in enumerate(result.errors[:5], 1):  # 只显示前5个
                print(f"\n  错误 {i}：")
                print(f"    查询：{error['query']}")
                print(f"    期望工具：{error.get('expected_tool')}")
                print(f"    实际工具：{error.get('actual_tool')}")
                if error.get('reasoning'):
                    print(f"    推理：{error['reasoning']}")
            
            if len(result.errors) > 5:
                print(f"\n  ... 还有 {len(result.errors) - 5} 个错误")


# ============================================================================
# 对比测试：优化前 vs 优化后
# ============================================================================

def compare_routers(router_before, router_after):
    """对比优化前后的路由器"""
    
    evaluator = RouterEvaluator(router_before)
    result_before = evaluator.evaluate(TestDataset.CASES)
    
    evaluator = RouterEvaluator(router_after)
    result_after = evaluator.evaluate(TestDataset.CASES)
    
    print("=" * 80)
    print("优化前 vs 优化后对比")
    print("=" * 80)
    
    print(f"\n【总体准确率】")
    print(f"  优化前：{result_before.accuracy:.1%}")
    print(f"  优化后：{result_after.accuracy:.1%}")
    print(f"  提升：{(result_after.accuracy - result_before.accuracy):.1%}")
    
    print(f"\n【按类别准确率】")
    for category in result_before.by_category:
        before_acc = result_before.by_category[category]["accuracy"]
        after_acc = result_after.by_category[category]["accuracy"]
        improvement = after_acc - before_acc
        print(f"  {category}:")
        print(f"    优化前：{before_acc:.1%}")
        print(f"    优化后：{after_acc:.1%}")
        print(f"    提升：{improvement:.1%}")
    
    print(f"\n【错误减少】")
    print(f"  优化前错误数：{result_before.total - result_before.correct}")
    print(f"  优化后错误数：{result_after.total - result_after.correct}")
    print(f"  减少：{(result_before.total - result_before.correct) - (result_after.total - result_after.correct)}")


if __name__ == "__main__":
    # 这是测试框架
    # 实际使用时，需要传入真实的路由器实例
    
    print("7B 模型优化效果测试框架")
    print("\n使用方式：")
    print("  from tests.unit.test_7b_optimization import RouterEvaluator, TestDataset")
    print("  evaluator = RouterEvaluator(router)")
    print("  result = evaluator.evaluate(TestDataset.CASES)")
    print("  evaluator.print_report(result)")
