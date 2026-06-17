#!/bin/bash
# 2026 浙江省高考志愿模拟填报系统 一键启动（macOS / Linux）

set -e

echo ""
echo "================================================"
echo "  2026 浙江省高考志愿模拟填报系统"
echo "================================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 python3，请先安装 Python 3.10+"
    echo "       macOS: brew install python3"
    echo "       Ubuntu: sudo apt install python3 python3-venv"
    exit 1
fi

echo "[1/3] 检查 Python... OK"
python3 --version

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo ""
    echo "[2/3] 创建虚拟环境（首次运行）..."
    python3 -m venv .venv
else
    echo "[2/3] 虚拟环境已存在"
fi

# 激活
source .venv/bin/activate

# 升级 pip + 安装依赖
echo ""
echo "[3/3] 安装依赖（首次约 1-2 分钟）..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 启动
echo ""
echo "================================================"
echo "  启动 Web 服务..."
echo "  浏览器访问: http://localhost:8501"
echo "  停止服务: 按 Ctrl+C"
echo "================================================"
echo ""

streamlit run app.py --server.headless false
