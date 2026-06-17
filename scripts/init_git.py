"""
Git 初始化和提交脚本。
准备部署到 Streamlit Cloud。
"""
import subprocess
from pathlib import Path

ROOT = Path("D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

def run(cmd, cwd=None, check=True):
    print(f"$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or ROOT,
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr and "warning" not in result.stderr.lower():
        print(f"[stderr] {result.stderr}")
    if check and result.returncode != 0:
        print(f"[error] exit {result.returncode}")
        return False
    return True

# 1. 初始化
run("git init -b main")
run('git config user.name "nengyong.wu"')
run('git config user.email "nengyong.wu@users.noreply.github.com"')

# 2. 添加文件
run("git add .")

# 3. 状态
run("git status --short")

# 4. 提交
run('git commit -m "feat: 2026 浙江高考志愿模拟填报系统 v1.0.0"')

# 5. 显示
run("git log --oneline -5")
print("\n✓ Git 初始化完成！")
print("下一步：")
print("1. 在 GitHub 创建新仓库（建议名：zjgk-volunteer）")
print("2. git remote add origin https://github.com/你的用户名/zjgk-volunteer.git")
print("3. git push -u origin main")
print("4. 访问 https://share.streamlit.io 部署")
