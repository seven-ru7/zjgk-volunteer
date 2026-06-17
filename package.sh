#!/bin/bash
# 打包分发版本（生成 zip）
set -e

VERSION="v1.0.0"
NAME="zjgk-volunteer-${VERSION}"
OUT="${NAME}.zip"

echo "================================================"
echo "  打包 ${OUT}"
echo "================================================"
echo ""

python3 -c "
import zipfile
from pathlib import Path

include = [
    'app.py', 'src', 'scripts',
    'data/institutions.json', 'data/programs.json', 'data/admission_history.json',
    'data/score_rank_2023.json', 'data/score_rank_2024.json', 'data/score_rank_2025.json',
    'requirements.txt', 'start.bat', 'start.sh', 'README.md',
    'Dockerfile', '.gitignore', '.dockerignore', 'tests',
]

out = Path('${OUT}')
out.parent.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for item in include:
        p = Path(item)
        if p.is_file():
            z.write(p, p.name)
            print(f'  + {p.name} ({p.stat().st_size:,} bytes)')
        elif p.is_dir():
            for f in p.rglob('*'):
                if f.is_file() and '__pycache__' not in str(f):
                    if p.name in ('src', 'scripts', 'tests'):
                        arcname = f.relative_to(p.parent)
                    else:
                        arcname = f.relative_to(p)
                    z.write(f, arcname)
                    print(f'  + {arcname} ({f.stat().st_size:,} bytes)')

kb = out.stat().st_size / 1024
print(f'\n✓ 打包完成: {out} ({kb:.0f} KB)')
"

echo ""
echo "分发方式："
echo "  1. 通过网盘 / 邮箱 / U 盘 / 微信发送这个 zip（246 KB）"
echo "  2. 接收方解压后双击 start.bat（macOS/Linux 用 start.sh）"
