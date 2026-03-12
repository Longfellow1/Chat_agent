"""LLM推理源管理CLI工具"""

from __future__ import annotations

import json
import logging
import sys
from typing import Optional

import click

from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

logger = logging.getLogger(__name__)


@click.group()
def llm_cli():
    """LLM推理源管理工具"""
    pass


@llm_cli.command()
def list_sources():
    """列出所有推理源"""
    manager = get_inference_source_manager()
    sources = manager.list_sources()
    
    click.echo("\n推理源列表:")
    click.echo("=" * 80)
    
    for source in sources:
        marker = "✓" if source["current"] else " "
        status = "✓ 启用" if source["enabled"] else "✗ 禁用"
        click.echo(f"[{marker}] {source['name']:<20} {source['provider']:<15} {status}")
        click.echo(f"    URL: {source['base_url']}")
        click.echo(f"    Model: {source['model_name']}")
        click.echo(f"    Priority: {source['priority']}")
        click.echo()


@llm_cli.command()
@click.argument('source_name')
def info(source_name: str):
    """获取推理源信息"""
    manager = get_inference_source_manager()
    info = manager.get_source_info(source_name)
    
    if not info:
        click.echo(f"错误: 推理源不存在: {source_name}", err=True)
        sys.exit(1)
    
    click.echo(f"\n推理源信息: {source_name}")
    click.echo("=" * 80)
    for key, value in info.items():
        click.echo(f"{key:<20}: {value}")


@llm_cli.command()
@click.argument('source_name')
def switch(source_name: str):
    """切换推理源"""
    manager = get_inference_source_manager()
    
    if source_name not in manager.sources:
        click.echo(f"错误: 推理源不存在: {source_name}", err=True)
        sys.exit(1)
    
    success = manager.switch_source(source_name)
    if success:
        click.echo(f"✓ 已切换到推理源: {source_name}")
    else:
        click.echo(f"✗ 切换失败: {source_name}", err=True)
        sys.exit(1)


@llm_cli.command()
@click.argument('source_name')
def enable(source_name: str):
    """启用推理源"""
    manager = get_inference_source_manager()
    
    success = manager.enable_source(source_name)
    if success:
        click.echo(f"✓ 已启用推理源: {source_name}")
    else:
        click.echo(f"✗ 推理源不存在: {source_name}", err=True)
        sys.exit(1)


@llm_cli.command()
@click.argument('source_name')
def disable(source_name: str):
    """禁用推理源"""
    manager = get_inference_source_manager()
    
    success = manager.disable_source(source_name)
    if success:
        click.echo(f"✓ 已禁用推理源: {source_name}")
    else:
        click.echo(f"✗ 推理源不存在: {source_name}", err=True)
        sys.exit(1)


@llm_cli.command()
def failover():
    """执行故障转移"""
    manager = get_inference_source_manager()
    
    success = manager.failover_to_next()
    if success:
        current = manager.get_current_source()
        click.echo(f"✓ 故障转移成功，当前推理源: {current}")
    else:
        click.echo("✗ 故障转移失败: 没有可用的推理源", err=True)
        sys.exit(1)


@llm_cli.command()
def status():
    """获取推理源状态"""
    manager = get_inference_source_manager()
    
    current = manager.get_current_source()
    cb_state = manager.get_circuit_breaker_state()
    metrics = manager.get_metrics()
    
    click.echo("\n推理源状态:")
    click.echo("=" * 80)
    click.echo(f"当前推理源: {current}")
    click.echo(f"熔断器状态: {cb_state}")
    click.echo()
    
    click.echo("性能指标:")
    for key, value in metrics.items():
        if key != "source":
            if isinstance(value, float):
                click.echo(f"  {key:<30}: {value:.2f}")
            else:
                click.echo(f"  {key:<30}: {value}")


@llm_cli.command()
@click.argument('query')
@click.option('--system-prompt', default='You are a helpful assistant.', help='系统提示')
def generate(query: str, system_prompt: str):
    """生成文本"""
    manager = get_inference_source_manager()
    
    try:
        click.echo(f"\n使用推理源: {manager.get_current_source()}")
        click.echo("生成中...")
        
        response = manager.generate(query, system_prompt)
        
        click.echo("\n生成结果:")
        click.echo("=" * 80)
        click.echo(response)
        click.echo()
    except Exception as e:
        click.echo(f"✗ 生成失败: {e}", err=True)
        sys.exit(1)


@llm_cli.command()
def metrics():
    """获取性能指标"""
    manager = get_inference_source_manager()
    metrics = manager.get_metrics()
    
    click.echo("\n性能指标:")
    click.echo("=" * 80)
    click.echo(json.dumps(metrics, indent=2, ensure_ascii=False))


@llm_cli.command()
@click.argument('source_name')
@click.argument('provider')
@click.argument('base_url')
@click.argument('model_name')
@click.option('--priority', default=0, type=int, help='优先级')
@click.option('--enabled', default=True, type=bool, help='是否启用')
def register(
    source_name: str,
    provider: str,
    base_url: str,
    model_name: str,
    priority: int,
    enabled: bool,
):
    """注册新的推理源"""
    from agent_service.infra.llm_clients.llm_config import LLMProvider
    
    manager = get_inference_source_manager()
    
    try:
        provider_enum = LLMProvider(provider)
    except ValueError:
        click.echo(f"✗ 无效的提供商: {provider}", err=True)
        click.echo(f"  支持的提供商: {', '.join([p.value for p in LLMProvider])}")
        sys.exit(1)
    
    manager.register_source(
        name=source_name,
        provider=provider_enum,
        base_url=base_url,
        model_name=model_name,
        priority=priority,
        enabled=enabled,
    )
    
    click.echo(f"✓ 已注册推理源: {source_name}")


if __name__ == '__main__':
    llm_cli()
