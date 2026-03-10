# Git 版本管理策略

## 概述
本项目采用 **Git Flow + Semantic Versioning** 的混合策略，支持多版本并行开发、稳定版本管理和完整的历史回滚能力。

---

## 分支模型

### 主要分支

#### 1. `main` - 生产稳定分支
- **用途**: 存储所有发布版本，每个提交都对应一个版本标签
- **保护规则**: 
  - 禁止直接推送，仅通过 PR 合并
  - 需要代码审查和 CI 通过
  - 每次合并自动创建版本标签
- **版本标签**: `v1.0.0`, `v1.1.0`, `v2.0.0` 等

#### 2. `develop` - 开发集成分支
- **用途**: 集成各功能分支，作为下一个版本的基础
- **保护规则**: 
  - 禁止直接推送，仅通过 PR 合并
  - 需要 CI 通过
- **版本标签**: `v1.0.0-rc.1`, `v1.0.0-beta.1` (预发布版本)

#### 3. `release/v*` - 发布准备分支
- **用途**: 准备新版本发布（修复 bug、更新版本号、更新 CHANGELOG）
- **命名**: `release/v1.0.0`, `release/v2.1.0`
- **生命周期**: 
  - 从 `develop` 创建
  - 完成后合并回 `main` 和 `develop`
  - 创建版本标签后删除

#### 4. `hotfix/v*` - 紧急修复分支
- **用途**: 修复生产环境的关键 bug
- **命名**: `hotfix/v1.0.1`, `hotfix/v1.0.2`
- **生命周期**:
  - 从 `main` 的特定版本标签创建
  - 完成后合并回 `main` 和 `develop`
  - 创建新的补丁版本标签

### 功能分支

#### 5. `feature/*` - 功能开发分支
- **命名**: `feature/user-auth`, `feature/payment-integration`
- **来源**: 从 `develop` 创建
- **合并**: 通过 PR 合并回 `develop`
- **删除**: 合并后删除

#### 6. `bugfix/*` - Bug 修复分支
- **命名**: `bugfix/login-issue`, `bugfix/data-validation`
- **来源**: 从 `develop` 创建
- **合并**: 通过 PR 合并回 `develop`

---

## 版本号规范 (Semantic Versioning)

格式: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

### 版本递增规则

| 版本类型 | 格式 | 场景 | 示例 |
|---------|------|------|------|
| 主版本 | `X.0.0` | 不兼容的 API 变更 | `1.0.0` → `2.0.0` |
| 次版本 | `X.Y.0` | 向后兼容的新功能 | `1.0.0` → `1.1.0` |
| 补丁版本 | `X.Y.Z` | 向后兼容的 bug 修复 | `1.0.0` → `1.0.1` |
| 预发布版本 | `X.Y.Z-alpha.N` | 内部测试版本 | `1.0.0-alpha.1` |
| 候选版本 | `X.Y.Z-rc.N` | 发布候选版本 | `1.0.0-rc.1` |

---

## 工作流程

### 场景 1: 开发新功能

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# 2. 开发并提交
git add .
git commit -m "feat: add new feature"

# 3. 推送并创建 PR
git push origin feature/new-feature
# 在 GitHub/GitLab 创建 PR 到 develop

# 4. PR 审查通过后合并
# 合并后自动删除分支
```

### 场景 2: 发布新版本

```bash
# 1. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# 2. 更新版本号和 CHANGELOG
# 编辑 package.json, setup.py 等版本文件
# 编辑 CHANGELOG.md

git add .
git commit -m "chore: bump version to v1.1.0"

# 3. 推送发布分支
git push origin release/v1.1.0

# 4. 创建 PR 到 main，审查通过后合并
# 合并后立即创建版本标签

# 5. 创建版本标签
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 6. 合并回 develop
git checkout develop
git pull origin develop
git merge main
git push origin develop

# 7. 删除发布分支
git push origin --delete release/v1.1.0
```

### 场景 3: 紧急修复生产 bug

```bash
# 1. 从 main 的特定版本创建 hotfix 分支
git checkout main
git pull origin main
git checkout -b hotfix/v1.0.1 v1.0.0

# 2. 修复 bug
git add .
git commit -m "fix: critical bug in production"

# 3. 推送并创建 PR 到 main
git push origin hotfix/v1.0.1

# 4. PR 审查通过后合并到 main
# 合并后创建新的补丁版本标签

# 5. 创建版本标签
git checkout main
git pull origin main
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin v1.0.1

# 6. 合并回 develop
git checkout develop
git pull origin develop
git merge main
git push origin develop

# 7. 删除 hotfix 分支
git push origin --delete hotfix/v1.0.1
```

### 场景 4: 多版本并行维护

```bash
# 维护 v1.x 版本线
git checkout -b maintain/v1.x v1.5.0
git push origin maintain/v1.x

