# -*- coding: utf-8 -*-
"""T-03: 翻訳キャッシュと劣化継続 — オフライン(API 呼び出しはモック)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import translate  # noqa: E402


def test_needs_translation():
    assert translate.needs_translation("Introducing Claude Opus 5")
    assert translate.needs_translation("文心大模型5.0正式版，上线！")  # 中国語(漢字のみ)は翻訳対象
    assert not translate.needs_translation("Sakana Chatがアップデート")


def test_translate_all_cache_and_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(translate, "CACHE_PATH", tmp_path / "translations.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    calls = []

    def fake_batch(titles):
        calls.append(list(titles))
        return [f"和訳:{t}" for t in titles]

    monkeypatch.setattr(translate, "translate_batch", fake_batch)
    out = translate.translate_all(["Hello world", "既に日本語です", "Hello world"])
    assert out == {"Hello world": "和訳:Hello world"}
    assert calls == [["Hello world"]]

    # 2 回目はキャッシュから(API 呼び出しなし)
    out2 = translate.translate_all(["Hello world"])
    assert out2 == {"Hello world": "和訳:Hello world"}
    assert len(calls) == 1
    cache = json.loads((tmp_path / "translations.json").read_text(encoding="utf-8"))
    assert cache == {"Hello world": "和訳:Hello world"}


def test_translate_all_degrades_on_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(translate, "CACHE_PATH", tmp_path / "translations.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    def boom(titles):
        raise RuntimeError("api down")

    monkeypatch.setattr(translate, "translate_batch", boom)
    out = translate.translate_all(["Hello"])
    assert out == {}  # 原文のまま(表示側フォールバック)
    assert "失敗" in capsys.readouterr().out


def test_translate_all_no_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(translate, "CACHE_PATH", tmp_path / "translations.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = translate.translate_all(["Hello"])
    assert out == {}
    assert "未設定" in capsys.readouterr().out
