"""収集パイプライン(T-04)。

collect(companies, fetcher, prev, now) -> (data, exit_code)

- fetcher(company) -> list[items]。例外 or 0 件は「失敗」: ok=False とし、
  prev に同 id があればその items / fetched_at を引き継ぐ(グレースフル劣化 F-02)
- 成功時は items を最新 5 件に切り詰め fetched_at=now
- 健全性の材料として fail_streak(連続失敗回数)と last_ok_at(最後に取得できた
  時刻)を記録する。経路が死んでいても前回分を表示し続けるため、これが無いと
  「生きているのか死んでいるのか」を後から判別できない(F-09)
- exit_code: 全社失敗のみ 1
"""

from __future__ import annotations

MAX_ITEMS = 5


def _prev_company(prev: dict | None, cid: str) -> dict | None:
    if not prev:
        return None
    return next((c for c in prev.get("companies", []) if c["id"] == cid), None)


def collect(companies, fetcher, prev, now):
    out = []
    ok_count = 0
    for co in companies:
        old = _prev_company(prev, co["id"])
        record = {
            "id": co["id"],
            "name": co["name"],
            "source_url": co["source_url"],
            "fetched_at": now,
            "ok": False,
            "fail_streak": 0,
            "last_ok_at": (old or {}).get("last_ok_at", ""),
            "items": [],
        }
        try:
            items = fetcher(co)
        except Exception:
            items = []
        if items:
            record["ok"] = True
            record["items"] = list(items)[:MAX_ITEMS]
            record["last_ok_at"] = now
            ok_count += 1
        else:
            record["fail_streak"] = (old or {}).get("fail_streak", 0) + 1
            if old:
                record["items"] = old["items"]
                record["fetched_at"] = old["fetched_at"]
        out.append(record)
    data = {"generated_at": now, "companies": out}
    return data, (0 if ok_count > 0 else 1)
