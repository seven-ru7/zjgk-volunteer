"""
一键推送到 GitHub + 部署到 Streamlit Cloud 的引导脚本。

⚠️ 安全提示：token 不要在聊天中明文发送！
推荐做法：
1. 撤销旧 token（https://github.com/settings/tokens）
2. 生成新 token（PAT，勾选 repo）
3. 复制到本地文件（不发送）：
   echo "https://七-ru7:<TOKEN>@github.com" > .git-credentials
   chmod 600 .git-credentials
4. 运行本脚本

用法：
    python scripts/deploy.py
"""
import subprocess
from pathlib import Path

ROOT = Path("D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

# ============================================
GITHUB_USERNAME = "seven-ru7"
REPO_NAME = "zjgk-volunteer"


def run(cmd, cwd=None, check=True, show=True, env=None):
    if show:
        print(f"\n$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or ROOT,
        capture_output=True, text=True, encoding="utf-8",
        env=env
    )
    if result.stdout and show:
        print(result.stdout)
    if result.stderr and "warning" not in result.stderr.lower() and show:
        print(f"[stderr] {result.stderr.strip()}")
    if check and result.returncode != 0:
        print(f"[ERROR] exit code {result.returncode}")
    return result


def main():
    print("=" * 60)
    print(f"  部署 {REPO_NAME} 到 GitHub + Streamlit Cloud")
    print("=" * 60)

    import os
    token = os.environ.get("GITHUB_TOKEN")
    cred_file = ROOT / ".git-credentials"

    # 1. 检查 token
    if not token and not cred_file.exists():
        print("\n❌ 未找到 GITHUB_TOKEN")
        print("\n推荐做法（避免在聊天中泄露 token）：")
        print(f"  1. 在 GitHub 生成新 token：https://github.com/settings/tokens/new")
        print(f"     - Note: zjgk-deploy")
        print(f"     - 勾选 ✅ repo")
        print(f"  2. 把 token 保存到本地文件（不发给 AI 助手）：")
        print(f'     echo "https://{GITHUB_USERNAME}:<新TOKEN>@github.com" > "{cred_file}"')
        print(f'     chmod 600 "{cred_file}"')
        print(f"  3. 重跑本脚本")
        print(f"\n或者用环境变量：")
        print(f"     export GITHUB_TOKEN=新TOKEN值")
        print(f"     python scripts/deploy.py")
        return

    if token:
        print("\n✓ 使用环境变量 GITHUB_TOKEN（安全）")
        remote_url = f"https://{GITHUB_USERNAME}:{token}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    else:
        print("\n✓ 使用 .git-credentials 文件（安全）")
        remote_url = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
        run(f'git config --local credential.helper "store --file=.git-credentials"')

    # 2. 检查 remote
    result = run("git remote -v", show=False)
    if f"{GITHUB_USERNAME}/{REPO_NAME}" in result.stdout:
        print("✓ Remote 已存在")
    else:
        run(f"git remote add origin {remote_url}")

    # 3. 推送
    print("\n推送代码到 GitHub...")
    result = run("git push -u origin main", check=False)

    if result.returncode == 0:
        print("\n✓ 推送成功！")
    else:
        if "could not read Username" in result.stderr or "Authentication failed" in result.stderr:
            print("\n❌ 认证失败。请检查 token 是否有效。")
            return
        else:
            print("\n❌ 推送失败：", result.stderr)
            return

    # 4. 清理：恢复 remote URL（移除 token）
    if token:
        clean_url = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
        run(f"git remote set-url origin {clean_url}")
        print("\n✓ 已清理 remote URL（移除 token）")

    # 5. 引导
    print("\n" + "=" * 60)
    print("  接下来：Streamlit Cloud 部署")
    print("=" * 60)
    print(f"""
1. 访问 https://share.streamlit.io/{GITHUB_USERNAME}/{REPO_NAME}
2. 或手动 Reboot app（如果已部署）
3. 等待 1-3 分钟重新部署完成

部署后访问：
  https://{REPO_NAME}-<hash>.streamlit.app
""")


if __name__ == "__main__":
    main()
