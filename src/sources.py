# -*- coding: utf-8 -*-
"""AI 基盤モデル 23 社の取得経路の宣言的定義(F-01)。

strategy:
- feed: primary_url が RSS/Atom/RDF フィード
- html: primary_url の静的 HTML 一覧から link_re でリンク採取 →
        各記事ページから日付抽出(fetchers.extract_date)
- pending: 取得経路が未確立(JS レンダリング必須・DNS 不達等)。
  collect では常に失敗扱い → カードに「経路調査中」を表示

調査経緯(2026-08-20 loop_001):
- OpenAI/DeepMind/Microsoft/Sakana は公式フィードあり。Meta AI 公式ブログの
  RSS は廃止済み(ai.meta.com/blog/rss/ が 404)→ 静的 HTML 解析
- Qwen のブログは qwen.ai へ移転済みだが JS レンダリング必須。旧 GitHub Pages
  のフィード(qwenlm.github.io)は実在の公式ブログだが更新が遅延する可能性
- Baidu は research.baidu.com が JS シェルのため公式コーポレートニュース
  (home.baidu.com)を、Tencent は hunyuan.tencent.com が JS シェルのため
  公式ニュースルーム(tencent.com/zh-cn/media)を使用
- Moonshot AI は全ページ SPA、rinna は当環境から DNS 不達 → pending
- 富士通/ABEJA は koho-lens で実証済みの公式 PR TIMES アカウント RDF
"""

PROJECT_UA = "kiban-lens/1.0 (+https://github.com/twill3c/kiban-lens)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

REGIONS = [("us", "米国"), ("cn", "中国"), ("jp", "日本")]

