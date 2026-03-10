# Coze Chatflow 相似开源方案调研

> 针对当前工作流的功能需求，调研相似度更高的开源替代方案

**调研时间**: 2026-03-01  
**目标工作流**: `Chat_2_0224-draft.yaml` (Coze Chatflow 闲聊智能体)

---

## 📋 当前工作流功能分析

### 核心功能模块

| 模块 | 功能 | 依赖 |
|------|------|------|
| **无目标闲聊** | 日常寒暄、轻松对话 | 豆包·1.5·Pro·32k |
| **常识/百科** | 生活常识、百科知识 | 豆包·1.6·自动深度思考 |
| **天气查询** | 城市天气预报 | 墨迹天气 API |
| **新闻资讯** | 实时新闻检索 | 头条新闻 API |
| **网络搜索** | 通用信息搜索 | 头条搜索 API |
| **股票查询** | 股价、行情 | 新浪财经 API |
| **行程规划** | 旅游路线规划 | 高德地图 POI + LLM |
| **周边搜索** | 美食/景点/设施 | 高德地图 API |
| **长期记忆** | 用户记忆读写 | Coze LTM |
| **安全兜底** | 违法/敏感/自杀干预 | 规则引擎 |

### 意图路由 (7 类)

```
ID1: 违法/敏感/无意义
ID2: 人身安全风险
ID3: 实时数据/行程查询
ID4: 常识/百科
ID5: 情绪表达
ID6: 无目标闲聊
ID7: 结束对话
```

---

## 🎯 推荐开源方案

### 方案一：Dify + 自研插件 ⭐⭐⭐⭐⭐

**GitHub**: https://github.com/langgenius/dify  
**Stars**: 50K+  
**匹配度**: 90%

#### 功能对比

| 功能 | Coze Chatflow | Dify | 实现方式 |
|------|--------------|------|---------|
| 闲聊对话 | ✅ | ✅ | LLM + 提示词 |
| 意图识别 | ✅ | ✅ | 分类模型/LLM |
| 天气查询 | ✅ (墨迹) | ✅ | 自定义 API |
| 新闻资讯 | ✅ (头条) | ✅ | RSS/API |
| 网络搜索 | ✅ (头条) | ✅ | SerpAPI/Tavily |
| 股票查询 | ✅ (新浪) | ✅ | Yahoo Finance API |
| 行程规划 | ✅ | ✅ | LLM + 地图 API |
| 长期记忆 | ✅ | ✅ | 向量数据库 |
| 安全过滤 | ✅ | ✅ | 敏感词 + 规则 |

#### 优势

- ✅ **可视化编排** - 拖拽式工作流设计，类似 Coze
- ✅ **内置 RAG** - 支持知识库检索
- ✅ **多模型支持** - OpenAI/Claude/本地模型
- ✅ **API 集成** - 轻松接入天气/新闻/股票 API
- ✅ **中文友好** - 团队来自中国，文档完善
- ✅ **自托管** - 完全控制数据和部署

#### 部署方案

```bash
# Docker Compose 一键部署
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker compose up -d

# 访问 http://localhost:3000
```

#### 插件开发示例

```python
# weather_plugin.py
import requests

def get_weather(city: str, date: str) -> dict:
    """获取天气信息"""
    response = requests.get(
        f"https://api.weather.com/v1/forecast",
        params={"city": city, "date": date}
    )
    return response.json()

# 在 Dify 中注册为工具
{
    "name": "get_weather",
    "description": "查询城市天气",
    "parameters": {
        "city": {"type": "string", "required": True},
        "date": {"type": "string", "required": False}
    }
}
```

---

### 方案二：Flowise ⭐⭐⭐⭐

**GitHub**: https://github.com/FlowiseAI/Flowise  
**Stars**: 30K+  
**匹配度**: 85%

#### 功能对比

| 功能 | Coze | Flowise | 说明 |
|------|------|---------|------|
| 工作流编排 | ✅ | ✅ | 拖拽式 |
| 意图识别 | ✅ | ✅ | LLM 分类 |
| API 集成 | ✅ | ✅ | Custom Tool |
| 长期记忆 | ✅ | ✅ | LangChain Memory |
| 多模型 | ✅ | ✅ | 支持 100+ |

#### 优势

- ✅ **LangChain 生态** - 基于 LangChain，组件丰富
- ✅ **低代码** - 可视化界面，无需编码
- ✅ **快速原型** - 几分钟搭建工作流
- ✅ **API 部署** - 一键发布为 API

#### 部署

```bash
npm install -g flowise
npx flowise start

# 访问 http://localhost:3000
```

---

### 方案三：LangFlow ⭐⭐⭐⭐

**GitHub**: https://github.com/langflow-ai/langflow  
**Stars**: 25K+  
**匹配度**: 80%

#### 特点

- ✅ **Python 原生** - 适合 Python 开发者
- ✅ **实时调试** - 可视化调试工作流
- ✅ **组件丰富** - 100+ 预置组件
- ✅ **代码导出** - 可导出为 Python 代码

#### 部署

```bash
pip install langflow
langflow run

# 访问 http://localhost:7860
```

---

### 方案四：OpenWebUI + Function Calling ⭐⭐⭐⭐

**GitHub**: https://github.com/open-webui/open-webui  
**Stars**: 40K+  
**匹配度**: 75%

#### 特点

- ✅ **Ollama 集成** - 本地模型友好
- ✅ **函数调用** - 支持自定义工具
- ✅ **Web 界面** - 类似 ChatGPT 的界面
- ✅ **RAG 支持** - 内置文档检索

