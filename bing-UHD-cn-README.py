# bing-UHD-cn-README-0.0.1.py
# github.com/shenjuexiao
# 20261008

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成 Bing 每日壁纸 - UHD 中文 的 README.md
"""

import random
from datetime import date, timedelta
from pathlib import Path

# 配置
YEARS = [2026, 2025, 2024, 2023, 2022]
YEAR_EMOJI = {
    2026: "🐎",
    2025: "🐍",
    2024: "🐉",
    2023: "🐇",
    2022: "🐅",
}
# 各年份可选的起始日期（不指定则从 1 月 1 日开始）
YEAR_START_DATE = {
    2022: date(2022, 4, 28),
}
THUMB_URL_TEMPLATE = (
    "https://cdn.jsdelivr.net/gh/bingmen/bing-UHD@main/"
    "bing-320-cn-{year}/{date}_320_cn.jpg"
)
COLS = 4
ROWS = 4
TOTAL = COLS * ROWS
OUTPUT = Path("README.md")


def random_dates(year: int, count: int = TOTAL) -> list[date]:
    """在指定年份内随机选取不重复日期，按时间顺序排列。"""
    start = YEAR_START_DATE.get(year, date(year, 1, 1))
    end = date(year, 12, 31)
    # 如果是 2026 年，且当前日期未到年底，则限制到昨天
    today = date.today()
    if year == today.year:
        end = min(end, today - timedelta(days=1))
    if end < start:
        return []

    span = (end - start).days + 1
    count = min(count, span)
    offsets = random.sample(range(span), count)
    return sorted(start + timedelta(days=o) for o in offsets)


def render_thumb_table(year: int, dates: list[date]) -> str:
    """生成 4×4 略缩图 + 日期表格（Markdown）。"""
    lines = []
    # 补齐到 TOTAL 个，避免表格不齐
    while len(dates) < TOTAL:
        dates.append(dates[-1] if dates else date(year, 1, 1))

    for r in range(ROWS):
        row_dates = dates[r * COLS:(r + 1) * COLS]
        # 略缩图行
        img_cells = []
        for d in row_dates:
            url = THUMB_URL_TEMPLATE.format(
                year=year, date=d.strftime("%Y%m%d")
            )
            img_cells.append(f'<img src="{url}" width="200">')
        lines.append("| " + " | ".join(img_cells) + " |")
        lines.append("| " + " | ".join(["---"] * COLS) + " |")
        # 日期行
        date_cells = [d.strftime("%Y-%m-%d") for d in row_dates]
        lines.append("| " + " | ".join(date_cells) + " |")
        lines.append("")  # 空行分隔

    return "\n".join(lines).rstrip()


def build_readme() -> str:
    parts = []
    parts.append("# Bing 每日壁纸 - UHD 中文\n")
    parts.append("🚀 [bingmen/bing-UHD](https://github.com/bingmen/bing-UHD)\n")
    parts.append("## 简介")
    parts.append(
        "👀 自动抓取 Bing 每日壁纸（中国地区），存储 UHD 和 320×240 格式，"
        "后者作为略缩图形成归档汇总表格。\n"
    )
    parts.append("## 归档")

    for year in YEARS:
        emoji = YEAR_EMOJI[year]
        parts.append(
            f"### {emoji} [{year}]"
            f"(https://github.com/bingmen/bing-UHD/blob/main/"
            f"bing-UHD-cn-{year}.md) "
        )
        dates = random_dates(year)
        parts.append(render_thumb_table(year, dates))
        parts.append("")

    parts.append("## 目录")
    parts.append("- 📄 数据：bing-JSON-cn-{year}")
    parts.append("- 🖼️ 略缩图：bing-320-cn-{year}")
    parts.append("- 🎞️ 高清图：bing-UHD-cn-{year}\n")

    parts.append("## 参考")
    parts.append("- [Bing-Wallpaper-Action 公开API](https://bing-wallpaper.apifox.cn/)")
    parts.append("")

    return "\n".join(parts)


def main():
    random.seed()  # 每次运行都不同；如需可复现可固定种子
    content = build_readme()
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"已生成 {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()

