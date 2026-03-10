"""验证百度新闻 provider 配置"""

import os
import sys
from pathlib import Path

# Load .env.agent first
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env.agent"
if env_path.exists():
    load_dotenv(env_path)

agent_service_root = Path(__file__).parent / "agent_service"
sys.path.insert(0, str(agent_service_root))

print("="*80)
print("验证百度新闻 Provider 配置")
print("="*80)

# 1. 检查环境变量
print("\n1. 检查环境变量:")
api_key = os.getenv("BAIDU_QIANFAN_API_KEY", "")
print(f"   BAIDU_QIANFAN_API_KEY: {'已设置' if api_key else '未设置'}")
if api_key:
    print(f"   Key 前缀: {api_key[:20]}...")

# 2. 检查 appbuilder 安装
print("\n2. 检查 appbuilder 安装:")
try:
    import appbuilder
    print(f"   ✅ appbuilder 已安装 (版本: {appbuilder.__version__})")
except ImportError as e:
    print(f"   ❌ appbuilder 未安装: {e}")
    print("   请运行: pip install appbuilder-sdk")
    sys.exit(1)

# 3. 测试 BaiduNewsProvider 初始化
print("\n3. 测试 BaiduNewsProvider 初始化:")
try:
    from infra.tool_clients.provider_base import ProviderConfig
    from infra.tool_clients.providers.baidu_news_provider import BaiduNewsProvider
    
    config = ProviderConfig(
        name="baidu_news",
        priority=1,
        timeout=3.0,
    )
    
    provider = BaiduNewsProvider(config)
    print(f"   ✅ Provider 初始化成功")
    print(f"   API Key: {'已配置' if provider.api_key else '未配置'}")
    print(f"   Search client: {'已初始化' if provider.search else '未初始化'}")
    
    # 4. 测试实际查询
    if provider.search:
        print("\n4. 测试实际查询:")
        result = provider.execute(query="比亚迪新能源汽车")
        print(f"   成功: {result.ok}")
        if result.ok:
            print(f"   Provider: {result.provider_name}")
            print(f"   结果数: {len(result.data.raw.get('results', [])) if result.data and result.data.raw else 0}")
        else:
            print(f"   错误: {result.error}")
    else:
        print("\n4. ⚠️  Search client 未初始化，跳过查询测试")
        
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试 MCPToolGateway 集成
print("\n5. 测试 MCPToolGateway 集成:")
try:
    from infra.tool_clients.mcp_gateway import MCPToolGateway
    
    gateway = MCPToolGateway()
    print(f"   ✅ Gateway 初始化成功")
    print(f"   use_get_news_chain: {getattr(gateway, 'use_get_news_chain', False)}")
    
    if hasattr(gateway, 'get_news_chain') and gateway.get_news_chain:
        print(f"   get_news_chain: 已初始化")
    else:
        print(f"   get_news_chain: 未初始化")
        
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
