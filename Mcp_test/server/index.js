import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { initTripPlannerAgent, tripPlannerAgent } from './agent/planner.js';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;
const isProduction = process.env.NODE_ENV === 'production';

// 中间件
app.use(cors());
app.use(express.json());

// 启动时初始化 Agent
console.log('🚀 启动服务器，初始化 Agent...');
initTripPlannerAgent().catch(err => {
  console.error('❌ Agent 初始化失败，服务器仍将启动但功能可能受限:', err.message);
});

// API 路由（必须在静态文件服务之前）
// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Trip Planner API is running' });
});

// 行程规划接口
app.post('/api/plan', async (req, res) => {
  try {
    const { query, location, days, preferences } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: '缺少必需参数: query' });
    }

    console.log('收到行程规划请求:', { query, location, days, preferences });

    // 构建用户查询
    const userQuery = `帮我规划一个行程：${query}${location ? `，地点：${location}` : ''}${days ? `，天数：${days}天` : ''}${preferences ? `，偏好：${preferences}` : ''}`;

    // 调用 Agent
    const result = await tripPlannerAgent.invoke({
      messages: [{ role: 'user', content: userQuery }],
    });

    console.log('Agent 执行结果:', result);

    res.json({
      success: true,
      plan: result.messages[result.messages.length - 1].content,
      toolCalls: result.messages.filter(m => m.additional_kwargs?.tool_calls),
    });
  } catch (error) {
    console.error('行程规划错误:', error);
    res.status(500).json({
      error: '行程规划失败',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    });
  }
});

// 生产环境：提供静态文件服务（必须在所有 API 路由之后）
if (isProduction) {
  const clientDistPath = join(__dirname, '..', 'client', 'dist');
  app.use(express.static(clientDistPath));
  
  // 所有非 API 路由都返回 index.html（支持前端路由）
  app.get('*', (req, res) => {
    res.sendFile(join(clientDistPath, 'index.html'));
  });
}

// 启动服务器
const server = app.listen(PORT, () => {
  console.log(`🚀 行程规划 API 服务器运行在 http://localhost:${PORT}`);
  console.log(`📝 健康检查: http://localhost:${PORT}/health`);
  if (isProduction) {
    console.log(`🌐 前端应用: http://localhost:${PORT}`);
  }
});

// 处理端口占用错误
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ 端口 ${PORT} 已被占用！`);
    console.error(`💡 解决方案：`);
    console.error(`   1. 查找并终止占用端口的进程：lsof -ti:${PORT} | xargs kill -9`);
    console.error(`   2. 或者修改 .env 文件中的 PORT 端口号`);
    process.exit(1);
  } else {
    throw err;
  }
});

