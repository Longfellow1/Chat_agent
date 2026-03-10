# 多版本并行开发指南

## 场景概述

你的项目需要在下周晚些时候产出多个版本，同时需要：
- ✅ 稳定版本可储存
- ✅ 历史版本可回滚
- ✅ 多版本共同推进

本指南提供具体的实施方案。

---

## 架构设计

### 版本线规划

假设当前状态和计划：

```
时间线:
├─ 现在 (2026-03-10)
│  └─ v1.0.0 (生产稳定版)
│
├─ 下周 (2026-03-17)
│  ├─ v1.1.0 (稳定版 - 小功能更新)
│  ├─ v2.0.0-beta (测试版 - 大功能)
│  └─ v1.0.1 (补丁版 - 紧急修复)
│
└─ 后续
   ├─ v1.1.1 (v1.x 维护线)
   ├─ v2.0.0 (v2.x 主线)
   └─ v3.0.0-alpha (v3.x 探索线)
```

### 分支结构

```
main (生产稳定版)
├─ v1.0.0 (当前生产版)
├─ v1.0.1 (紧急修复)
├─ v1.1.0 (下周发布)
└─ v2.0.0 (未来发布)

develop (开发集成版)
├─ feature/v1.1-feature-a
├─ feature/v2.0-feature-b
└─ feature/v2.0-feature-c

maintain/v1.x (v1.x 维护线)
├─ bugfix/v1-critical-issue
└─ v1.0.1, v1.1.0, v1.1.1 标签

maintain/v2.x (v2.x 维护线)
└─ feature/v2-new-feature

release/v1.1.0 (发布准备)
release/v2.0.0-beta (测试版准备)
```

---

## 实施步骤

### 第 1 步: 初始化版本管理

```bash
# 1. 运行初始化脚本
bash init_git_versioning.sh

# 2. 配置远程仓库
git remote add origin https://github.com/your-org/your-repo.git

# 3. 推送初始分支和标签
git push -u origin main
git push -u origin develop
git push origin --tags
```

### 第 2 步: 设置分支保护规则

在 GitHub/GitLab 中配置：

**main 分支保护:**
- ✅ 需要 PR 审查（至少 1 人）
- ✅ 需要 CI 通过
- ✅ 禁止直接推送
- ✅ 禁止强制推送

**develop 分支保护:**
- ✅ 需要 CI 通过
- ✅ 禁止直接推送
- ✅ 禁止强制推送

### 第 3 步: 创建多版本维护线

```bash
# 创建 v1.x 维护线（维护现有 v1.0.0）
git checkout -b maintain/v1.x v1.0.0
git push -u origin maintain/v1.x

# 创建 v2.x 维护线（为 v2.0.0 做准备）
git checkout develop
git checkout -b maintain/v2.x
git push -u origin maintain/v2.x
```

### 第 4 步: 并行开发多个版本

#### 场景 A: 在 v1.x 上修复紧急 bug（v1.0.1）

```bash
# 1. 从 v1.x 维护线创建 bugfix 分支
git checkout maintain/v1.x
git pull origin maintain/v1.x
git checkout -b bugfix/v1-critical-issue

# 2. 修复 bug
# 编辑文件...
git add .
git commit -m "fix: critical issue in v1.0.x"

# 3. 推送并创建 PR
git push origin bugfix/v1-critical-issue
# 在 GitHub 创建 PR 到 maintain/v1.x

# 4. PR 审查通过后合并
# 合并后在 maintain/v1.x 上创建新版本标签

git checkout maintain/v1.x
git pull origin maintain/v1.x
git tag -a v1.0.1 -m "Patch version 1.0.1 - critical fix"
git push origin v1.0.1

# 5. 同步回 develop
git checkout develop
git pull origin develop
git merge maintain/v1.x
git push origin develop
```

#### 场景 B: 在 develop 上开发 v1.1.0 新功能

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/v1.1-new-feature

# 2. 开发新功能
# 编辑文件...
git add .
git commit -m "feat: add new feature for v1.1"

# 3. 推送并创建 PR
git push origin feature/v1.1-new-feature
# 在 GitHub 创建 PR 到 develop

