"""
M2 任务4：端到端测试

验证 web_search 在真实数据上的效果，重点检查：
1. Tavily 返回数据的字段完整性（published_date、url 占比）
2. 排序算法在真实数据上是否生效
3. 停用词是否误删时间词
4. 相关性有效率是否达到 85%
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agent_service"))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env.agent')

# 检查 Tavily API key
if not os.getenv("TAVILY_API_KEY"):
    print("错误: 未设置 TAVILY_API_KEY 环境变量")
    print("请运行: export TAVILY_API_KEY=your_key")
    sys.exit(1)

from infra.tool_clients.providers.tavily_provider import TavilyProvider
from infra.tool_clients.provider_base import ProviderConfig
from infra.tool_clients.search_result_processor import SearchResultProcessor
from domain.tools.query_preprocessor import preprocess_web_search_query

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

RAW_DATA_FILE = DATA_DIR / "m2_task4_raw_data.json"
SCORES_FILE = DATA_DIR / "m2_task4_scores.json"
REPORT_FILE = Path(__file__).parent / "m2_task4_report.md"


# 测试集：30条查询，覆盖各种场景
TEST_CASES = [
    # === 时效性查询（5条）- 验证时间词是否被误删 ===
    {
        "query": "最近的油价",
        "category": "时效性",
        "expected_time_word": "最近",
    },
    {
        "query": "今天的新闻",
        "category": "时效性",
        "expected_time_word": "今天",
    },
    {
        "query": "2026年世界杯",
        "category": "时效性",
        "expected_time_word": "2026",
    },
    {
        "query": "最新的iPhone",
        "category": "时效性",
        "expected_time_word": "最新",
    },
    {
        "query": "现在的天气",
        "category": "时效性",
        "expected_time_word": "现在",
    },
    
    # === 新闻类（5条）===
    {
        "query": "特斯拉最新消息",
        "category": "新闻",
    },
    {
        "query": "苹果发布会",
        "category": "新闻",
    },
    {
        "query": "世界杯比赛结果",
        "category": "新闻",
    },
    {
        "query": "iPhone 15价格",
        "category": "新闻",
    },
    {
        "query": "华为Mate 60评测",
        "category": "新闻",
    },
    
    # === 百科类（5条）===
    {
        "query": "量子计算原理",
        "category": "百科",
    },
    {
        "query": "区块链技术",
        "category": "百科",
    },
    {
        "query": "人工智能发展史",
        "category": "百科",
    },
    {
        "query": "马斯克个人经历",
        "category": "百科",
    },
    {
        "query": "五条人乐队成员",
        "category": "百科",
    },
    
    # === 问答类（5条）===
    {
        "query": "Python怎么学",
        "category": "问答",
    },
    {
        "query": "React框架优缺点",
        "category": "问答",
    },
    {
        "query": "如何学习量子计算",
        "category": "问答",
    },
    {
        "query": "特斯拉值得买吗",
        "category": "问答",
    },
    {
        "query": "iPhone和华为哪个好",
        "category": "问答",
    },
    
    # === 攻略类（5条）===
    {
        "query": "杭州西湖旅游攻略",
        "category": "攻略",
    },
    {
        "query": "格里菲斯天文台游玩攻略",
        "category": "攻略",
    },
    {
        "query": "洛杉矶旅游景点推荐",
        "category": "攻略",
    },
    {
        "query": "北京美食推荐",
        "category": "攻略",
    },
    {
        "query": "上海购物攻略",
        "category": "攻略",
    },
    
    # === 技术类（5条）===
    {
        "query": "Docker教程",
        "category": "技术",
    },
    {
        "query": "Kubernetes部署",
        "category": "技术",
    },
    {
        "query": "Git使用指南",
        "category": "技术",
    },
    {
        "query": "MySQL优化",
        "category": "技术",
    },
    {
        "query": "Redis缓存",
        "category": "技术",
    },
]


class TestRecorder:
    """测试记录器：记录原始数据和评分"""
    
    def __init__(self):
        self.raw_data = []
        self.scores = []
    
    def record_query(self, query_id, query, response, preprocessed=None):
        """记录问答对原始内容"""
        self.raw_data.append({
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "preprocessed": preprocessed,
            "response": response,
        })
    
    def record_score(self, query_id, query, scores, final_judgment):
        """记录过程分数"""
        self.scores.append({
            "query_id": query_id,
            "query": query,
            "scores": scores,
            "final_judgment": final_judgment,
        })
    
    def save(self):
        """保存数据到文件"""
        with open(RAW_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, ensure_ascii=False, indent=2)
        
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)
        
        print(f"\n原始数据已保存: {RAW_DATA_FILE}")
        print(f"评分数据已保存: {SCORES_FILE}")


class ReportGenerator:
    """报告生成器：生成 Markdown 报告"""
    
    def __init__(self, raw_data, scores, field_stats, time_word_stats):
        self.raw_data = raw_data
        self.scores = scores
        self.field_stats = field_stats
        self.time_word_stats = time_word_stats
    
    def generate(self):
        """生成报告"""
        report = []
        
        # 标题
        report.append("# M2 任务4：端到端测试报告\n\n")
        report.append(f"**测试日期**: {datetime.now().strftime('%Y-%m-%d')}\n")
        report.append(f"**测试集**: {len(self.scores)} 条查询\n")
        report.append(f"**测试目标**: 验证 web_search 在真实数据上的效果\n")
        report.append("\n---\n\n")
        
        # 测试概览
        report.append("## 一、测试概览\n\n")
        report.append(self._generate_overview())
        report.append("\n---\n\n")
        
        # 字段完整性统计
        report.append("## 二、Tavily 数据字段完整性\n\n")
        report.append(self._generate_field_stats())
        report.append("\n---\n\n")
        
        # 时间词保留率
        report.append("## 三、时间词保留率\n\n")
        report.append(self._generate_time_word_stats())
        report.append("\n---\n\n")
        
        # 技术有效率
        report.append("## 四、技术有效率\n\n")
        report.append(self._generate_technical_validity())
        report.append("\n---\n\n")
        
        # 问答对示例
        report.append("## 五、问答对示例\n\n")
        report.append(self._generate_qa_examples())
        report.append("\n---\n\n")
        
        # 失败案例分析
        report.append("## 六、失败案例分析\n\n")
        report.append(self._generate_failure_analysis())
        report.append("\n---\n\n")
        
        # 改进建议
        report.append("## 七、改进建议\n\n")
        report.append(self._generate_suggestions())
        report.append("\n---\n\n")
        
        # 下一步
        report.append("## 八、下一步\n\n")
        report.append("1. **相关性评估**: 需要人工评估 30 条查询的相关性（目标 ≥ 85%）\n")
        report.append("2. **用户满意度**: 需要人工评估 30 条查询的满意度（目标 ≥ 75%）\n")
        report.append("3. **排序算法优化**: 根据字段完整性调整权重配置\n")
        report.append("\n---\n\n")
        
        # 原始数据链接
        report.append("## 九、原始数据\n\n")
        report.append(f"完整原始数据见: `{RAW_DATA_FILE.relative_to(Path.cwd())}`\n")
        report.append(f"完整评分数据见: `{SCORES_FILE.relative_to(Path.cwd())}`\n")
        report.append("\n---\n\n")
        
        # 人工复核提示
        report.append("## 人工复核\n\n")
        report.append("**复核人**: [待填写]\n")
        report.append(f"**复核日期**: [待填写]\n")
        report.append("**复核结果**: [ ] 通过 / [ ] 需要修正\n\n")
        report.append("**复核意见**:\n")
        report.append("1. [待填写]\n")
        report.append("\n---\n\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**测试脚本**: `tests/integration/test_m2_task4_end_to_end.py`\n")
        
        return "".join(report)
    
    def _generate_overview(self):
        """生成概览"""
        total = len(self.scores)
        passed = sum(1 for s in self.scores if s['final_judgment'] == 'pass')
        failed = total - passed
        pass_rate = passed / total * 100 if total > 0 else 0
        
        return f"""| 指标 | 结果 | 目标 | 状态 |
