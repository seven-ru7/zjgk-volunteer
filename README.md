# 2026 浙江省高考志愿模拟填报系统

> 基于位次匹配的「冲稳保」志愿推荐系统，**仅 985 + 211 院校**，**仅普通类一段（80 个平行志愿）**。

## ✨ 功能

- **院校范围**：118 所 985+211 院校（覆盖全部 39 所 985 + 79 所 211）
- **专业库**：~670 个代表性专业（理工/医学/文法/商/农林/师范）
- **核心算法**：位次差 → 概率分档（保 95% / 稳 75% / 冲 45% / 冲 10%）
- **冲稳保分配**：默认 30/50/20，可自定义
- **选科筛选**：严格按 3 门选考科目匹配
- **偏好过滤**：城市 / 专业关键词
- **一键爬取**：从 zjzs.net 自动拉取最新数据；失败时回退到手动下载
- **导出**：Excel / CSV / 在线下载

## 🚀 快速开始

### 方式 1：Windows 一键启动（推荐）

1. 解压下载的 zip
2. 双击 `start.bat`
3. 等待 1-2 分钟（首次安装依赖）
4. 浏览器自动打开 http://localhost:8501

### 方式 2：macOS / Linux

```bash
chmod +x start.sh
./start.sh
```

### 方式 3：手动启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

然后浏览器访问 http://localhost:8501

### 跑测试

```bash
python -m pytest tests/ -v
```

当前：**101 个测试全部通过** ✅

## 📖 使用流程

1. **输入分数**：在左侧输入高考总分（如 595），系统自动反查全省位次
2. **选考科目**：选择 3 门选考（如 物理+化学+生物）
3. **偏好（可选）**：筛选城市（如 杭州/上海/北京）、专业关键词（如 计算机,人工智能,临床医学）
4. **调整冲稳保比例**：默认 30/50/20，可改为 20/60/20 等
5. **点击「🎲 生成志愿表」**：查看 80 个志愿推荐
6. **导出**：点击 Excel / CSV 按钮下载到本地

## 🕷️ 数据更新（爬虫）

### 自动抓取

侧边栏 → 「🕷️ 数据更新」 → 选择目标年份 → 点击按钮

| 数据 | 抓取源 | 备注 |
|---|---|---|
| 一分一段表 | zjzs.net 招考资讯 HTML | URL 每年可能变化 |
| 投档数据 | zjzs.net PDF 附件 | 已配置 2024 年 PDF URL |

### 手动导入（自动抓取失败时）