#### 适用场景

- 本地模型部署 (Llama/Qwen/DeepSeek)
- 需要 Function Calling 能力
- 简单的工具调用需求

---

### 方案五：Rasa + Custom Actions ⭐⭐⭐

**GitHub**: https://github.com/RasaHQ/rasa  
**Stars**: 18K+  
**匹配度**: 70%

#### 特点

- ✅ **意图识别** - 专业的 NLU 引擎
- ✅ **对话管理** - 状态机管理对话
- ✅ **自定义 Action** - Python 编写工具
- ✅ **企业级** - 适合生产环境

#### 适用场景

- 需要精确意图识别
- 复杂对话流程管理
- 企业级部署需求

---

## 📊 方案对比总结

| 方案 | 匹配度 | 学习曲线 | 部署难度 | 社区活跃度 | 推荐指数 |
|------|--------|---------|---------|-----------|---------|
| **Dify** | 90% | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Flowise** | 85% | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **LangFlow** | 80% | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **OpenWebUI** | 75% | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Rasa** | 70% | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 🛠️ 迁移方案 (以 Dify 为例)

### 步骤 1：环境准备

```bash
# 克隆 Dify
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 启动服务
docker compose up -d

# 访问 http://localhost:3000
```

### 步骤 2：创建工作流

1. **创建应用** → 选择 "Chatflow" 类型
2. **配置 LLM** → 选择模型 (Qwen/Claude/GPT)
3. **添加工具** → 集成天气/新闻/股票 API
4. **设置记忆** → 配置向量数据库
5. **发布应用** → 获取 API Key

### 步骤 3：开发自定义工具

```python
# tools/weather.py
import requests
from typing import Optional

def get_weather(
    city: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """
    查询城市天气
    
    Args:
        city: 城市名
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        天气信息字典
    """
    # 使用 OpenWeatherMap 或其他天气 API
    api_key = "YOUR_API_KEY"
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "q": city,
            "appid": api_key,
            "units": "metric"
        }
    )
    return response.json()
```

### 步骤 4：配置意图识别

```yaml
# intents.yaml
intents:
  - name: illegal_sensitive
    patterns:
      - "违法.*"
      - "敏感.*"
      - "无意义.*"
    
  - name: safety_risk
    patterns:
      - "自杀.*"
      - "自残.*"
      - "不想活了.*"
    
  - name: real_time_query
    patterns:
      - "天气.*"
      - "新闻.*"
      - "股票.*"
      - "搜索.*"
    
  - name: chitchat
    patterns:
      - "你好.*"
      - "闲聊.*"
      - "无聊.*"
```

### 步骤 5：集成现有 API

| 原 API | 替代方案 | 成本 |
|--------|---------|------|
| 墨迹天气 | OpenWeatherMap | 免费 60 次/分钟 |
| 头条新闻 | NewsAPI | 免费 500 次/天 |
| 头条搜索 | Tavily/SerpAPI | 免费 1000 次/月 |
| 新浪财经 | Yahoo Finance | 免费 |
| 高德地图 | OpenStreetMap | 免费 |

---

## 💡 推荐配置

### 技术栈

```
┌─────────────────────────────────────┐
│           前端界面                    │
│         Dify / Flowise              │
├─────────────────────────────────────┤
│           编排引擎                    │
│         LangChain / LlamaIndex      │
├─────────────────────────────────────┤
│           工具层                      │
│ 天气 API | 新闻 API | 搜索 API | ... │
├─────────────────────────────────────┤
│           模型层                      │
│   Qwen | Claude | GPT | 本地模型    │
├─────────────────────────────────────┤
│           存储层                      │
│   PostgreSQL | Redis | Chroma       │
└─────────────────────────────────────┘
```

### 成本估算

| 项目 | 方案 | 月成本 |
|------|------|--------|
| **模型** | Qwen-72B (本地) | ¥0 (电费) |
| **天气** | OpenWeatherMap | ¥0 (免费) |
| **新闻** | NewsAPI | ¥0 (免费) |
| **搜索** | Tavily | ¥0 (免费 1000 次) |
| **股票** | Yahoo Finance | ¥0 (免费) |
| **地图** | OpenStreetMap | ¥0 (免费) |
| **总计** | - | **¥0-100/月** |

---

## 🚀 快速开始

### 15 分钟搭建类似工作流

```bash
# 1. 安装 Dify (5 分钟)
git clone https://github.com/langgenius/dify.git
cd dify/docker && docker compose up -d

# 2. 创建应用 (3 分钟)
# 访问 http://localhost:3000
# 创建 Chatflow 应用

# 3. 配置工具 (5 分钟)
# 添加天气/新闻/搜索工具
# 配置 API Key

# 4. 测试发布 (2 分钟)
# 测试对话
# 发布应用
```

---

## 📚 参考资料

- [Dify 官方文档](https://docs.dify.ai)
- [Flowise 文档](https://docs.flowiseai.com)
- [LangChain 中文教程](https://liaokong.gitbook.io/llm-kai-fa-jiao-cheng)
- [OpenWebUI 文档](https://docs.openwebui.com)

---

## ✅ 结论

**最佳推荐**: **Dify**

**理由**:
1. **功能最接近 Coze** - 可视化编排、插件系统、长期记忆
2. **中文支持好** - 文档、社区、团队都在中国
3. **自托管友好** - Docker 一键部署
4. **扩展性强** - 支持自定义 API 和工具
5. **成本可控** - 免费开源，只需支付 API 费用

**迁移成本**: 低 (1-2 天完成迁移)

---

**文档结束**
