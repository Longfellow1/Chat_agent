"""LLM推理源管理集成示例"""

import os
import sys
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)
from agent_service.infra.llm_clients.llm_config import LLMProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """示例1：基础使用"""
    print("\n" + "="*60)
    print("示例1：基础使用")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 列出所有推理源
    print("\n可用的推理源:")
    for source in manager.list_sources():
        marker = "✓" if source["current"] else " "
        print(f"[{marker}] {source['name']:<20} {source['provider']:<15}")
    
    # 获取当前推理源
    current = manager.get_current_source()
    print(f"\n当前推理源: {current}")
    
    # 生成文本
    try:
        response = manager.generate(
            user_query="What is AI?",
            system_prompt="You are a helpful assistant."
        )
        print(f"\n生成结果: {response[:100]}...")
    except Exception as e:
        print(f"生成失败: {e}")


def example_2_switch_sources():
    """示例2：切换推理源"""
    print("\n" + "="*60)
    print("示例2：切换推理源")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 列出所有推理源
    sources = manager.list_sources()
    print(f"\n可用的推理源: {len(sources)}")
    
    # 切换到第一个可用的推理源
    for source in sources:
        if source["enabled"] and source["name"] != manager.get_current_source():
            print(f"\n切换到: {source['name']}")
            success = manager.switch_source(source["name"])
            if success:
                print(f"✓ 切换成功")
                print(f"当前推理源: {manager.get_current_source()}")
            else:
                print(f"✗ 切换失败")
            break


def example_3_register_new_source():
    """示例3：注册新推理源"""
    print("\n" + "="*60)
    print("示例3：注册新推理源")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 注册新推理源
    print("\n注册新推理源...")
    manager.register_source(
        name="ollama_local",
        provider=LLMProvider.OLLAMA,
        base_url="http://localhost:11434",
        model_name="qwen2.5:7b",
        priority=80,
        enabled=True,
    )
    print("✓ 已注册 ollama_local")
    
    # 列出所有推理源
    print("\n更新后的推理源列表:")
    for source in manager.list_sources():
        print(f"  - {source['name']:<20} {source['provider']:<15} Priority: {source['priority']}")


def example_4_enable_disable():
    """示例4：启用/禁用推理源"""
    print("\n" + "="*60)
    print("示例4：启用/禁用推理源")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 获取所有推理源
    sources = manager.list_sources()
    
    if len(sources) > 1:
        # 禁用第二个推理源
        source_to_disable = sources[1]["name"]
        print(f"\n禁用推理源: {source_to_disable}")
        manager.disable_source(source_to_disable)
        print("✓ 已禁用")
        
        # 启用推理源
        print(f"\n启用推理源: {source_to_disable}")
        manager.enable_source(source_to_disable)
        print("✓ 已启用")


def example_5_failover():
    """示例5：故障转移"""
    print("\n" + "="*60)
    print("示例5：故障转移")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    current = manager.get_current_source()
    print(f"\n当前推理源: {current}")
    
    # 执行故障转移
    print("\n执行故障转移...")
    success = manager.failover_to_next()
    
    if success:
        new_source = manager.get_current_source()
        print(f"✓ 故障转移成功")
        print(f"新推理源: {new_source}")
    else:
        print("✗ 故障转移失败: 没有可用的推理源")


def example_6_monitoring():
    """示例6：监控和指标"""
    print("\n" + "="*60)
    print("示例6：监控和指标")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 生成多个请求
    queries = [
        "What is machine learning?",
        "Explain deep learning",
        "What is NLP?",
    ]
    
    print("\n生成多个请求...")
    for query in queries:
        try:
            response = manager.generate(query, "You are helpful.")
            print(f"✓ {query[:30]}...")
        except Exception as e:
            print(f"✗ {query[:30]}... - {e}")
    
    # 获取指标
    print("\n性能指标:")
    metrics = manager.get_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key:<30}: {value:.2f}")
        else:
            print(f"  {key:<30}: {value}")
    
    # 获取熔断器状态
    print(f"\n熔断器状态: {manager.get_circuit_breaker_state()}")


def example_7_source_info():
    """示例7：获取推理源信息"""
    print("\n" + "="*60)
    print("示例7：获取推理源信息")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 获取当前推理源信息
    current = manager.get_current_source()
    print(f"\n当前推理源: {current}")
    
    info = manager.get_source_info(current)
    if info:
        print("\n推理源信息:")
        for key, value in info.items():
            print(f"  {key:<20}: {value}")


def example_8_integration_with_router():
    """示例8：与Intent Router集成"""
    print("\n" + "="*60)
    print("示例8：与Intent Router集成")
    print("="*60)
    
    from agent_service.infra.llm_clients.inference_source_manager import (
        get_inference_source_manager,
    )
    
    class SimpleRouter:
        """简单的Intent Router示例"""
        
        def __init__(self):
            self.llm_manager = get_inference_source_manager()
        
        def route_query(self, query: str) -> str:
            """路由查询"""
            system_prompt = """You are an intent classifier.
            Classify the user query into one of: location, weather, news, finance.
            Return only the intent name."""
            
            try:
                intent = self.llm_manager.generate(query, system_prompt)
                return intent.strip().lower()
            except Exception as e:
                logger.error(f"Routing failed: {e}")
                return "unknown"
    
    # 使用Router
    router = SimpleRouter()
    
    test_queries = [
        "Where is the nearest restaurant?",
        "What's the weather today?",
        "Show me the latest news",
        "What's the stock price?",
    ]
    
    print("\n测试Intent Router:")
    for query in test_queries:
        intent = router.route_query(query)
        print(f"  Query: {query}")
        print(f"  Intent: {intent}\n")


def example_9_dynamic_configuration():
    """示例9：动态配置"""
    print("\n" + "="*60)
    print("示例9：动态配置")
    print("="*60)
    
    manager = get_inference_source_manager()
    
    # 注册多个推理源
    print("\n注册多个推理源...")
    
    sources_config = [
        {
            "name": "vllm_prod_1",
            "provider": LLMProvider.VLLM,
            "base_url": "http://vllm-1:8000",
            "model_name": "qwen2.5-7b-instruct",
            "priority": 100,
        },
        {
            "name": "vllm_prod_2",
            "provider": LLMProvider.VLLM,
            "base_url": "http://vllm-2:8000",
            "model_name": "qwen2.5-7b-instruct",
            "priority": 90,
        },
        {
            "name": "ollama_fallback",
            "provider": LLMProvider.OLLAMA,
            "base_url": "http://ollama:11434",
            "model_name": "qwen2.5:7b",
            "priority": 50,
        },
    ]
    
    for config in sources_config:
        manager.register_source(**config)
        print(f"  ✓ {config['name']}")
    
    # 列出所有推理源
    print("\n所有推理源:")
    for source in manager.list_sources():
        print(f"  {source['name']:<20} Priority: {source['priority']:<3} Enabled: {source['enabled']}")


if __name__ == "__main__":
    print("LLM推理源管理集成示例")
    print("=" * 60)
    
    # 运行示例
    example_1_basic_usage()
    # example_2_switch_sources()
    # example_3_register_new_source()
    # example_4_enable_disable()
    # example_5_failover()
    # example_6_monitoring()
    # example_7_source_info()
    # example_8_integration_with_router()
    # example_9_dynamic_configuration()
    
    print("\n提示：取消注释上面的示例函数调用来运行特定示例")
