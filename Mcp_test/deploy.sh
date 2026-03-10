#!/bin/bash

# ============================================
# 行程规划助手 - 一键部署脚本
# ============================================
# 使用方法: ./deploy.sh
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 检查 Node.js 版本
check_node_version() {
    print_info "检查 Node.js 版本..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_success "Node.js 版本: $(node -v) ✓"
        else
            print_error "Node.js 版本过低，需要 18+，当前版本: $(node -v)"
            exit 1
        fi
    else
        print_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi
}

# 检查 npm 版本
check_npm_version() {
    print_info "检查 npm 版本..."
    if command -v npm &> /dev/null; then
        print_success "npm 版本: $(npm -v) ✓"
    else
        print_error "npm 未安装"
        exit 1
    fi
}

# 检查环境变量文件
check_env_file() {
    print_info "检查环境变量配置..."
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，正在从 env.example 创建..."
        if [ -f "env.example" ]; then
            cp env.example .env
            print_success ".env 文件已创建"
            print_warning "⚠️  请编辑 .env 文件，填入必要的配置（特别是 OPENAI_API_KEY）"
        else
            print_error "env.example 文件不存在"
            exit 1
        fi
    else
        print_success ".env 文件已存在"
    fi
    
    # 检查必需的配置
    if grep -q "your_openai_api_key_here\|your-openai-api-key-here" .env 2>/dev/null; then
        print_warning "⚠️  检测到 .env 文件中可能包含示例配置，请确保已填入实际的 API Key"
    fi
}

# 安装依赖
install_dependencies() {
    print_header "安装项目依赖"
    
    print_info "安装根目录依赖..."
    if npm install; then
        print_success "根目录依赖安装完成"
    else
        print_error "根目录依赖安装失败"
        exit 1
    fi
    
    print_info "安装客户端依赖..."
    cd client
    if npm install; then
        print_success "客户端依赖安装完成"
    else
        print_error "客户端依赖安装失败"
        exit 1
    fi
    cd ..
}

# 构建前端
build_frontend() {
    print_header "构建前端应用"
    
    print_info "开始构建前端..."
    cd client
    if npm run build; then
        print_success "前端构建完成"
    else
        print_error "前端构建失败"
        exit 1
    fi
    cd ..
}

# 检查构建结果
check_build() {
    print_info "检查构建结果..."
    if [ -d "client/dist" ]; then
        print_success "前端构建文件已生成: client/dist/"
    else
        print_error "前端构建文件不存在"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    print_header "部署完成"
    
    print_success "项目已成功部署！"
    echo ""
    print_info "下一步操作："
    echo ""
    echo "1. 确保 .env 文件已正确配置："
    echo "   - OPENAI_API_KEY (必需)"
    echo "   - AMAP_API_KEY (可选)"
    echo "   - XHS_MCP_COMMAND (可选)"
    echo ""
    echo "2. 启动生产服务器："
    echo "   ${GREEN}npm run start${NC}"
    echo ""
    echo "   或者启动开发服务器："
    echo "   ${GREEN}npm run dev${NC}"
    echo ""
    echo "3. 访问应用："
    echo "   - 生产模式: http://localhost:3001 (需要配置静态文件服务)"
    echo "   - 开发模式: http://localhost:5173 (前端) + http://localhost:3001 (后端)"
    echo ""
    print_warning "注意：生产环境需要配置 Express 静态文件服务来提供前端文件"
    echo ""
}

# 主函数
main() {
    print_header "行程规划助手 - 一键部署"
    
    # 检查基本命令
    check_command "node"
    check_command "npm"
    
    # 环境检查
    check_node_version
    check_npm_version
    check_env_file
    
    # 安装和构建
    install_dependencies
    build_frontend
    check_build
    
    # 显示部署信息
    show_deployment_info
    
    print_success "部署脚本执行完成！"
}

# 运行主函数
main
