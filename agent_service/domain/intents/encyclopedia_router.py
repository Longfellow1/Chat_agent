"""Encyclopedia vs web search router."""


class EncyclopediaRouter:
    """Route queries to encyclopedia or web search."""
    
    # Encyclopedia keywords
    ENCYCLOPEDIA_KEYWORDS = [
        "是什么", "什么是", "介绍", "定义", "概念", "原理",
        "历史", "发展", "起源", "由来", "背景",
        "是谁", "谁是", "人物", "创始人",
    ]
    
    # Web search keywords
    WEB_SEARCH_KEYWORDS = [
        "价格", "多少钱", "售价", "报价",
        "怎么样", "如何", "哪个好", "对比", "评测",
        "最新", "新闻", "消息", "动态",
        "攻略", "指南", "教程", "方法",
        "政策", "补贴", "优惠",
    ]
    
    def should_use_encyclopedia(self, query: str) -> bool:
        """Check if query should use encyclopedia.
        
        Args:
            query: User query
            
        Returns:
            True if should use encyclopedia, False otherwise
        """
        query_lower = query.lower()
        
        # Check encyclopedia keywords
        for keyword in self.ENCYCLOPEDIA_KEYWORDS:
            if keyword in query_lower:
                return True
        
        # Check if single entity query (simple heuristic)
        # If query is short and doesn't contain search keywords, might be encyclopedia
        if len(query) < 10 and not any(kw in query_lower for kw in self.WEB_SEARCH_KEYWORDS):
            return True
        
        return False
    
    def route(self, query: str) -> str:
        """Route query to appropriate tool.
        
        Args:
            query: User query
            
        Returns:
            "encyclopedia" or "web_search"
        """
        if self.should_use_encyclopedia(query):
            return "encyclopedia"
        return "web_search"
