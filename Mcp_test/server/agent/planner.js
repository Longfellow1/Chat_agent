import { createAgent } from 'langchain';
import { ChatOpenAI } from '@langchain/openai';
import { getAmapTools } from '../mcp/amap.js';
import { getXhsTools } from '../mcp/xhs.js';

let plannerAgent = null;
let isInitializing = false;

/**
 * 初始化行程规划 Agent
 * 集成高德地图和小红书 MCP 工具
 */
export async function initTripPlannerAgent() {
  if (plannerAgent) {
    return plannerAgent;
  }

  if (isInitializing) {
    // 等待初始化完成
    while (isInitializing) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return plannerAgent;
  }

  isInitializing = true;

  try {
    console.log('🚀 初始化行程规划 Agent...');

    // 初始化 LLM（支持 OpenAI 或自定义 LLM 服务）
    let model;
    
    // 检查是否使用自定义 LLM 服务（火山引擎等）
    if (process.env.LM_CLOUD_ENDPOINT && process.env.LM_CLOUD_API_KEY) {
      // 使用自定义 LLM 服务
      console.log('📡 使用自定义 LLM 服务:', process.env.LM_CLOUD_ENDPOINT);
      // 提取基础 URL：ChatOpenAI 会自动在 baseURL 后添加 /v1/chat/completions
      // 但火山引擎使用 /api/v3/chat/completions，所以 baseURL 应该到 /api/v3
      let baseURL = process.env.LM_CLOUD_ENDPOINT;
      if (baseURL.includes('/chat/completions')) {
        baseURL = baseURL.replace('/chat/completions', '');
      }
      console.log('🔧 BaseURL 配置:', baseURL);
      console.log('🔧 API Key:', process.env.LM_CLOUD_API_KEY ? `${process.env.LM_CLOUD_API_KEY.substring(0, 10)}...` : '未设置');
      
      // 同时传递 apiKey 和 configuration.baseURL
      // ChatOpenAI 会优先使用 fields.apiKey，但 baseURL 需要通过 configuration 传递
      model = new ChatOpenAI({
        apiKey: process.env.LM_CLOUD_API_KEY,
        configuration: {
          baseURL: baseURL,
        },
        model: process.env.LM_CLOUD_MODEL || 'ep-20251120140152-wp4hl',
        temperature: parseFloat(process.env.LM_CLOUD_TEMPERATURE || '0.7'),
        maxTokens: parseInt(process.env.LM_CLOUD_MAX_TOKENS || '4000'),
      });
    } else if (process.env.OPENAI_API_KEY) {
      // 使用 OpenAI 服务
      console.log('📡 使用 OpenAI 服务');
      model = new ChatOpenAI({
        model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
        temperature: 0.7,
      });
    } else {
      throw new Error('缺少 LLM 配置：需要设置 OPENAI_API_KEY 或 LM_CLOUD_ENDPOINT + LM_CLOUD_API_KEY');
    }

    // 获取所有 MCP 工具
    console.log('📦 加载 MCP 工具...');
    const [amapTools, xhsTools] = await Promise.all([
      getAmapTools(),
      getXhsTools(),
    ]);

    const allTools = [...amapTools, ...xhsTools];

    if (allTools.length === 0) {
      console.warn('⚠️  未找到任何 MCP 工具，Agent 将以仅 LLM 模式运行');
    } else {
      console.log(`✅ 已加载 ${allTools.length} 个工具:`);
      allTools.forEach(tool => {
        console.log(`  - ${tool.name}`);
      });
    }

    // 创建 Agent
    plannerAgent = createAgent({
      model: model,
      tools: allTools,
      // 系统提示词，指导 Agent 如何使用工具
      systemMessage: `你是一个专业的行程规划助手。你可以使用以下工具来帮助用户规划行程：

1. 高德地图工具（amap_*）:
   - 搜索地点、获取位置信息
   - 规划路线和导航
   - 查询天气信息
   - 查找附近的餐厅、景点等

2. 小红书工具（xiaohongshu_*）:
   - 搜索旅游攻略
   - 查找美食推荐
   - 获取景点评价和热门打卡地

当用户提出行程规划需求时，你应该：
1. 首先使用高德地图工具搜索相关地点和获取位置信息
2. 使用小红书工具查找相关的旅游攻略和推荐
3. 根据获取的信息，生成一个详细的行程规划
4. 行程规划应该包括：每天的行程安排、推荐景点、餐厅、路线建议等
5. 如果工具调用失败，根据常识给出建议，并告知用户

请用中文回复，格式清晰易读。`,
    });

    console.log('✅ 行程规划 Agent 初始化完成');
    isInitializing = false;
    return plannerAgent;
  } catch (error) {
    isInitializing = false;
    console.error('❌ Agent 初始化失败:', error);
    throw error;
  }
}

/**
 * 获取行程规划 Agent（单例模式）
 */
export const tripPlannerAgent = {
  async invoke(input) {
    if (!plannerAgent) {
      await initTripPlannerAgent();
    }
    return plannerAgent.invoke(input);
  },
};