COMPANIES = [
    # ---- 米国 6 ----
    {"id": "openai", "name": "OpenAI", "region": "us",
     "source_url": "https://openai.com/news/",
     "primary_url": "https://openai.com/news/rss.xml", "strategy": "feed"},
    {"id": "anthropic", "name": "Anthropic", "region": "us",
     "source_url": "https://www.anthropic.com/news",
     "primary_url": "https://www.anthropic.com/news", "strategy": "html",
     "link_re": r'href="(/news/[a-z0-9-]+)"'},
    {"id": "deepmind", "name": "Google DeepMind", "region": "us",
     "source_url": "https://deepmind.google/blog/",
     "primary_url": "https://deepmind.google/blog/rss.xml", "strategy": "feed"},
    {"id": "meta", "name": "Meta AI", "region": "us",
     "source_url": "https://ai.meta.com/blog/",
     "primary_url": "https://ai.meta.com/blog/", "strategy": "html", "ua": "project",
     "link_re": r'href="(https://ai\.meta\.com/blog/[a-z0-9-]+/)"'},
    {"id": "xai", "name": "xAI", "region": "us",
     "source_url": "https://x.ai/news",
     "primary_url": "https://x.ai/news", "strategy": "html",
     "link_re": r'href="(/news/[a-z0-9-]+)"'},
    {"id": "microsoft", "name": "Microsoft", "region": "us",
     "source_url": "https://news.microsoft.com/source/topics/ai/",
     "primary_url": "https://news.microsoft.com/source/topics/ai/feed/", "strategy": "feed"},
    # ---- 中国 7 ----
    {"id": "deepseek", "name": "DeepSeek", "region": "cn",
     "source_url": "https://api-docs.deepseek.com/news/",
     "primary_url": "https://api-docs.deepseek.com/sitemap.xml", "strategy": "html",
     "link_re": r"<loc>(https://api-docs\.deepseek\.com/news/news[0-9]+)</loc>", "sort_desc": True},
    {"id": "qwen", "name": "Alibaba(Qwen)", "region": "cn",
     "source_url": "https://qwen.ai/blog",
     "primary_url": "https://qwenlm.github.io/blog/index.xml", "strategy": "feed",
     "note": "公式ブログは qwen.ai へ移転済み(JS 必須)。旧公式フィードのため新着が遅延する可能性"},
    {"id": "moonshot", "name": "Moonshot AI(Kimi)", "region": "cn",
     "source_url": "https://www.moonshot.ai/",
     "primary_url": "", "strategy": "pending",
     "note": "全ページ JS レンダリング必須のため取得経路調査中"},
    {"id": "zhipu", "name": "Zhipu AI(GLM)", "region": "cn",
     "source_url": "https://www.zhipuai.cn/news",
     "primary_url": "", "strategy": "pending",
     "note": "ニュース一覧が JS レンダリング必須のため取得経路調査中"},
    {"id": "bytedance", "name": "ByteDance Seed(豆包)", "region": "cn",
     "source_url": "https://seed.bytedance.com/en/blog",
     "primary_url": "", "strategy": "pending",
     "note": "ブログ一覧が JS レンダリング必須のため取得経路調査中"},
    {"id": "baidu", "name": "Baidu(ERNIE)", "region": "cn",
     "source_url": "https://home.baidu.com/home/index/news_list",
     "primary_url": "https://home.baidu.com/home/index/news_list", "strategy": "html",
     "list_re": r'href="((?:https?://home\.baidu\.com)?/home/index/news_detail[^"]*)"[^>]*>.*?news-item-con">([^<]+)<',
     "note": "AI 研究ブログ(research.baidu.com)は JS 必須のため公式コーポレートニュースを表示"},
    {"id": "tencent", "name": "Tencent(混元)", "region": "cn",
     "source_url": "https://www.tencent.com/zh-cn/media/news.html",
     "primary_url": "", "strategy": "pending",
     "note": "混元公式・ニュースルームとも JS レンダリング必須のため取得経路調査中"},
    # ---- 日本 10 ----
    {"id": "sbintuitions", "name": "SB Intuitions", "region": "jp",
     "source_url": "https://www.sbintuitions.co.jp/news/",
     "primary_url": "https://note.com/sb_intuitions/rss", "strategy": "feed",
     "note": "公式サイトのニュース一覧は JS レンダリング必須のため公式 note の RSS を使用"},
    {"id": "ntt", "name": "NTT(tsuzumi)", "region": "jp",
     "source_url": "https://group.ntt/jp/newsrelease/",
     "primary_url": "https://group.ntt/jp/newsrelease/", "strategy": "html",
     "link_re": r'href="(/jp/newsrelease/2[0-9]{3}/[^"]+\.html)"'},
    {"id": "pfn", "name": "Preferred Networks(PLaMo)", "region": "jp",
     "source_url": "https://www.preferred.jp/ja/news/",
     "primary_url": "https://www.preferred.jp/ja/news/", "strategy": "html",
     "link_re": r'href="(?:https://www\.preferred\.jp)?(/ja/news/pr[0-9]+/?)"'},
    {"id": "sakana", "name": "Sakana AI", "region": "jp",
     "source_url": "https://sakana.ai/blog/",
     "primary_url": "https://sakana.ai/feed.xml", "strategy": "feed"},
    {"id": "elyza", "name": "ELYZA", "region": "jp",
     "source_url": "https://elyza.ai/news",
     "primary_url": "https://elyza.ai/news", "strategy": "html",
     "link_re": r'href="(/news/2[0-9]{3}/[^"]+)"'},
    {"id": "rinna", "name": "rinna", "region": "jp",
     "source_url": "https://rinna.co.jp/news/",
     "primary_url": "", "strategy": "pending",
     "note": "rinna.co.jp が収集環境から DNS 不達のため取得経路調査中"},
    {"id": "cyberagent", "name": "CyberAgent(CALM)", "region": "jp",
     "source_url": "https://www.cyberagent.co.jp/news/",
     "primary_url": "https://www.cyberagent.co.jp/news/", "strategy": "html",
     "link_re": r'href="(https://www\.cyberagent\.co\.jp/news/detail/id=[0-9]+)"'},
    {"id": "stockmark", "name": "Stockmark", "region": "jp",
     "source_url": "https://stockmark.co.jp/news",
     "primary_url": "https://stockmark.co.jp/news", "strategy": "html",
     "link_re": r'href="(https://stockmark\.co\.jp/news/[0-9]+/?)"'},
    {"id": "abeja", "name": "ABEJA", "region": "jp",
     "source_url": "https://www.abejainc.com/news",
     "primary_url": "https://prtimes.jp/companyrdf.php?company_id=10628", "strategy": "feed"},
    {"id": "fujitsu", "name": "富士通(Takane)", "region": "jp",
     "source_url": "https://global.fujitsu/ja-jp/pr/news",
     "primary_url": "https://prtimes.jp/companyrdf.php?company_id=93942", "strategy": "feed"},
]
