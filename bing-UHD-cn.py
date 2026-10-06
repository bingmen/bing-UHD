# bing-UHD-cn-0.0.5.py
# github.com/shenjuexiao
# 20261006

# bing-UHD-cn.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bing 每日壁纸抓取脚本
- 获取 Bing 壁纸 JSON (cn 区域)
- 下载 UHD 高清图到 bing-UHD-cn-年份/ 目录
- 下载 320x240 缩略图到 bing-320-cn-年份/ 目录
- 保存 JSON 数据到 bing-JSON-cn-年份/ 目录
- 生成 bing-UHD-cn-年份.md 表格：日期 | 标题 | 版权 | 略缩图 | 高清图
- 生成/追加 bing-JSON-cn-年份.json（按年汇总，同日期去重后按日期排序）
- 图片命名：日期_标题_UHD_cn.jpg / 日期_320_cn.jpg
- JSON 命名：日期_JSON_cn.json
- 日期前缀统一为 yyyymmdd 格式
"""

import os
import re
import json
import requests
from datetime import datetime

# ============ 配置 ============
API_URL = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=zh-CN"
UHD_BASE = "https://www.bing.com"
TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
# jsDelivr CDN 前缀
CDN_BASE = "https://cdn.jsdelivr.net/gh/bingmen/bing-UHD@main"


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80] if len(name) > 80 else name


def fetch_images():
    """获取 Bing 壁纸 JSON 数据"""
    resp = requests.get(API_URL, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("images", [])


def download_image(url: str, save_path: str) -> bool:
    """下载图片，若已存在则跳过"""
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        print(f"  [跳过] 已存在: {save_path}")
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"  [下载] {save_path}")
        return True
    except Exception as e:
        print(f"  [失败] {url} -> {e}")
        return False


def save_json(img: dict, json_dir: str, date_compact: str) -> None:
    """保存单张图片的 JSON 数据到对应年份目录"""
    json_filename = f"{date_compact}_JSON_cn.json"
    json_filepath = os.path.join(json_dir, json_filename)
    if os.path.exists(json_filepath) and os.path.getsize(json_filepath) > 0:
        print(f"  [跳过] 已存在: {json_filepath}")
        return
    try:
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(img, f, ensure_ascii=False, indent=2)
        print(f"  [保存] {json_filepath}")
    except Exception as e:
        print(f"  [失败] 保存 JSON {json_filepath} -> {e}")


def append_yearly_json(year: str, new_images: list) -> None:
    """将本次获取的图片追加到 bing-JSON-cn-年份.json，按日期去重并排序"""
    yearly_json_file = f"bing-JSON-cn-{year}.json"

    # 读取已有数据
    existing: list = []
    if os.path.exists(yearly_json_file) and os.path.getsize(yearly_json_file) > 0:
        try:
            with open(yearly_json_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except Exception as e:
            print(f"  [警告] 读取 {yearly_json_file} 失败，将重新生成: {e}")
            existing = []

    # 以 enddate 为键去重（后获取的覆盖旧的）
    merged = {}
    for item in existing:
        key = item.get("enddate", "")
        if key:
            merged[key] = item
    for item in new_images:
        key = item.get("enddate", "")
        if key:
            merged[key] = item

    # 按日期倒序排列（最新在前）
    merged_list = sorted(merged.values(), key=lambda x: x.get("enddate", ""), reverse=True)

    try:
        with open(yearly_json_file, "w", encoding="utf-8") as f:
            json.dump(merged_list, f, ensure_ascii=False, indent=2)
        print(f"  [汇总] {yearly_json_file} 共 {len(merged_list)} 条记录")
    except Exception as e:
        print(f"  [失败] 写入 {yearly_json_file} -> {e}")


def main():
    images = fetch_images()
    if not images:
        print("未获取到任何图片数据")
        return

    # 按年份分组收集行，最后分别写入各自的 Markdown
    # 结构: { "2025": [row, ...], ... }
    year_rows: dict[str, list] = {}
    # 按年份收集本次获取的原始 JSON 数据，用于追加年度 JSON
    year_images: dict[str, list] = {}

    for img in images:
        # 日期：Bing 格式 yyyymmdd
        date_str = img.get("enddate", "")
        if len(date_str) == 8:
            date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            date_compact = date_str  # 统一使用 yyyymmdd 作为文件名前缀
            year = date_str[:4]
        else:
            date_fmt = date_str
            date_compact = date_str
            # 无法解析年份时，尝试用当前年份兜底
            year = datetime.utcnow().strftime("%Y")

        # 按年份构造目录名
        output_dir = f"bing-UHD-cn-{year}"
        thumb_dir = f"bing-320-cn-{year}"
        json_dir = f"bing-JSON-cn-{year}"
        md_file = f"bing-UHD-cn-{year}.md"

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(thumb_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)

        title = img.get("title", "").strip()
        copyright_ = img.get("copyright", "").strip()

        # 保存 JSON 数据（单日文件）
        save_json(img, json_dir, date_compact)

        # 收集到年度列表
        year_images.setdefault(year, []).append(img)

        # UHD 链接：优先使用 urlbase + _UHD.jpg
        urlbase = img.get("urlbase", "")
        if urlbase:
            uhd_url = f"{UHD_BASE}{urlbase}_UHD.jpg"
        else:
            # 兜底：将 url 中的 _1920x1080 替换为 _UHD
            raw_url = img.get("url", "")
            uhd_url = raw_url.replace("_1920x1080", "_UHD")

        # 320x240 链接：优先使用 urlbase + _320x240.jpg
        if urlbase:
            thumb_url = f"{UHD_BASE}{urlbase}_320x240.jpg"
        else:
            raw_url = img.get("url", "")
            thumb_url = raw_url.replace("_1920x1080", "_320x240")

        # UHD 文件名：日期_标题_UHD_cn.jpg（日期前缀统一为 yyyymmdd）
        safe_title = sanitize_filename(title) if title else "Bing"
        uhd_filename = f"{date_compact}_{safe_title}_UHD_cn.jpg"
        uhd_filepath = os.path.join(output_dir, uhd_filename)

        # 320 文件名：日期_320_cn.jpg（日期前缀统一为 yyyymmdd）
        thumb_filename = f"{date_compact}_320_cn.jpg"
        thumb_filepath = os.path.join(thumb_dir, thumb_filename)

        # 下载图片
        download_image(uhd_url, uhd_filepath)
        download_image(thumb_url, thumb_filepath)

        # 缩略图 CDN 链接（指向对应年份目录）
        thumb_cdn_url = f"{CDN_BASE}/{thumb_dir}/{thumb_filename}"

        # Markdown 表格行
        md_title = title.replace("|", "\\|") if title else ""
        md_copy = copyright_.replace("|", "\\|") if copyright_ else ""
        row = (
            f"| {date_fmt} | {md_title} | {md_copy} "
            f"| ![{md_title}]({thumb_cdn_url}) "
            f"| [UHD]({uhd_url}) |"
        )
        year_rows.setdefault(year, []).append(row)

    # 每个年份分别写入 Markdown
    for year, rows in year_rows.items():
        md_file = f"bing-UHD-cn-{year}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Bing 每日壁纸（UHD 中文 {year}）\n\n")
            f.write(f"> 最后更新：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            f.write("| 日期 | 标题 | 版权 | 略缩图 | 高清图 |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            f.write("\n".join(rows) + "\n")
        print(f"\n{year} 年共处理 {len(rows)} 张图片，Markdown 已写入 {md_file}")

    # 追加年度汇总 JSON
    for year, imgs in year_images.items():
        append_yearly_json(year, imgs)


if __name__ == "__main__":
    main()



