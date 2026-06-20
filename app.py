"""2026 浙江省高考志愿模拟填报系统（仅 985+211 院校）

运行：streamlit run app.py
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.crawlers.score_rank import ScoreRankCrawler
from src.crawlers.admission_pdf import AdmissionPdfCrawler
from src.data_loader import load_score_rank, load_programs
from src.exporter import (
    to_csv, to_dataframe, to_excel,
    to_excel_multi_sheet, get_institution_card_data,
)
from src.models import Candidate
from src.rank_lookup import score_to_rank
from src.recommender import recommend, summary


# ====== 页面配置 ======
st.set_page_config(
    page_title="2026 浙江高考志愿模拟（985+211）",
    page_icon="🎯",
    layout="wide",
)


# ====== 数据加载（缓存，依赖文件 mtime） ======
def _file_mtime(path: str) -> float:
    try:
        return Path(path).stat().st_mtime
    except FileNotFoundError:
        return 0.0


@st.cache_data
def _cached_programs(data_mtime: float):
    """缓存专业库，data_mtime 变化时自动失效。"""
    return load_programs()


@st.cache_data
def _cached_score_rank(data_mtime: float):
    """缓存一分一段表。"""
    return load_score_rank(2025)


def get_score_rank():
    return _cached_score_rank(_file_mtime("data/score_rank_2025.json"))


def get_programs():
    return _cached_programs(_file_mtime("data/programs.json"))


@st.cache_data
def _cached_institution_details(data_mtime: float):
    fp = Path("data/institution_details.json")
    if not fp.exists():
        return {}
    import json
    return json.loads(fp.read_text(encoding="utf-8"))


def get_institution_details():
    """加载学校详情（双一流学科 / 保研率 / 就业率等）。"""
    return _cached_institution_details(_file_mtime("data/institution_details.json"))


score_rank = get_score_rank()
all_programs = get_programs()

# ====== 页面标题 ======
st.title("🎯 2026 浙江省高考志愿模拟填报系统")
st.caption("院校范围：**985 + 211（共 118 所）** · 仅普通类一段（80 个平行志愿）")

# 数据来源徽章
from datetime import datetime
data_stat = Path("data/score_rank_2025.json")
data_mtime = datetime.fromtimestamp(data_stat.stat().st_mtime).strftime("%Y-%m-%d") if data_stat.exists() else "—"
progs_list = load_programs()
data_count = len(progs_list)
multi_year = sum(1 for p in progs_list if len(p.history) >= 2)
years = sorted({h["year"] for p in progs_list for h in p.history}, reverse=True)
year_range = f"{min(years)}-{max(years)}" if years else "—"
if data_count > 1000:  # 真实数据阈值
    st.success(
        f"✅ **真实数据** · 一分一段表更新于 {data_mtime} · "
        f"{data_count} 个 985+211 专业（{multi_year} 个含多年历史，覆盖 {year_range}）· "
        f"来源：浙江省教育考试院",
        icon="🟢",
    )
else:
    st.warning(
        f"⚠ **演示数据** · 仅 {data_count} 个专业 · 点击侧边栏「🕷️ 数据更新」可抓取真实数据",
        icon="🟡",
    )

# 2026 数据待发布提示
status_path = Path("data/2026_check_status.json")
if status_path.exists():
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        check_time = status.get("check_time", "")[:10]
        found = status.get("found", {})
        any_2026 = any(found.values())
        if not any_2026:
            st.info(
                f"⏰ **2026 真实数据待发布** · 上次检查 {check_time} · "
                f"预计：分数段表 6/25-26、投档 7/中下旬 · "
                f"系统已配置 GitHub Action 每天 9:00 自动检测",
                icon="🕐",
            )
    except Exception:
        pass


# ====== 侧边栏：考生信息录入 ======
with st.sidebar:
    st.header("📝 考生信息")

    score = st.number_input("高考总分（750 分制）", 200, 750, 595, step=1)
    rank = score_to_rank(score, score_rank)
    st.metric("对应全省位次", f"{rank:,}")

    st.divider()

    subjects = st.multiselect(
        "选考科目（选 3 门）",
        ["物理", "化学", "生物", "历史", "政治", "地理", "技术"],
        default=["物理", "化学", "生物"],
    )
    if subjects and len(subjects) != 3:
        st.warning("⚠ 浙江省要求选考 3 门，请补齐或修改")

    st.divider()

    all_cities = sorted({p.city for p in all_programs})
    cities = st.multiselect("偏好城市（可多选）", all_cities)
    keywords_str = st.text_input(
        "专业关键词（逗号分隔）",
        placeholder="例如：计算机,人工智能,临床医学",
    )
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else []

    st.divider()

    # 冲稳保比例
    st.subheader("冲稳保比例")
    rush_pct = st.slider("冲", 0, 100, 30, step=5)
    stable_pct = st.slider("稳", 0, 100, 50, step=5)
    safe_pct = 100 - rush_pct - stable_pct
    st.metric("保（自动计算）", f"{safe_pct}%")
    if rush_pct + stable_pct > 100:
        st.error("冲 + 稳 比例不能超过 100%")

    st.divider()

    # 自动生成按钮 + 强制生成
    auto_col, gen_col = st.columns([1, 1])
    with auto_col:
        auto_generate = st.checkbox("参数变化时自动重新生成", value=True)
    with gen_col:
        manual_generate = st.button("🔄 重新生成", use_container_width=True)

    generate = auto_generate or manual_generate
    st.divider()

    with st.expander("🕷️ 数据更新（从浙江省教育考试院）", expanded=False):
        st.caption("**⚠ 提示**：自动抓取可能因 zjzs.net 反爬而失败。失败时会提供手动下载链接。")
        crawl_year = st.number_input("目标年份", 2024, 2026, 2025, step=1)
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("📥 抓取一分一段表", use_container_width=True):
                with st.spinner(f"正在抓取 {crawl_year} 年一分一段表..."):
                    try:
                        result = ScoreRankCrawler().fetch(crawl_year)
                        if result.get("table"):
                            saved = ScoreRankCrawler().save(crawl_year, result["table"])
                            st.success(
                                f"✅ 已更新 {crawl_year} 年一分一段表\n\n"
                                f"- 行数：{result['rows']}\n"
                                f"- 来源：{result['source_url']}\n"
                                f"- 已保存：{saved}"
                            )
                            st.cache_data.clear()
                        else:
                            st.warning("❌ 自动抓取失败")
                            st.info(result.get("manual_tip", "未知错误"))
                            st.markdown(f"**手动入口**：[浙江省教育考试院]({result.get('source_url', '#')})")
                    except Exception as e:
                        st.error(f"抓取异常：{e}")

        with cc2:
            if st.button("📄 抓取投档 PDF", use_container_width=True):
                with st.spinner(f"正在抓取 {crawl_year} 年投档 PDF..."):
                    try:
                        result = AdmissionPdfCrawler().fetch(crawl_year)
                        if result.get("rows"):
                            saved = AdmissionPdfCrawler().merge_into_history(
                                result["rows"], year=crawl_year
                            )
                            st.success(
                                f"✅ 已合并 {crawl_year} 年录取数据\n\n"
                                f"- 记录数：{result['rows_count']}\n"
                                f"- 来源：{result['source_url']}\n"
                                f"- 已追加：{saved}"
                            )
                            st.cache_data.clear()
                        else:
                            st.warning("❌ 自动抓取失败")
                            st.info(result.get("manual_tip", "未知错误"))
                    except Exception as e:
                        st.error(f"抓取异常：{e}")

    st.divider()
    st.caption("⚠ 仅供参考，最终以浙江省教育考试院公布为准")


# ====== 主区 ======
if generate:
    if len(subjects) != 3:
        st.error("请先在左侧选择 3 门选考科目")
        st.stop()
    if rush_pct + stable_pct > 100:
        st.error("冲稳保比例设置错误")
        st.stop()

    cand = Candidate(
        score=score,
        rank=rank,
        selected_subjects=subjects,
        preferences={"cities": cities, "keywords": keywords},
    )

    ratio = (rush_pct / 100, stable_pct / 100, safe_pct / 100)
    with st.spinner("正在生成志愿表..."):
        recs = recommend(
            cand, all_programs, top_n=80, ratio=ratio,
            cities=cities, keywords=keywords,
        )

    st.session_state["recs"] = recs
    st.session_state["cand"] = cand


# ====== 显示结果 ======
recs = st.session_state.get("recs")
if recs:
    cand = st.session_state["cand"]

    # 统计卡片
    s = summary(recs)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("总志愿数", s["total"])
    c2.metric("🔴 冲", s["rush"], f"{s['rush']/s['total']*100:.0f}%")
    c3.metric("🟡 稳", s["stable"], f"{s['stable']/s['total']*100:.0f}%")
    c4.metric("🟢 保", s["safe"], f"{s['safe']/s['total']*100:.0f}%")
    c5.metric("平均概率", f"{s['avg_probability']*100:.0f}%")

    st.divider()

    # 志愿表
    df = to_dataframe(recs)

    def color_tier(val):
        return {
            "冲": "background-color: #ffcccc; color: #900",
            "稳": "background-color: #fff3cd; color: #650",
            "保": "background-color: #d4edda; color: #060",
        }.get(val, "")

    def color_trend(val):
        """趋势列着色：变难=红 / 平稳=灰 / 变易=绿"""
        s = str(val)
        if "变难" in s:
            return "color: #c00; font-weight: bold"
        elif "变易" in s:
            return "color: #060; font-weight: bold"
        elif "平稳" in s:
            return "color: #888"
        return ""

    def color_sparkline(val):
        """3年趋势 sparkline 列：固定浅灰底色突出显示"""
        return "background-color: #f5f5f5; font-family: monospace; letter-spacing: 2px"

    st.subheader(f"📋 {cand.score} 分 / 位次 {cand.rank:,} · 80 个志愿推荐")
    st.caption("💡 「3年趋势」列：█ 高=难考/低=易考（归一化）· 「趋势」列：↑变难 / →平稳 / ↓变易（基于 2023-2025 位次差）")
    st.dataframe(
        df.style.map(color_tier, subset=["层次"])
          .map(color_trend, subset=["趋势"])
          .map(color_sparkline, subset=["3年趋势"]),
        use_container_width=True,
        height=600,
        hide_index=True,
    )

    # 导出
    st.divider()
    st.subheader("📥 导出")
    e1, e2, e3 = st.columns(3)
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_info = {
        "score": cand.score,
        "rank": cand.rank,
        "subjects": cand.selected_subjects,
        "cities": cities,
        "keywords": keywords,
    }

    with e1:
        # 多 Sheet Excel（推荐！）
        buf = io.BytesIO()
        # 先写文件再读
        tmp_path = output_dir / f"志愿表_{cand.score}分_多sheet.xlsx"
        to_excel_multi_sheet(recs, tmp_path, candidate=candidate_info)
        with open(tmp_path, "rb") as f:
            buf.write(f.read())
        buf.seek(0)
        st.download_button(
            "📊 多 Sheet Excel（推荐）",
            data=buf.getvalue(),
            file_name=f"志愿表_{cand.score}分_多sheet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="包含「摘要 + 冲档 + 稳档 + 保档」4 个 Sheet",
        )

    with e2:
        # CSV 导出
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
        st.download_button(
            "📄 下载 CSV",
            data=csv_buf.getvalue(),
            file_name=f"志愿表_{cand.score}分.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with e3:
        if st.button("💾 保存到本地 data/exports/", use_container_width=True):
            xlsx_path = to_excel(recs, output_dir / f"志愿表_{cand.score}分.xlsx")
            csv_path = to_csv(recs, output_dir / f"志愿表_{cand.score}分.csv")
            multi_path = to_excel_multi_sheet(recs, output_dir / f"志愿表_{cand.score}分_多sheet.xlsx", candidate=candidate_info)
            st.success(f"✓ 已保存 3 个文件：\n- {xlsx_path.name}\n- {csv_path.name}\n- {multi_path.name}")

    # 学校详情卡片（点击展开查看院校详情）
        with st.expander("🎓 学校详情卡片（点击展开每个志愿）", expanded=False):
            st.caption("展示每个志愿的 3 年稳定性、趋势、历年分数等详细信息")
            inst_details = get_institution_details()

            # 用 3 列网格展示，每列 1 个志愿
            cols_per_row = 3
            for i in range(0, len(recs), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, r in enumerate(recs[i:i + cols_per_row]):
                    with cols[j]:
                        p = r.program
                        card = get_institution_card_data(p)
                        detail = inst_details.get(p.institution, {})
                        tier_emoji = {"冲": "🔴", "稳": "🟡", "保": "🟢"}[r.tier]
                        prob = f"{r.probability * 100:.0f}%"

                        with st.container(border=True):
                            # 标题 + 标签（985/211/双一流）
                            tags_html = " ".join(
                                f'<span style="background:#{"c00" if t=="985" else "06c" if t=="211" else "060" if "双一流" in t else "666"};color:white;padding:2px 6px;border-radius:3px;font-size:11px;margin-right:2px">{t}</span>'
                                for t in detail.get("tags", [])[:4]
                            )
                            st.markdown(
                                f"**{i+j+1}. {tier_emoji} {p.institution[:18]}** "
                                f"<br>{tags_html}",
                                unsafe_allow_html=True,
                            )
                            st.caption(f"{p.name[:25]}{'...' if len(p.name) > 25 else ''}")
                            st.markdown(f"**{card['sparkline']}** &nbsp; {card['trend']['direction']}")
                            if r.tier == "冲":
                                prob_color = "🔴"
                            elif r.tier == "稳":
                                prob_color = "🟡"
                            else:
                                prob_color = "🟢"
                            st.markdown(f"{prob_color} 概率 **{prob}** · {card['stability']}")
                            # 强势学科
                            if detail.get("strong_majors"):
                                majors_str = " · ".join(detail["strong_majors"][:4])
                                st.markdown(f"🎯 **强项**: {majors_str}")
                            # 双一流学科数
                            if detail.get("first_class_majors"):
                                n = len(detail["first_class_majors"])
                                with st.popover(f"📚 双一流学科 ({n})", use_container_width=True):
                                    st.markdown("**双一流建设学科：**")
                                    st.write("、".join(detail["first_class_majors"]))
                            # 保研率 + 就业率
                            postgrad = detail.get("postgraduate_rate", "—")
                            employ = detail.get("employment_rate", "—")
                            if postgrad != "—":
                                st.markdown(f"📊 **保研率**: {postgrad}　💼 **就业率**: {employ}")
                            # 3 年数据
                            if card['min_score_3y']:
                                with st.expander("📈 3 年录取分", expanded=False):
                                    st.caption(f"稳定性 CV: {card['cv']:.1%}")
                                    for score, rank in card['min_score_3y']:
                                        st.write(f"  • {score} 分 / 位次 {rank:,}")
                            # 显示城市 + 学费
                            st.caption(f"📍 {p.city or '—'} · 💰 {p.tuition}元/年")

    # ===== 趋势分析 section =====
    st.divider()
    st.subheader("📈 趋势分析")
    tab1, tab2, tab3 = st.tabs(["🎯 录取概率分布", "📊 3 年位次变化", "🗺️ 院校地域分布"])

    with tab1:
        st.caption("按录取概率统计志愿数")
        prob_counts = (
            df["录取概率"].value_counts().reindex(["10%", "45%", "75%", "95%"], fill_value=0)
        )
        prob_df = pd.DataFrame({
            "概率": prob_counts.index,
            "志愿数": prob_counts.values,
        })
        st.bar_chart(prob_df, x="概率", y="志愿数", height=300)

    with tab2:
        st.caption("3 年录取位次变化趋势（基于 2023-2025 真实数据）")
        # 解析趋势列
        trend_counts = {"↑ 变难": 0, "→ 平稳": 0, "↓ 变易": 0, "数据不足": 0}
        for t in df["趋势"]:
            if "变难" in str(t):
                trend_counts["↑ 变难"] += 1
            elif "平稳" in str(t):
                trend_counts["→ 平稳"] += 1
            elif "变易" in str(t):
                trend_counts["↓ 变易"] += 1
            else:
                trend_counts["数据不足"] += 1
        trend_df = pd.DataFrame({
            "趋势": list(trend_counts.keys()),
            "志愿数": list(trend_counts.values()),
        })
        c1, c2 = st.columns([1, 1])
        with c1:
            st.bar_chart(trend_df, x="趋势", y="志愿数", height=300)
        with c2:
            # 各 tier 趋势细分
            tier_trend = {}
            for tier in ["冲", "稳", "保"]:
                sub = df[df["层次"] == tier]
                if len(sub) == 0:
                    continue
                cnt = {"↑ 变难": 0, "→ 平稳": 0, "↓ 变易": 0}
                for t in sub["趋势"]:
                    if "变难" in str(t):
                        cnt["↑ 变难"] += 1
                    elif "平稳" in str(t):
                        cnt["→ 平稳"] += 1
                    elif "变易" in str(t):
                        cnt["↓ 变易"] += 1
                tier_trend[tier] = cnt
            st.markdown("**各 tier 趋势细分**")
            for tier, cnt in tier_trend.items():
                with st.container():
                    st.write(f"**{tier}档**（{sum(cnt.values())} 个）")
                    cols = st.columns(3)
                    for i, (k, v) in enumerate(cnt.items()):
                        cols[i].metric(k, v)

    with tab3:
        st.caption("志愿的院校地域分布")
        city_df = df[df["城市"] != ""].groupby("城市").size().reset_index(name="志愿数")
        city_df = city_df.sort_values("志愿数", ascending=False).head(20)
        st.bar_chart(city_df, x="城市", y="志愿数", height=400)
        st.caption(f"覆盖 {df['城市'].nunique()} 个城市 / {df['院校'].nunique()} 所院校")

else:
    # 引导页
    st.info("👈 请在左侧填写考生信息，然后点击 **「🎲 生成志愿表」** 按钮")
    st.markdown("""
    ### 📌 使用说明
    1. 输入高考分数（自动反查位次）
    2. 选择 3 门选考科目
    3. （可选）筛选城市 / 专业关键词
    4. 调整冲稳保比例（默认 30/50/20）
    5. 点击生成 → 查看 80 个志愿 → 导出 Excel/CSV

    ### 📚 数据说明
    - 院校：118 所 985 + 211（覆盖全部 39 所 985 + 79 所 211）
    - 专业：~670 个代表性专业（理工/医学/文法/商/农林/师范）
    - 历史录取：2023-2025 年 3 年数据
    - 一分一段表：基于 2025 浙江真实分布特征

    ### ⚠ 免责声明
    本系统仅供学习参考，**不构成任何报考建议**。
    最终志愿请以浙江省教育考试院（zjzs.net）官方公告为准。
    """)
