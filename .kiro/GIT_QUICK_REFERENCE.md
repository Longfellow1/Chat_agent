# Git 版本管理快速参考

## 常用命令速查表

### 分支操作

```bash
# 查看分支
git branch                    # 本地分支
git branch -a                 # 所有分支
git branch -r                 # 远程分支

# 创建分支
git checkout -b feature/name  # 创建并切换
git branch feature/name       # 仅创建

# 切换分支
git checkout develop          # 切换到 develop
git switch develop            # 新语法

# 删除分支
git branch -d feature/name    # 删除本地
git push origin --delete feature/name  # 删除远程

# 重命名分支
git branch -m old-name new-name
```

### 标签操作

```bash
# 查看标签
git tag                       # 所有标签
git tag -l "v1.*"            # 特定模式

# 创建标签
git tag v1.0.0                # 轻量标签
git tag -a v1.0.0 -m "msg"   # 带注解标签

# 推送标签
git push origin v1.0.0        # 推送单个
git push origin --tags        # 推送所有

# 删除标签
git tag -d v1.0.0             # 删除本地
git push origin --delete v1.0.0  # 删除远程

# 查看标签详情
git show v1.0.0
```

### 提交操作

```bash
# 查看日志
git log                       # 完整日志
git log --oneline             # 简洁日志
git log --graph --all         # 图形化
git log v1.0.0..v1.1.0        # 版本间差异

# 提交
git add .                     # 暂存所有
git commit -m "msg"          # 提交
git commit --amend            # 修改最后一次提交

# 撤销
git revert <commit>           # 创建回滚提交
git reset --hard <commit>     # 重置（谨慎）
git reset --soft <commit>     # 保留更改
```

### 同步操作

```bash
# 获取更新
git fetch origin              # 获取远程更新
git pull origin develop       # 拉取并合并

# 推送
git push origin develop       # 推送分支
git push origin --tags        # 推送标签
git push origin --all         # 推送所有

# 同步分支
git rebase origin/develop     # 变基
git merge origin/develop      # 合并
```

---

## 工作流速查

### 开发新功能

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
# ... 编辑代码 ...
git add .
git commit -m "feat: description"
git push origin feature/my-feature
# 创建 PR 到 develop
```

### 发布新版本

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0
# 更新版本号和 CHANGELOG
git add .
git commit -m "chore: bump version to v1.1.0"
git push origin release/v1.1.0
# 创建 PR 到 main，审查通过后合并
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
git checkout develop
git merge main
git push origin develop
```

### 紧急修复

```bash
git checkout main
git pull origin main
git checkout -b hotfix/v1.0.1 v1.0.0
# ... 修复代码 ...
git add .
git commit -m "fix: critical issue"
git push origin hotfix/v1.0.1
# 创建 PR 到 main，审查通过后合并
git checkout main
git pull origin main
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin v1.0.1
git checkout develop
git merge main
git push origin develop
```

### 版本回滚

```bash
# 查看版本
git tag -l
git log --oneline --all

# 创建回滚分支
git checkout -b rollback-v1.0.0 v1.0.0
git push origin rollback-v1.0.0
# 创建 PR 到 main

# 或创建回滚提交
git checkout main
git revert v1.0.0..HEAD
git push origin main
```

---

## 版本查询

### 查看版本信息

```bash
# 所有版本
git tag -l

# 版本详情
git show v1.0.0

# 版本间差异
git diff v1.0.0 v1.1.0

# 版本提交
git log v1.0.0..v1.1.0 --oneline

# 特定版本的文件
git show v1.0.0:path/to/file

# 检出特定版本
git checkout v1.0.0
```

### 查看分支状态

```bash
# 分支列表
git branch -a

# 分支追踪
git branch -vv

# 未合并分支
git branch --no-merged main

# 已合并分支
git branch --merged main
```

---

## 多版本并行开发

### 创建维护线

```bash
# v1.x 维护线
git checkout -b maintain/v1.x v1.0.0
git push -u origin maintain/v1.x

# v2.x 开发线
git checkout develop
git checkout -b maintain/v2.x
git push -u origin maintain/v2.x
```

### 在维护线上开发

```bash
# 在 v1.x 上修复 bug
git checkout maintain/v1.x
git checkout -b bugfix/v1-issue
# ... 修复 ...
git push origin bugfix/v1-issue
# 创建 PR 到 maintain/v1.x

# 在 v2.x 上开发新功能
git checkout maintain/v2.x
git checkout -b feature/v2-feature
# ... 开发 ...
git push origin feature/v2-feature
# 创建 PR 到 maintain/v2.x
```

### 同步版本线

```bash
# 同步 main 到 v1.x
git checkout maintain/v1.x
git merge main
git push origin maintain/v1.x

# 同步 v1.x 到 develop
git checkout develop
git merge maintain/v1.x
git push origin develop
```

---

## 提交信息规范

### Conventional Commits 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- `feat`: 新功能
- `fix`: bug 修复
- `docs`: 文档
- `style`: 代码风格
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建、依赖等

### 示例

```bash
git commit -m "feat(auth): add login functionality"
git commit -m "fix(api): resolve timeout issue"
git commit -m "docs: update README"
git commit -m "chore: bump version to v1.1.0"
```

---

## 故障排查

### 分支落后

```bash
git fetch origin
git rebase origin/develop
# 或
git merge origin/develop
```

### 误删分支恢复

```bash
git reflog
git checkout -b recovered-branch <commit-hash>
```

### 撤销推送

```bash
# 创建回滚提交
git revert <commit>
git push origin develop

# 或重置（仅限未发布分支）
git reset --hard <commit>
git push origin develop --force
```

### 解决合并冲突

```bash
# 查看冲突
git status

# 手动编辑冲突文件
# 标记为已解决
git add .

# 完成合并
git commit -m "resolve merge conflict"
```

### 查看谁修改了什么

```bash
git blame path/to/file
git log -p path/to/file
```

---

## 配置技巧

### 全局配置

```bash
# 用户信息
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# 默认编辑器
git config --global core.editor "vim"

# 别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --graph --oneline --all'
```

### 项目配置

```bash
# 仅对当前项目
git config user.name "Project Name"
git config user.email "project@email.com"

# 查看配置
git config --list
```

---

## 性能优化

### 大仓库优化

```bash
# 浅克隆
git clone --depth 1 <url>

# 部分克隆
git clone --filter=blob:none <url>

# 垃圾回收
git gc --aggressive
```

### 加速操作

```bash
# 并行操作
git config --global fetch.parallel 10

# 压缩
git config --global core.compression 9
```

---

## 安全建议

### 保护敏感信息

```bash
# 使用 .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore

# 移除已提交的敏感信息
git filter-branch --tree-filter 'rm -f .env' HEAD
```

### 签名提交

```bash
# 生成 GPG 密钥
gpg --gen-key

# 配置签名
git config --global user.signingkey <key-id>

# 签名提交
git commit -S -m "message"

# 验证签名
git log --show-signature
```

---

## 相关文档

- 详细策略: `.kiro/GIT_VERSIONING_STRATEGY.md`
- 多版本指南: `.kiro/MULTI_VERSION_PARALLEL_GUIDE.md`
- 设置检查清单: `.kiro/GIT_SETUP_CHECKLIST.md`
- 初始化脚本: `init_git_versioning.sh`

---

## 快速链接

- [Git 官方文档](https://git-scm.com/doc)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
