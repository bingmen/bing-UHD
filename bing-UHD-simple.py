# bing-UHD-simple-0.0.1.py
# github.com/shenjuexiao
# 20261024

# bing-UHD-simple.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bing 每日壁纸（精简版）：抓取 JSON + 年度汇总 + Markdown 生成

流程：
1. 抓取 Bing 每日壁纸 JSON
   - 每日：bing-UHD-{year}/bing-JSON-{mkt}-{year}/YYYYMMDD_JSON_{mkt}.json
   - 年度：bing-UHD-{year}/bing-JSON-{mkt}-{year}.json
     （同日期去重，以 enddate 为键保留最后写入；按 enddate 字符串降序）
2. 根据年度 JSON 生成 bing-UHD-{year}/bing-UHD-{mkt}-{year}.md
   无数据时仍输出 H1、更新时间、表头、分隔行，表格体为空
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------- 常量配置

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

BING_BASE = "https://www.bing.com"
BING_ARCHIVE = "https://www.bing.com/HPImageArchive.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

SUPPORTED_MKTS = [
    "de-DE", "en-CA", "en-GB", "en-IN", "en-US",
    "fr-FR", "it-IT", "ja-JP", "zh-CN",
]

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

# ---------------------------------------------------------------- JSON 抓取

def fetch_one(mkt: str, idx: int) -> dict | None:
    """抓取 Bing 归档中第 idx 天的记录，返回精简字段。"""
    params = {"format": "js", "idx": str(idx), "n": "1", "mkt": mkt}
    try:
        resp = requests.get(BING_ARCHIVE, params=params,
                            headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        print(f"  [警告] 抓取 JSON 失败 idx={idx}：{e}")
        return None

    images = data.get("images") or []
    if not images:
        return None
    img = images[0]

    urlbase = img.get("urlbase", "") or ""
    startdate = img.get("startdate", "")
    enddate = img.get("enddate", startdate) or startdate
    if not enddate:
        return None

    return {
        "startdate": startdate,
        "enddate": enddate,
        "title": img.get("title", ""),
        "copyright": img.get("copyright", ""),
        "urlbase": urlbase,
    }


def fetch_json(mkt: str, year: str, max_idx: int = 16) -> list[dict]:
    """回溯抓取，返回该年度记录（按 enddate 字符串降序）。"""
    print(f"[信息] 抓取 Bing JSON：{mkt} / {year}")
    collected: dict[str, dict] = {}
    empty_streak = 0

    for idx in range(0, max_idx + 1):
        item = fetch_one(mkt, idx)
        if not item:
            empty_streak += 1
            if empty_streak >= 3 and idx > 0:
                break
            continue
        empty_streak = 0
        enddate = item["enddate"]
        if enddate[:4] != str(year):
            # 越过目标年份
            if enddate[:4] < str(year):
                break
            continue
        collected[enddate] = item
        time.sleep(0.5)

    result = sorted(collected.values(), key=lambda x: x["enddate"], reverse=True)
    print(f"[信息] 抓取到 {len(result)} 条 {year} 年记录")
    return result

# ---------------------------------------------------------------- 主流程

def merge_and_save_json(mkt: str, year: str, out_root: Path) -> Path:
    """抓取并合并 JSON，返回年度 JSON 路径。"""
    json_dir = out_root / f"bing-JSON-{mkt}-{year}"
    ensure_dir(json_dir)

    json_file = out_root / f"bing-JSON-{mkt}-{year}.json"

    # 读取已有年度 JSON
    existing: dict[str, dict] = {}
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                old = json.load(f)
            if isinstance(old, list):
                for it in old:
                    ed = it.get("enddate", "")
                    if ed:
                        existing[ed] = it
        except Exception as e:  # noqa: BLE001
            print(f"  [警告] 读取已有 JSON 失败：{e}")

    # 抓取并覆盖同日期的记录
    fetched = fetch_json(mkt, year)
    for it in fetched:
        existing[it["enddate"]] = it

    merged = sorted(existing.values(), key=lambda x: x["enddate"], reverse=True)

    # 写年度 JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # 写每日 JSON
    for it in merged:
        ed = it["enddate"]
        if not ed:
            continue
        day_file = json_dir / f"{ed}_JSON_{mkt}.json"
        day_file.write_text(
            json.dumps(it, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"[信息] 年度 JSON 已写入：{json_file}（{len(merged)} 条）")
    return json_file


def build_markdown(mkt: str, year: str, results: list[dict], out_root: Path) -> Path:
    """生成 Markdown。results 为空时只输出表头。"""
    md_lines = []
    md_lines.append(f"# {H1[mkt]} - UHD - {mkt} - {year}")
    md_lines.append("")
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    md_lines.append(f"> {LAST_UPDATED[mkt]}: {utc_now} UTC")
    md_lines.append("")
    md_lines.append(TABLE_HEADERS[mkt])
    md_lines.append(TABLE_SEPARATOR)

    for r in results:
        title_cell = escape_md_cell(r["title"])
        copyright_cell = escape_md_cell(r["copyright"])
        link_text = escape_md_link_text(r["title"])

        urlbase = r["urlbase"]
        thumb = f"{BING_BASE}{urlbase}_320x240.jpg"
        uhd = f"{BING_BASE}{urlbase}_UHD.jpg"

        md_lines.append(
            f"| {r['date_display']} | {title_cell} | {copyright_cell} "
            f"| [![{link_text}]({thumb})]({uhd}) |"
        )

    md_path = out_root / f"bing-UHD-{mkt}-{year}.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[完成] Markdown 已写入：{md_path}")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bing 每日壁纸 JSON 抓取与 Markdown 生成（精简版）"
    )
    parser.add_argument("--mkt", required=True, choices=SUPPORTED_MKTS,
                        help="市场，例如 zh-CN")
    parser.add_argument("--year", required=True, help="年份，例如 2026")
    parser.add_argument("--out-dir", default=".",
                        help="可选：输出根目录，默认为当前目录")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="可选：跳过 JSON 抓取，直接用已有年度 JSON")
    args = parser.parse_args()

    mkt = args.mkt
    year = args.year
    out_root = Path(args.out_dir).resolve()

    # 所有输出放在 bing-UHD-{year}/ 下
    base_dir = out_root / f"bing-UHD-{year}"
    ensure_dir(base_dir)

    # 1) 抓取并合并 JSON
    json_file = base_dir / f"bing-JSON-{mkt}-{year}.json"
    if not args.skip_fetch:
        try:
            json_file = merge_and_save_json(mkt, year, base_dir)
        except Exception as e:  # noqa: BLE001
            print(f"[错误] 抓取 JSON 失败：{e}")

    # 2) 读取年度 JSON（不存在则视为空）
    data: list[dict] = []
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                data = loaded
        except Exception as e:  # noqa: BLE001
            print(f"[错误] 读取 JSON 失败：{e}")
            data = []
    else:
        print(f"[信息] 年度 JSON 不存在，仅生成表头：{json_file}")

    # 3) 构造 Markdown 行（日期倒序，全量重建）
    results: list[dict] = []
    for item in sorted(data, key=lambda x: x.get("enddate", ""), reverse=True):
        enddate = item.get("enddate", "") or item.get("startdate", "")
        if not enddate:
            continue
        results.append({
            "enddate": enddate,
            "date_display": format_date(enddate),
            "title": item.get("title", ""),
            "copyright": item.get("copyright", ""),
            "urlbase": item.get("urlbase", ""),
        })

    # 4) 生成 Markdown
    build_markdown(mkt, year, results, base_dir)
    print(f"[完成] 输出目录：{base_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
