@echo off
chcp 65001 > nul
setlocal

REM ============================================
REM  2026 浙江省高考志愿模拟填报系统 一键启动
REM  Windows 启动脚本
REM ============================================

echo.
echo ================================================
echo   2026 浙江省高考志愿模拟填报系统
echo ================================================
echo.

REM 检查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo        下载: https://www.python.org/downloads/
    echo        安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 检查 Python... OK
python --version

REM 创建虚拟环境（如果不存在）
if not exist ".venv" (
    echo.
    echo [2/3] 创建虚拟环境（首次运行）...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
) else (
    echo [2/3] 虚拟环境已存在，跳过
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 安装/更新依赖
echo.
echo [3/3] 安装依赖（首次约 1-2 分钟）...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

REM 启动 Streamlit
echo.
echo ================================================
echo   启动 Web 服务...
echo   浏览器会自动打开: http://localhost:8501
echo   关闭服务: 在此窗口按 Ctrl+C
echo ================================================
echo.

streamlit run app.py --server.headless false

pause
