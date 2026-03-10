# 百度地图 MCP 集成指南

**目的**: 为 find_nearby 和 plan_trip 提供百度地图 MCP 作为降级方案  
**优先级**: P0（车展前必做）  
**时间**: M5.1

---

## 一、背景

### 1.1 为什么需要百度地图 MCP？

**问题**: 当前 find_nearby 单一依赖高德 MCP，无降级方案
- 高德 MCP 故障 → 直接降级到 Mock（返回假数据）
- 车展现场"附近停车场"、"附近餐厅"是高频刚需
- 单一信源风险高，健壮性不足

**解决方案**: 双地图源保障
```
高德 MCP (3s) → 百度地图 MCP (3s) → Mock
```

**重要**: 百度地图 MCP 客户端实现必须参照高德 MCP 的实现方式（`amap_mcp_client.py`），不要自己重新造轮子。进程管理和健康检查逻辑需要对齐。

### 1.2 百度地图 MCP 优势

- 官方支持：https://github.com/baidu-maps/mcp
- MCP World 收录：https://www.mcpworld.com/zh/detail/9e63a8ffadfa0ffe381910dece2a565d
- 国内主流地图服务，数据质量有保障
- 与高德互补，提升整体可用性

---

## 二、百度地图 MCP 能力

### 2.1 支持的工具

根据 GitHub 仓库，百度地图 MCP 提供以下工具：

1. **place_search**: 地点搜索（对应 find_nearby）
2. **geocoding**: 地理编码（地址 → 坐标）
3. **reverse_geocoding**: 逆地理编码（坐标 → 地址）
4. **route_planning**: 路线规划（对应 plan_trip）
5. **distance_matrix**: 距离矩阵

### 2.2 与高德 MCP 对比

| 功能 | 高德 MCP | 百度地图 MCP | 备注 |
|------|----------|--------------|------|
| 地点搜索 | ✅ maps_text_search | ✅ place_search | 核心功能 |
| 周边搜索 | ✅ maps_around_search | ✅ place_search (radius) | 核心功能 |
| 地理编码 | ✅ maps_geo | ✅ geocoding | 辅助功能 |
| 路线规划 | ✅ maps_direction | ✅ route_planning | plan_trip 需要 |

---

## 三、集成方案

### 3.1 架构设计

```
用户查询 "附近停车场"
    ↓
chat_flow.py (路由到 find_nearby)
    ↓
mcp_gateway.py::_nearby()
    ↓
provider_chain.execute("find_nearby", keyword="停车场")
    ↓
┌─────────────────────────────────────┐
│ Provider Chain                      │
│                                     │
│ 1. AmapMCPProvider (3s timeout)    │
│    ├─ 成功 → 返回结果              │
│    └─ 失败/超时 → 降级到 2         │
│                                     │
│ 2. BaiduMapsMCPProvider (3s)       │
│    ├─ 成功 → 返回结果              │
│    └─ 失败 → 降级到 3              │
│                                     │
│ 3. MockProvider                     │
│    └─ 返回友好错误信息             │
└─────────────────────────────────────┘
    ↓
返回用户
```

### 3.2 代码结构

```
agent_service/infra/tool_clients/
├── amap_mcp_client.py              # 高德 MCP 客户端（已存在）
├── baidu_maps_mcp_client.py        # 百度地图 MCP 客户端（新建）
├── mcp_gateway.py                  # 统一网关（修改）
├── provider_config.py              # Provider 配置（已更新）
└── providers/
    ├── amap_mcp_provider.py        # 高德 MCP Provider（新建）
    └── baidu_maps_mcp_provider.py  # 百度地图 MCP Provider（新建）
```

---

## 四、实现步骤

### 4.1 创建 BaiduMapsMCPClient（参照高德 MCP 实现）

**重要**: 直接参照 `amap_mcp_client.py` 的实现方式，只修改以下部分：
1. 环境变量名: `AMAP_MAPS_API_KEY` → `BAIDU_MAPS_API_KEY`
2. MCP 包名: `@amap/amap-maps-mcp-server` → `@baidu-maps/mcp-server`
3. 工具名: `maps_text_search` → `place_search`
4. 响应字段: `pois` → `results`

