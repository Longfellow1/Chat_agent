import { MultiServerMCPClient } from '@langchain/mcp-adapters';

let amapClient = null;
let amapTools = [];

/**
 * 初始化高德地图 MCP 客户端
 * 根据实际的高德地图 MCP 服务配置进行调整
 */
export async function initAmapMCPClient() {
  if (amapClient) {
    return { client: amapClient, tools: amapTools };
  }

  // 如果未配置，返回空工具列表
  if (!process.env.AMAP_MCP_SERVER_URL && !process.env.AMAP_MCP_COMMAND) {
    console.log('ℹ️  高德地图 MCP 未配置，跳过初始化');
    return { client: null, tools: [] };
  }

  try {
    // 优先使用 Node.js I/O 模式（官方推荐方式）
    // 参考：https://lbs.amap.com/api/mcp-server/gettingstarted
    const amapConfig = process.env.AMAP_MCP_COMMAND
      ? {
          // 方式1: stdio transport - Node.js I/O 模式（推荐）
          // 使用官方提供的 npm 包：@amap/amap-maps-mcp-server
          transport: 'stdio',
          command: process.env.AMAP_MCP_COMMAND,
          args: process.env.AMAP_MCP_ARGS?.split(',') || [],
          env: {
            AMAP_MAPS_API_KEY: process.env.AMAP_API_KEY,
          },
        }
      : process.env.AMAP_MCP_SERVER_URL
      ? {
          // 方式2: SSE transport
          // URL 格式：https://mcp.amap.com/api/v1/sse?key=<your_key>
          transport: 'sse',
          url: (() => {
            let url = process.env.AMAP_MCP_SERVER_URL;
            // 自动修复错误的 URL 路径（/v1 -> /api/v1/sse）
            if (url.includes('/v1') && !url.includes('/api/v1/sse')) {
              url = url.replace('/v1', '/api/v1/sse');
              console.log(`ℹ️  自动修复高德地图 MCP URL: ${process.env.AMAP_MCP_SERVER_URL} -> ${url}`);
            }
            // 如果 URL 中没有 key 参数，自动添加
            if (!url.includes('?key=')) {
              url = `${url}?key=${process.env.AMAP_API_KEY}`;
            }
            return url;
          })(),
          reconnect: {
            enabled: true,
            maxAttempts: 3,
            delayMs: 1000,
          },
        }
      : null;

    if (!amapConfig) {
      console.log('ℹ️  高德地图 MCP 未配置，跳过初始化');
      return { client: null, tools: [] };
    }

    amapClient = new MultiServerMCPClient({
      throwOnLoadError: false, // 允许加载失败，便于调试
      prefixToolNameWithServerName: true,
      useStandardContentBlocks: true,
      mcpServers: {
        amap: amapConfig,
      },
    });

    amapTools = await amapClient.getTools();
    console.log(`✅ 高德地图 MCP 客户端已连接，可用工具数: ${amapTools.length}`);
    amapTools.forEach(tool => {
      console.log(`  - ${tool.name}: ${tool.description || '无描述'}`);
    });
    return { client: amapClient, tools: amapTools };
  } catch (error) {
    console.warn('⚠️  高德地图 MCP 客户端连接失败，将在演示模式下运行:', error.message);
    return { client: null, tools: [] };
  }
}

/**
 * 创建高德地图 MCP 工具列表（用于 Agent）
 */
export async function getAmapTools() {
  const { tools } = await initAmapMCPClient();
  return tools;
}

/**
 * 关闭高德地图 MCP 客户端
 */
export async function closeAmapClient() {
  if (amapClient) {
    try {
      await amapClient.close();
      amapClient = null;
      amapTools = [];
    } catch (error) {
      console.error('关闭高德地图 MCP 客户端失败:', error);
    }
  }
}

