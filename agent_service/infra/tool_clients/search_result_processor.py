"""
搜索结果处理模块

提供相关性过滤、去重、可信度评分、时效性排序等功能
"""

from typing import Any
from urllib.parse import urlparse
from datetime import datetime


class SearchResultProcessor:
    """搜索结果处理器"""
    
    def __init__(
        self,
        max_results: int = 3,
        relevance_threshold: float = 0.3,
        dedup_threshold: float = 0.8,
    ):
        """
        初始化处理器
        
        Args:
            max_results: 最大返回结果数
            relevance_threshold: 相关性阈值
            dedup_threshold: 去重相似度阈值
        """
        self.max_results = max_results
        self.relevance_threshold = relevance_threshold
        self.dedup_threshold = dedup_threshold
    
    def process_results(
        self,
        results: list[dict[str, Any]],
        query: str,
        keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        处理搜索结果：相关性过滤 → 综合评分 → 去重（保留高分） → 排序
        
        Args:
            results: 原始搜索结果列表
            query: 用户查询
            keywords: 查询关键词列表
            
        Returns:
            处理后的结果列表
        """
        if not results:
            return []
        
        # 1. 提取关键词（如果未提供）
        if keywords is None:
            try:
                from domain.tools.query_preprocessor import extract_keywords
            except ImportError:
                from agent_service.domain.tools.query_preprocessor import extract_keywords
            keywords = extract_keywords(query, top_k=5)
        
        # 2. 相关性过滤
        filtered = []
        for result in results:
            relevance = calculate_relevance(result, keywords)
            if relevance >= self.relevance_threshold:
                result["relevance"] = relevance
                filtered.append(result)
        
        # 3. 综合评分（相关性 + 可信度 + 时效性）
        for result in filtered:
            # 可信度评分
            url = result.get("url", "")
            credibility = score_credibility(url) / 10.0  # 归一化到 [0, 1]
            
            # 时效性评分
            published_date = result.get("published_date", "")
            timeliness = calculate_timeliness(published_date)
            
            # 综合评分
            # NOTE: Timeliness weight is 0% because Tavily doesn't return published_date
            # If switching to Bing (which provides dates), can restore timeliness weight
            # Original design: relevance 60% + credibility 25% + timeliness 15%
            # Current: relevance 70% + credibility 30% + timeliness 0%
            result["credibility"] = credibility
            result["timeliness"] = timeliness
            result["score"] = (
                result["relevance"] * 0.7 +    # Relevance: 70% (was 60%)
                credibility * 0.3 +            # Credibility: 30% (was 25%)
                timeliness * 0.0               # Timeliness: 0% (was 15%, disabled)
            )
        
        # 4. 去重（保留高分的）
        unique = dedup_results_keep_best(filtered, threshold=self.dedup_threshold)
        
        # 5. 排序
        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return unique[:self.max_results]


def calculate_timeliness(published_date: str) -> float:
    """
    计算时效性得分
    
    Args:
        published_date: 发布日期（ISO 格式，如 "2026-03-05"）
        
    Returns:
        时效性得分 [0.0, 1.0]
    """
    if not published_date:
        return 0.5  # 无日期时返回中等分数
    
    try:
        # 解析日期
        pub_date = datetime.fromisoformat(published_date.split("T")[0])
        now = datetime.now()
        
        # 计算天数差
        days_diff = (now - pub_date).days
        
        # 评分规则
        if days_diff < 0:
            return 1.0  # 未来日期（可能是预告）
        elif days_diff <= 7:
            return 1.0  # 一周内
        elif days_diff <= 30:
            return 0.9  # 一个月内
        elif days_diff <= 90:
            return 0.7  # 三个月内
        elif days_diff <= 180:
            return 0.5  # 半年内
        elif days_diff <= 365:
            return 0.3  # 一年内
        else:
            return 0.1  # 一年以上
    except Exception:
        return 0.5  # 解析失败时返回中等分数


def calculate_relevance(result: dict[str, Any], keywords: list[str]) -> float:
    """
    计算搜索结果的相关性得分
    
    Args:
        result: 搜索结果字典，包含 title, snippet 等字段
        keywords: 查询关键词列表
        
    Returns:
        相关性得分 [0.0, 1.0]
    """
    if not keywords:
        return 0.5  # 无关键词时返回中等分数
    
    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()
    
    score = 0.0
    
    # 标题匹配（权重 0.6）
    title_match = sum(1 for kw in keywords if kw.lower() in title)
    if keywords:
        score += (title_match / len(keywords)) * 0.6
    
    # 摘要匹配（权重 0.4）
    snippet_match = sum(1 for kw in keywords if kw.lower() in snippet)
    if keywords:
        score += (snippet_match / len(keywords)) * 0.4
    
    return min(score, 1.0)


def dedup_results_keep_best(results: list[dict[str, Any]], threshold: float = 0.8) -> list[dict[str, Any]]:
    """
    去重搜索结果（保留评分更高的）
    
    Args:
        results: 搜索结果列表（必须已经有 score 字段）
        threshold: 相似度阈值，超过此值视为重复
        
    Returns:
        去重后的结果列表
    """
    if not results:
        return []
    
    # 按评分降序排序
    sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    
    deduped = []
    seen_titles = []
    
    for result in sorted_results:
        title = result.get("title", "")
        if not title:
            deduped.append(result)
            continue
        
        # 检查是否与已有标题相似
        is_duplicate = False
        for seen_title in seen_titles:
            if _title_similarity(title, seen_title) > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduped.append(result)
            seen_titles.append(title)
    
    return deduped


def dedup_results(results: list[dict[str, Any]], threshold: float = 0.8) -> list[dict[str, Any]]:
    """
    去重搜索结果（基于标题相似度）
    
    Args:
        results: 搜索结果列表
        threshold: 相似度阈值，超过此值视为重复
        
    Returns:
        去重后的结果列表
    """
    if not results:
        return []
    
    deduped = []
    seen_titles = []
    
    for result in results:
        title = result.get("title", "")
        if not title:
            deduped.append(result)
            continue
        
        # 检查是否与已有标题相似
        is_duplicate = False
        for seen_title in seen_titles:
            if _title_similarity(title, seen_title) > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduped.append(result)
            seen_titles.append(title)
    
    return deduped


def _title_similarity(title1: str, title2: str) -> float:
    """
    计算两个标题的相似度（基于字符级 Jaccard 相似度）
    
    Args:
        title1: 标题1
        title2: 标题2
        
    Returns:
        相似度 [0.0, 1.0]
    """
    # 移除空格和标点，转小写
    import re
    clean1 = re.sub(r'[\s\W]+', '', title1.lower())
    clean2 = re.sub(r'[\s\W]+', '', title2.lower())
    
    if not clean1 or not clean2:
        return 0.0
    
    # 使用字符级 n-gram (bigram)
    def get_bigrams(s):
        return set(s[i:i+2] for i in range(len(s)-1))
    
    bigrams1 = get_bigrams(clean1)
    bigrams2 = get_bigrams(clean2)
    
    if not bigrams1 or not bigrams2:
        # 降级到字符集合
        chars1 = set(clean1)
        chars2 = set(clean2)
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        return intersection / union if union > 0 else 0.0
    
    intersection = len(bigrams1 & bigrams2)
    union = len(bigrams1 | bigrams2)
    
    return intersection / union if union > 0 else 0.0


def score_credibility(url: str) -> int:
    """
    计算来源可信度评分
    
    实现方案：
    - 基于域名后缀规则（.gov.cn > .edu.cn > 知名媒体）
    - 维护白名单（避免硬编码字符串）
    
    评分规则：
    - .gov.cn: 10 分（政府网站）
    - .edu.cn: 9 分（教育机构）
    - .org.cn: 8 分（组织机构）
    - 知名媒体白名单: 7-10 分
    - 其他有明确域名: 5 分
    - 无域名: 0 分
    
    性能：< 1ms
    
    Args:
        url: 来源 URL
        
    Returns:
        可信度评分 [0, 10]
    """
    if not url:
        return 0
    
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 0
    
    if not domain:
        return 0
    
    # 后缀规则
    if domain.endswith(".gov.cn") or domain.endswith(".gov"):
        return 10
    if domain.endswith(".edu.cn") or domain.endswith(".edu"):
        return 9
    if domain.endswith(".org.cn") or domain.endswith(".org"):
        return 8
    
    # 白名单（知名媒体和平台）
    TRUSTED_DOMAINS = {
        # 官方媒体（10分）
        "xinhuanet.com": 10,
        "people.com.cn": 10,
        "cctv.com": 10,
        "chinanews.com": 10,
        
        # 主流媒体（9分）
        "sina.com.cn": 9,
        "sohu.com": 9,
        "163.com": 9,
        "qq.com": 9,
        
        # 百科类（8分）
        "baike.baidu.com": 8,
        "wikipedia.org": 8,
        
        # 科技媒体（7分）
        "36kr.com": 7,
        "ithome.com": 7,
        "cnbeta.com": 7,
        
        # UGC 平台（6分）- 内容质量参差不齐
        "zhihu.com": 6,
        "weibo.com": 6,
        "douban.com": 6,
        "xiaohongshu.com": 6,
    }
    
    if domain in TRUSTED_DOMAINS:
        return TRUSTED_DOMAINS[domain]
    
    # 检查是否是子域名
    for trusted_domain, score in TRUSTED_DOMAINS.items():
        if domain.endswith("." + trusted_domain):
            return score
    
    # 默认：有明确域名得 5 分
    return 5


def process_search_results(
    results: list[dict[str, Any]],
    query: str,
    keywords: list[str] | None = None,
    max_results: int = 3,
    relevance_threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """
    处理搜索结果：相关性过滤 → 去重 → 可信度评分 → 排序
    
    Args:
        results: 原始搜索结果列表
        query: 用户查询
        keywords: 查询关键词列表（如果为 None，从 query 中提取）
        max_results: 最大返回结果数
        relevance_threshold: 相关性阈值，低于此值的结果被过滤
        
    Returns:
        处理后的结果列表
    """
    if not results:
        return []
    
    # 1. 提取关键词（如果未提供）
    if keywords is None:
        try:
            from domain.tools.query_preprocessor import extract_keywords
        except ImportError:
            from agent_service.domain.tools.query_preprocessor import extract_keywords
        keywords = extract_keywords(query, top_k=5)
    
    # 2. 相关性过滤
    filtered = []
    for result in results:
        relevance = calculate_relevance(result, keywords)
        if relevance >= relevance_threshold:
            result["relevance"] = relevance
            filtered.append(result)
    
    # 3. 去重
    unique = dedup_results(filtered, threshold=0.8)
    
    # 4. 来源可信度评分
    for result in unique:
        url = result.get("url", "")
        result["credibility"] = score_credibility(url)
    
    # 5. 排序（相关性 * 可信度）
    # 归一化可信度到 [0, 1]
    for result in unique:
        credibility_normalized = result["credibility"] / 10.0
        result["score"] = result["relevance"] * 0.7 + credibility_normalized * 0.3
    
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return unique[:max_results]
