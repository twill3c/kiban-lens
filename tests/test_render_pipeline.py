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
    data, _ = collect(COMPANIES, fake_fetcher({c["id"] for c in COMPANIES if c["strategy"] != "pending"}),
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


def test_render_pending_note_and_footer():
    html = render_html(make_data(), COMPANIES, {})
    assert "取得経路調査中" in html
    for needle in ("MIT License", "© 2026 坂田哲朗",
                   "https://github.com/twill3c/kiban-lens",
                   "https://app-menu-amber.vercel.app"):
        assert needle in html


def test_render_deterministic():
    data = make_data()
    assert render_html(data, COMPANIES, {}) == render_html(data, COMPANIES, {})
