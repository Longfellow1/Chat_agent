import { MultiServerMCPClient } from '@langchain/mcp-adapters';

let xhsClient = null;
let xhsTools = [];

/**
 * 初始化小红书 MCP 客户端
 * 参考: https://github.com/xpzouying/xiaohongshu-mcp
 */
export async function initXhsMCPClient() {
  if (xhsClient) {
    return { client: xhsClient, tools: xhsTools };
  }

  // 如果未配置，返回空工具列表
  if (!process.env.XHS_MCP_SERVER_URL && !process.env.XHS_MCP_COMMAND) {
    console.log('ℹ️  小红书 MCP 未配置，跳过初始化');
    return { client: null, tools: [] };
  }

  try {
    const xhsConfig = process.env.XHS_MCP_COMMAND
      ? {
          // 方式2: stdio transport (如果使用本地 MCP 服务器)
          transport: 'stdio',
          command: process.env.XHS_MCP_COMMAND,
          args: process.env.XHS_MCP_ARGS?.split(',') || [],
        }
      : {
          // 方式1: HTTP/SSE transport
          transport: process.env.XHS_MCP_TRANSPORT || 'sse',
          url: process.env.XHS_MCP_SERVER_URL,
          headers: {
            'Authorization': process.env.XHS_API_KEY ? `Bearer ${process.env.XHS_API_KEY}` : undefined,
            'Content-Type': 'application/json',
          },
          reconnect: {
            enabled: true,
            maxAttempts: 3,
            delayMs: 1000,
          },
        };

    xhsClient = new MultiServerMCPClient({
      throwOnLoadError: false,
      prefixToolNameWithServerName: true,
      useStandardContentBlocks: true,
      mcpServers: {
        xiaohongshu: xhsConfig,
      },
    });

    xhsTools = await xhsClient.getTools();
    console.log(`✅ 小红书 MCP 客户端已连接，可用工具数: ${xhsTools.length}`);
    xhsTools.forEach(tool => {
      console.log(`  - ${tool.name}: ${tool.description || '无描述'}`);
    });
    return { client: xhsClient, tools: xhsTools };
  } catch (error) {
    console.warn('⚠️  小红书 MCP 客户端连接失败，将在演示模式下运行:', error.message);
    return { client: null, tools: [] };
  }
}

/**
 * 创建小红书 MCP 工具列表（用于 Agent）
 */
export async function getXhsTools() {
  const { tools } = await initXhsMCPClient();
  return tools;
}

/**
 * 关闭小红书 MCP 客户端
 */
export async function closeXhsClient() {
  if (xhsClient) {
    try {
      await xhsClient.close();
      xhsClient = null;
      xhsTools = [];
    } catch (error) {
      console.error('关闭小红书 MCP 客户端失败:', error);
    }
  }
}

