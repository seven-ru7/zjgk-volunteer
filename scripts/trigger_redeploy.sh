#!/bin/bash
# 安全部署脚本：触发 Streamlit Cloud 重新部署
#
# 用法：
#   1. 编辑下方 GITHUB_USERNAME（如未填）
#   2. 把新 token 写到 .git-credentials 文件（不要 echo！）
#      echo "https://七-ru7:<TOKEN>@github.com" > .git-credentials
#      chmod 600 .git-credentials
#   3. 运行：bash scripts/trigger_redeploy.sh
#
# 或者用环境变量：
#   GITHUB_TOKEN=<新TOKEN> bash scripts/trigger_redeploy.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

GITHUB_USERNAME="${GITHUB_USERNAME:-seven-ru7}"
REPO_NAME="zjgk-volunteer"

echo "============================================="
echo "  Streamlit Cloud 重新部署触发器"
echo "============================================="
echo ""

# 1. 检查 token 来源
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✓ 使用环境变量 GITHUB_TOKEN"
elif [ -f .git-credentials ]; then
    echo "✓ 使用 .git-credentials 文件"
else
    echo "❌ 未找到 token"
    echo ""
    echo "请选择一种方式提供 token："
    echo ""
    echo "方式 A（推荐）：保存到文件"
    echo "  echo 'https://${GITHUB_USERNAME}:你的新TOKEN@github.com' > .git-credentials"
    echo "  chmod 600 .git-credentials"
    echo ""
    echo "方式 B：环境变量"
    echo "  export GITHUB_TOKEN=你的新TOKEN"
    echo "  bash scripts/trigger_redeploy.sh"
    exit 1
fi

# 2. 配置 remote（使用 token）
if [ -n "$GITHUB_TOKEN" ]; then
    REMOTE_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
else
    REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    # 让 git 用 credential helper
    git config --local credential.helper "store --file=.git-credentials"
fi

# 3. 检查 git 状态
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 不是 git 仓库"
    exit 1
fi

CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
echo ""
echo "当前 remote: $CURRENT_REMOTE"

# 4. 更新 remote URL（带 token）
if [ -n "$GITHUB_TOKEN" ]; then
    git remote set-url origin "$REMOTE_URL"
fi

# 5. 空 commit 触发 GitHub Actions / Streamlit Cloud 重新部署
echo ""
echo "创建空 commit 触发重新部署..."
git commit --allow-empty -m "chore: trigger Streamlit Cloud redeploy"

echo ""
echo "推送到 GitHub..."
git push origin main

# 6. 清理（避免 token 留在 git config）
if [ -n "$GITHUB_TOKEN" ]; then
    # 恢复无 token 的 URL
    CLEAN_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    git remote set-url origin "$CLEAN_URL"
    echo ""
    echo "✓ 已清理 git remote URL（移除 token）"
fi

echo ""
echo "============================================="
echo "  ✅ 推送成功！"
echo "  Streamlit Cloud 将在 1-3 分钟内自动重新部署"
echo "============================================="