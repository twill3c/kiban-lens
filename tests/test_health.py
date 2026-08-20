# -*- coding: utf-8 -*-
"""T-08: 経路健全性チェック — オフライン。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.health import (  # noqa: E402
    FAIL_STREAK_ALERT, STALE_DAYS, check, classify, format_report, latest_item_date,
)
from src.pipeline import collect  # noqa: E402
from src.sources import COMPANIES  # noqa: E402

NOW = "2026-08-21T00:00:00Z"


def rec(cid="x", items=None, fail_streak=0, last_ok_at="2026-08-21T00:00:00Z"):
    return {"id": cid, "name": cid, "source_url": "https://ex.com",
            "items": items if items is not None else [{"date": "2026-08-20", "title": "t"}],
            "fail_streak": fail_streak, "last_ok_at": last_ok_at}


def test_healthy():
    r = classify(rec(), NOW)
    assert r["status"] == "healthy"
    assert r["latest"] == "2026-08-20"
    assert r["days_since_latest"] == 1


def test_failing_on_streak():
    r = classify(rec(fail_streak=FAIL_STREAK_ALERT), NOW)
    assert r["status"] == "failing"
    assert str(FAIL_STREAK_ALERT) in r["detail"]
    # 閾値未満は healthy(一時的な失敗で騒がない)
    assert classify(rec(fail_streak=FAIL_STREAK_ALERT - 1), NOW)["status"] == "healthy"


def test_failing_when_never_fetched():
    assert classify(rec(items=[]), NOW)["status"] == "failing"


def test_stale_when_latest_is_old():
    old = "2026-01-01"  # NOW から 232 日前
    r = classify(rec(items=[{"date": old, "title": "t"}]), NOW)
    assert r["status"] == "stale"
    assert str(r["days_since_latest"]) in r["detail"]
    # 閾値の内側なら healthy
    fresh = classify(rec(items=[{"date": "2026-06-01", "title": "t"}]), NOW)
    assert fresh["days_since_latest"] < STALE_DAYS
    assert fresh["status"] == "healthy"


def test_undated():
    r = classify(rec(items=[{"date": "", "title": "t"}]), NOW)
    assert r["status"] == "undated"


def test_latest_item_date_helper():
    assert latest_item_date({"items": [{"date": "2026-01-01"}, {"date": "2026-05-05"}]}) == "2026-05-05"
    assert latest_item_date({"items": [{"date": ""}]}) == ""
    assert latest_item_date({}) == ""


def test_check_sorts_by_severity_and_counts():
    data = {"generated_at": NOW, "companies": [
        rec("ok1"),
        rec("stale1", items=[{"date": "2026-01-01", "title": "t"}]),
        rec("fail1", fail_streak=FAIL_STREAK_ALERT),
        rec("undated1", items=[{"date": "", "title": "t"}]),
    ]}
    report = check(data)
    assert report["total"] == 4 and report["healthy"] == 1
    assert [i["id"] for i in report["issues"]] == ["fail1", "stale1", "undated1"]
    assert report["thresholds"]["stale_days"] == STALE_DAYS
    text = format_report(report)
    assert "正常 1/4" in text and "[failing] fail1" in text


def test_format_report_when_all_healthy():
    report = check({"generated_at": NOW, "companies": [rec("ok1")]})
    assert "要点検なし" in format_report(report)


# ---- pipeline が健全性の材料を記録する ----

def failing_fetcher(co):
    raise OSError("down")


def test_pipeline_tracks_fail_streak_and_last_ok():
    ok_all = collect(COMPANIES, lambda co: [{"date": "2026-08-20", "title": "t", "url": "u"}],
                     None, "2026-08-20T00:00:00Z")[0]
    rec_ok = next(r for r in ok_all["companies"] if r["id"] == "openai")
    assert rec_ok["fail_streak"] == 0 and rec_ok["last_ok_at"] == "2026-08-20T00:00:00Z"

    d1 = collect(COMPANIES, failing_fetcher, ok_all, "2026-08-21T00:00:00Z")[0]
    d2 = collect(COMPANIES, failing_fetcher, d1, "2026-08-21T06:00:00Z")[0]
    r = next(x for x in d2["companies"] if x["id"] == "openai")
    assert r["fail_streak"] == 2                          # 連続失敗を数える
    assert r["last_ok_at"] == "2026-08-20T00:00:00Z"      # 最後の成功時刻は保持
    assert r["items"]                                     # 前回分は保持(劣化継続)


def test_pipeline_resets_streak_on_success():
    d1 = collect(COMPANIES, failing_fetcher, None, "2026-08-21T00:00:00Z")[0]
    d2 = collect(COMPANIES, lambda co: [{"date": "2026-08-21", "title": "t", "url": "u"}],
                 d1, "2026-08-21T06:00:00Z")[0]
    r = next(x for x in d2["companies"] if x["id"] == "openai")
    assert r["fail_streak"] == 0 and r["last_ok_at"] == "2026-08-21T06:00:00Z"