|------|------|------|------|
| 总查询数 | {total} | - | - |
| 通过数 | {passed} | - | - |
| 失败数 | {failed} | - | - |
| 通过率 | {pass_rate:.1f}% | ≥ 90% | {'✅' if pass_rate >= 90 else '❌'} |
"""
    
    def _generate_field_stats(self):
        """生成字段完整性统计"""
        total_results = self.field_stats['total_results']
        if total_results == 0:
            return "❌ 无结果数据\n"
        
        url_pct = self.field_stats['has_url'] / total_results * 100
        date_pct = self.field_stats['has_published_date'] / total_results * 100
        both_pct = self.field_stats['has_both'] / total_results * 100
        
        result = f"""| 指标 | 数值 | 占比 |
|------|------|------|
| 总结果数 | {total_results} | 100% |
| 有 URL | {self.field_stats['has_url']} | {url_pct:.1f}% |
| 有发布日期 | {self.field_stats['has_published_date']} | {date_pct:.1f}% |
| 两者都有 | {self.field_stats['has_both']} | {both_pct:.1f}% |

"""
        
        if date_pct >= 50 and url_pct >= 50:
            result += "**结论**: ✅ 字段完整性 ≥ 50%，排序算法有效\n"
        else:
            result += "**结论**: ⚠️ 字段完整性 < 50%，排序算法可能退化\n"
            result += "**建议**: 重新设计排序算法，降低可信度和时效性权重\n"
        
        return result
    
    def _generate_time_word_stats(self):
        """生成时间词保留率统计"""
        preserved = self.time_word_stats['preserved']
        total = self.time_word_stats['total']
        
        if total == 0:
            return "无时间词测试用例\n"
        
        pct = preserved / total * 100
        
        result = f"""| 指标 | 数值 |
