# -*- coding: utf-8 -*-
"""収集エントリポイント: python -m src.fetch

data/releases.json を更新 → 新出見出しを和訳(キャッシュ)→ out/index.html を再生成。
exit code: 全社失敗のみ 1(劣化継続で前回分は保持される)。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .fetchers import fetch_company
from .pipeline import collect
from .render import render_html
from .sources import COMPANIES
from .translate import translate_all

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "releases.json"
OUT = ROOT / "out" / "index.html"


def http_get(url: str, ua: str) -> bytes:
    time.sleep(0.5)  # 記事ページ連続取得の礼儀
    req = urllib.request.Request(
        url, headers={"User-Agent": ua, "Accept-Language": "ja,en"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    prev = None
    if DATA.exists():
        prev = json.loads(DATA.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data, code = collect(
        COMPANIES, lambda co: fetch_company(co, http_get), prev, now)

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")

    titles = [i["title"] for rec in data["companies"] for i in rec["items"]]
    translations = translate_all(titles)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_html(data, COMPANIES, translations),
                   encoding="utf-8", newline="\n")

    ok = sum(1 for c in data["companies"] if c["ok"])
    n_tr = sum(1 for t in set(titles) if t in translations)
    print(f"collect: {ok}/{len(data['companies'])} 社成功, 和訳 {n_tr} 件 → {DATA.name}, {OUT.name}")
    for c in data["companies"]:
        mark = "ok " if c["ok"] else "NG "
        print(f"  {mark}{c['id']}: {len(c['items'])} 件")
    return code


if __name__ == "__main__":
    sys.exit(main())
