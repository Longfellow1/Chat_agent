"""
Boundary Response Detection - 能力边界拒识策略

目标: 高准确率 + 自然话术
策略: 分层检测 + 场景化回复
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class BoundaryMatch:
    """边界匹配结果"""
    matched: bool
    category: str  # 类别: financial_prediction, medical_diagnosis, legal_document, etc.
    confidence: float  # 置信度: 0.0-1.0
    reply_template: str  # 回复模板


# ============================================================================
# 第一层: 绝对化承诺检测 (Financial Predictions)
# ============================================================================

FINANCIAL_ABSOLUTE_PATTERNS = [
    # 直接模式
    (r"(一定|必定|肯定|保证|确保|绝对).*(涨停|涨|赚|盈利)", 1.0),
    (r"(100%|百分百|百分之百).*(盈利|赚钱|成功|涨)", 1.0),
    (r"哪(只|个|支)股票.*(一定|必定|肯定).*(涨停|涨|赚)", 1.0),
    
    # 迂回模式
    (r"(直接|马上|立刻)告诉我.*(涨停|必涨|暴涨)", 0.9),
    (r"(保证|确保).*(盈利|赚钱|不亏).*(商业计划|创业|投资)", 0.9),
    (r"(不会|绝不).*(亏|赔|失败).*(方案|计划|策略)", 0.8),
]

FINANCIAL_REPLY = (
    "我无法预测股市走势或保证投资收益。"
    "金融市场存在不确定性，任何投资都有风险。"
    "建议您根据自身风险承受能力，咨询专业投资顾问后谨慎决策。"
)


# ============================================================================
# 第二层: 实时监控/持续服务检测 (Impossible Services)
# ============================================================================

MONITORING_PATTERNS = [
    # 实时监控
    (r"(实时|持续|不间断).*(监控|跟踪|追踪)", 1.0),
    (r"(每分钟|每秒|每小时).*(推送|更新|通知)", 1.0),
    (r"(24小时|全天).*(监控|跟踪)", 1.0),
    
    # 持续服务
    (r"(一直|始终|持续).*(帮我|为我).*(监控|跟踪|关注)", 0.9),
    (r"(自动|定时).*(推送|提醒|通知).*(新闻|消息|动态)", 0.9),
]

MONITORING_REPLY = (
    "我目前无法提供实时监控或定时推送服务。"
    "我可以帮您查询当前的信息，但无法持续跟踪或自动推送。"
    "如需实时监控，建议使用专业的监控工具或订阅相关服务。"
)


# ============================================================================
# 第三层: 医疗诊断检测 (Medical Diagnosis)
# ============================================================================

MEDICAL_DIAGNOSIS_PATTERNS = [
    # 直接诊断
    (r"(直接|马上|立刻).*(判断|诊断|确诊)", 1.0),
    (r"(帮我|给我|为我).*(判断|诊断).*(是不是|是否)", 1.0),
    (r"(给|开|写).*(处方|药方|用药)", 1.0),
    
    # 医疗决策
    (r"(直接|马上).*(医疗|治疗).*(决策|方案|建议)", 0.9),
    (r"(确定|肯定).*(病|症|疾病)", 0.8),
]

MEDICAL_DIAGNOSIS_REPLY = (
    "我无法提供医疗诊断或开具处方。"
    "您描述的症状可能需要专业医生评估。"
    "建议您尽快就医或拨打急救电话，以便获得及时准确的诊疗。"
)


# ============================================================================
# 第四层: 法律文件检测 (Legal Documents)
# ============================================================================

LEGAL_DOCUMENT_PATTERNS = [
    # 直接生成
    (r"(直接|马上).*(生成|起草|写).*(合同|协议|文件)", 1.0),
    (r"(可直接|能直接|立即).*(签署|签字|盖章).*(合同|协议)", 1.0),
    (r"(给我|帮我).*(一份|完整).*(合同|协议|文件)", 0.9),
    
    # 法律意见
    (r"(给|提供).*(法律|律师).*(意见|建议|咨询)", 0.9),
    (r"(适用于|通用).*(所有|全部|任何).*(国家|地区).*(法律|合同)", 0.8),
]

LEGAL_DOCUMENT_REPLY = (
    "我无法生成具有法律效力的合同或提供法律意见。"
    "法律文件需要根据具体情况定制，并由专业律师审核。"
    "建议您咨询专业律师，确保文件的合法性和有效性。"
)


# ============================================================================
# 第五层: 对抗性表述检测 (Adversarial Requests)
# ============================================================================

ADVERSARIAL_PATTERNS = [
    # 明确对抗
    (r"不要(建议|让|叫)我.*(咨询|找|问).*(专业|律师|医生)", 1.0),
    (r"(我就要|必须给我|一定要).*(确定|肯定|绝对).*(答案|结果)", 0.9),
    (r"不要.*(废话|多说|啰嗦)", 0.8),
    
    # 强制要求
    (r"(直接|马上|立刻)给我.*(答案|结果|方案)", 0.7),
]

ADVERSARIAL_REPLY = (
    "我理解您希望快速获得答案，但某些问题确实超出了我的能力范围。"
    "为了您的利益，我建议咨询相关领域的专业人士。"
    "我可以提供一般性信息，但无法替代专业意见。"
)


# ============================================================================
# 第六层: 创业/商业计划检测 (Business Plans)
# ============================================================================

BUSINESS_PLAN_PATTERNS = [
    # 保证成功
    (r"(100%|百分百|保证|确保).*(成功|盈利|赚钱).*(商业|创业|生意)", 1.0),
    (r"(一定|必定|肯定).*(成功|盈利).*(计划|方案|策略)", 0.9),
    (r"(可执行|能执行).*(且|并).*(保证|确保).*(盈利|赚钱)", 0.9),
]

BUSINESS_PLAN_REPLY = (
    "我无法提供保证盈利的商业计划。"
    "创业存在不确定性，成功受多种因素影响。"
    "我可以提供一般性的创业思路，但建议您结合市场调研和专业咨询制定具体方案。"
)


# ============================================================================
# 主检测函数
# ============================================================================

def detect_boundary_response(query: str) -> Optional[BoundaryMatch]:
    """
    检测能力边界请求
    
    返回:
        BoundaryMatch: 如果匹配到边界请求
        None: 如果是正常请求
    """
    text = query.strip().lower()
    
    # 第一层: 金融预测
    for pattern, confidence in FINANCIAL_ABSOLUTE_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="financial_prediction",
                confidence=confidence,
                reply_template=FINANCIAL_REPLY
            )
    
    # 第二层: 实时监控
    for pattern, confidence in MONITORING_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="impossible_service",
                confidence=confidence,
                reply_template=MONITORING_REPLY
            )
    
    # 第三层: 医疗诊断
    for pattern, confidence in MEDICAL_DIAGNOSIS_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="medical_diagnosis",
                confidence=confidence,
                reply_template=MEDICAL_DIAGNOSIS_REPLY
            )
    
    # 第四层: 法律文件
    for pattern, confidence in LEGAL_DOCUMENT_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="legal_document",
                confidence=confidence,
                reply_template=LEGAL_DOCUMENT_REPLY
            )
    
    # 第五层: 对抗性表述
    for pattern, confidence in ADVERSARIAL_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="adversarial",
                confidence=confidence,
                reply_template=ADVERSARIAL_REPLY
            )
    
    # 第六层: 商业计划
    for pattern, confidence in BUSINESS_PLAN_PATTERNS:
        if re.search(pattern, text):
            return BoundaryMatch(
                matched=True,
                category="business_plan",
                confidence=confidence,
                reply_template=BUSINESS_PLAN_REPLY
            )
    
    return None


def get_boundary_reply(query: str) -> Optional[str]:
    """
    获取边界拒识回复
    
    返回:
        str: 拒识回复文本
        None: 如果不需要拒识
    """
    match = detect_boundary_response(query)
    if match and match.confidence >= 0.7:  # 置信度阈值
        return match.reply_template
    return None
