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
  --muted:#9aa3b2;--faint:#6b7280;--accent:#7aa2f7;--us:#79c0ff;--cn:#f8a3a3;--jp:#7ee787;
  --time:#c4b5fd;--warnc:#f0b072}
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
.controls{position:sticky;top:0;z-index:10;background:rgba(15,17,21,.94);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);padding:11px 24px;margin-bottom:4px}
.controls-in{max-width:1400px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.chip{background:var(--panel2);border:1px solid var(--line);color:var(--muted);border-radius:999px;
  padding:5px 12px;font-size:12.5px;cursor:pointer;user-select:none;white-space:nowrap}
.chip:hover{color:var(--fg)}
.chip.c-all.on{background:var(--accent);border-color:var(--accent);color:#0f1115;font-weight:600}
.chip.c-us{color:var(--us);border-color:rgba(121,192,255,.45)}
.chip.c-cn{color:var(--cn);border-color:rgba(248,163,163,.45)}
.chip.c-jp{color:var(--jp);border-color:rgba(126,231,135,.45)}
.chip.c-time{color:var(--time);border-color:rgba(196,181,253,.45)}
.chip.c-us:hover{color:var(--us)}.chip.c-cn:hover{color:var(--cn)}
.chip.c-jp:hover{color:var(--jp)}.chip.c-time:hover{color:var(--time)}
.chip.c-us.on{background:var(--us);border-color:var(--us);color:#0f1115;font-weight:600}
.chip.c-cn.on{background:var(--cn);border-color:var(--cn);color:#0f1115;font-weight:600}
.chip.c-jp.on{background:var(--jp);border-color:var(--jp);color:#0f1115;font-weight:600}
.chip.c-time.on{background:var(--time);border-color:var(--time);color:#0f1115;font-weight:600}
.spacer{flex:1}
.bio{font-size:12.4px;color:#c9cfd9;margin:8px 0 2px;padding:8px 10px;background:var(--panel2);
  border-radius:7px;border-left:2px solid var(--line)}
.warn{font-size:11.5px;color:var(--warnc);margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}
.hidden{display:none}
.empty{color:var(--faint);font-size:13px;padding:20px 0}
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


def latest_date(record: dict) -> str:
    """カード内の最新日付(不明のみなら空)。フィルタの判定に使う。"""
    dates = [i["date"] for i in record["items"] if i["date"]]
    return max(dates) if dates else ""


HEALTH_LABEL = {
    "failing": "経路の点検対象 — ",
    "stale": "経路の点検対象 — ",
    "undated": "",
}


def _card_html(co: dict, record: dict, translations: dict, profile: str = "",
               health: dict | None = None) -> str:
    h = (f'<div class="card" data-region="{co["region"]}" '
         f'data-latest="{latest_date(record)}">'
         f'<div class="chead"><span class="name">{escape(co["name"])}</span>')
    h += f'<span class="badge b-{co["region"]}">{REGION_LABEL[co["region"]]}</span>'
    h += f'<a class="home" href="{escape(co["source_url"])}" target="_blank" rel="noopener">{escape(co["source_url"])}</a></div>'
    if profile:
        h += f'<div class="bio">{escape(profile)}</div>'
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
    if health and health["status"] in ("failing", "stale"):
        h += (f'<div class="warn">⚠ {HEALTH_LABEL[health["status"]]}'
              f'{escape(health["detail"])}</div>')
    return h + "</div>"


def render_html(data: dict, companies: list[dict], translations: dict,
                profiles: dict | None = None, health: dict | None = None) -> str:
    by_id = {c["id"]: c for c in companies}
    profiles = profiles or {}
    health_by_id = {h["id"]: h for h in (health or {}).get("companies", [])}
    generated = _jst(data["generated_at"])
    n_ok = sum(1 for r in data["companies"] if r["ok"])
    n_all = len(data["companies"])
    n_attention = sum(1 for h in health_by_id.values()
                      if h["status"] in ("failing", "stale"))
    attention = (f" · 経路の点検対象 {n_attention} 社" if n_attention else
                 " · 経路はすべて正常")

    body = ""
    for rid, rlabel in REGIONS:
        cards = ""
        for rec in data["companies"]:
            co = by_id[rec["id"]]
            if co["region"] != rid:
                continue
            cards += _card_html(co, rec, translations, profiles.get(co["id"], ""),
                                health_by_id.get(co["id"]))
        n = sum(1 for c in companies if c["region"] == rid)
        body += (f'<section data-section="{rid}">'
                 f'<div class="secthead">{rlabel}({n}社)</div>'
                 f'<div class="grid">{cards}</div></section>')

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
  <p class="updated">最終更新 {generated} JST(6 時間ごとに自動更新)· 取得成功 {n_ok}/{n_all} 社{attention}</p>
</header>
<div class="controls"><div class="controls-in">
  <span class="chip c-all on" data-region="ALL">すべての地域</span>
  <span class="chip c-us" data-region="us">米国のみ</span>
  <span class="chip c-cn" data-region="cn">中国のみ</span>
  <span class="chip c-jp" data-region="jp">日本のみ</span>
  <span class="spacer"></span>
  <span class="chip c-time" id="f1m">直近1ヶ月の発信がある組織</span>
  <span class="chip c-time" id="f1w">直近1週間の発信がある組織</span>
</div></div>
<main>{body}<div class="empty hidden" id="empty">該当する組織がありません</div></main>
<footer>
  <p><a href="https://github.com/twill3c/kiban-lens/blob/main/LICENSE" target="_blank" rel="noopener">MIT License</a> © 2026 坂田哲朗
  ・ <a href="https://github.com/twill3c/kiban-lens" target="_blank" rel="noopener">GitHub</a>
  ・ <a href="https://claude.ai/code/artifact/a54f70b8-6542-48a6-b13b-c3bb29829011" target="_blank" rel="noopener">kiban-lens の歩き方</a>
  ・ <a href="https://claude.ai/code/artifact/de6f4153-3e2a-4727-91af-77c881b36b60" target="_blank" rel="noopener">kiban-lens 設計図</a>
  ・ <a href="https://app-menu-amber.vercel.app" target="_blank" rel="noopener">App Menu</a></p>
</footer>
<script>
// 期間の基準は閲覧時点(ビルド時に焼き込まない)
const cutoff = days => new Date(Date.now() - days*864e5).toISOString().slice(0,10);
let curRegion = "ALL", only1m = false, only1w = false;

function render() {{
  const c1m = cutoff(30), c1w = cutoff(7);
  let shown = 0;
  for (const sec of document.querySelectorAll("[data-section]")) {{
    let visible = 0;
    for (const card of sec.querySelectorAll(".card")) {{
      const latest = card.dataset.latest;
      let ok = curRegion === "ALL" || card.dataset.region === curRegion;
      if (ok && only1m) ok = latest >= c1m;
      if (ok && only1w) ok = latest >= c1w;
      card.classList.toggle("hidden", !ok);
      if (ok) visible++;
    }}
    sec.classList.toggle("hidden", visible === 0);
    shown += visible;
  }}
  document.getElementById("empty").classList.toggle("hidden", shown > 0);
}}

document.querySelectorAll(".chip[data-region]").forEach(el => el.onclick = () => {{
  document.querySelectorAll(".chip[data-region]").forEach(x => x.classList.remove("on"));
  el.classList.add("on"); curRegion = el.dataset.region; render();
}});
document.getElementById("f1m").onclick = e => {{
  only1m = !only1m;
  if (only1m) {{ only1w = false; document.getElementById("f1w").classList.remove("on"); }}
  e.target.classList.toggle("on", only1m); render();
}};
document.getElementById("f1w").onclick = e => {{
  only1w = !only1w;
  if (only1w) {{ only1m = false; document.getElementById("f1m").classList.remove("on"); }}
  e.target.classList.toggle("on", only1w); render();
}};
render();
</script>
</body>
</html>
"""
