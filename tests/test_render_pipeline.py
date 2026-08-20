# -*- coding: utf-8 -*-
"""T-04/T-05: 劣化継続パイプラインとレンダラ — オフライン。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import collect  # noqa: E402
from src.render import render_html  # noqa: E402
from src.sources import COMPANIES  # noqa: E402

ITEM = {"title": "Hello release", "url": "https://ex.com/1", "date": "2026-08-01"}


def fake_fetcher(ok_ids):
    def f(co):
        if co["id"] in ok_ids:
            return [ITEM]
        raise OSError("down")
    return f


def test_collect_degrades_to_prev():
    prev, _ = collect(COMPANIES, fake_fetcher({c["id"] for c in COMPANIES}), None, "2026-08-20T00:00:00Z")
    data, code = collect(COMPANIES, fake_fetcher({"openai"}), prev, "2026-08-21T00:00:00Z")
    assert code == 0
    rec = next(r for r in data["companies"] if r["id"] == "anthropic")
    assert rec["ok"] is False
    assert rec["items"] == [ITEM]                       # 前回分を保持
    assert rec["fetched_at"] == "2026-08-20T00:00:00Z"  # 取得時刻も前回のまま


def test_collect_all_fail_exit_1():
    _, code = collect(COMPANIES, fake_fetcher(set()), None, "2026-08-21T00:00:00Z")
    assert code == 1


def make_data():
    data, _ = collect(COMPANIES, fake_fetcher({c["id"] for c in COMPANIES}),
                      None, "2026-08-21T03:00:00Z")
    return data


def test_render_contains_all_companies_and_sections():
    html = render_html(make_data(), COMPANIES, {})
    for c in COMPANIES:
        assert c["name"] in html
    for label in ("米国(6社)", "中国(7社)", "日本(10社)"):
        assert label in html
    assert "最終更新 2026-08-21 12:00 JST" in html  # UTC03:00 → JST12:00


def test_render_translation_with_original():
    html = render_html(make_data(), COMPANIES, {"Hello release": "こんにちはリリース"})
    assert "こんにちはリリース" in html
    assert "原文: Hello release" in html


def test_render_failure_and_footer():
    # 一度も取得できていない会社は再試行の案内を出す(pending の場合は理由を表示)
    data, _ = collect(COMPANIES, fake_fetcher({"openai"}), None, "2026-08-21T03:00:00Z")
    html = render_html(data, COMPANIES, {})
    assert "取得できませんでした(次回自動再試行)" in html

    html = render_html(make_data(), COMPANIES, {})
    for needle in ("MIT License", "© 2026 坂田哲朗",
                   "https://github.com/twill3c/kiban-lens",
                   "kiban-lens の歩き方", "kiban-lens 設計図",
                   "https://app-menu-amber.vercel.app"):
        assert needle in html


def test_render_deterministic():
    data = make_data()
    assert render_html(data, COMPANIES, {}) == render_html(data, COMPANIES, {})


# ---- T-06: 説明文 / T-07: フィルタ ----

def test_profiles_cover_all_companies():
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parent.parent / "data" / "profiles.json")
                      .read_text(encoding="utf-8"))
    profiles = data["profiles"]
    ids = {c["id"] for c in COMPANIES}
    assert set(profiles) == ids, f"過不足: {set(profiles) ^ ids}"
    for cid, text in profiles.items():
        assert 20 <= len(text) <= 200, f"{cid}: {len(text)} 字"
    assert "updated_on" in data


def test_render_shows_profiles():
    import json
    from pathlib import Path
    profiles = json.loads((Path(__file__).resolve().parent.parent / "data" / "profiles.json")
                          .read_text(encoding="utf-8"))["profiles"]
    html = render_html(make_data(), COMPANIES, {}, profiles)
    assert 'class="bio"' in html
    assert profiles["openai"] in html
    # 説明文なしでも描画できる(劣化継続)
    assert 'class="bio"' not in render_html(make_data(), COMPANIES, {})


def test_render_filter_chips_and_metadata():
    html = render_html(make_data(), COMPANIES, {})
    for needle in ('data-region="ALL"', 'data-region="us"', 'data-region="cn"',
                   'data-region="jp"', 'id="f1m"', 'id="f1w"',
                   "米国のみ", "中国のみ", "日本のみ",
                   "直近1ヶ月の発信がある組織", "直近1週間の発信がある組織"):
        assert needle in html, needle
    # カードは地域と最新日付を持ち、セクションは地域で束ねられる
    assert 'class="card" data-region="us" data-latest="2026-08-01"' in html
    assert '<section data-section="jp">' in html
    # 期間の基準は閲覧時点(ビルド時に焼き込まない)
    assert "const cutoff = days =>" in html


def test_latest_date_helper():
    from src.render import latest_date
    assert latest_date({"items": [{"date": "2026-01-01"}, {"date": "2026-08-05"}]}) == "2026-08-05"
    assert latest_date({"items": [{"date": ""}, {"date": ""}]}) == ""
    assert latest_date({"items": []}) == ""


# ---- T-08: 健全性のページ表示 ----

def test_render_health_warnings():
    from src.health import FAIL_STREAK_ALERT, check
    data = make_data()
    # 1 社を長期未更新、1 社を連続失敗に見せかける
    for r in data["companies"]:
        if r["id"] == "qwen":
            r["items"] = [{"title": "old", "url": "https://ex.com/o", "date": "2026-01-01"}]
        if r["id"] == "baidu":
            r["fail_streak"] = FAIL_STREAK_ALERT
    report = check(data)
    html = render_html(data, COMPANIES, {}, {}, report)
    assert "経路の点検対象 2 社" in html
    assert html.count('class="warn"') == 2
    assert "回連続で取得に失敗" in html

    # 全社正常ならヘッダーは「すべて正常」、警告は出ない
    clean = render_html(make_data(), COMPANIES, {}, {}, check(make_data()))
    assert "経路はすべて正常" in clean
    assert 'class="warn"' not in clean


def test_render_without_health_is_backward_compatible():
    html = render_html(make_data(), COMPANIES, {})
    assert 'class="warn"' not in html