|------|------|
| 时间词总数 | {total} |
| 保留数 | {preserved} |
| 保留率 | {pct:.1f}% |

"""
        
        if pct >= 80:
            result += "**结论**: ✅ 时间词保留率 ≥ 80%\n"
        else:
            result += "**结论**: ⚠️ 时间词保留率 < 80%，停用词可能过度删除\n"
            result += "**建议**: 从停用词列表中移除时间相关词汇\n"
        
        return result
    
    def _generate_technical_validity(self):
        """生成技术有效率统计"""
        total = len(self.scores)
        valid = sum(1 for s in self.scores if s['scores']['technical_validity']['score'] == 1.0)
        validity_rate = valid / total * 100 if total > 0 else 0
        
        result = f"""| 指标 | 数值 |
|------|------|
| 总查询数 | {total} |
| 有效数 | {valid} |
| 技术有效率 | {validity_rate:.1f}% |

**M2 目标**: ≥ 90%  
**当前状态**: {'✅ 达标' if validity_rate >= 90 else '❌ 未达标'}
"""
        
        return result
    
    def _generate_qa_examples(self):
        """生成问答对示例（展示前5条成功案例和前3条失败案例）"""
        examples = []
        
        # 成功案例
        examples.append("### 成功案例\n\n")
        success_cases = [s for s in self.scores if s['final_judgment'] == 'pass'][:5]
        
        for i, case in enumerate(success_cases, 1):
            raw = next((r for r in self.raw_data if r['query_id'] == case['query_id']), None)
            if not raw:
                continue
            
            examples.append(f"#### 案例 {i}\n\n")
            examples.append(f"**Query**: {case['query']}\n\n")
            
            # 预处理信息
            if raw.get('preprocessed'):
                preprocessed = raw['preprocessed']
                examples.append(f"**预处理**:\n")
                examples.append(f"- 标准化: {preprocessed.get('normalized_query', 'N/A')}\n")
                examples.append(f"- 关键词: {', '.join(preprocessed.get('keywords', []))}\n\n")
            
            # 返回结果
            response = raw.get('response', {})
            if response.get('ok') and response.get('ranked_results'):
                ranked = response['ranked_results']
                examples.append(f"**返回结果数**: {len(ranked)}\n\n")
                
                # Top 3 结果
                examples.append("**Top 3 结果**:\n")
                for j, result in enumerate(ranked[:3], 1):
                    examples.append(f"{j}. {result.get('title', 'N/A')}\n")
                    examples.append(f"   - URL: {result.get('url', 'N/A')}\n")
                    
                    # 添加 snippet/content
                    content = result.get('content') or result.get('snippet', '')
                    if content:
                        # 检测乱码：正常中英文字符比例过低
                        normal_chars = sum(1 for c in content if (
                            (0x4E00 <= ord(c) <= 0x9FFF) or  # 常用汉字
                            (0x0041 <= ord(c) <= 0x005A) or  # 大写字母
                            (0x0061 <= ord(c) <= 0x007A) or  # 小写字母
                            (0x0030 <= ord(c) <= 0x0039) or  # 数字
                            c in ' \n\r\t.,;:!?，。；：！？、'  # 常见标点
                        ))
                        normal_ratio = normal_chars / len(content) if len(content) > 0 else 0
                        
                        if normal_ratio < 0.5:  # 正常字符少于50%
                            examples.append(f"   - 概述: [内容编码异常，无法正常显示]\n")
                        else:
                            # 智能截断：优先在句号、问号、感叹号处截断
                            max_len = 400
                            if len(content) > max_len:
                                # 找最后一个句子结束符
                                truncated = content[:max_len]
                                last_period = max(truncated.rfind('。'), truncated.rfind('.'), 
                                                 truncated.rfind('！'), truncated.rfind('!'),
                                                 truncated.rfind('？'), truncated.rfind('?'))
                                if last_period > max_len * 0.6:  # 如果句子结束符在后60%位置
                                    content = truncated[:last_period + 1]
                                else:
                                    content = truncated + "..."
                            
                            examples.append(f"   - 概述: {content}\n")
                    else:
                        examples.append(f"   - 概述: [无内容摘要]\n")
                    
                    examples.append(f"   - 综合分: {result.get('score', 0):.2f} (相关性: {result.get('relevance', 0):.2f}, 可信度: {result.get('credibility', 0):.2f}, 时效性: {result.get('timeliness', 0):.2f})\n")
                examples.append("\n")
            
            examples.append("---\n\n")
        
        # 失败案例
        examples.append("### 失败案例\n\n")
        failure_cases = [s for s in self.scores if s['final_judgment'] == 'fail'][:3]
        
        if not failure_cases:
            examples.append("无失败案例\n\n")
        else:
            for i, case in enumerate(failure_cases, 1):
                raw = next((r for r in self.raw_data if r['query_id'] == case['query_id']), None)
                if not raw:
                    continue
                
                examples.append(f"#### 案例 {i}\n\n")
                examples.append(f"**Query**: {case['query']}\n\n")
                
                # 预处理信息
                if raw.get('preprocessed'):
                    preprocessed = raw['preprocessed']
                    examples.append(f"**预处理**:\n")
                    examples.append(f"- 标准化: {preprocessed.get('normalized_query', 'N/A')}\n")
                    examples.append(f"- 关键词: {', '.join(preprocessed.get('keywords', []))}\n\n")
                
                # 错误信息
                response = raw.get('response', {})
                if 'error' in response:
                    examples.append(f"**错误**: {response['error']}\n\n")
                elif not response.get('ok'):
                    examples.append(f"**问题**: 返回结果为空或无效\n\n")
                
                # 评分
                examples.append("**评分**:\n")
                for dim, score_data in case['scores'].items():
                    if isinstance(score_data, dict):
                        examples.append(f"- {dim}: {score_data.get('score', 'N/A')} - {score_data.get('reason', 'N/A')}\n")
                examples.append("\n")
                
                examples.append("---\n\n")
        
        return "".join(examples)
    
    def _generate_failure_analysis(self):
        """生成失败案例分析"""
        failures = [s for s in self.scores if s['final_judgment'] == 'fail']
        
        if not failures:
            return "无失败案例\n"
        
        analysis = []
        for i, failure in enumerate(failures, 1):
            analysis.append(f"### 案例{i}: {failure['query']}\n\n")
            
            # 找到对应的原始数据
            raw = next((r for r in self.raw_data if r['query_id'] == failure['query_id']), None)
            
            if raw and 'error' in raw['response']:
                analysis.append(f"**问题**: {raw['response']['error']}\n\n")
            else:
                analysis.append(f"**问题**: 技术有效性检查失败\n\n")
            
            analysis.append("**分数**:\n")
            for dim, score_data in failure['scores'].items():
                if isinstance(score_data, dict):
                    analysis.append(f"- {dim}: {score_data.get('score', 'N/A')} - {score_data.get('reason', 'N/A')}\n")
            analysis.append("\n")
        
        return "".join(analysis)
    
    def _generate_suggestions(self):
        """生成改进建议"""
        suggestions = []
        
        # 基于字段完整性
        total_results = self.field_stats['total_results']
        if total_results > 0:
            date_pct = self.field_stats['has_published_date'] / total_results * 100
            url_pct = self.field_stats['has_url'] / total_results * 100
            
            if date_pct < 50:
                suggestions.append("1. Tavily 发布日期字段缺失严重，建议降低时效性权重或移除该维度\n")
            if url_pct < 50:
                suggestions.append("2. Tavily URL 字段缺失严重，建议降低可信度权重\n")
        
        # 基于时间词保留率
        preserved = self.time_word_stats['preserved']
        total = self.time_word_stats['total']
        if total > 0:
            pct = preserved / total * 100
            if pct < 80:
                suggestions.append("3. 时间词保留率低，建议从停用词列表中移除时间相关词汇\n")
        
        # 基于技术有效率
        total_queries = len(self.scores)
        valid = sum(1 for s in self.scores if s['scores']['technical_validity']['score'] == 1.0)
        validity_rate = valid / total_queries * 100 if total_queries > 0 else 0
        
        if validity_rate < 90:
            suggestions.append("4. 技术有效率未达标，建议检查 Tavily API 稳定性和错误处理\n")
        
        if not suggestions:
            suggestions.append("暂无改进建议，系统运行正常\n")
        
        return "".join(suggestions)
    
    def save(self):
        """保存报告到文件"""
        report = self.generate()
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"报告已生成: {REPORT_FILE}")


def test_end_to_end():
    """端到端测试"""
    print("=" * 80)
    print("M2 任务4：端到端测试")
    print("=" * 80)
    print()
    
    tavily_config = ProviderConfig(
        name="tavily",
        priority=1,
        enabled=True,
        timeout=30,
        max_retries=2,
    )
    tavily = TavilyProvider(tavily_config)
    processor = SearchResultProcessor(max_results=3, relevance_threshold=0.3)
    
    # 初始化记录器
    recorder = TestRecorder()
    
    # 统计数据
    field_stats = {
        "has_url": 0,
        "has_published_date": 0,
        "has_both": 0,
        "total_results": 0,
    }
    
    time_word_stats = {
        "preserved": 0,
        "total": 0,
    }
    
    for i, case in enumerate(TEST_CASES, 1):
        query = case['query']
        category = case['category']
        
        print(f"[{i}/{len(TEST_CASES)}] {query} ({category})")
        
        # 1. Query 预处理
        preprocessed = preprocess_web_search_query(query)
        normalized = preprocessed['normalized_query']
        keywords = preprocessed['keywords']
        
        # 检查时间词是否被保留
        time_word_preserved = None
        if 'expected_time_word' in case:
            time_word = case['expected_time_word']
            time_word_stats['total'] += 1
            if time_word in normalized or time_word in ' '.join(keywords):
                time_word_stats['preserved'] += 1
                time_word_preserved = True
                print(f"  ✅ 时间词保留: {time_word}")
            else:
                time_word_preserved = False
                print(f"  ❌ 时间词丢失: {time_word}")
                print(f"     标准化: {normalized}")
                print(f"     关键词: {keywords}")
        
        # 2. 调用 Tavily
        response_data = {}
        scores = {}
        
        try:
            result = tavily.execute(query=query)
            
            if not result.ok:
                print(f"  ❌ Tavily 错误: {result.error}")
                
                response_data = {
                    "error": result.error,
                    "ok": False,
                }
                
                scores = {
                    "technical_validity": {
                        "score": 0.0,
                        "reason": f"Tavily 返回错误: {result.error}",
                    },
                    "time_word_preservation": {
                        "score": 1.0 if time_word_preserved is None or time_word_preserved else 0.0,
                        "reason": "时间词保留" if time_word_preserved else "时间词丢失" if time_word_preserved is not None else "无时间词",
                    },
                }
                
                recorder.record_query(i, query, response_data, preprocessed)
                recorder.record_score(i, query, scores, "fail")
                print()
                continue
            
            # 提取搜索结果
            raw_results = []
            if result.data and hasattr(result.data, 'raw') and 'results' in result.data.raw:
                raw_results = result.data.raw['results']
            
            # 统计字段完整性
            for result_item in raw_results:
                field_stats['total_results'] += 1
                
                has_url = bool(result_item.get('url'))
                has_date = bool(result_item.get('published_date'))
                
                if has_url:
                    field_stats['has_url'] += 1
                if has_date:
                    field_stats['has_published_date'] += 1
                if has_url and has_date:
                    field_stats['has_both'] += 1
            
            # 3. 应用排序
            ranked_results = processor.process_results(raw_results, query, keywords)
            
            print(f"  原始结果数: {len(raw_results)}")
            print(f"  排序后结果数: {len(ranked_results)}")
            
            if ranked_results:
                top1 = ranked_results[0]
                print(f"  Top1: {top1.get('title', 'N/A')[:50]}")
                print(f"    相关性: {top1.get('relevance', 0):.2f}")
                print(f"    可信度: {top1.get('credibility', 0):.2f}")
                print(f"    时效性: {top1.get('timeliness', 0):.2f}")
                print(f"    综合分: {top1.get('score', 0):.2f}")
            
            response_data = {
                "ok": True,
                "raw_count": len(raw_results),
                "ranked_count": len(ranked_results),
                "raw_results": raw_results,
                "ranked_results": ranked_results,
            }
            
            # 评分
            technical_valid = len(ranked_results) > 0
            scores = {
                "technical_validity": {
                    "score": 1.0 if technical_valid else 0.0,
                    "reason": f"返回 {len(ranked_results)} 条结果" if technical_valid else "无结果",
                },
                "time_word_preservation": {
                    "score": 1.0 if time_word_preserved is None or time_word_preserved else 0.0,
                    "reason": "时间词保留" if time_word_preserved else "时间词丢失" if time_word_preserved is not None else "无时间词",
                },
            }
            
            final_judgment = "pass" if technical_valid and (time_word_preserved is None or time_word_preserved) else "fail"
            
            recorder.record_query(i, query, response_data, preprocessed)
            recorder.record_score(i, query, scores, final_judgment)
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            
            response_data = {
                "error": str(e),
                "ok": False,
            }
            
            scores = {
                "technical_validity": {
                    "score": 0.0,
                    "reason": f"异常: {str(e)}",
                },
                "time_word_preservation": {
                    "score": 1.0 if time_word_preserved is None or time_word_preserved else 0.0,
                    "reason": "时间词保留" if time_word_preserved else "时间词丢失" if time_word_preserved is not None else "无时间词",
                },
            }
            
            recorder.record_query(i, query, response_data, preprocessed)
            recorder.record_score(i, query, scores, "fail")
        
        print()
    
    # 保存数据
    recorder.save()
    
    # 生成报告
    generator = ReportGenerator(recorder.raw_data, recorder.scores, field_stats, time_word_stats)
    generator.save()
    
    print("\n测试完成！请查看报告进行人工复核。")


if __name__ == "__main__":
    test_end_to_end()