# 维护 v2.x 版本线
git checkout -b maintain/v2.x v2.0.0
git push origin maintain/v2.x

# 在各版本线上创建 bugfix 分支
git checkout maintain/v1.x
git checkout -b bugfix/v1-critical-issue
# 修复后合并回 maintain/v1.x，创建 v1.x.x 标签
```

---

## 标签管理

### 标签命名规范

```bash
# 发布版本标签
v1.0.0          # 正式版本
v1.0.0-alpha.1  # Alpha 版本
v1.0.0-beta.1   # Beta 版本
v1.0.0-rc.1     # Release Candidate

# 查看所有标签
git tag -l

# 查看特定版本的标签
git tag -l "v1.*"

# 查看标签详情
git show v1.0.0
```

### 标签操作

```bash
# 创建带注解的标签（推荐）
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0

# 推送所有标签
git push origin --tags

# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin --delete v1.0.0

# 检出特定版本
git checkout v1.0.0
```

---

## 历史版本回滚

### 回滚到特定版本

```bash
# 方式 1: 创建新分支回到特定版本
git checkout -b rollback-branch v1.0.0

# 方式 2: 重置当前分支到特定版本（谨慎使用）
git reset --hard v1.0.0

# 方式 3: 创建回滚提交（推荐用于已发布版本）
git revert v1.0.0..HEAD  # 回滚 v1.0.0 之后的所有提交

# 方式 4: 查看特定版本的代码
git show v1.0.0:path/to/file
```

### 查看版本历史

```bash
# 查看所有版本标签及其提交
git log --oneline --decorate --all

# 查看特定版本之间的差异
git diff v1.0.0 v1.1.0

# 查看特定版本的提交日志
git log v1.0.0..v1.1.0

# 查看某个文件的版本历史
git log --oneline path/to/file
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Version Management

on:
  push:
    branches: [main, develop]
    tags: ['v*']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate version format
        run: |
          VERSION=$(git describe --tags --always)
          echo "Current version: $VERSION"
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
```

---

## 最佳实践

### ✅ 推荐做法

1. **提交信息规范** (Conventional Commits)
   ```
   feat: add new feature
   fix: resolve bug
   docs: update documentation
   style: format code
   refactor: restructure code
   test: add tests
   chore: update dependencies
   ```

2. **定期同步分支**
   ```bash
   git fetch origin
   git rebase origin/develop
   ```

3. **使用 .gitignore** 排除不必要的文件
   ```
   node_modules/
   .env
   .DS_Store
   __pycache__/
   *.pyc
   ```

4. **保持提交历史清晰**
   - 在合并前进行 rebase 或 squash
   - 避免过多的 merge commit

5. **定期备份重要版本**
   ```bash
   git push origin --tags
   ```

### ❌ 避免做法

1. 直接推送到 `main` 或 `develop`
2. 使用 `git push --force` 到共享分支
3. 在发布分支上进行大量开发
4. 忘记更新版本号和 CHANGELOG
5. 创建过多的长期分支

---

## 版本维护时间表

| 版本 | 发布日期 | 维护期 | 状态 |
|------|---------|--------|------|
| v1.0.x | 2026-03-15 | 6 个月 | 活跃 |
| v1.1.x | 2026-04-15 | 6 个月 | 计划中 |
| v2.0.x | 2026-06-15 | 12 个月 | 计划中 |

---

## 常见问题

### Q: 如何从旧版本创建新的维护分支？
```bash
git checkout -b maintain/v1.x v1.5.0
git push origin maintain/v1.x
```

### Q: 如何查看某个版本包含了哪些功能？
```bash
git log v1.0.0..v1.1.0 --oneline
```

### Q: 如何撤销已推送的提交？
```bash
# 创建回滚提交（推荐）
git revert <commit-hash>
git push origin develop

# 或重置（仅限未发布分支）
git reset --hard <commit-hash>
git push origin develop --force
```

### Q: 如何处理版本冲突？
```bash
# 查看冲突
git status

# 手动解决冲突后
git add .
git commit -m "resolve merge conflict"
git push origin <branch>
```

---

## 初始化项目

```bash
# 初始化 Git 仓库
git init

# 创建初始提交
git add .
git commit -m "chore: initial commit"

# 创建 main 分支
git branch -M main

# 创建 develop 分支
git checkout -b develop

# 推送到远程
git remote add origin <repository-url>
git push -u origin main
git push -u origin develop

# 创建初始版本标签
git tag -a v0.1.0 -m "Initial version"
git push origin v0.1.0
```

---

## 参考资源

- [Git Flow 详解](https://nvie.com/posts/a-successful-git-branching-model/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
