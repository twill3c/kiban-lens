# -*- coding: utf-8 -*-
"""T-02: HTML フェッチャ(リンク採取・日付/タイトル抽出)— オフライン。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetchers import (  # noqa: E402
    extract_date, extract_title, fetch_company, fetch_html,
)

LISTING = """<html><body>
<a href="/news/post-one">One</a>
<a href="/news/post-two">Two</a>
<a href="/news/post-one">One again</a>
<a href="/assets/style.css">x</a>
</body></html>"""

ARTICLE = """<html><head>
<title>Post {n} | Example Site</title>
<meta property="article:published_time" content="2026-08-0{n}T10:00:00Z">
</head><body></body></html>"""


def fake_get_factory(listing=LISTING):
    def get(url, ua):
        if url.endswith("/list"):
            return listing.encode()
        n = url[-1] if url[-1].isdigit() else ("1" if "one" in url else "2")
        return ARTICLE.replace("{n}", n).encode()
    return get


CO = {"id": "t", "strategy": "html", "primary_url": "https://ex.com/list",
      "link_re": r'href="(/news/[a-z-]+)"'}


def test_fetch_html_harvest_dedupe():
    items = fetch_html(CO, fake_get_factory())
    assert [i["url"] for i in items] == ["https://ex.com/news/post-one", "https://ex.com/news/post-two"]
    assert items[0]["title"] == "Post 1"      # サイト名サフィックス除去
    assert items[0]["date"] == "2026-08-01"   # meta から抽出


def test_fetch_html_list_re_titles():
    listing = ('<a href="/news/a1">x</a><span class="t">見出しA</span>'
               '<a href="/news/a2">y</a><span class="t">見出しB</span>')
    co = dict(CO, list_re=r'href="(/news/[a-z0-9]+)">[^<]*</a><span class="t">([^<]+)<')
    items = fetch_html(co, fake_get_factory(listing))
    assert [i["title"] for i in items] == ["見出しA", "見出しB"]


def test_fetch_html_sort_desc_and_template_filter():
    listing = ('<a href="/news/news250101">a</a><a href="/news/news260101">b</a>')
    co = dict(CO, sort_desc=True, link_re=r'href="(/news/news[0-9]+)"')
    def get(url, ua):
        if url.endswith("/list"):
            return listing.encode()
        if "260101" in url:
            return b"<title>{{title}}</title>"  # テンプレート残骸 → 除外
        return b"<title>Real</title>"
    items = fetch_html(co, get)
    assert [i["title"] for i in items] == ["Real"]


def test_pending_returns_empty():
    assert fetch_company({"strategy": "pending"}, None) == []


def test_extract_date_variants():
    assert extract_date('"datePublished": "2026-05-01T00:00:00+09:00"') == "2026-05-01"
    assert extract_date('<time datetime="2026-06-02T12:00:00Z">') == "2026-06-02"
    assert extract_date("公開日: 2026年7月3日") == "2026-07-03"
    assert extract_date("no date here") == ""


def test_extract_date_english():
    # 機械可読な日付を持たないサイト(Meta AI 等)向けの英文日付
    assert extract_date("<span>July 9, 2026</span>") == "2026-07-09"
    assert extract_date("<span>9 July 2026</span>") == "2026-07-09"
    assert extract_date("<p>Jubilee 2026</p>") == ""  # 月名でない語は拾わない


def test_extract_title_variants():
    assert extract_title('<meta property="og:title" content="A &amp; B">') == "A & B"
    assert extract_title("<title>Hello – Site Name</title>") == "Hello"
    assert extract_title("<p>nothing</p>") == ""


def test_extract_title_skips_site_name():
    # og:title が全記事共通のサイト名になっているサイト(ELYZA 等)
    page = ('<meta property="og:title" content="ELYZA | 未踏の領域で、あたりまえを創る">'
            "<title>記事の見出し | 株式会社ELYZA</title>")
    assert extract_title(page, site_name="ELYZA") == "記事の見出し"
    assert extract_title(page) == "ELYZA"  # site_name 未指定なら従来どおり


def test_extract_title_falls_back_to_h1():
    page = '<meta property="og:title" content="SiteName"><h1>  実際の見出し  </h1>'
    assert extract_title(page, site_name="SiteName") == "実際の見出し"
