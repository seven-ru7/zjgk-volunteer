@echo off
chcp 65001 > nul
REM ============================================
REM  打包分发版本（生成 zip）
REM ============================================

set VERSION=v1.0.0
set NAME=zjgk-volunteer-%VERSION%
set OUT=%NAME%.zip

echo ================================================
echo   打包 %OUT%
echo ================================================
echo.

REM 用 Python 打包（避免 PowerShell 转义问题）
python -c "import zipfile, os; from pathlib import Path; include=['app.py','src','scripts','data/institutions.json','data/programs.json','data/admission_history.json','data/score_rank_2023.json','data/score_rank_2024.json','data/score_rank_2025.json','requirements.txt','start.bat','start.sh','README.md','Dockerfile','.gitignore','.dockerignore','tests']; out=Path('%OUT%'); out.parent.mkdir(parents=True, exist_ok=True); [z.write(f, f.relative_to(f.parent.parent if f.parent.name in ('src','scripts','tests') else f.parent)) or print(f'  + {f.name} ({f.stat().st_size:,} bytes)') for item in include for z in [zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9)] for f in (Path(item).iterdir() if Path(item).is_dir() else [Path(item)]) if f.is_file() and '__pycache__' not in str(f)]; kb=out.stat().st_size/1024; print(f'\n✓ 打包完成: {out} ({kb:.0f} KB)')"

echo.
echo 分发方式：
echo   1. 通过网盘 / 邮箱 / U 盘 / 微信发送这个 zip（246 KB）
echo   2. 接收方解压后双击 start.bat
echo.

pause
