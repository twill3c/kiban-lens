# -*- coding: utf-8 -*-
"""会社別の取得・抽出(F-01/F-02)。

fetch_company(company, get) -> [{"title","url","date"}...](新しい順・最大 5 件)
get(url, ua) -> bytes は注入可能(テストではフィクスチャ、実運用では http_get)。

- feed: フィードをパースして先頭 5 件
- html: 一覧 HTML から link_re/list_re でリンク採取 → 記事ページを取得し、
  タイトル(list_re / title_re / og:title / <title> / <h1>)と日付を抽出する統一方式
- browser: JS レンダリング必須サイト。一覧を Playwright で描画してから html と同じ抽出
- pending: 常に空(pipeline 側で ok=False → 劣化継続)

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

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
# 英文日付("July 9, 2026" / "9 July 2026")— 機械可読な日付を持たないサイト向け(Meta AI 等)
_MONTH_ALT = "|".join(m.capitalize() for m in _MONTHS)
_EN_DATE_MDY = re.compile(rf"\b({_MONTH_ALT})\s+(\d{{1,2}}),\s*(\d{{4}})\b")
_EN_DATE_DMY = re.compile(rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\s+(\d{{4}})\b")

_BAD_TITLE_RE = re.compile(r"(404|403|500|not found|page not found|页面不存在|お探しのページ.*)", re.I)

_TITLE_PATTERNS = [
    re.compile(r'property="og:title"\s+content="([^"]+)"'),
    re.compile(r'content="([^"]+)"\s+property="og:title"'),
    re.compile(r"<title[^>]*>([^<]+)</title>"),
    re.compile(r"<h1[^>]*>\s*([^<]{4,160}?)\s*</h1>"),
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
    m = _EN_DATE_MDY.search(page)
    if m:
        mo, d, y = _MONTHS[m.group(1).lower()], int(m.group(2)), int(m.group(3))
        if 2000 <= y <= 2100 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    m = _EN_DATE_DMY.search(page)
    if m:
        d, mo, y = int(m.group(1)), _MONTHS[m.group(2).lower()], int(m.group(3))
        if 2000 <= y <= 2100 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def extract_title(page: str, site_name: str = "") -> str:
    """記事タイトルを抽出する。

    og:title がサイト共通名(全記事で同じ)になっているサイトがあるため、
    site_name と一致する候補は捨てて次の候補(<title> / <h1>)に進む。"""
    for pat in _TITLE_PATTERNS:
        m = pat.search(page)
        if not m:
            continue
        t = html_mod.unescape(m.group(1)).strip()
        # サイト名サフィックスの除去(" | Site" / " - Site" / " – Site")
        t = re.split(r"\s+[|–—]\s+", t)[0].strip()
        if not t:
            continue
        if site_name and t.strip().casefold() == site_name.strip().casefold():
            continue  # サイト共通名 — 記事タイトルではない
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


def render_page(url: str, ua: str = BROWSER_UA, wait_ms: int = 4000,
                attempts: int = 3) -> bytes:
    """JS 描画後の HTML を返す(browser 戦略)。

    描画対象は海外サイトで揺らぎが大きいため、タイムアウトを伸ばしつつ 3 回試す。
    Playwright 未導入・全試行失敗時は例外を上げ、pipeline が劣化継続で受け止める。
    実取得は CI(collect.yml が Chromium を導入)で行う。"""
    from playwright.sync_api import sync_playwright

    last = None
    for i in range(attempts):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(args=["--no-sandbox"])
                try:
                    page = browser.new_page(user_agent=ua, locale="ja-JP")
                    # networkidle は常時通信のあるサイト(中国系に多い)で成立しないため
                    # DOM 構築完了で待ち、以後は固定待機でハイドレーションを待つ
                    page.goto(url, wait_until="domcontentloaded",
                              timeout=45000 + 30000 * i)
                    page.wait_for_timeout(wait_ms + 2000 * i)
                    return page.content().encode("utf-8")
                finally:
                    browser.close()
        except Exception as e:  # 次の試行へ(最後の例外は呼び出し側へ)
            last = e
    raise last


def fetch_html(company: dict, get) -> list[dict]:
    base = company["primary_url"]
    ua = PROJECT_UA if company.get("ua") == "project" else BROWSER_UA
    if company["strategy"] == "browser":
        listing = render_page(base, ua).decode("utf-8", "replace")
    else:
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
    # 除外(エラーページ・タイトル取得失敗)を見込んで多めに当たり、MAX_ITEMS で打ち切る
    for url in urls[: MAX_ITEMS * 2]:
        if len(items) >= MAX_ITEMS:
            break
        try:
            page = get(url, ua).decode("utf-8", "replace")
            title = list_titles.get(abs_map[url]) or ""
            if not title and company.get("title_re"):
                # og:title がサイト共通名のサイト向けに、記事ページ内の位置を明示指定
                m = re.search(company["title_re"], page)
                if m:
                    title = html_mod.unescape(m.group(1)).strip()
            if not title:
                title = extract_title(page, company.get("name", ""))
            date = extract_date(page)
        except Exception:
            title, date = list_titles.get(abs_map[url], ""), ""
        # テンプレート残骸・エラーページ・空タイトルは除外
        if not title or "{{" in title or _BAD_TITLE_RE.fullmatch(title.strip()):
            continue
        items.append({"title": title, "url": url, "date": date})
    return items


def fetch_company(company: dict, get) -> list[dict]:
    if company["strategy"] == "feed":
        return fetch_feed(company, get)
    if company["strategy"] in ("html", "browser"):
        return fetch_html(company, get)
    return []  # pending


def json_dumps_stable(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False)