```python
# agent_service/infra/tool_clients/baidu_maps_mcp_client.py
"""Baidu Maps MCP client for location services."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any

from domain.tools.types import ToolResult


class BaiduMapsMCPClient:
    """Client for Baidu Maps MCP server.
    
    Implementation follows AmapMCPClient pattern for consistency.
    """
    
    def __init__(self) -> None:
        self.api_key = os.getenv("BAIDU_MAPS_API_KEY", "").strip()
        self.process: subprocess.Popen | None = None
        self._started = False
    
    def _ensure_started(self) -> None:
        """Ensure MCP server is started."""
        if self._started:
            return
        
        if not self.api_key:
            raise RuntimeError("BAIDU_MAPS_API_KEY not configured")
        
        # Start MCP server process (same pattern as Amap)
        env = os.environ.copy()
        env["BAIDU_MAPS_API_KEY"] = self.api_key
        
        self.process = subprocess.Popen(
            ["npx", "-y", "@baidu-maps/mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )
        self._started = True
    
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call MCP tool synchronously."""
        return asyncio.run(self.call_tool_async(tool_name, arguments))
    
    async def call_tool_async(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call MCP tool asynchronously."""
        self._ensure_started()
        
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP server not running")
        
        # Build JSON-RPC request (same as Amap)
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        response = json.loads(response_line)
        
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        
        return response.get("result", {})
    
    def find_nearby(self, keyword: str, city: str | None = None, location: str | None = None) -> ToolResult:
        """Find nearby POIs using Baidu Maps MCP.
        
        Args:
            keyword: Search keyword (e.g., "停车场", "餐厅")
            city: City name (e.g., "上海")
            location: Location coordinates (e.g., "121.445,31.227")
        
        Returns:
            ToolResult with POI data
        """
        try:
            # Build arguments for place_search
            arguments: dict[str, Any] = {
                "query": keyword,
                "region": city or "全国",
            }
            
            if location:
                arguments["location"] = location
                arguments["radius"] = 3000  # 3km radius
            
            # Call place_search tool
            result = self.call_tool("place_search", arguments)
            
            # Parse result (same pattern as Amap)
            content = result.get("content", [])
            if not content:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            # Extract POIs from content
            pois_text = content[0].get("text", "")
            pois_data = json.loads(pois_text) if isinstance(pois_text, str) else pois_text
            
            # Baidu uses "results" instead of "pois"
            pois = pois_data.get("results", [])
            
            if not pois:
                return ToolResult(ok=False, text=f"未找到{city or '附近'}的{keyword}", error="no_results")
            
            return ToolResult(
                ok=True,
                text=self._format_pois(pois[:10]),
                raw={"provider": "baidu_maps_mcp", "pois": pois[:10], "keyword": keyword, "city": city},
            )
        
        except Exception as e:
            return ToolResult(ok=False, text=f"百度地图MCP调用失败: {e}", error=str(e))
    
    def _format_pois(self, pois: list[dict[str, Any]]) -> str:
        """Format POI list to text (same as Amap)."""
        lines = []
        for i, poi in enumerate(pois[:3], 1):
            name = poi.get("name", "未知")
            address = poi.get("address", "")
            distance = poi.get("distance", "")
            
            suffix = f"，距离{distance}米" if distance else ""
            lines.append(f"{i}. {name}（{address}{suffix}）".strip())
        
        return "\n".join(lines)
    
    def close(self) -> None:
        """Close MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self._started = False
```

**关键改进**:
1. ✅ 进程管理逻辑与高德 MCP 完全一致
2. ✅ 健康检查逻辑对齐（`_ensure_started` 检查 `_started` 标志）
3. ✅ 异步调用模式一致（`call_tool` 包装 `call_tool_async`）
4. ✅ 错误处理模式一致

### 4.2 创建 BaiduMapsMCPProvider

