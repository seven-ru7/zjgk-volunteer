"""
一键推送到 GitHub + 部署到 Streamlit Cloud 的引导脚本。

用法：
1. 在 GitHub 创建空仓库：https://github.com/new
   - 名称：zjgk-volunteer
   - 可见性：Public（Streamlit Cloud 免费版要求）
   - 不要勾选 Add README / .gitignore / license（用我们本地的）
2. 替换下面的 GITHUB_USERNAME 为你的 GitHub 用户名
3. 运行：python scripts/deploy.py
4. 推送成功后访问 https://share.streamlit.io 完成部署
"""
import subprocess
from pathlib import Path

ROOT = Path("D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

# ============================================
# ⚠️ 改成你的 GitHub 用户名！
# ============================================
GITHUB_USERNAME = "YOUR_GITHUB_USERNAME"
REPO_NAME = "zjgk-volunteer"
REMOTE_URL = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"


def run(cmd, cwd=None, check=True, show=True):
    if show:
        print(f"\n$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or ROOT,
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout and show:
        print(result.stdout)
    if result.stderr and "warning" not in result.stderr.lower() and show:
        print(f"[stderr] {result.stderr.strip()}")
    if check and result.returncode != 0:
        print(f"[ERROR] exit code {result.returncode}")
    return result


def main():
    if GITHUB_USERNAME == "YOUR_GITHUB_USERNAME":
        print("=" * 60)
        print("❌ 请先编辑 scripts/deploy.py")
        print(f"   把 GITHUB_USERNAME 改为你的 GitHub 用户名")
        print("=" * 60)
        return

    print("=" * 60)
    print(f"  部署 {REPO_NAME} 到 GitHub + Streamlit Cloud")
    print("=" * 60)
    print(f"GitHub: {REMOTE_URL}")

    # 1. 检查 remote
    result = run("git remote -v", show=False)
    if REMOTE_URL in result.stdout:
        print("✓ Remote 已存在")
    else:
        print("\n[1/3] 添加 remote...")
        run(f"git remote add origin {REMOTE_URL}")
        print("✓ Remote 已添加")

    # 2. 推送到 GitHub
    print("\n[2/3] 推送到 GitHub...")
    print("    (首次推送会要求输入 GitHub 凭据)")
    print("    推荐用 Personal Access Token (PAT)")
    result = run("git push -u origin main", check=False)

    if result.returncode == 0:
        print("\n✓ 推送成功！")
    else:
        if "could not read Username" in result.stderr or "Authentication failed" in result.stderr:
            print("\n❌ 认证失败。请按以下步骤：")
            print("1. 访问 https://github.com/settings/tokens")
            print("2. 生成 Token（勾选 repo 权限）")
            print("3. 用 token 替换 URL：")
            print(f"   https://YOUR_TOKEN@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git")
            print("\n或者配置 SSH key：")
            print("   ssh-keygen -t ed25519")
            print("   cat ~/.ssh/id_ed25519.pub  # 复制到 GitHub Settings > SSH keys")
            return
        else:
            print("\n❌ 推送失败，请检查上方错误信息")
            return

    # 3. 引导 Streamlit Cloud
    print("\n" + "=" * 60)
    print("  接下来：Streamlit Cloud 部署")
    print("=" * 60)
    print(f"""
1. 访问 https://share.streamlit.io/
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 填写：
   - Repository: {GITHUB_USERNAME}/{REPO_NAME}
   - Branch: main
   - Main file path: app.py
   - App URL: 自定义（如 zjgk-volunteer）
5. 点击 "Deploy!"
6. 等待 3-5 分钟构建
7. 完成后会得到：https://zjgk-volunteer.streamlit.app

部署后如果报错：
- 查看 logs（多半是依赖或路径问题）
- 我的 .python-version 已锁定 3.11
- requirements.txt 列了所有包
- 第一次部署失败时 logs 末尾会显示具体错误

✅ 部署完成后把 URL 分享给任何人即可访问！
""")


if __name__ == "__main__":
    main()
