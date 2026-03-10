# 百度千帆 AI 搜索接入指南

## 概述

百度千帆平台提供两种搜索能力：
1. **AppBuilder AI 搜索**：智能搜索生成，返回 AI 总结的对话式文本（SUMMARIZED）
2. **百度搜索 API**：传统搜索，返回原始搜索结果列表（RAW）

## 鉴权方式

### 方式1: API Key + Secret Key（推荐）

百度千帆使用 AK/SK 鉴权机制：
- **API Key (AK)**: 用于标识调用者身份
- **Secret Key (SK)**: 用于签名验证，保证请求安全

### 方式2: Access Token

通过 AK/SK 获取 Access Token，然后使用 Token 调用 API。

## 获取 API Key 和 Secret Key

### 步骤1: 注册百度智能云账号

1. 访问 [百度智能云](https://cloud.baidu.com/)
2. 点击右上角"注册"
3. 完成手机号/邮箱验证
4. 实名认证（企业或个人）

### 步骤2: 开通千帆服务

1. 登录 [百度智能云控制台](https://console.bce.baidu.com/)
2. 搜索"千帆大模型平台"或访问 [千帆控制台](https://console.bce.baidu.com/qianfan/overview)
3. 点击"立即使用"开通服务
4. 选择付费方式：
   - 按量付费（推荐车展演示）
   - 资源包（大量使用）

### 步骤3: 创建应用获取密钥

#### 方法A: 在千帆控制台创建

1. 进入 [千帆控制台](https://console.bce.baidu.com/qianfan/overview)
2. 左侧菜单选择"应用接入" → "应用列表"
3. 点击"创建应用"
4. 填写应用信息：
   - 应用名称：如 "车展演示应用"
   - 应用描述：如 "车展AI助手搜索功能"
   - 应用类型：选择"服务端应用"
5. 创建成功后，在应用详情页可以看到：
   - **API Key (AK)**
   - **Secret Key (SK)**
6. 点击"显示"查看 Secret Key（只显示一次，请妥善保存）

#### 方法B: 在安全认证页面创建

1. 进入 [安全认证](https://console.bce.baidu.com/iam/#/iam/accesslist)
2. 点击"创建密钥"
3. 系统生成 Access Key ID (AK) 和 Secret Access Key (SK)
4. 下载密钥文件（CSV格式）保存

### 步骤4: 开通具体服务

#### AppBuilder AI 搜索

1. 进入 [AppBuilder 控制台](https://console.bce.baidu.com/appbuilder/overview)
2. 左侧菜单选择"组件" → "搜索组件"
3. 找到"智能搜索生成"组件
4. 点击"开通"或"试用"
5. 确认服务协议和计费说明

#### 百度搜索 API

1. 进入千帆控制台
2. 左侧菜单选择"工具" → "百度搜索"
3. 点击"开通服务"
4. 确认计费方式

## API 接入方式

### 1. AppBuilder AI 搜索（推荐）

#### 安装 SDK

```bash
pip install appbuilder-sdk
```

#### 使用示例

```python
import appbuilder
import os

# 设置密钥
os.environ["APPBUILDER_TOKEN"] = "your_access_token"
# 或者
appbuilder.set_token("your_access_token")

# 使用智能搜索组件
search = appbuilder.BaiduSearch()

# 执行搜索
result = search.run(query="特斯拉 Model 3 价格")

print(result.content)  # AI 总结的答案
print(result.references)  # 参考来源
```

#### 获取 Access Token

```python
import requests

def get_access_token(api_key: str, secret_key: str) -> str:
    """
    使用 AK/SK 获取 Access Token
    
    Args:
        api_key: API Key
        secret_key: Secret Key
        
    Returns:
        Access Token
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key,
    }
    
    response = requests.post(url, params=params)
    response.raise_for_status()
    
    return response.json()["access_token"]

# 使用
api_key = "your_api_key"
secret_key = "your_secret_key"
access_token = get_access_token(api_key, secret_key)
```

### 2. 直接调用 REST API

#### AppBuilder AI 搜索 API

```python
import requests
import json

def baidu_ai_search(query: str, access_token: str) -> dict:
    """
    调用百度 AI 搜索
    
    Args:
        query: 搜索查询
        access_token: Access Token
        
    Returns:
        搜索结果
    """
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "enable_search": True,  # 启用搜索
        "search_type": "baidu_search",  # 使用百度搜索
    }
    
    params = {
        "access_token": access_token
    }
    
    response = requests.post(url, headers=headers, json=payload, params=params)
    response.raise_for_status()
    
    return response.json()

# 使用
result = baidu_ai_search("特斯拉 Model 3 价格", access_token)
print(result["result"])  # AI 生成的答案
```

#### 百度搜索 API（传统搜索）

```python
def baidu_search(query: str, access_token: str, max_results: int = 10) -> dict:
    """
    调用百度传统搜索 API
    
    Args:
        query: 搜索查询
        access_token: Access Token
        max_results: 最大结果数
        
    Returns:
        搜索结果列表
    """
    url = "https://aip.baidubce.com/rpc/2.0/search/v1/search"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "num": max_results,
    }
    
    params = {
        "access_token": access_token
    }
    
    response = requests.post(url, headers=headers, json=payload, params=params)
    response.raise_for_status()
    
    return response.json()

# 使用
result = baidu_search("比亚迪汉 EV 续航", access_token)
for item in result["results"]:
    print(f"{item['title']}: {item['url']}")
```

## 集成到 Provider Chain

### 更新 BaiduAISearchProvider

```python
"""agent_service/infra/tool_clients/providers/baidu_providers.py"""

import os
import requests
from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


class BaiduAISearchProvider(ToolProvider):
    """Baidu AppBuilder AI search provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("BAIDU_QIANFAN_API_KEY", "").strip()
        self.secret_key = os.getenv("BAIDU_QIANFAN_SECRET_KEY", "").strip()
        self.access_token = None
        self.token_expires_at = 0
        self.timeout = config.timeout
    
    def _get_access_token(self) -> str:
        """Get or refresh access token."""
        import time
        
        # Check if token is still valid
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # Get new token
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        
        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        # Token valid for 30 days, refresh 1 day before expiry
        self.token_expires_at = time.time() + data.get("expires_in", 2592000) - 86400
        
        return self.access_token
    
    def execute(self, **kwargs) -> ProviderResult:
        """Execute AI search via Baidu AppBuilder."""
        if not self.api_key or not self.secret_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="baidu_credentials_missing",
                result_type=ResultType.SUMMARIZED,
            )
        
        query = kwargs.get("query", "")
        if not query:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_query",
                result_type=ResultType.SUMMARIZED,
            )
        
        try:
            # Get access token
            access_token = self._get_access_token()
            
            # Call AI search API
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "enable_search": True,
                "search_type": "baidu_search",
            }
            
            params = {
                "access_token": access_token
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract answer
            answer = data.get("result", "")
            if not answer:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="no_answer",
                    result_type=ResultType.SUMMARIZED,
                )
            
            # Extract references if available
            references = []
            if "search_info" in data:
                search_results = data["search_info"].get("search_results", [])
                references = [
                    {"title": r.get("title"), "url": r.get("url")}
                    for r in search_results
                ]
            
            # Create result
            result = ToolResult(
                ok=True,
                text=answer,  # AI-generated answer, direct use
                raw={
                    "provider": "baidu_ai_search",
                    "query": query,
                    "answer": answer,
                    "references": references,
                },
            )
            
            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.SUMMARIZED,  # AI-processed, direct use
            )
            
        except requests.exceptions.Timeout:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="timeout",
                result_type=ResultType.SUMMARIZED,
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"http_error:{e.response.status_code}"
            if e.response.status_code == 429:
                error_msg = "rate_limit"
            elif e.response.status_code == 403:
                error_msg = "quota_exceeded"
            
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=error_msg,
                result_type=ResultType.SUMMARIZED,
            )
        except Exception as e:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=f"error:{e}",
                result_type=ResultType.SUMMARIZED,
            )
    
    def health_check(self) -> bool:
        """Check if Baidu credentials are available."""
        if not self.api_key or not self.secret_key:
            return False
        
        try:
            # Try to get access token
            self._get_access_token()
            return True
        except Exception:
            return False
```

## 环境变量配置

```bash
# .env 文件

# 百度千帆 API 密钥
export BAIDU_QIANFAN_API_KEY=your_api_key_here
export BAIDU_QIANFAN_SECRET_KEY=your_secret_key_here

# 或者直接使用 Access Token（不推荐，Token 会过期）
# export BAIDU_QIANFAN_ACCESS_TOKEN=your_access_token_here

# 超时配置
export BAIDU_AI_SEARCH_TIMEOUT=2.5
export BAIDU_SEARCH_TIMEOUT=3.0
```

## 测试接入

```python
"""test_baidu_integration.py"""

from infra.tool_clients.providers.baidu_providers import BaiduAISearchProvider
from infra.tool_clients.provider_base import ProviderConfig

# 创建配置
config = ProviderConfig(
    name="baidu_ai_search",
    priority=1,
    timeout=2.5,
)

# 创建 Provider
provider = BaiduAISearchProvider(config)

# 健康检查
if not provider.health_check():
    print("❌ 健康检查失败，请检查 API Key 和 Secret Key")
    exit(1)

print("✅ 健康检查通过")

# 测试搜索
test_queries = [
    "特斯拉 Model 3 价格",
    "比亚迪汉 EV 续航",
    "蔚来 ET7 配置",
]

for query in test_queries:
    print(f"\n测试查询: {query}")
    result = provider.execute(query=query)
    
    if result.ok:
        print(f"✅ 成功")
        print(f"答案: {result.data.text[:100]}...")
        print(f"延迟: {result.latency_ms:.0f}ms")
    else:
        print(f"❌ 失败: {result.error}")
```

## 计费说明

### AppBuilder AI 搜索

- 按调用次数计费
- 免费额度：通常有试用额度（如 100 次/天）
- 付费价格：约 0.01-0.05 元/次（具体以控制台为准）

### 百度搜索 API

- 按调用次数计费
- 免费额度：通常有试用额度（如 1000 次/天）
- 付费价格：约 0.001-0.01 元/次

### 车展演示预算估算

假设演示期间：
- 每小时 50 次查询
- 演示 8 小时
- 总计 400 次查询

成本估算：
- AppBuilder AI 搜索：400 × 0.02 = 8 元
- 百度搜索 API：400 × 0.005 = 2 元
- 总计：约 10 元

## 常见问题

### Q1: Access Token 多久过期？

A: 默认 30 天。建议在代码中自动刷新，不要硬编码 Token。

### Q2: API Key 和 Secret Key 在哪里查看？

A: 千帆控制台 → 应用接入 → 应用列表 → 选择应用 → 查看密钥

### Q3: 如何查看剩余额度？

A: 千帆控制台 → 费用中心 → 资源包管理

### Q4: 调用失败返回 403 怎么办？

A: 可能原因：
1. API Key/Secret Key 错误
2. 服务未开通
3. 额度用完
4. IP 白名单限制

### Q5: 如何设置 IP 白名单？

A: 千帆控制台 → 应用接入 → 应用列表 → 选择应用 → 安全设置 → IP 白名单

## 参考链接

- [百度智能云官网](https://cloud.baidu.com/)
- [千帆大模型平台](https://console.bce.baidu.com/qianfan/overview)
- [AppBuilder 文档](https://cloud.baidu.com/doc/AppBuilder/index.html)
- [API 文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html)
- [计费说明](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/pricing)