```python
# agent_service/infra/tool_clients/providers/baidu_maps_mcp_provider.py
"""Baidu Maps MCP provider for find_nearby."""

from __future__ import annotations

from typing import Any

from domain.tools.types import ToolResult
from infra.tool_clients.baidu_maps_mcp_client import BaiduMapsMCPClient
from infra.tool_clients.provider_base import ProviderBase, ProviderResult


class BaiduMapsMCPProvider(ProviderBase):
    """Provider for Baidu Maps MCP."""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.client = BaiduMapsMCPClient()
    
    def execute(self, **kwargs: Any) -> ProviderResult:
        """Execute find_nearby using Baidu Maps MCP.
        
        Args:
            keyword: Search keyword
            city: City name (optional)
            location: Location coordinates (optional)
        
        Returns:
            ProviderResult with tool result
        """
        keyword = kwargs.get("keyword", "")
        city = kwargs.get("city")
        location = kwargs.get("location")
        
        if not keyword:
            return ProviderResult(
                success=False,
                data=None,
                error="missing_keyword",
                provider_name="baidu_maps_mcp",
            )
        
        try:
            result = self.client.find_nearby(keyword=keyword, city=city, location=location)
            
            if result.ok:
                return ProviderResult(
                    success=True,
                    data=result,
                    error=None,
                    provider_name="baidu_maps_mcp",
                )
            else:
                return ProviderResult(
                    success=False,
                    data=None,
                    error=result.error or "baidu_maps_mcp_failed",
                    provider_name="baidu_maps_mcp",
                )
        
        except Exception as e:
            return ProviderResult(
                success=False,
                data=None,
                error=f"baidu_maps_mcp_exception:{e}",
                provider_name="baidu_maps_mcp",
            )
```

### 4.3 更新 mcp_gateway.py

```python
# mcp_gateway.py::__init__()
def _init_find_nearby_chain(self) -> None:
    """Initialize find_nearby provider chain (Amap MCP -> Baidu Maps MCP -> Mock)."""
    try:
        from infra.tool_clients.provider_chain import ProviderChainManager
        from infra.tool_clients.provider_config import load_provider_configs
        from infra.tool_clients.providers.amap_mcp_provider import AmapMCPProvider
        from infra.tool_clients.providers.baidu_maps_mcp_provider import BaiduMapsMCPProvider
        from infra.tool_clients.providers.mock_provider import MockProvider
        
        self.find_nearby_chain = ProviderChainManager()
        
        # Register providers
        self.find_nearby_chain.register_provider("amap_mcp", AmapMCPProvider)
        self.find_nearby_chain.register_provider("baidu_maps_mcp", BaiduMapsMCPProvider)
        self.find_nearby_chain.register_provider("mock", MockProvider)
        
        # Load configuration
        configs = load_provider_configs()
        if "find_nearby" in configs:
            self.find_nearby_chain.configure_chain("find_nearby", configs["find_nearby"])
            self.use_find_nearby_chain = True
        else:
            self.use_find_nearby_chain = False
        
    except Exception as e:
        print(f"Warning: Failed to initialize find_nearby provider chain: {e}")
        self.find_nearby_chain = None
        self.use_find_nearby_chain = False
```

---

## 五、环境配置

### 5.1 环境变量

```bash
# .env
# 百度地图 API Key（用户提供）
BAIDU_MAPS_API_KEY=<your_baidu_maps_key>

# 百度地图 MCP 配置
BAIDU_MAPS_MCP_ENABLED=true
BAIDU_MAPS_MCP_TIMEOUT=3.0
```

### 5.2 MCP 配置（可选）

如果需要在 Kiro 中配置百度地图 MCP：

```json
// ~/.kiro/settings/mcp.json
{
  "mcpServers": {
    "baidu-maps": {
      "command": "npx",
      "args": ["-y", "@baidu-maps/mcp-server"],
      "env": {
        "BAIDU_MAPS_API_KEY": "<your_key>"
      },
      "disabled": false
    }
  }
}
```

---

## 六、测试计划

### 6.1 单元测试

```python
# tests/unit/test_baidu_maps_mcp_client.py
def test_baidu_maps_mcp_find_nearby():
    client = BaiduMapsMCPClient()
    result = client.find_nearby(keyword="停车场", city="上海")
    
    assert result.ok
    assert "停车场" in result.text
    assert result.raw["provider"] == "baidu_maps_mcp"
```

### 6.2 集成测试

