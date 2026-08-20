# -*- coding: utf-8 -*-
"""23 社の候補エンドポイント一斉調査(loop_001 の経路調査)。

各候補 URL を取得し、フィードとして解釈できるか / HTML なら記事リンクらしき
ものが拾えるかを判定して結果を出力する。sources.py 確定のための一回性ツール。"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.feedparse import parse_feed  # noqa: E402

UA = "kiban-lens/1.0 (+https://github.com/twill3c/kiban-lens)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

CANDIDATES = {
    # 米国 6
    "openai": ["https://openai.com/news/rss.xml"],
    "anthropic": ["https://www.anthropic.com/news", "https://www.anthropic.com/rss.xml"],
    "deepmind": ["https://deepmind.google/blog/rss.xml", "https://blog.google/technology/google-deepmind/rss/"],
    "meta": ["https://ai.meta.com/blog/rss/", "https://about.fb.com/news/category/technology-and-innovation/feed/"],
    "xai": ["https://x.ai/news", "https://x.ai/rss.xml", "https://x.ai/feed.xml"],
    "microsoft": ["https://blogs.microsoft.com/ai/feed/", "https://news.microsoft.com/source/topics/ai/feed/",
                  "https://azure.microsoft.com/en-us/blog/feed/"],
    # 中国 7
    "deepseek": ["https://api-docs.deepseek.com/news/", "https://api-docs.deepseek.com/sitemap.xml"],
    "qwen": ["https://qwenlm.github.io/blog/index.xml", "https://qwenlm.github.io/index.xml", "https://qwen.ai/blog"],
    "moonshot": ["https://platform.moonshot.ai/blog", "https://www.moonshot.ai/", "https://kimi.moonshot.cn/"],
    "zhipu": ["https://z.ai/blog", "https://www.zhipuai.cn/news"],
    "bytedance_seed": ["https://seed.bytedance.com/en/blog", "https://seed.bytedance.com/zh/blog"],
    "baidu": ["http://research.baidu.com/Blog", "https://research.baidu.com/Blog"],
    "tencent": ["https://hunyuan.tencent.com/", "https://www.tencent.com/ja-jp/media.html"],
    # 日本 10
    "sbintuitions": ["https://www.sbintuitions.co.jp/news/feed/", "https://www.sbintuitions.co.jp/feed/",
                     "https://www.sbintuitions.co.jp/news/"],
    "ntt": ["https://group.ntt/jp/rss/news.xml", "https://group.ntt/jp/newsrelease/rss.xml", "https://group.ntt/jp/newsrelease/"],
    "pfn": ["https://www.preferred.jp/ja/news/feed/", "https://www.preferred.jp/ja/feed/", "https://www.preferred.jp/ja/news/"],
    "sakana": ["https://sakana.ai/feed.xml"],
    "elyza": ["https://elyza.ai/feed", "https://note.com/elyza_inc/rss", "https://elyza.ai/news"],
    "rinna": ["https://rinna.co.jp/feed", "https://rinna.co.jp/news/", "https://prtimes.jp/companyrdf.php?company_id=70041"],
    "cyberagent": ["https://www.cyberagent.co.jp/news/rss/", "https://www.cyberagent.co.jp/feed/", "https://www.cyberagent.co.jp/news/"],
    "stockmark": ["https://stockmark.co.jp/feed", "https://stockmark.co.jp/news", "https://note.com/stockmark_news/rss"],
    "abeja": ["https://www.abejainc.com/rss", "https://www.abejainc.com/news", "https://prtimes.jp/companyrdf.php?company_id=10628"],
    "fujitsu": ["https://prtimes.jp/companyrdf.php?company_id=93942"],
}


def get(url, ua=UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "ja,en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def sniff_html(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    n_links = text.count("<a ")
    js_markers = sum(text.count(m) for m in ("__NEXT_DATA__", "window.__NUXT__", "id=\"root\"></div>", "id=\"app\"></div>"))
    return f"HTML {len(raw)}B links={n_links} js_markers={js_markers}"


def main():
    for cid, urls in CANDIDATES.items():
        for url in urls:
            for ua in (UA, BROWSER_UA):
                try:
                    raw = get(url, ua)
                except Exception as e:
                    tag = f"ERR {type(e).__name__} {e}"
                    if ua == BROWSER_UA:
                        print(f"  {cid}: {url} [browser] {tag[:80]}")
                    else:
                        print(f"  {cid}: {url} {tag[:80]}")
                        continue  # try browser UA
                    break
                try:
                    items = parse_feed(raw)
                    print(f"  {cid}: {url} {'[browser] ' if ua == BROWSER_UA else ''}FEED {len(items)} 件 例: {items[0]['title'][:40]!r} d={items[0]['date']!r}")
                except Exception:
                    print(f"  {cid}: {url} {'[browser] ' if ua == BROWSER_UA else ''}{sniff_html(raw)}")
                break


if __name__ == "__main__":
    main()
