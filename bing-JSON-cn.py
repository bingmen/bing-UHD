# bing-JSON-cn.py
# github.com/shenjuexiao
# 20261007

# bing-JSON-cn.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
from pathlib import Path
from datetime import datetime

# ========== 配置 ==========
YEAR = "2026"
JSON_FILE = f"bing-JSON-cn-{YEAR}.json"
UHD_DIR = f"bing-UHD-cn-{YEAR}"
THUMB_DIR = f"bing-320-cn-{YEAR}"
MD_FILE = f"bing-UHD-cn-{YEAR}.md"

# GitHub CDN 前缀（用于 Markdown 中的缩略图链接）
CDN_PREFIX = "https://cdn.jsdelivr.net/gh/bingmen/bing-UHD@main"

# ========== 工具函数 ==========
def sanitize_filename(name: str) -> str:
    """去除文件名中的非法字符"""
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = name.strip().replace(' ', '_')
    return name

def build_urls(raw_url: str):
    """
    根据原始 url 生成 UHD 和 320x240 的完整 URL
    """
    # 原始 url 形如: /th?id=OHR.NorwayNYD_ZH-CN7856439066_1920x1080.jpg&rf=LaDigue_1920x1080.jpg&pid=hp
    uhd_url = raw_url.replace("1920x1080.jpg", "UHD.jpg")
    thumb_url = raw_url.replace("1920x1080.jpg", "320x240.jpg")
    return f"https://www.bing.com{uhd_url}", f"https://www.bing.com{thumb_url}"

def download_file(url: str, dest: Path) -> bool:
    """下载文件到指定路径，成功返回 True"""
    if dest.exists():
        print(f"  [跳过] 已存在: {dest}")
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        print(f"  [完成] {dest}")
        return True
    except Exception as e:
        print(f"  [失败] {url} -> {e}")
        return False

# ========== 主流程 ==========
def main():
    # 读取 JSON
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建目录
    os.makedirs(UHD_DIR, exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

    # 按 enddate 倒序排序
    data.sort(key=lambda x: x["enddate"], reverse=True)

    md_lines = [
        # 20261006
        # "# Bing 每日壁纸（中国区） - {} 年 UHD 高清图\n".format(YEAR),
        f"# Bing 每日壁纸 - UHD 中文 - {YEAR}",
        "",
        f"> 最后更新：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        "| 日期 | 标题 | 版权 | 略缩图 | 高清图 |",
        "|------|------|------|--------|--------|",
    ]

    for item in data:
        enddate = item["enddate"]          # 如 "20230101"
        title = item["title"]
        copyright_text = item["copyright"]
        raw_url = item["url"]

        # YYYYMMDD
        date_str = enddate.replace("-", "")  # "20230101"

        # 文件名
        safe_title = sanitize_filename(title)
        uhd_filename = f"{date_str}_{safe_title}_UHD_cn.jpg"
        thumb_filename = f"{date_str}_320_cn.jpg"

        # 完整 URL
        uhd_url, thumb_url = build_urls(raw_url)

        # 下载
        download_file(uhd_url, Path(UHD_DIR) / uhd_filename)
        download_file(thumb_url, Path(THUMB_DIR) / thumb_filename)

        # Markdown 行
        thumb_md = f"{CDN_PREFIX}/bing-320-cn-{YEAR}/{thumb_filename}"
        uhd_md = f"[UHD]({uhd_url})"

        md_lines.append(
            f"| {enddate} | {title} | {copyright_text} | ![]({thumb_md}) | {uhd_md} |"
        )

    # 写入 Markdown
    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n✅ 全部完成！")
    print(f"   UHD 目录: {UHD_DIR}")
    print(f"   320 目录: {THUMB_DIR}")
    print(f"   Markdown: {MD_FILE}")

if __name__ == "__main__":
    main()