# 4. PR 审查通过后合并
# 合并后继续开发其他功能或准备发布
```

#### 场景 C: 在 maintain/v2.x 上开发 v2.0.0 新功能

```bash
# 1. 从 maintain/v2.x 创建功能分支
git checkout maintain/v2.x
git pull origin maintain/v2.x
git checkout -b feature/v2.0-major-feature

# 2. 开发新功能（可能是大的重构）
# 编辑文件...
git add .
git commit -m "feat: major feature for v2.0"

# 3. 推送并创建 PR
git push origin feature/v2.0-major-feature
# 在 GitHub 创建 PR 到 maintain/v2.x

# 4. PR 审查通过后合并
# 合并后继续开发或准备 beta 版本
```

### 第 5 步: 发布 v1.1.0 稳定版

```bash
# 1. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# 2. 更新版本号和 CHANGELOG
# 编辑 package.json: "version": "1.1.0"
# 编辑 CHANGELOG.md:
#   ## [1.1.0] - 2026-03-17
#   ### Added
#   - New feature A
#   - New feature B

git add .
git commit -m "chore: bump version to v1.1.0"

# 3. 推送发布分支
git push origin release/v1.1.0

# 4. 创建 PR 到 main，审查通过后合并
# 在 GitHub 创建 PR: release/v1.1.0 → main

# 5. 合并后创建版本标签
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 6. 合并回 develop
git checkout develop
git pull origin develop
git merge main
git push origin develop

# 7. 同步到 v1.x 维护线
git checkout maintain/v1.x
git pull origin maintain/v1.x
git merge main
git push origin maintain/v1.x

# 8. 删除发布分支
git push origin --delete release/v1.1.0
```

### 第 6 步: 发布 v2.0.0-beta 测试版

```bash
# 1. 从 maintain/v2.x 创建发布分支
git checkout maintain/v2.x
git pull origin maintain/v2.x
git checkout -b release/v2.0.0-beta

# 2. 更新版本号和 CHANGELOG
# 编辑 package.json: "version": "2.0.0-beta.1"
# 编辑 CHANGELOG.md:
#   ## [2.0.0-beta.1] - 2026-03-17
#   ### Added
#   - Major feature X
#   - Major feature Y

git add .
git commit -m "chore: bump version to v2.0.0-beta.1"

# 3. 推送发布分支
git push origin release/v2.0.0-beta

# 4. 创建 PR 到 main（标记为 beta）
# 在 GitHub 创建 PR: release/v2.0.0-beta → main
# PR 标题: "[BETA] Release v2.0.0-beta.1"

# 5. 合并后创建 beta 版本标签
git checkout main
git pull origin main
git tag -a v2.0.0-beta.1 -m "Beta version 2.0.0-beta.1"
git push origin v2.0.0-beta.1

# 6. 删除发布分支
git push origin --delete release/v2.0.0-beta
```

---

## 版本状态追踪

### 创建版本状态文件

```bash
# 创建 VERSION_STATUS.md
cat > VERSION_STATUS.md << 'EOF'
# 版本状态追踪

## 当前版本

| 版本 | 分支 | 状态 | 发布日期 | 维护期 |
|------|------|------|---------|--------|
| v1.0.0 | main | 生产稳定 | 2026-03-10 | 6 个月 |
| v1.0.1 | maintain/v1.x | 补丁版 | 2026-03-17 | 6 个月 |
| v1.1.0 | main | 稳定版 | 2026-03-17 | 6 个月 |
| v2.0.0-beta.1 | main | 测试版 | 2026-03-17 | - |
| v2.0.0 | maintain/v2.x | 开发中 | 计划中 | 12 个月 |

## 分支状态

| 分支 | 用途 | 最后更新 | 状态 |
|------|------|---------|------|
| main | 生产稳定版 | 2026-03-17 | 活跃 |
| develop | 开发集成版 | 2026-03-17 | 活跃 |
| maintain/v1.x | v1.x 维护线 | 2026-03-17 | 活跃 |
| maintain/v2.x | v2.x 开发线 | 2026-03-17 | 活跃 |

## 进行中的功能

