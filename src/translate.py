# -*- coding: utf-8 -*-
"""ヘッドラインの和訳(F-03)。Claude API(Haiku)+キャッシュ。

- data/translations.json に {原文: 和訳} を永続キャッシュし、新出見出しだけを
  1 リクエストにまとめて翻訳する(コストは 1 日数見出し分でほぼゼロ)
- ANTHROPIC_API_KEY 未設定・API 障害時は原文のまま返す(劣化継続)
- もともと日本語の見出し(日本企業)は翻訳せずそのまま
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "data" / "translations.json"
MODEL = "claude-haiku-4-5"

_JA_RE = re.compile(r"[぀-ヿ]")  # ひらがな・カタカナがあれば日本語とみなす

SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "required": ["translations"],
    "additionalProperties": False,
}

PROMPT = (
    "以下は AI 企業の公式ブログ・ニュースの見出しです。それぞれを自然な日本語の見出しに翻訳し、"
    "入力と同じ順序・同じ件数の配列で返してください。固有名詞(製品名・モデル名・企業名)は"
    "原文表記のまま残してください。すでに日本語の見出しはそのまま返してください。\n\n"
)


def needs_translation(title: str) -> bool:
    return not _JA_RE.search(title)


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")


def translate_batch(titles: list[str]) -> list[str]:
    """新出見出しの一括翻訳。API キー未設定・失敗時は例外を上げる(呼び出し側で劣化継続)。"""
    import anthropic

    client = anthropic.Anthropic()
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": PROMPT + numbered}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    out = json.loads(text)["translations"]
    if len(out) != len(titles):
        raise ValueError(f"翻訳件数不一致: {len(out)} != {len(titles)}")
    return out


def translate_all(titles: list[str]) -> dict:
    """全見出し(重複可)→ {原文: 和訳} を返す。キャッシュ更新込み。

    和訳が得られない場合は辞書に載せない(表示側は原文のまま)。"""
    cache = load_cache()
    todo = sorted({t for t in titles if needs_translation(t) and t not in cache})
    if todo and os.environ.get("ANTHROPIC_API_KEY", "").strip():
        try:
            for original, ja in zip(todo, translate_batch(todo)):
                ja = ja.strip()
                if ja:
                    cache[original] = ja
            save_cache(cache)
        except Exception as e:
            print(f"translate: 失敗(原文のまま継続): {type(e).__name__}: {e}")
    elif todo:
        print(f"translate: ANTHROPIC_API_KEY 未設定 — {len(todo)} 件を原文のまま表示")
    return {t: cache[t] for t in titles if t in cache}
