"""财经股票场景30条query评测"""
import sys
sys.path.insert(0, 'agent_service')

from app.factory import build_flow

# 30条财经股票相关query
FINANCE_QUERIES = [
    # 指数类 (5条)
    "上证指数今天怎么样",
    "深证成指最新行情",
    "创业板指数涨了吗",
    "沪深300现在多少点",
    "今天A股大盘走势如何",
    
    # 热门股票-中文名称 (8条)
    "贵州茅台股价",
    "比亚迪今天涨了多少",
    "宁德时代最新价格",
    "中国平安现在多少钱",
    "招商银行股票行情",
    "五粮液今天表现怎么样",
    "中国移动股价查询",
    "工商银行现在什么价位",
    
    # 股票代码查询 (5条)
    "600519今天行情",
    "000858最新价格",
    "002594涨跌情况",
    "601318股价多少",
    "300750现在什么价",
    
    # 模糊/口语化查询 (6条)
    "茅台股票怎么样了",
    "平安保险的股票多少钱",
    "比亚迪股票今天涨没涨",
    "查一下招行的股价",
    "看看宁德时代的行情",
    "上证今天收盘价",
    
    # 财经新闻类 (6条) - 应该路由到get_news或web_search
    "今天有什么财经新闻",
    "最新股市消息",
    "A股今天为什么大跌",
    "茅台为什么跌了",
    "最近有哪些热门股票",
    "今天股市行情分析",
]

def evaluate_finance_queries():
    """评测财经查询"""
    flow = build_flow()
    
    results = []
    stock_correct = 0
    news_correct = 0
    total_stock = 0
    total_news = 0
    
    print("=" * 80)
    print("财经股票场景评测 - 30条Query")
    print("=" * 80)
    
    for i, query in enumerate(FINANCE_QUERIES, 1):
        print(f"\n[{i}/30] Query: {query}")
        
        # 判断预期工具
        is_news_query = any(kw in query for kw in ["新闻", "消息", "为什么", "分析", "热门"])
        expected_tool = "get_news" if is_news_query else "get_stock"
        
        if is_news_query:
            total_news += 1
        else:
            total_stock += 1
        
        try:
            from app.schemas.contracts import ChatRequest
            req = ChatRequest(query=query, session_id=f"test_finance_{i}")
            response = flow.run(req=req)
            
            # 提取实际使用的工具
            actual_tool = response.tool_name or "reply"
            
            # 判断是否正确
            is_correct = False
            if is_news_query:
                # 新闻类query应该路由到get_news或web_search
                is_correct = actual_tool in ["get_news", "web_search"]
                if is_correct:
                    news_correct += 1
            else:
                # 股票类query应该路由到get_stock
                is_correct = actual_tool == "get_stock"
                if is_correct:
                    stock_correct += 1
            
            status = "✅" if is_correct else "❌"
            print(f"{status} 预期: {expected_tool}, 实际: {actual_tool}")
            
            # 显示响应内容
            final_text = response.final_text or ""
            if len(final_text) > 150:
                final_text = final_text[:150] + "..."
            print(f"   回复: {final_text}")
            
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": actual_tool,
                "correct": is_correct,
                "response": final_text
            })
            
        except Exception as e:
            print(f"❌ 执行失败: {str(e)}")
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": "error",
                "correct": False,
                "response": str(e)
            })
    
    # 统计结果
    print("\n" + "=" * 80)
    print("评测结果统计")
    print("=" * 80)
    
    stock_accuracy = (stock_correct / total_stock * 100) if total_stock > 0 else 0
    news_accuracy = (news_correct / total_news * 100) if total_news > 0 else 0
    total_correct = stock_correct + news_correct
    total_accuracy = (total_correct / len(FINANCE_QUERIES) * 100)
    
    print(f"\n股票查询 (get_stock):")
    print(f"  总数: {total_stock}")
    print(f"  正确: {stock_correct}")
    print(f"  准确率: {stock_accuracy:.1f}%")
    
    print(f"\n新闻查询 (get_news/web_search):")
    print(f"  总数: {total_news}")
    print(f"  正确: {news_correct}")
    print(f"  准确率: {news_accuracy:.1f}%")
    
    print(f"\n总体:")
    print(f"  总数: {len(FINANCE_QUERIES)}")
    print(f"  正确: {total_correct}")
    print(f"  准确率: {total_accuracy:.1f}%")
    
    # 错误案例分析
    errors = [r for r in results if not r["correct"]]
    if errors:
        print(f"\n错误案例 ({len(errors)}条):")
        for err in errors:
            print(f"  - {err['query']}")
            print(f"    预期: {err['expected']}, 实际: {err['actual']}")
    
    return results

if __name__ == "__main__":
    evaluate_finance_queries()
