#!/bin/bash

# ============================================
# Agent Service 快速启动指引
# ============================================

echo "🚀 Agent Service 快速启动"
echo ""

# 1. 激活虚拟环境
echo "📦 步骤 1: 激活虚拟环境"
source .venv/bin/activate

# 2. 加载环境变量
echo "🔧 步骤 2: 加载环境变量"
export $(cat .env.agent | grep -v '^#' | xargs)

# 3. 设置后端（默认使用 lmstudio）
echo "🤖 步骤 3: 设置 LLM 后端"
export AGENT_BACKEND=lmstudio
export LM_STUDIO_BASE=http://localhost:1234
export LM_STUDIO_MODEL=qwen2.5-7b-instruct-mlx

# 4. 进入服务目录
cd agent_service

# 5. 启动服务
echo ""
echo "✅ 环境准备完成！"
echo ""
echo "现在可以启动服务："
echo "  python -m app.api.server"
echo ""
echo "或者使用 uvicorn："
echo "  uvicorn app.api.server:app --host 0.0.0.0 --port 8000"
echo ""
echo "服务启动后，可以在另一个终端测试："
echo "  curl http://127.0.0.1:8000/health"
echo "  curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{\"query\":\"北京天气怎么样\"}'"
echo ""

