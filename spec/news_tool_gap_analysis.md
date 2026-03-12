    # 新闻工具现状与产品需求差距分析

    ## 1. 现状分析

    ### 1.1 当前实现（mcp_gateway.py）

    ```python
    def _news(self, topic: str) -> ToolResult:
        query = f"{topic} 最新新闻"
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": self.news_depth or "basic",
            "topic": "news",
            "max_results": max(1, self.search_max_results),
        }
        # 调用 Tavily API
        results = body.get("results") or []
        packed = _pack_search_results(results, ...)
        
        # 直接拼接原始结果
        lines = [f"{i}. {r['title']} | {r['url']} | {r['snippet']}" for i, r in enumerate(packed, 1)]
        text = f""{topic}"相关新闻：\n" + "\n".join(lines)
        return ToolResult(ok=True, text=text, ...)
    ```

    **问题**：
    1. ❌ 直接返回原始格式：`title | url | snippet`
    2. ❌ 包含大量噪声：URL、格式标记、转义字符
    3. ❌ 没有内容重写和摘要提取
    4. ❌ 用户体验差：需要手动清理和理解

    ### 1.2 用户反馈的实际输出

    ```
    以下是今天的部分财经新闻：\n\n
    1. CNBC的《市场收盘后》报道：提供快速、准确和实用的市场更新。[查看原文](https://www.cnbc.com/video/2026/03/03/the-post-market-wrap-march-3-2026.html)\n\n
    2. 芯片巨头英伟达财报公布后，道指期货小幅下跌；投资者关注英伟达业绩——[查看原文](https://www.wsj.com/livecoverage/stock-market-today-dow-sp-500-nasdaq-02-26-2026)
    ```

    **噪声类型**：
    - URL 链接（完整的 https://...）
    - Markdown 格式标记（`[查看原文](...)`）
    - 转义字符（`\n`）
    - 冗余文本（"查看原文"、"——"）

    ---

    ## 2. 产品需求

    ### 2.1 用户期望

    用户问："今天财经新闻有什么"

    期望得到：
    ```
    今日财经市场概要：

    1. 美股收盘：道指下跌700点，科技股表现不佳，美国通胀报告超预期
    2. 芯片行业：英伟达财报公布后市场反应谨慎，投资者关注业绩指引
    3. 市场趋势：CNBC报道显示市场波动加剧，投资者情绪偏谨慎
    ```

    **核心要求**：
    - ✅ 清晰的摘要（无噪声）
    - ✅ 提取核心信息（趋势、数据、事件）
    - ✅ 结构化呈现（分类、编号）
    - ✅ 用户友好的语言

    ### 2.2 产品设计目标

    1. **内容质量**：去噪 + 摘要 + 重写
    2. **信息密度**：每条新闻 50-100 字
    3. **可读性**：清晰、专业、无冗余
    4. **时效性**：保留时间信息（今日、最新）

    ---

    ## 3. 差距总结

    | 维度 | 现状 | 需求 | 差距 |
    |------|------|------|------|
    | **输出格式** | `title \| url \| snippet` | 清晰的摘要文本 | ❌ 需要重写 |
    | **噪声处理** | 无处理，直接返回 | 去除 URL、格式标记 | ❌ 需要清理 |
    | **内容提取** | 原始 snippet | 核心信息（趋势、数据） | ❌ 需要 LLM 提取 |
    | **结构化** | 简单列表 | 分类、编号、摘要 | ❌ 需要后处理 |
    | **用户体验** | 需要手动理解 | 直接可读 | ❌ 需要优化 |

    ---

    ## 4. 解决方案

    ### 4.1 架构设计

    ```
    用户查询 "今天财经新闻"
        ↓
    [Planner] 识别意图 → get_news(topic="财经")
        ↓
    [Gateway] 调用 Tavily API → 获取原始结果
        ↓
    [ContentRewriter] 后处理
        ├─ 清理噪声（URL、格式标记）
        ├─ LLM 重写（提取核心信息）
        └─ 结构化输出（分类、摘要）
        ↓
    返回用户友好的摘要
    ```

    ### 4.2 实施方案

    #### Phase 1：集成 ContentRewriter（已完成）

    ✅ 创建 `content_rewriter.py` 模块
    ✅ 实现噪声清理逻辑
    ✅ 实现 LLM 重写接口
    ✅ 添加单元测试

    #### Phase 2：在 Gateway 中集成（待实施）

    修改 `mcp_gateway.py` 的 `_news()` 方法：

    ```python
    def _news(self, topic: str) -> ToolResult:
        # 1. 调用 Tavily API（现有逻辑）
        results = self._call_tavily_news(topic)
        
        # 2. 后处理：重写内容
        if results.ok and self.enable_content_rewrite:
            from infra.tool_clients.content_rewriter import rewrite_news_batch
            
            # 提取原始新闻列表
            raw_results = results.raw.get("results", [])
            
            # 批量重写
            rewritten = rewrite_news_batch(
                news_items=raw_results,
                llm_client=self.llm_client,  # 需要注入
                config=RewriteConfig(enable_llm=True)
            )
            
            # 3. 格式化输出
            lines = []
            for i, item in enumerate(rewritten, 1):
                content = item["content"]
                lines.append(f"{i}. {content}")
            
            text = f""{topic}"相关新闻摘要：\n" + "\n\n".join(lines)
            results.text = text
        
        return results
    ```

    #### Phase 3：配置管理

    添加环境变量：
    ```bash
    # 是否启用内容重写
    ENABLE_CONTENT_REWRITE=true

    # 重写配置
    CONTENT_REWRITE_MAX_LENGTH=200
    CONTENT_REWRITE_TIMEOUT=5.0
    ```

    ---

    ## 5. 实施计划

    ### 5.1 短期（1-2天）

    - [ ] 在 `mcp_gateway.py` 中集成 `ContentRewriter`
    - [ ] 添加配置开关（`ENABLE_CONTENT_REWRITE`）
    - [ ] 注入 LLM 客户端到 Gateway
    - [ ] 添加集成测试

    ### 5.2 中期（3-5天）

    - [ ] 优化 LLM 提示词（针对不同新闻类型）
    - [ ] 添加缓存机制（避免重复重写）
    - [ ] 性能优化（批量处理、并发）
    - [ ] 添加降级策略（LLM 失败时的规则提取）

    ### 5.3 长期（可选）

    - [ ] 支持多种新闻类型（财经、科技、体育）
    - [ ] 个性化摘要（根据用户偏好）
    - [ ] 多语言支持
    - [ ] 实时新闻流

    ---

    ## 6. 风险评估

    | 风险 | 影响 | 概率 | 缓解措施 |
    |------|------|------|----------|
    | LLM 重写失败 | 高 | 中 | 降级到规则提取 |
    | 性能开销（LLM 调用） | 中 | 高 | 批量处理 + 缓存 |
    | 内容质量不稳定 | 中 | 中 | 优化提示词 + 人工评测 |
    | 配置复杂度 | 低 | 低 | 提供默认配置 |

    ---

    ## 7. 验收标准

    ### 7.1 功能验收

    - [ ] 新闻输出无 URL 和格式标记
    - [ ] 每条新闻摘要 50-200 字
    - [ ] 保留核心信息（趋势、数据、事件）
    - [ ] 用户可读性良好

    ### 7.2 性能验收

    - [ ] 重写时延 < 500ms（单条）
    - [ ] 批量重写时延 < 2s（5条）
    - [ ] LLM 失败时降级正常

    ### 7.3 质量验收

    - [ ] 人工评测准确率 >= 85%
    - [ ] 用户满意度 >= 4/5
    - [ ] 无信息丢失或曲解

    ---

    ## 8. 总结

    **核心问题**：新闻工具直接返回原始格式，包含大量噪声，用户体验差

    **解决方案**：集成 ContentRewriter 进行后处理（清理 + 重写 + 结构化）

    **优先级**：高（影响用户体验的核心问题）

    **工作量**：2-3 天（Phase 1-2）

    **依赖**：LLM 客户端（已有）、ContentRewriter 模块（已完成）
