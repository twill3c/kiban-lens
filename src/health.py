# -*- coding: utf-8 -*-
"""経路の健全性チェック(F-09)。

取得失敗は劣化継続で受け止めるため、経路が死んでいても前回分が表示され続ける。
「気づかないまま古い内容を見せ続ける」ことを防ぐのがこのモジュールの役目。

判定(重い順):
- failing : 連続失敗が FAIL_STREAK_ALERT 回以上 → 経路が壊れた可能性が高い
- stale   : 取得は成功しているが最新記事が STALE_DAYS 日より古い → 一覧を
            拾えていない(ページ構造変更で古い記事だけ拾い続ける等)か、
            本当に発信が止まっている。どちらかは人間(月次 routine)が判断する
- undated : 取得できているが日付が 1 件も取れない → 鮮度が判断できない
- healthy : 上記以外

STALE_DAYS は「四半期に一度も発信がない基盤モデル企業は考えにくい」という
経験則。誤検知(本当に静かなだけ)は routine 側で見て判断する。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

FAIL_STREAK_ALERT = 4   # 6 時間 cron ×4 = 約 1 日連続で失敗
STALE_DAYS = 120

SEVERITY = {"failing": 0, "stale": 1, "undated": 2, "healthy": 3}


def _today(now: str) -> date:
    return datetime.strptime(now[:10], "%Y-%m-%d").date()


def latest_item_date(record: dict) -> str:
    dates = [i["date"] for i in record.get("items", []) if i.get("date")]
    return max(dates) if dates else ""


def classify(record: dict, now: str) -> dict:
    """1 社の健全性を判定して {id, status, detail, ...} を返す。"""
    fail_streak = record.get("fail_streak", 0)
    latest = latest_item_date(record)
    days = None
    if latest:
        days = (_today(now) - date.fromisoformat(latest[:10])).days

    if fail_streak >= FAIL_STREAK_ALERT:
        status = "failing"
        detail = f"{fail_streak} 回連続で取得に失敗(最後の成功: {record.get('last_ok_at', '')[:10] or '不明'})"
    elif not record.get("items"):
        status = "failing"
        detail = "一度も取得できていない"
    elif not latest:
        status = "undated"
        detail = "取得できているが日付が 1 件も取れない"
    elif days is not None and days >= STALE_DAYS:
        status = "stale"
        detail = f"最新記事が {days} 日前({latest})— 一覧を拾えていない可能性"
    else:
        status = "healthy"
        detail = f"最新記事 {latest}" if latest else "正常"

    return {"id": record["id"], "name": record.get("name", record["id"]),
            "status": status, "detail": detail, "fail_streak": fail_streak,
            "latest": latest, "days_since_latest": days,
            "source_url": record.get("source_url", "")}


def check(data: dict) -> dict:
    """収集結果全体の健全性レポートを返す。"""
    now = data["generated_at"]
    results = [classify(r, now) for r in data["companies"]]
    results.sort(key=lambda r: (SEVERITY[r["status"]], r["id"]))
    issues = [r for r in results if r["status"] != "healthy"]
    return {
        "generated_at": now,
        "healthy": len(results) - len(issues),
        "total": len(results),
        "thresholds": {"fail_streak_alert": FAIL_STREAK_ALERT, "stale_days": STALE_DAYS},
        "issues": issues,
        "companies": results,
    }


def format_report(report: dict) -> str:
    """人間・エージェント向けの 1 行 1 社レポート。"""
    lines = [f"経路健全性: 正常 {report['healthy']}/{report['total']} 社"]
    for r in report["issues"]:
        lines.append(f"  [{r['status']}] {r['name']}({r['id']}): {r['detail']} — {r['source_url']}")
    if not report["issues"]:
        lines.append("  要点検なし")
    return "\n".join(lines)
