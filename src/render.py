# -*- coding: utf-8 -*-
"""静的ページ生成(F-04)。data(collect 結果+翻訳)→ out/index.html。

決定論: 出力は入力 JSON のみで決まる(時刻は generated_at 由来、乱数なし)。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape

from .sources import REGIONS

REGION_LABEL = dict(REGIONS)

CSS = """
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1d212a;--line:#2a2f3a;--fg:#e6e8ec;
  --muted:#9aa3b2;--faint:#6b7280;--accent:#7aa2f7;--us:#79c0ff;--cn:#f8a3a3;--jp:#7ee787}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);line-height:1.65;
  font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP","Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:inherit}
header{padding:30px 24px 14px;max-width:1400px;margin:0 auto}
h1{font-size:22px;margin:0 0 6px}
.sub{color:var(--muted);font-size:13.5px;margin:0}
.updated{color:var(--faint);font-size:12.5px;margin-top:8px}
main{max-width:1400px;margin:0 auto;padding:8px 24px 40px}
.secthead{margin:22px 0 10px;font-size:14px;color:var(--muted);border-bottom:1px solid var(--line);
  padding-bottom:6px;letter-spacing:.05em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:14px;align-items:start}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px 12px}
.chead{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.name{font-size:15.5px;font-weight:650}
.badge{font-size:10px;padding:0 6px;border-radius:3px;font-weight:600}
.b-us{background:rgba(121,192,255,.14);color:var(--us)}
.b-cn{background:rgba(248,163,163,.14);color:var(--cn)}
.b-jp{background:rgba(126,231,135,.14);color:var(--jp)}
.home{font-size:11px;color:var(--faint);text-decoration:none;word-break:break-all}
.home:hover{color:var(--accent)}
ol{list-style:none;margin:8px 0 0;padding:0}
li{padding:7px 0;border-top:1px solid var(--line)}
.date{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums;margin-right:7px}
.date.unk{color:var(--faint)}
.title{font-size:13px;text-decoration:none}
.title:hover{color:var(--accent);text-decoration:underline}
.orig{font-size:11px;color:var(--faint);margin-top:1px;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.stale{font-size:11.5px;color:var(--faint);margin-top:6px}
.none{font-size:12.5px;color:var(--faint);padding:8px 0 4px}
footer{max-width:1400px;margin:0 auto;padding:10px 24px 40px;color:var(--faint);font-size:12px;
  border-top:1px solid var(--line)}
@media(max-width:640px){.grid{grid-template-columns:1fr}header,main{padding-left:16px;padding-right:16px}}
"""


def _jst(iso: str) -> str:
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")


def _item_html(item: dict, translations: dict) -> str:
    title = item["title"]
    ja = translations.get(title)
    date = item["date"] or "不明"
    unk = ' class="date unk"' if not item["date"] else ' class="date"'
    h = f"<li><span{unk}>{escape(date)}</span>"
    h += f'<a class="title" href="{escape(item["url"])}" target="_blank" rel="noopener">{escape(ja or title)}</a>'
    if ja:
        h += f'<div class="orig" title="{escape(title)}">原文: {escape(title)}</div>'
    return h + "</li>"


def _card_html(co: dict, record: dict, translations: dict) -> str:
    h = f'<div class="card"><div class="chead"><span class="name">{escape(co["name"])}</span>'
    h += f'<span class="badge b-{co["region"]}">{REGION_LABEL[co["region"]]}</span>'
    h += f'<a class="home" href="{escape(co["source_url"])}" target="_blank" rel="noopener">{escape(co["source_url"])}</a></div>'
    if record["items"]:
        h += "<ol>" + "".join(_item_html(i, translations) for i in record["items"]) + "</ol>"
        if not record["ok"]:
            h += (f'<div class="stale">最新取得に失敗 — '
                  f'{escape(_jst(record["fetched_at"]))} JST 時点の内容</div>')
    elif co["strategy"] == "pending":
        h += f'<div class="none">取得経路調査中 — {escape(co.get("note", ""))}</div>'
    else:
        h += '<div class="none">取得できませんでした(次回自動再試行)</div>'
    if co.get("note") and co["strategy"] != "pending":
        h += f'<div class="stale">{escape(co["note"])}</div>'
    return h + "</div>"


def render_html(data: dict, companies: list[dict], translations: dict) -> str:
    by_id = {c["id"]: c for c in companies}
    generated = _jst(data["generated_at"])
    n_ok = sum(1 for r in data["companies"] if r["ok"])
    n_all = len(data["companies"])

    body = ""
    for rid, rlabel in REGIONS:
        cards = ""
        for rec in data["companies"]:
            co = by_id[rec["id"]]
            if co["region"] != rid:
                continue
            cards += _card_html(co, rec, translations)
        n = sum(1 for c in companies if c["region"] == rid)
        body += f'<div class="secthead">{rlabel}({n}社)</div><div class="grid">{cards}</div>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI基盤モデル企業 公式ブログレンズ</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>AI基盤モデル企業 公式ブログレンズ — 基盤レンズ</h1>
  <p class="sub">AI 基盤モデルを提供する米国 6・中国 7・日本 10 の計 {n_all} 社について、公式ブログ / ニュースの最新 5 件を和訳付きで一覧。英語・中国語の見出しは Claude(Haiku)が和訳し、原文を併記します。</p>
  <p class="updated">最終更新 {generated} JST(6 時間ごとに自動更新)· 取得成功 {n_ok}/{n_all} 社 · 取得失敗時は前回分を保持</p>
</header>
<main>{body}</main>
<footer>
  <p><a href="https://github.com/twill3c/kiban-lens/blob/main/LICENSE" target="_blank" rel="noopener">MIT License</a> © 2026 坂田哲朗
  ・ <a href="https://github.com/twill3c/kiban-lens" target="_blank" rel="noopener">GitHub</a>
  ・ <a href="https://app-menu-amber.vercel.app" target="_blank" rel="noopener">App Menu</a></p>
</footer>
</body>
</html>
"""
