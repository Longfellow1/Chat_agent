from __future__ import annotations

import re

from app.policies.boundary_response import get_boundary_reply

END_CHAT_PATTERNS = [
    r"^不聊了$",
    r"^就到这$",
    r"^先这样$",
    r"^我先走了$",
]

ILLEGAL_PATTERNS = (
    # 证件相关
    "伪造证件",
    "假身份证",
    "办假证",
    # 爆炸物/武器
    "制作炸弹",
    "爆炸物",
    "炸药",
    "危险武器",
    "制造武器",
    # 网络犯罪
    "黑客攻击",
    "黑进",
    "黑客入侵",
    "入侵账号",
    "盗号",
    "ddos",
    "撞库",
    "攻击网站",
    # 诈骗/洗钱
    "诈骗话术",
    "洗钱",
    # 毒品
    "贩毒",
    "毒品",
    "违禁品",
    # 赌博
    "开赌场",
    "赌博局",
    "赌博",
    # 逃避执法
    "警方追踪",
    "逃避警察",
    "躲避执法",
    # 其他非法
    "教我做",  # 通用模式: 教我做[非法事项]
)

CRISIS_PATTERNS = (
    "不想活了",
    "想自杀",
    "结束生命",
    "活着没意思",
    "我想死",
    "轻生",
)



def detect_end_chat(query: str) -> bool:
    text = query.strip()
    for pat in END_CHAT_PATTERNS:
        if re.match(pat, text):
            return True
    return False


def detect_meaningless_noise(query: str) -> bool:
    text = query.strip()
    if not text:
        return True
    if len(text) >= 6 and len(set(text)) <= 2:
        # 放行 6 位股票代码（如 000001 只有 2 种字符但是合法代码）
        if not re.fullmatch(r"\d{6}", text):
            return True
    if re.fullmatch(r"[0-9\W_]+", text):
        # 放行：6位股票代码（如 600519, 000001）
        if re.fullmatch(r"\d{6}", text):
            return False
        # 放行：快递/运单号（字母+数字，10位以上，如 SF1234567890）
        if re.fullmatch(r"[A-Za-z]{1,4}\d{8,}", text):
            return False
        return True
    return False


def detect_illegal_sensitive(query: str) -> bool:
    text = query.strip().lower()
    return any(k in text for k in ILLEGAL_PATTERNS)


def detect_crisis(query: str) -> bool:
    text = query.strip().lower()
    return any(k in text for k in CRISIS_PATTERNS)


def detect_boundary_response(query: str) -> bool:
    """检测能力边界请求 - 使用新的分层策略"""
    return get_boundary_reply(query) is not None
