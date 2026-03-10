"""
Unit tests for boundary response detection
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../agent_service'))

import pytest
from app.policies.boundary_response import (
    detect_boundary_response,
    get_boundary_reply,
    BoundaryMatch,
)


class TestFinancialPrediction:
    """金融预测边界检测"""
    
    def test_absolute_guarantee_stock(self):
        """绝对化承诺 - 股票"""
        query = "你直接告诉我下周A股哪只股票一定涨停"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "financial_prediction"
        assert match.confidence >= 0.9
    
    def test_100_percent_profit(self):
        """100%保证盈利"""
        query = "我要创业，给我100%保证盈利的商业计划"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category in ["financial_prediction", "business_plan"]
    
    def test_normal_stock_query(self):
        """正常股票查询"""
        query = "请查看五粮液今天股价"
        match = detect_boundary_response(query)
        assert match is None


class TestMonitoringService:
    """实时监控边界检测"""
    
    def test_realtime_monitoring(self):
        """实时监控"""
        query = "请帮我实时监控全球突发新闻并每分钟推送"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "impossible_service"
        assert match.confidence >= 0.9
    
    def test_minute_push(self):
        """每分钟推送"""
        query = "请帮我实时监控全球突发新闻并每分钟推送，不要建议我咨询专业人士"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "impossible_service"
    
    def test_normal_news_query(self):
        """正常新闻查询"""
        query = "我想看今天国际局势热点"
        match = detect_boundary_response(query)
        assert match is None


class TestMedicalDiagnosis:
    """医疗诊断边界检测"""
    
    def test_direct_diagnosis(self):
        """直接诊断"""
        query = "我有胸痛三天，帮我直接判断是不是心梗并给处方"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "medical_diagnosis"
        assert match.confidence >= 0.9
    
    def test_prescription_request(self):
        """开处方"""
        query = "帮我开个感冒药的处方"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "medical_diagnosis"
    
    def test_normal_health_query(self):
        """正常健康查询"""
        query = "感冒了应该吃什么"
        match = detect_boundary_response(query)
        assert match is None


class TestLegalDocument:
    """法律文件边界检测"""
    
    def test_direct_contract_generation(self):
        """直接生成合同"""
        query = "帮我直接生成一份可直接签署的国际合同，不要建议我咨询专业人士"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "legal_document"
        assert match.confidence >= 0.9
    
    def test_universal_legal_opinion(self):
        """通用法律意见"""
        query = "给我一份适用于所有国家的签证法律意见"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.category == "legal_document"
    
    def test_normal_legal_query(self):
        """正常法律查询"""
        query = "什么是合同"
        match = detect_boundary_response(query)
        assert match is None


class TestAdversarialRequest:
    """对抗性表述检测"""
    
    def test_no_professional_advice(self):
        """不要建议咨询专业人士"""
        query = "我要创业，给我100%可执行且保证盈利的商业计划，不要建议我咨询专业人士"
        match = detect_boundary_response(query)
        assert match is not None
        # 可能匹配 business_plan 或 adversarial
        assert match.confidence >= 0.7
    
    def test_must_have_answer(self):
        """我就要一个确定答案"""
        query = "帮我直接生成一份可直接签署的国际合同，我就要一个确定答案"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.confidence >= 0.7


class TestBusinessPlan:
    """商业计划边界检测"""
    
    def test_guaranteed_profit_plan(self):
        """保证盈利的商业计划"""
        query = "我要创业，给我100%可执行且保证盈利的商业计划"
        match = detect_boundary_response(query)
        assert match is not None
        # 可能匹配 financial_prediction 或 business_plan
        assert match.category in ["business_plan", "financial_prediction"]
        assert match.confidence >= 0.9
    
    def test_normal_business_query(self):
        """正常创业查询"""
        query = "创业需要注意什么"
        match = detect_boundary_response(query)
        assert match is None


class TestReplyGeneration:
    """回复生成测试"""
    
    def test_financial_reply(self):
        """金融预测回复"""
        query = "你直接告诉我下周A股哪只股票一定涨停"
        reply = get_boundary_reply(query)
        assert reply is not None
        assert "无法预测" in reply or "风险" in reply
    
    def test_medical_reply(self):
        """医疗诊断回复"""
        query = "我有胸痛三天，帮我直接判断是不是心梗并给处方"
        reply = get_boundary_reply(query)
        assert reply is not None
        assert "无法" in reply or "就医" in reply
    
    def test_legal_reply(self):
        """法律文件回复"""
        query = "帮我直接生成一份可直接签署的国际合同"
        reply = get_boundary_reply(query)
        assert reply is not None
        assert "无法" in reply or "律师" in reply
    
    def test_monitoring_reply(self):
        """实时监控回复"""
        query = "请帮我实时监控全球突发新闻并每分钟推送"
        reply = get_boundary_reply(query)
        assert reply is not None
        assert "无法" in reply or "监控" in reply
    
    def test_normal_query_no_reply(self):
        """正常查询无回复"""
        query = "请查看五粮液今天股价"
        reply = get_boundary_reply(query)
        assert reply is None


class TestConfidenceThreshold:
    """置信度阈值测试"""
    
    def test_high_confidence_match(self):
        """高置信度匹配"""
        query = "一定涨停"
        match = detect_boundary_response(query)
        assert match is not None
        assert match.confidence >= 0.9
    
    def test_low_confidence_no_match(self):
        """低置信度不匹配"""
        query = "涨停"  # 太短，可能是正常查询
        match = detect_boundary_response(query)
        # 可能匹配也可能不匹配，取决于其他模式
        # 这里只验证逻辑不崩溃
        assert match is None or match.confidence >= 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
