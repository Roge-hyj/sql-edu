# 上传到 GitHub 指南

本文说明如何将本项目安全地上传到 GitHub，并避免泄露敏感信息。

---

## 一、上传前检查（敏感信息）

已完成的清理工作：

- 已移除 `config.py` 中的硬编码 JWT 密钥
- 已移除登录页调试时展示的 token 明文
- 已将 `sql-edu-backend/.env` 替换为占位符模板
- 已创建 `.env.example` 作为配置模板
- 已在根目录和 `sql-edu-backend` 中通过 `.gitignore` 忽略 `.env`

**本地运行前**：请复制 `sql-edu-backend/.env.example` 为 `sql-edu-backend/.env`，并填入真实配置（数据库、邮件、AI API 等）。

---

## 二、上传到 GitHub 的步骤

### 1. 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 右上角点击 **+** → **New repository**
3. 填写仓库名（如 `sql-edu`），选择 Public，点击 **Create repository**
4. 先不要勾选 “Add a README” 等初始化选项（本地已有代码）

### 2. 初始化本地 Git（如尚未初始化）

```bash
cd /mnt/d/web_project
git init
```

### 3. 检查是否曾提交过 .env

若项目之前已用 Git 管理过，先确认 `.env` 未被跟踪：

```bash
git status
git ls-files sql-edu-backend/.env
```

若 `git ls-files` 有输出，说明 `.env` 曾被提交，需从索引中移除：

```bash
git rm --cached sql-edu-backend/.env
```

这会取消跟踪 `.env`，但不会删除本地文件。

### 4. 添加文件并提交

```bash
git add .
git status   # 再次确认没有 .env 被加入
git commit -m "Initial commit: SQL 智能教学系统"
```

### 5. 关联远程仓库并推送

将 `YOUR_USERNAME` 和 `YOUR_REPO` 替换为你的 GitHub 用户名和仓库名：

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

如使用 SSH：

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 6. 首次推送时登录

- **HTTPS**：会提示输入 GitHub 用户名和密码（或 Personal Access Token）
- **SSH**：需已配置 SSH 公钥，一般无需再输入密码

---

## 三、常见问题

| 问题 | 处理方式 |
|------|----------|
| 推送时要求输入密码 | 建议使用 [Personal Access Token](https://github.com/settings/tokens) 或配置 SSH 密钥 |
| 提示 `Permission denied` | 检查 SSH 配置，或改用 HTTPS 并确保有仓库权限 |
| 误把 .env 提交到历史 | 使用 `git filter-branch` 或 [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) 清理历史后再强制推送 |
| 推送被拒绝 | 若远程已有提交，先执行 `git pull origin main --rebase`，解决冲突后再推送 |

---

## 四、克隆后本地运行

他人克隆仓库后：

1. 复制 `sql-edu-backend/.env.example` 为 `sql-edu-backend/.env`
2. 在 `.env` 中填写自己的数据库、邮件、AI API 等配置
3. 按 README 和 `04-从零到运行-环境与安装步骤.md` 完成环境搭建与运行
