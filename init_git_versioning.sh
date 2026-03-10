#!/bin/bash

# Git 版本管理初始化脚本
# 用途: 为项目设置 Git Flow 工作流

set -e

echo "=========================================="
echo "Git 版本管理初始化"
echo "=========================================="

# 1. 初始化 Git 仓库
if [ ! -d ".git" ]; then
    echo "✓ 初始化 Git 仓库..."
    git init
else
    echo "✓ Git 仓库已存在"
fi

# 2. 配置 Git 用户信息（如果未配置）
if [ -z "$(git config user.name)" ]; then
    echo "✓ 配置 Git 用户信息..."
    read -p "请输入 Git 用户名: " git_name
    read -p "请输入 Git 邮箱: " git_email
    git config user.name "$git_name"
    git config user.email "$git_email"
else
    echo "✓ Git 用户信息已配置: $(git config user.name) <$(git config user.email)>"
fi

# 3. 创建 .gitignore（如果不存在）
if [ ! -f ".gitignore" ]; then
    echo "✓ 创建 .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Testing
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
npm-debug.log
yarn-error.log

# Build
dist/
build/
*.egg-info/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
EOF
else
    echo "✓ .gitignore 已存在"
fi

# 4. 创建 CHANGELOG.md（如果不存在）
if [ ! -f "CHANGELOG.md" ]; then
    echo "✓ 创建 CHANGELOG.md..."
    cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-03-10

### Added
- Initial release
EOF
else
    echo "✓ CHANGELOG.md 已存在"
fi

# 5. 初始提交
if [ -z "$(git log --oneline 2>/dev/null | head -1)" ]; then
    echo "✓ 创建初始提交..."
    git add .
    git commit -m "chore: initial commit with git versioning strategy"
else
    echo "✓ 仓库已有提交历史"
fi

# 6. 创建 main 分支（如果不存在）
if ! git rev-parse --verify main >/dev/null 2>&1; then
    echo "✓ 创建 main 分支..."
    git branch -M main
else
    echo "✓ main 分支已存在"
fi

# 7. 创建 develop 分支（如果不存在）
if ! git rev-parse --verify develop >/dev/null 2>&1; then
    echo "✓ 创建 develop 分支..."
    git checkout -b develop
else
    echo "✓ develop 分支已存在"
fi

# 8. 创建初始版本标签
if ! git rev-parse --verify v0.1.0 >/dev/null 2>&1; then
    echo "✓ 创建初始版本标签 v0.1.0..."
    git tag -a v0.1.0 -m "Initial version 0.1.0"
else
    echo "✓ 版本标签 v0.1.0 已存在"
fi

# 9. 显示当前状态
echo ""
echo "=========================================="
echo "初始化完成！"
echo "=========================================="
echo ""
echo "当前分支:"
git branch -a
echo ""
echo "版本标签:"
git tag -l
echo ""
echo "下一步:"
echo "1. 配置远程仓库: git remote add origin <repository-url>"
echo "2. 推送分支: git push -u origin main develop"
echo "3. 推送标签: git push origin --tags"
echo "4. 配置分支保护规则（在 GitHub/GitLab 中）"
echo ""
echo "详细文档: .kiro/GIT_VERSIONING_STRATEGY.md"
echo "检查清单: .kiro/GIT_SETUP_CHECKLIST.md"
