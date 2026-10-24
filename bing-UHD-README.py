# bing-UHD-README-0.0.2.py
# github.com/shenjuexiao
# 20261025

# bing-UHD-cn-README.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bing 每日壁纸 README 汇总生成器

参考：bing-UHD-simple.py
输出：bing-UHD-{year}/README-{mkt}-{year}.md
      并把 README-zh-CN-{year}.md 复制为 README.md

对每个 outer_mkt × year：
  读取 bing-UHD-{year}/bing-JSON-{inner_mkt}-{year}.json（九种 mkt）
  为每个 inner_mkt 生成 H2 + 一段 4 列表格（随机 3 条）
"""

import argparse
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- 常量配置

MKTS = ["de-DE", "en-CA", "en-GB", "en-IN", "en-US", "fr-FR", "it-IT", "ja-JP", "zh-CN"]
YEARS = [2026, 2025, 2024, 2023, 2022]

H1 = {
    "de-DE": "Bing-Tägliches Hintergrundbild",
    "en-CA": "Bing Daily Wallpaper",
    "en-GB": "Bing Daily Wallpaper",
    "en-IN": "Bing Daily Wallpaper",
    "en-US": "Bing Daily Wallpaper",
    "fr-FR": "Fond d'écran quotidien Bing",
    "it-IT": "Sfondo giornaliero di Bing",
    "ja-JP": "Bing デイリー壁紙",
    "zh-CN": "Bing 每日壁纸",
}

LAST_UPDATED = {
    "de-DE": "Zuletzt aktualisiert",
    "en-CA": "Last updated",
    "en-GB": "Last updated",
    "en-IN": "Last updated",
    "en-US": "Last updated",
    "fr-FR": "Dernière mise à jour",
    "it-IT": "Ultimo aggiornamento",
    "ja-JP": "最終更新",
    "zh-CN": "最后更新",
}

TABLE_HEADERS = {
    "de-DE": "| Datum | Titel | Urheberrecht | Vorschaubild |",
    "en-CA": "| Date | Title | Copyright | Thumbnail |",
    "en-GB": "| Date | Title | Copyright | Thumbnail |",
    "en-IN": "| Date | Title | Copyright | Thumbnail |",
    "en-US": "| Date | Title | Copyright | Thumbnail |",
    "fr-FR": "| Date | Titre | Droits d'auteur | Vignette |",
    "it-IT": "| Data | Titolo | Copyright | Miniatura |",
    "ja-JP": "| 日付 | タイトル | 著作権 | サムネイル |",
    "zh-CN": "| 日期 | 标题 | 版权 | 缩略图 |",
}

# TABLE_SEPARATOR = "| --- | --- | --- | --- |"
TABLE_SEPARATOR = "| :---: | :---: | :---: | :---: |"

H2 = {
    # ── 行语言：德语（德国）──
    "de-DE": {
        "de-DE": "Deutsch (Deutschland)",
        "en-CA": "Englisch (Kanada)",
        "en-GB": "Englisch (Vereinigtes Königreich)",
        "en-IN": "Englisch (Indien)",
        "en-US": "Englisch (Vereinigte Staaten)",
        "fr-FR": "Französisch (Frankreich)",
        "it-IT": "Italienisch (Italien)",
        "ja-JP": "Japanisch (Japan)",
        "zh-CN": "Vereinfachtes Chinesisch (China)",
    },
    # ── 行语言：英语（加拿大）──
    "en-CA": {
        "de-DE": "German (Germany)",
        "en-CA": "English (Canada)",
        "en-GB": "English (United Kingdom)",
        "en-IN": "English (India)",
        "en-US": "English (United States)",
        "fr-FR": "French (France)",
        "it-IT": "Italian (Italy)",
        "ja-JP": "Japanese (Japan)",
        "zh-CN": "Simplified Chinese (China)",
    },
    # ── 行语言：英语（英国）──
    "en-GB": {
        "de-DE": "German (Germany)",
        "en-CA": "English (Canada)",
        "en-GB": "English (United Kingdom)",
        "en-IN": "English (India)",
        "en-US": "English (United States)",
        "fr-FR": "French (France)",
        "it-IT": "Italian (Italy)",
        "ja-JP": "Japanese (Japan)",
        "zh-CN": "Simplified Chinese (China)",
    },
    # ── 行语言：英语（印度）──
    "en-IN": {
        "de-DE": "German (Germany)",
        "en-CA": "English (Canada)",
        "en-GB": "English (United Kingdom)",
        "en-IN": "English (India)",
        "en-US": "English (United States)",
        "fr-FR": "French (France)",
        "it-IT": "Italian (Italy)",
        "ja-JP": "Japanese (Japan)",
        "zh-CN": "Simplified Chinese (China)",
    },
    # ── 行语言：英语（美国）──
    "en-US": {
        "de-DE": "German (Germany)",
        "en-CA": "English (Canada)",
        "en-GB": "English (United Kingdom)",
        "en-IN": "English (India)",
        "en-US": "English (United States)",
        "fr-FR": "French (France)",
        "it-IT": "Italian (Italy)",
        "ja-JP": "Japanese (Japan)",
        "zh-CN": "Simplified Chinese (China)",
    },
    # ── 行语言：法语（法国）──
    "fr-FR": {
        "de-DE": "Allemand (Allemagne)",
        "en-CA": "Anglais (Canada)",
        "en-GB": "Anglais (Royaume-Uni)",
        "en-IN": "Anglais (Inde)",
        "en-US": "Anglais (États-Unis)",
        "fr-FR": "Français (France)",
        "it-IT": "Italien (Italie)",
        "ja-JP": "Japonais (Japon)",
        "zh-CN": "Chinois simplifié (Chine)",
    },
    # ── 行语言：意大利语（意大利）──
    "it-IT": {
        "de-DE": "Tedesco (Germania)",
        "en-CA": "Inglese (Canada)",
        "en-GB": "Inglese (Regno Unito)",
        "en-IN": "Inglese (India)",
        "en-US": "Inglese (Stati Uniti)",
        "fr-FR": "Francese (Francia)",
        "it-IT": "Italiano (Italia)",
        "ja-JP": "Giapponese (Giappone)",
        "zh-CN": "Cinese semplificato (Cina)",
    },
    # ── 行语言：日语（日本）──
    "ja-JP": {
        "de-DE": "ドイツ語（ドイツ）",
        "en-CA": "英語（カナダ）",
        "en-GB": "英語（イギリス）",
        "en-IN": "英語（インド）",
        "en-US": "英語（アメリカ合衆国）",
        "fr-FR": "フランス語（フランス）",
        "it-IT": "イタリア語（イタリア）",
        "ja-JP": "日本語（日本）",
        "zh-CN": "簡体字中国語（中国）",
    },
    # ── 行语言：简体中文（中国）──
    "zh-CN": {
        "de-DE": "德语（德国）",
        "en-CA": "英语（加拿大）",
        "en-GB": "英语（英国）",
        "en-IN": "英语（印度）",
        "en-US": "英语（美国）",
        "fr-FR": "法语（法国）",
        "it-IT": "意大利语（意大利）",
        "ja-JP": "日语（日本）",
        "zh-CN": "简体中文（中国）",
    },
}

SYMBOLS = {
    "de-DE": "🦅",
    "en-CA": "🍁",
    "en-GB": "🌹",
    "en-IN": "🦁",
    "en-US": "🗽",
    "fr-FR": "🐓",
    "it-IT": "⭐",
    "ja-JP": "🌸",
    "zh-CN": "🐉",
}

BING_BASE = "https://www.bing.com"

# ---------------------------------------------------------------- 工具函数


def escape_md_cell(text: str) -> str:
    """Markdown 表格单元格：| -> \\|，换行 -> 空格。"""
    if not text:
        return ""
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def escape_md_link_text(text: str) -> str:
    """链接文字：替换 [ ] 为可读形式。"""
    if not text:
        return ""
    return str(text).replace("[", "(").replace("]", ")")


def format_date(enddate: str) -> str:
    """'YYYYMMDD' -> 'YYYY-MM-DD'"""
    if len(enddate) == 8 and enddate.isdigit():
        return f"{enddate[0:4]}-{enddate[4:6]}-{enddate[6:8]}"
    return enddate


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json_items(json_path: Path) -> list[dict]:
    """读取年度 JSON，返回 list（失败返回空列表）。"""
    if not json_path.exists():
        print(f"  [信息] JSON 不存在：{json_path}")
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [it for it in data if isinstance(it, dict)]
        print(f"  [警告] JSON 不是列表：{json_path}")
        return []
    except Exception as e:  # noqa: BLE001
        print(f"  [警告] 读取 JSON 失败 {json_path}：{e}")
        return []


# ---------------------------------------------------------------- 表格构造


def build_row(item: dict) -> str:
    """把单条 JSON 对象渲染为 Markdown 表格的一行。"""
    enddate = item.get("enddate", "") or item.get("startdate", "")
    date_display = format_date(enddate)
    title = item.get("title", "")
    copyright_ = item.get("copyright", "")
    urlbase = item.get("urlbase", "") or ""

    title_cell = escape_md_cell(title)
    copyright_cell = escape_md_cell(copyright_)
    link_text = escape_md_link_text(title)

    thumb = f"{BING_BASE}{urlbase}_320x240.jpg"
    uhd = f"{BING_BASE}{urlbase}_UHD.jpg"
    fallback = f"{BING_BASE}{urlbase}_1920x1080.jpg"

    image_link = uhd if urlbase else fallback
    _ = fallback

    return (
        f"| {date_display} | {title_cell} | {copyright_cell} "
        f"| [![{link_text}]({thumb})]({image_link}) |"
    )


def build_section(inner_mkt: str, outer_mkt: str, year: str,
                  items: list[dict]) -> list[str]:
    """构造单个 inner_mkt 的 H2 + 表头 + 随机 3 行。"""
    lines: list[str] = []
    h2_text = H2[outer_mkt][inner_mkt]
    symbol = SYMBOLS[inner_mkt]
    # ★ 修改：md_name 改为 bing-UHD-{inner_mkt}-{year}.md
    md_name = f"bing-UHD-{inner_mkt}-{year}.md"
    lines.append(f"## {symbol} [{h2_text}]({md_name})")
    lines.append("")
    lines.append(TABLE_HEADERS[inner_mkt])
    lines.append(TABLE_SEPARATOR)

    if items:
        k = min(3, len(items))
        sampled = random.sample(items, k)
        for it in sampled:
            lines.append(build_row(it))

    lines.append("")
    return lines


# ---------------------------------------------------------------- 主流程


def build_readme(outer_mkt: str, year: str, base_dir: Path) -> Path:
    """生成 bing-UHD-{year}/README-{outer_mkt}-{year}.md。"""
    lines: list[str] = []
    lines.append(f"# {H1[outer_mkt]} - UHD - {outer_mkt} - {year}")
    lines.append("")
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"> {LAST_UPDATED[outer_mkt]}：{utc_now} UTC")
    lines.append("")
    # ★ 新增：9 种语言的 README 导航行
    nav = " | ".join(
        f"[{mkt}](README-{mkt}-{year}.md)" for mkt in MKTS
    )
    lines.append(nav)
    lines.append("")

    # H2 + 表格循环九次（inner_mkt 顺序遍历）
    for inner_mkt in MKTS:
        json_path = base_dir / f"bing-JSON-{inner_mkt}-{year}.json"
        items = load_json_items(json_path)
        lines.extend(build_section(inner_mkt, outer_mkt, year, items))

    md_path = base_dir / f"README-{outer_mkt}-{year}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[完成] README 已写入：{md_path}")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bing 每日壁纸 README 汇总生成器"
    )
    parser.add_argument("--out-dir", default=".",
                        help="可选：输出根目录，默认为当前目录")
    parser.add_argument("--year", default=None,
                        help="可选：只处理指定年份；缺省遍历 YEARS")
    parser.add_argument("--seed", default=None,
                        help="可选：随机种子，便于可复现")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    out_root = Path(args.out_dir).resolve()
    years = [args.year] if args.year else [str(y) for y in YEARS]

    for year in years:
        base_dir = out_root / f"bing-UHD-{year}"
        if not base_dir.exists():
            print(f"[信息] 目录不存在，跳过：{base_dir}")
            continue
        ensure_dir(base_dir)

        for outer_mkt in MKTS:
            build_readme(outer_mkt, str(year), base_dir)

        # 复制 README-zh-CN-{year}.md -> README.md
        src = base_dir / f"README-zh-CN-{year}.md"
        dst = base_dir / "README.md"
        if src.exists():
            shutil.copyfile(src, dst)
            print(f"[完成] 复制：{src} -> {dst}")
        else:
            print(f"[警告] 源文件不存在，跳过复制：{src}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