- feature/v1.1-new-feature (PR #1)
- feature/v2.0-major-feature (PR #2)
- bugfix/v1-critical-issue (PR #3)

## 计划发布

- v1.1.1 (2026-03-24)
- v2.0.0-beta.2 (2026-03-31)
- v2.0.0 (2026-04-14)
EOF
```

---

## 版本回滚方案

### 场景 1: 回滚 v1.1.0 到 v1.0.0

```bash
# 方式 1: 创建回滚分支
git checkout -b rollback-to-v1.0.0 v1.0.0
git push origin rollback-to-v1.0.0

# 方式 2: 创建回滚提交（推荐用于已发布版本）
git checkout main
git pull origin main
git revert v1.0.0..v1.1.0
git push origin main

# 方式 3: 重置到特定版本（仅限未发布分支）
git reset --hard v1.0.0
git push origin main --force
```

### 场景 2: 从 v2.0.0-beta 回滚到 v1.1.0

```bash
# 1. 查看版本历史
git log --oneline --all --graph

# 2. 创建回滚分支
git checkout -b rollback-to-v1.1.0 v1.1.0

# 3. 推送并创建 PR
git push origin rollback-to-v1.1.0
# 创建 PR 到 main

# 4. 审查通过后合并
```

### 场景 3: 恢复误删的版本

```bash
# 1. 查看 reflog
git reflog

# 2. 找到要恢复的提交
git show <commit-hash>

# 3. 创建恢复分支
git checkout -b recover-version <commit-hash>

# 4. 创建新的版本标签
git tag -a v1.0.2-recovered -m "Recovered version"
git push origin v1.0.2-recovered
```

---

## 历史版本查询

### 查看所有版本

```bash
# 查看所有版本标签
git tag -l

# 查看版本详情
git show v1.1.0

# 查看版本之间的差异
git diff v1.0.0 v1.1.0

# 查看版本的提交日志
git log v1.0.0..v1.1.0 --oneline
```

### 查看特定版本的代码

```bash
# 查看特定版本的文件
git show v1.1.0:path/to/file

# 检出特定版本
git checkout v1.1.0

# 从特定版本创建分支
git checkout -b hotfix-v1.1.0 v1.1.0
```

---

## 自动化脚本

### 版本发布脚本

```bash
#!/bin/bash
# release.sh - 自动化版本发布

VERSION=$1
BRANCH=${2:-develop}

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version> [branch]"
    exit 1
fi

echo "准备发布版本: $VERSION"

# 1. 创建发布分支
git checkout $BRANCH
git pull origin $BRANCH
git checkout -b release/$VERSION

# 2. 更新版本号
sed -i "" "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json

# 3. 提交
git add .
git commit -m "chore: bump version to $VERSION"
git push origin release/$VERSION

echo "✓ 发布分支已创建: release/$VERSION"
echo "✓ 请创建 PR 到 main 分支"
```

### 版本回滚脚本

```bash
#!/bin/bash
# rollback.sh - 自动化版本回滚

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./rollback.sh <version>"
    exit 1
fi

echo "准备回滚到版本: $VERSION"

git checkout main
git pull origin main
git revert $VERSION..HEAD
git push origin main

echo "✓ 已创建回滚提交"
```

---

## 监控与维护

### 定期检查

```bash
# 检查分支状态
git branch -a

# 检查标签状态
git tag -l

# 检查远程状态
git remote -v

# 检查未合并的分支
git branch --no-merged main
```

### 清理过期分支

```bash
# 删除本地已合并的分支
git branch -d feature/old-feature

# 删除远程已合并的分支
git push origin --delete feature/old-feature

# 清理本地已删除的远程分支
git fetch origin --prune
```

---

## 常见问题

### Q: 如何同时维护多个版本线？
A: 使用 `maintain/v*.x` 分支，每条线独立维护，定期同步回 develop。

### Q: 如何处理版本冲突？
A: 在合并前进行 rebase，解决冲突后再合并。

### Q: 如何快速查看某个版本的功能？
A: 使用 `git log v1.0.0..v1.1.0 --oneline` 查看版本间的提交。

### Q: 如何从旧版本创建新的维护线？
A: 使用 `git checkout -b maintain/v*.x <tag>` 从特定版本标签创建。

### Q: 如何处理紧急修复？
A: 从 main 的特定版本创建 hotfix 分支，修复后合并回 main 和 develop。

---

## 参考资源

- 详细策略: `.kiro/GIT_VERSIONING_STRATEGY.md`
- 设置检查清单: `.kiro/GIT_SETUP_CHECKLIST.md`
- 初始化脚本: `init_git_versioning.sh`
- 版本状态: `VERSION_STATUS.md`