```python
# tests/integration/test_m5_find_nearby.py

# 测试集（30条，包含带坐标的查询）
test_queries = [
    # 基础城市查询（15条）
    {"keyword": "停车场", "city": "上海"},
    {"keyword": "餐厅", "city": "北京"},
    {"keyword": "充电桩", "city": "深圳"},
    {"keyword": "洗手间", "city": "广州"},
    {"keyword": "咖啡厅", "city": "杭州"},
    {"keyword": "加油站", "city": "成都"},
    {"keyword": "便利店", "city": "武汉"},
    {"keyword": "银行", "city": "南京"},
    {"keyword": "药店", "city": "西安"},
    {"keyword": "超市", "city": "重庆"},
    {"keyword": "酒店", "city": "苏州"},
    {"keyword": "医院", "city": "长沙"},
    {"keyword": "地铁站", "city": "天津"},
    {"keyword": "公交站", "city": "郑州"},
    {"keyword": "出租车", "city": "青岛"},
    
    # 车展场景（10条）
    {"keyword": "停车场", "city": "上海", "location": None},  # 会展中心附近
    {"keyword": "餐厅", "city": "上海", "location": None},
    {"keyword": "充电桩", "city": "上海", "location": None},
    {"keyword": "洗手间", "city": "上海", "location": None},
    {"keyword": "咖啡厅", "city": "上海", "location": None},
    {"keyword": "便利店", "city": "上海", "location": None},
    {"keyword": "ATM", "city": "上海", "location": None},
    {"keyword": "地铁站", "city": "上海", "location": None},
    {"keyword": "出租车", "city": "上海", "location": None},
    {"keyword": "酒店", "city": "上海", "location": None},
    
    # 带坐标的查询（5条，覆盖 location 参数路径）
    {"keyword": "停车场", "city": "上海", "location": "121.445,31.227"},  # 静安寺
    {"keyword": "餐厅", "city": "北京", "location": "116.397,39.909"},  # 天安门
    {"keyword": "充电桩", "city": "深圳", "location": "114.057,22.543"},  # 深圳湾
    {"keyword": "咖啡厅", "city": "杭州", "location": "120.153,30.287"},  # 西湖
    {"keyword": "加油站", "city": "成都", "location": "104.066,30.572"},  # 春熙路
]

def test_find_nearby_fallback_to_baidu():
    """测试高德 MCP 故障时 fallback 到百度地图"""
    # 模拟高德 MCP 故障
    with patch.object(AmapMCPProvider, 'execute', side_effect=TimeoutError):
        result = gateway.invoke("find_nearby", {"keyword": "停车场", "city": "上海"})
        
        # 验证 fallback 到百度地图
        assert result.ok
        assert "fallback_chain" in result.raw
        assert "baidu_maps_mcp" in result.raw["fallback_chain"]

def test_find_nearby_with_location():
    """测试带坐标的查询（覆盖 location 参数路径）"""
    result = gateway.invoke("find_nearby", {
        "keyword": "停车场",
        "city": "上海",
        "location": "121.445,31.227"  # 静安寺坐标
    })
    
    assert result.ok
    assert "停车场" in result.text
    # 验证返回的 POI 距离静安寺较近
    assert result.raw.get("location") == "121.445,31.227"
```

---

## 七、验收标准

### 7.1 代码实现
- [x] BaiduMapsMCPClient 实现完成（参照高德 MCP 实现）
- [x] BaiduMapsMCPProvider 实现完成
- [x] AmapMCPProvider 实现完成
- [ ] mcp_gateway.py 集成完成（添加 _init_find_nearby_chain）
- [ ] provider_config.py 配置正确（高德 → 百度 → Mock）

### 7.2 测试验收
- [ ] 单元测试通过（覆盖率 > 90%）
- [ ] 集成测试通过（30条查询，成功率 100%）
- [ ] 带坐标查询测试通过（5条，覆盖 location 参数）
- [ ] Fallback 机制验证通过（高德故障 → 百度接管）
- [ ] 高德 MCP 使用率 > 95%

### 7.3 关键修正
- [x] 数字不一致问题修正（67% 统一）
- [x] 测试集错误查询替换（天气查询明确化）
- [x] 带坐标测试用例添加（5条）
- [x] 进程管理对齐高德 MCP 实现

---

**文档作者**: Kiro AI  
**审核人**: Tech Lead  
**创建日期**: 2026-03-07  
**状态**: Draft → Review → Approved
