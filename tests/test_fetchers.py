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


def test_extract_title_variants():
    assert extract_title('<meta property="og:title" content="A &amp; B">') == "A & B"
    assert extract_title("<title>Hello – Site Name</title>") == "Hello"
    assert extract_title("<p>nothing</p>") == ""
