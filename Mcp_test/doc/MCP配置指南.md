# MCP 服务配置指南

## 📌 回答你的问题

### 1. 小红书 MCP - **不需要 API Key**

小红书 MCP 使用**扫码登录**方式，不需要 API Key。

**工作原理：**
- 首次使用时通过扫码登录小红书账号
- 登录状态会保存，后续使用无需重复登录
- 主要通过 Python MCP 服务器运行（stdio transport）

**配置方式（可选）：**
如果使用本地 Python MCP 服务器，在 `.env` 中配置：

```bash
# 方式1: 使用本地 Python MCP 服务器（推荐）
XHS_MCP_COMMAND=python
XHS_MCP_ARGS=-m,xiaohongshu_mcp

# 方式2: 使用 HTTP/SSE MCP 服务（如果提供）
XHS_MCP_SERVER_URL=https://api.xiaohongshu.com/mcp
# 注意：即使使用 HTTP 方式，通常也不需要 API Key，而是通过登录 token
```

**注意：**
- 小红书 MCP 项目：https://github.com/xpzouying/xiaohongshu-mcp
- 需要使用 Python 环境运行 MCP 服务器
- 首次运行时会提示扫码登录

---

### 2. 高德地图 MCP - **需要 API Key**

高德地图 MCP **需要申请 API Key**。

## 🗺️ 高德地图 API Key 申请步骤

### 步骤 1: 注册高德开放平台账号

1. 访问 **高德开放平台**: https://lbs.amap.com/
2. 点击右上角"注册"或"登录"
3. 完成账号注册和开发者认证

### 步骤 2: 创建应用并获取 API Key

1. **登录控制台**
   - 访问: https://console.amap.com/dev/key/app
   - 登录你的账号

2. **创建应用**
   - 点击"应用管理" → "我的应用"
   - 点击"创建新应用"
   - 填写应用信息：
     - 应用名称：例如 "行程规划助手"
     - 应用类型：选择 "Web端" 或 "服务端"

3. **添加 Key**
   - 在创建的应用中，点击"添加"按钮
   - 填写 Key 信息：
     - **Key 名称**：例如 "MCP-Server-Key"
     - **服务平台**：选择 **"Web服务"** ⚠️（重要！）
     - **IP 白名单**：可以暂时不填（开发阶段）
   - 点击"提交"

4. **获取 API Key**
   - 提交后，在 Key 列表中可以看到生成的 Key
   - 复制这个 Key（格式类似：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`）

### 步骤 3: 配置到项目中

编辑 `.env` 文件，添加高德地图配置：

```bash
# 高德地图 API Key（必需）
AMAP_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# 高德地图 MCP 服务器地址
# 注意：高德 MCP 的实际地址请参考官方文档
AMAP_MCP_SERVER_URL=https://mcp.amap.com/v1
```

### 参考文档

- **高德地图 MCP Server 文档**: https://lbs.amap.com/api/mcp-server/summary
- **高德开放平台控制台**: https://console.amap.com/dev/key/app
- **应用管理页面**: https://console.amap.com/dev/key/app

---

## 📝 完整配置示例

### `.env` 文件完整配置

```bash
# ========== 必需配置 ==========
# OpenAI API Key（必需）
OPENAI_API_KEY=sk-your-openai-api-key-here

# ========== 高德地图 MCP（推荐配置）==========
# 高德地图 API Key（必需，如果使用高德 MCP）
AMAP_API_KEY=your-amap-api-key-here

# 高德地图 MCP 服务器地址（根据官方文档填写实际地址）
AMAP_MCP_SERVER_URL=https://mcp.amap.com/v1
# 或使用传输方式：sse（默认）或 http
AMAP_MCP_TRANSPORT=sse

# ========== 小红书 MCP（可选配置）==========
# 方式1: 使用本地 Python MCP 服务器（推荐）
XHS_MCP_COMMAND=python
XHS_MCP_ARGS=-m,xiaohongshu_mcp

# 方式2: 使用 HTTP/SSE MCP 服务（如果提供）
# XHS_MCP_SERVER_URL=https://api.xiaohongshu.com/mcp
# XHS_MCP_TRANSPORT=sse

# ========== 服务器配置 ==========
PORT=3001
NODE_ENV=development
```

---

## ⚠️ 重要提示

### 关于高德地图 MCP

1. **API Key 是必需的** - 必须先申请才能使用高德地图 MCP
2. **MCP 服务器地址** - 请参考高德地图官方 MCP 文档确认实际的服务地址
3. **平台选择** - 申请 Key 时，服务平台务必选择 **"Web服务"**
4. **IP 白名单** - 开发阶段可以不配置，生产环境建议配置

### 关于小红书 MCP

1. **不需要 API Key** - 使用扫码登录方式
2. **需要 Python 环境** - 如果使用本地 MCP 服务器，需要安装 Python
3. **首次使用需登录** - 第一次运行时会提示扫码登录
4. **登录状态保存** - 登录后状态会保存，无需重复登录

---

## 🧪 验证配置

配置完成后，启动服务器：

```bash
npm run server
```

查看控制台输出，应该看到：

```
✅ 高德地图 MCP 客户端已连接，可用工具数: X
  - amap_search_place: 地点搜索
  - amap_route_plan: 路线规划
  ...
```

如果看到警告信息，说明配置有问题：
```
⚠️  高德地图 MCP 客户端连接失败，将在演示模式下运行
```

检查：
1. `AMAP_API_KEY` 是否正确
2. `AMAP_MCP_SERVER_URL` 是否正确
3. 网络连接是否正常

---

## 📚 相关链接

- [高德开放平台](https://lbs.amap.com/)
- [高德地图 MCP Server 文档](https://lbs.amap.com/api/mcp-server/summary)
- [小红书 MCP GitHub](https://github.com/xpzouying/xiaohongshu-mcp)
- [应用管理控制台](https://console.amap.com/dev/key/app)

