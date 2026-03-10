"""
测试路由修复：确保三个失败案例正确路由
"""

import pytest
from agent_service.domain.intents.router import route_query


class TestRouterFixes:
    """测试路由修复"""
    
    def test_sports_query_routes_to_web_search(self):
        """体育赛事查询应该路由到 web_search"""
        query = "查询一下洛杉矶湖人队最近的比赛情况"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "web_search", f"Expected web_search, got {decision.tool_name}"
    
    def test_location_info_query_routes_to_web_search(self):
        """地点信息查询应该路由到 web_search"""
        query = "查询一下格里菲斯天文台在哪个具体位置"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "web_search", f"Expected web_search, got {decision.tool_name}"
    
    def test_person_info_query_routes_to_web_search(self):
        """人物信息查询应该路由到 web_search"""
        query = "五条人乐队的成员都有谁"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "web_search", f"Expected web_search, got {decision.tool_name}"
    
    def test_who_is_query_routes_to_web_search(self):
        """'谁是'查询应该路由到 web_search"""
        query = "谁是马斯克"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "web_search"
    
    def test_band_members_query_routes_to_web_search(self):
        """乐队成员查询应该路由到 web_search"""
        query = "五条人乐队成员"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "web_search"
    
    def test_nearby_restaurant_still_works(self):
        """附近餐厅查询应该仍然路由到 find_nearby"""
        query = "附近有什么好吃的餐厅"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "find_nearby"
    
    def test_weather_query_still_works(self):
        """天气查询应该仍然路由到 get_weather"""
        query = "北京今天天气怎么样"
        decision = route_query(query)
        
        assert decision.decision_mode == "tool_call"
        assert decision.tool_name == "get_weather"


class TestInfoQueryDetection:
    """测试信息查询检测"""
    
    def test_sports_team_not_nearby(self):
        """体育球队查询不应该路由到 find_nearby"""
        query = "洛杉矶湖人队最近的比赛"
        decision = route_query(query)
        
        assert decision.tool_name != "find_nearby", "Sports query should not route to find_nearby"
    
    def test_celebrity_not_nearby(self):
        """明星查询不应该路由到 find_nearby"""
        query = "周杰伦最新专辑"
        decision = route_query(query)
        
        # 可能路由到 web_search 或 get_news，但不应该是 find_nearby
        assert decision.tool_name != "find_nearby", "Celebrity query should not route to find_nearby"
    
    def test_band_members_not_nearby(self):
        """乐队成员查询不应该路由到 find_nearby"""
        query = "五条人乐队的成员"
        decision = route_query(query)
        
        assert decision.tool_name != "find_nearby", "Band members query should not route to find_nearby"
