# LLM推理源管理 - 生产部署检查清单

## 📋 部署前检查

### 配置检查
- [ ] 配置文件 `config/llm_sources.json` 已创建
- [ ] 所有推理源地址正确
- [ ] 模型名称与实际部署一致
- [ ] 优先级设置合理
- [ ] 默认推理源已设置
- [ ] 故障转移已启用

### 推理源检查
- [ ] 所有推理源都已启动
- [ ] 推理源健康检查通过
- [ ] 网络连接正常
- [ ] API密钥已配置
- [ ] 超时时间设置合理

### 环境变量检查
- [ ] `LLM_ENVIRONMENT` 已设置为 `prod`
- [ ] `LLM_SOURCES_CONFIG` 指向正确的配置文件
- [ ] 敏感信息（API密钥）已通过环境变量配置
- [ ] 日志级别设置为 `INFO`

### 监控检查
- [ ] 监控系统已配置
- [ ] 告警规则已设置
- [ ] 日志收集已配置
- [ ] 指标导出已启用

## 🚀 部署步骤

### 1. 准备阶段

```bash
# 复制配置文件
cp config/llm_sources.json.example config/llm_sources.json

# 编辑配置文件
vim config/llm_sources.json

# 验证配置
python -c "
import json
with open('config/llm_sources.json') as f:
    config = json.load(f)
    print('Sources:', list(config['sources'].keys()))
    print('Default:', config['default_source'])
"
```

### 2. 启动推理源

```bash
# 启动vLLM集群
docker-compose -f docker-compose.llm.prod.yml up -d

# 验证推理源
curl http://vllm-1:8000/health
curl http://vllm-2:8000/health
curl http://vllm-3:8000/health
```

### 3. 测试推理源管理

```bash
# 列出推理源
python -m agent_service.cli.llm_sources_cli list-sources

# 测试生成
python -m agent_service.cli.llm_sources_cli generate "Hello"

# 获取状态
python -m agent_service.cli.llm_sources_cli status
```

### 4. 集成到应用

```python
# 在应用启动时初始化
from agent_service.infra.llm_clients.inference_source_manager import (
    get_inference_source_manager,
)

manager = get_inference_source_manager()
print(f"Current source: {manager.get_current_source()}")
```

### 5. 配置监控

```python
# 定期检查推理源状态
import threading
import time

def monitor_sources():
    manager = get_inference_source_manager()
    while True:
        metrics = manager.get_metrics()
        if metrics['success_rate'] < 0.95:
            alert("Low success rate")
        time.sleep(60)

monitor_thread = threading.Thread(target=monitor_sources, daemon=True)
monitor_thread.start()
```

## 🔍 验证清单

### 功能验证
- [ ] 可以列出所有推理源
- [ ] 可以获取推理源信息
- [ ] 可以切换推理源
- [ ] 可以启用/禁用推理源
- [ ] 可以执行故障转移
- [ ] 可以生成文本
- [ ] 可以获取性能指标

### 性能验证
- [ ] 推理延迟在预期范围内
- [ ] 吞吐量满足要求
- [ ] 内存使用正常
- [ ] CPU使用率正常
- [ ] 网络带宽充足

### 可靠性验证
- [ ] 熔断器正常工作
- [ ] 重试机制正常工作
- [ ] 故障转移正常工作
- [ ] 日志记录完整
- [ ] 错误处理正确

### 监控验证
- [ ] 指标收集正常
- [ ] 告警规则生效
- [ ] 日志收集正常
- [ ] 仪表板显示正确

## 📊 性能基准

### 推荐配置

| 环境 | 推理源 | 实例数 | 吞吐量 | 延迟 |
|------|--------|--------|--------|------|
| 生产 | vLLM | 3 | 150-300 req/s | 100-200ms |
| 生产 | Ollama | 1 | 5-10 req/s | 500-1000ms |

### 监控指标

| 指标 | 目标 | 告警阈值 |
|------|------|---------|
| 成功率 | > 99% | < 95% |
| 平均延迟 | < 200ms | > 1000ms |
| P95延迟 | < 500ms | > 2000ms |
| 熔断器状态 | CLOSED | OPEN |

## 🔐 安全检查

- [ ] API密钥已加密
- [ ] 敏感信息不在日志中
- [ ] 访问控制已配置
- [ ] 速率限制已设置
- [ ] 输入验证已实现
- [ ] 错误信息不泄露敏感信息

## 📝 文档检查

- [ ] 部署文档已更新
- [ ] 运维手册已准备
- [ ] 故障排查指南已准备
- [ ] API文档已准备
- [ ] 配置示例已准备

## 🚨 故障转移测试

### 测试场景1：单个推理源故障

```bash
# 1. 停止一个推理源
docker stop vllm-1

# 2. 验证故障转移
python -m agent_service.cli.llm_sources_cli status

# 3. 验证请求转移到其他源
python -m agent_service.cli.llm_sources_cli generate "Test"

# 4. 重启推理源
docker start vllm-1
```

### 测试场景2：多个推理源故障

```bash
# 1. 停止多个推理源
docker stop vllm-1 vllm-2

# 2. 验证故障转移到最后一个源
python -m agent_service.cli.llm_sources_cli status

# 3. 验证请求仍然可以处理
python -m agent_service.cli.llm_sources_cli generate "Test"

# 4. 重启推理源
docker start vllm-1 vllm-2
```

### 测试场景3：所有推理源故障

```bash
# 1. 停止所有推理源
docker stop vllm-1 vllm-2 vllm-3

# 2. 验证错误处理
python -m agent_service.cli.llm_sources_cli generate "Test"

# 3. 验证告警触发
# 检查监控系统

# 4. 重启推理源
docker start vllm-1 vllm-2 vllm-3
```

## 📈 上线步骤

### 灰度发布

1. **第一阶段：10%流量**
   - [ ] 部署到10%的服务器
   - [ ] 监控性能指标
   - [ ] 监控错误率
   - [ ] 持续1小时

2. **第二阶段：50%流量**
   - [ ] 部署到50%的服务器
   - [ ] 监控性能指标
   - [ ] 监控错误率
   - [ ] 持续2小时

3. **第三阶段：100%流量**
   - [ ] 部署到所有服务器
   - [ ] 监控性能指标
   - [ ] 监控错误率
   - [ ] 持续观察

### 回滚计划

如果出现问题：

```bash
# 1. 立即切换到旧版本
git revert <commit>

# 2. 重启应用
docker-compose restart

# 3. 验证恢复
python -m agent_service.cli.llm_sources_cli status

# 4. 分析问题
# 查看日志和指标
```

## 🎯 上线后检查

### 第一天
- [ ] 监控所有指标
- [ ] 检查错误日志
- [ ] 验证故障转移
- [ ] 收集用户反馈

### 第一周
- [ ] 分析性能数据
- [ ] 优化配置
- [ ] 更新文档
- [ ] 总结经验

### 持续运维
- [ ] 定期检查推理源状态
- [ ] 定期更新配置
- [ ] 定期备份配置
- [ ] 定期测试故障转移

## 📞 支持联系

- **技术支持**: [support@example.com]
- **紧急热线**: [emergency@example.com]
- **文档**: [docs/llm_sources_management_guide.md]

## ✅ 最终确认

- [ ] 所有检查项已完成
- [ ] 所有测试已通过
- [ ] 所有文档已准备
- [ ] 所有人员已培训
- [ ] 已获得上线批准

**上线日期**: _______________
**负责人**: _______________
**审批人**: _______________

---

**注意**: 此清单必须在生产部署前完成。任何未完成的项目都可能导致生产问题。
