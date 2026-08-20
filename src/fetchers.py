# -*- coding: utf-8 -*-
"""会社別の取得・抽出(F-01/F-02)。

fetch_company(company, get) -> [{"title","url","date"}...](新しい順・最大 5 件)
get(url, ua) -> bytes は注入可能(テストではフィクスチャ、実運用では http_get)。

- feed: フィードをパースして先頭 5 件
- html: 一覧 HTML から link_re でリンク採取 → 上位 5 件の記事ページを取得し、
  タイトル(og:title / <title>)と日付(extract_date)を抽出する統一方式
- pending: 常に空(pipeline 側で ok=False → 劣化継続 / 経路調査中表示)

失敗は例外にせず 0 件で返す(pipeline が前回分を保持する)。
"""

from __future__ import annotations

import html as html_mod
import json
import re

from .dates import normalize_date
from .feedparse import parse_feed
from .sources import BROWSER_UA, PROJECT_UA
from .urlutil import absolutize

MAX_ITEMS = 5

_DATE_PATTERNS = [
    re.compile(r'(?:property|name)="(?:article:published_time|og:article:published_time|publishdate|date)"\s+content="([^"]+)"'),
    re.compile(r'content="([^"]+)"\s+(?:property|name)="(?:article:published_time|publishdate|date)"'),
    re.compile(r'"datePublished"\s*:\s*"([^"]+)"'),
    re.compile(r'<time[^>]+datetime="([^"]+)"'),
    re.compile(r"(\d{4})[年/.\-](\d{1,2})[月/.\-](\d{1,2})"),
]
_TITLE_PATTERNS = [
    re.compile(r'property="og:title"\s+content="([^"]+)"'),
    re.compile(r'content="([^"]+)"\s+property="og:title"'),
    re.compile(r"<title[^>]*>([^<]+)</title>"),
]


def extract_date(page: str) -> str:
    for pat in _DATE_PATTERNS[:-1]:
        m = pat.search(page)
        if m:
            d = normalize_date(m.group(1))
            if d:
                return d
    m = _DATE_PATTERNS[-1].search(page)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        if 2000 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def extract_title(page: str) -> str:
    for pat in _TITLE_PATTERNS:
        m = pat.search(page)
        if m:
            t = html_mod.unescape(m.group(1)).strip()
            # サイト名サフィックスの除去(" | Site" / " - Site" / " – Site")
            t = re.split(r"\s+[|–—]\s+", t)[0].strip()
            if t:
                return t
    return ""


def _dedupe_keep_order(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_feed(company: dict, get) -> list[dict]:
    raw = get(company["primary_url"], PROJECT_UA)
    items = parse_feed(raw)[: MAX_ITEMS]
    return [{"title": i["title"], "url": i["url"], "date": i["date"]} for i in items]


def fetch_html(company: dict, get) -> list[dict]:
    base = company["primary_url"]
    ua = PROJECT_UA if company.get("ua") == "project" else BROWSER_UA
    listing = get(base, ua).decode("utf-8", "replace")
    list_titles: dict[str, str] = {}
    if "list_re" in company:
        # 2 グループ(href, title)。タイトルは一覧のアンカーテキストから取る
        pairs = re.findall(company["list_re"], listing, re.S)
        hrefs = []
        for h, t in pairs:
            hrefs.append(h)
            list_titles.setdefault(h, html_mod.unescape(t).strip())
    else:
        hrefs = re.findall(company["link_re"], listing)
    abs_map = {absolutize(base, h): h for h in _dedupe_keep_order(hrefs)}
    urls = [u for u in abs_map if u.rstrip("/") != base.rstrip("/")]
    if company.get("sort_desc"):
        urls = sorted(urls, reverse=True)
    items = []
    for url in urls[: MAX_ITEMS]:
        try:
            page = get(url, ua).decode("utf-8", "replace")
            title = list_titles.get(abs_map[url]) or extract_title(page)
            date = extract_date(page)
        except Exception:
            title, date = list_titles.get(abs_map[url], ""), ""
        if not title or "{{" in title:  # テンプレート残骸は除外
            continue
        items.append({"title": title, "url": url, "date": date})
    return items


def fetch_company(company: dict, get) -> list[dict]:
    if company["strategy"] == "feed":
        return fetch_feed(company, get)
    if company["strategy"] == "html":
        return fetch_html(company, get)
    return []  # pending


def json_dumps_stable(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False)
