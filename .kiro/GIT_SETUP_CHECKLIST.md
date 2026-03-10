# Git 版本管理实施检查清单

## 仓库初始化

- [ ] 确认 Git 仓库已初始化
- [ ] 配置 Git 用户信息
  ```bash
  git config user.name "Your Name"
  git config user.email "your.email@example.com"
  ```
- [ ] 创建 `.gitignore` 文件
- [ ] 创建初始 `README.md`

## 分支设置

- [ ] 创建 `main` 分支（生产稳定版）
- [ ] 创建 `develop` 分支（开发集成版）
- [ ] 配置分支保护规则
  - [ ] `main` 分支：禁止直接推送，需要 PR 审查
  - [ ] `develop` 分支：禁止直接推送，需要 CI 通过

## 版本标签

- [ ] 创建初始版本标签 `v0.1.0`
- [ ] 推送所有标签到远程
  ```bash
  git push origin --tags
  ```

## 文档准备

- [ ] 创建 `CHANGELOG.md` 文件
  ```markdown
  # Changelog

  ## [Unreleased]

  ## [0.1.0] - 2026-03-10
  - Initial release
  ```

- [ ] 创建 `VERSION` 文件（可选）
  ```
  0.1.0
  ```

- [ ] 更新 `package.json` 或 `setup.py` 中的版本号

## CI/CD 配置

- [ ] 创建 `.github/workflows/ci.yml` 或等效的 CI 配置
- [ ] 配置自动化测试
- [ ] 配置自动化构建
- [ ] 配置版本验证

## 团队协作

- [ ] 制定 PR 审查规则
- [ ] 制定提交信息规范
- [ ] 制定代码审查标准
- [ ] 建立发布流程文档

## 备份与恢复

- [ ] 配置远程备份
- [ ] 测试版本回滚流程
- [ ] 文档化灾难恢复步骤

## 监控与维护

- [ ] 设置版本发布通知
- [ ] 建立版本维护计划
- [ ] 定期审查分支策略

---

## 快速开始命令

```bash
# 1. 初始化仓库
git init
git add .
git commit -m "chore: initial commit"

# 2. 创建 develop 分支
git checkout -b develop
git push -u origin develop

# 3. 创建初始版本标签
git tag -a v0.1.0 -m "Initial version"
git push origin v0.1.0

# 4. 验证分支和标签
git branch -a
git tag -l
```

---

## 多版本并行开发示例

### 当前状态
- `main`: v1.0.0 (生产稳定版)
- `develop`: v1.1.0-dev (下一个版本开发中)

### 需要同时维护 v1.x 和开发 v2.0

```bash
# 1. 创建 v1.x 维护分支
git checkout -b maintain/v1.x v1.0.0
git push origin maintain/v1.x

# 2. 在 v1.x 上修复 bug
git checkout maintain/v1.x
git checkout -b bugfix/v1-critical-issue
# ... 修复代码 ...
git commit -m "fix: critical issue in v1.x"
git push origin bugfix/v1-critical-issue
# 创建 PR 到 maintain/v1.x

# 3. 合并后创建新的补丁版本
git checkout maintain/v1.x
git pull origin maintain/v1.x
git tag -a v1.0.1 -m "Patch version 1.0.1"
git push origin v1.0.1

# 4. 同时在 develop 上开发 v2.0
git checkout develop
git checkout -b feature/v2-new-feature
# ... 开发新功能 ...
git commit -m "feat: new feature for v2.0"
git push origin feature/v2-new-feature
# 创建 PR 到 develop
```

---

## 版本发布流程

### 发布 v1.1.0

```bash
# 1. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# 2. 更新版本号
# 编辑 package.json: "version": "1.1.0"
# 编辑 CHANGELOG.md

git add .
git commit -m "chore: bump version to v1.1.0"
git push origin release/v1.1.0

# 3. 创建 PR 到 main，审查通过后合并

# 4. 创建版本标签
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 5. 合并回 develop
git checkout develop
git pull origin develop
git merge main
git push origin develop

# 6. 删除发布分支
git push origin --delete release/v1.1.0
```

---

## 故障排查

### 问题：分支落后于主分支

```bash
git fetch origin
git rebase origin/develop
# 或
git merge origin/develop
```

### 问题：需要回滚到特定版本

```bash
# 查看版本历史
git log --oneline --all

# 创建回滚分支
git checkout -b rollback-v1.0.0 v1.0.0

# 或创建回滚提交
git revert v1.0.0..HEAD
```

### 问题：误删分支恢复

```bash
# 查看最近的操作
git reflog

# 恢复分支
git checkout -b recovered-branch <commit-hash>
```

---

## 相关文件

- 详细策略: `.kiro/GIT_VERSIONING_STRATEGY.md`
- CI/CD 配置: `.github/workflows/ci.yml`
- 版本历史: `CHANGELOG.md`
- 项目版本: `package.json` 或 `setup.py`