1. 访问 [浙江省教育考试院](https://www.zjzs.net/zjgj/ksfw/)
2. 下载数据（一分一段表 或 投档 PDF）
3. 处理后放入 `data/` 目录：
   - 一分一段表 → `data/score_rank_<year>.json`（格式：`{"750": 200, "700": 2000, ...}`）
   - 投档数据 → 调用 `AdmissionPdfCrawler().parse_local("data/xxx.pdf")` 解析
4. 重新加载页面

## 📁 项目结构

```
zjgk-volunteer/
├── data/                          # 数据目录
│   ├── institutions.json          # 118 所 985+211 院校
│   ├── programs.json              # 670 个专业（含 3 年历史）
│   ├── score_rank_2023.json       # 2023 一分一段表
│   ├── score_rank_2024.json       # 2024 一分一段表
│   ├── score_rank_2025.json       # 2025 一分一段表
│   └── admission_history.json     # 历年录取数据
├── src/
│   ├── models.py                  # 数据模型
│   ├── data_loader.py             # JSON 加载
│   ├── rank_lookup.py             # 分数↔位次
│   ├── matcher.py                 # 选科匹配
│   ├── probability.py             # 概率估算
│   ├── recommender.py             # 冲稳保分配
│   ├── exporter.py                # Excel/CSV 导出
│   └── crawlers/                  # 在线数据爬取
│       ├── base.py                # 爬虫基类（UA/重试/日志）
│       ├── score_rank.py          # 一分一段表爬取
│       └── admission_pdf.py       # PDF 解析
├── scripts/                       # 数据生成器
│   ├── gen_institutions.py        # 生成院校名单
│   ├── gen_programs.py            # 生成专业库
│   ├── gen_score_rank.py          # 生成一分一段表
│   └── gen_admission.py           # 生成历史录取
├── tests/                         # pytest 测试（89 个）
├── app.py                         # Streamlit 入口
├── requirements.txt
└── README.md
```

## 📊 数据来源声明

- **院校名单**：教育部官方 985/211 名单（截至 2025 年）
- **一分一段表**：基于 2025 浙江真实分布特征建模（演示用）
- **录取历史**：基于 118 所院校档次 + 专业热度算法生成（演示用）
- **2026 真实数据**：发布后可通过爬虫自动更新

> ⚠ 本系统的初始数据为**演示数据**，与浙江省教育考试院真实数据可能存在偏差。**最终志愿请以官方公告为准**。

## 🔧 核心算法说明

### 概率分档（基于 2025 历史最低投档位次）

```
delta = 考生位次 - 专业 2025 最低投档位次

delta < -8000       → 保 档（95%）
-8000 ≤ delta < 2000 → 稳 档（75%）
2000 ≤ delta < 10000 → 冲 档（45%）
delta ≥ 10000       → 冲 档（10%）
```

正 delta 表示考生位次靠后（更难录取）。

### 冲稳保分配

默认比例 **30/50/20**（依据招办主任建议）：
- 冲 30%：考生有希望冲一冲
- 稳 50%：考生有较大把握
- 保 20%：确保不滑档

可在 UI 中实时调整（左侧滑块）。

## 🛠 故障排查

| 问题 | 解决方案 |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | 重新 `pip install -r requirements.txt` |
| `FileNotFoundError: 缺少年份数据 2025` | 跑 `python scripts/gen_score_rank.py` 或用爬虫拉取 |
| 爬虫一直失败 | 检查网络；切换到手动导入 |
| Streamlit 启动后看不到数据 | 检查 `data/` 目录下 JSON 文件是否完整 |
| Excel 导出失败 | `pip install openpyxl --upgrade` |

## 📝 注意事项

1. **本系统仅供参考**，不能替代浙江省教育考试院的官方志愿填报系统
2. **2026 年招生计划**通常在 6 月中旬发布，发布后通过爬虫可自动更新
3. **同分撞车风险**：2025 年一段线内同分考生最多 127 人/分，志愿顺序需谨慎
4. **位次比分数重要**：每年高考试题难度不同，绝对分数参考价值有限

## 📜 免责声明

本工具仅用于学习和技术演示目的。所有数据（包括院校名单、专业信息、历史录取、一分一段表）的**最终权威来源为浙江省教育考试院**（https://www.zjzs.net）。因使用本工具产生的任何填报决策风险由用户自行承担。

---

## 📦 分发给其他人

### 方式 A：发送项目压缩包（适合 5-50 人本地使用）

**打包（你的机器）**：
```cmd
package.bat
```
生成 `zjgk-volunteer-v1.0.0.zip`（约 500KB-1MB）。

**接收方使用**：
1. 解压 zip
2. 双击 `start.bat`（Windows）/ `./start.sh`（macOS/Linux）
3. 自动安装 Python 依赖、启动服务
4. 浏览器打开 http://localhost:8501

**接收方要求**：Windows 10+/macOS/Linux + Python 3.10+（脚本会自动检测）

### 方式 B：局域网共享（适合家庭/同办公室）

1. 在你的电脑上运行 `start.bat`
2. 查看你的局域网 IP（如 `192.168.1.100`）：
   ```cmd
   ipconfig
   ```
3. 其他设备浏览器访问：`http://192.168.1.100:8501`
4. **注意**：关闭 Windows 防火墙或允许 8501 端口入站

### 方式 C：部署到云端（适合大规模 / 远程访问）

#### C1. Streamlit Cloud（免费，最简单）
1. 把项目 push 到 GitHub
2. 访问 https://share.streamlit.io 连接 GitHub
3. 选择 `app.py` 一键部署
4. ⚠ 中国大陆访问较慢

#### C2. 阿里云 / 腾讯云（国内访问快）
1. 买云服务器（2核4G 约 100 元/月）
2. 装 Python 3.11 + git
3. 克隆项目 → 启动 `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
4. 安全组开放 8501 端口
5. 用 Nginx 反向代理 + 域名（可选）

#### C3. Docker（环境一致）
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t zjgk-volunteer .
docker run -p 8501:8501 zjgk-volunteer
```

### 方式 D：打包成可执行文件（适合非技术用户）

**PyInstaller 打包 .exe**：
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "data;data" --add-data "src;src" app.py
```
生成 `dist/app.exe`，双击运行。

⚠ **限制**：
- 体积大（200-300MB）
- 启动慢（首次解压）
- Windows 杀软可能误报
- 跨平台需分别打包

### 各方式对比

| 方式 | 适合场景 | 难度 | 维护 |
|---|---|---|---|
| A. 压缩包 | 5-50 人本地用 | ⭐ | 各自维护 |
| B. 局域网 | 家庭/同办公室 | ⭐ | 1 台机器常开 |
| C1. Streamlit Cloud | 海外/爱好 | ⭐ | 零运维 |
| C2. 国内云 | 大规模/正式 | ⭐⭐⭐ | 需要运维 |
| C3. Docker | 技术团队 | ⭐⭐ | 简单 |
| D. .exe | 非技术用户 | ⭐⭐ | 各自维护 |

---

## 📄 License

MIT
