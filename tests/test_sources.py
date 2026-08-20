# -*- coding: utf-8 -*-
"""T-01: sources.py の宣言的定義の検証。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sources import COMPANIES, REGIONS  # noqa: E402


def test_23_companies_by_region():
    counts = {rid: 0 for rid, _ in REGIONS}
    for c in COMPANIES:
        counts[c["region"]] += 1
    assert counts == {"us": 6, "cn": 7, "jp": 10}
    assert len(COMPANIES) == 23


def test_unique_ids_and_names():
    ids = [c["id"] for c in COMPANIES]
    names = [c["name"] for c in COMPANIES]
    assert len(set(ids)) == len(ids)
    assert len(set(names)) == len(names)


def test_strategy_shape():
    for c in COMPANIES:
        assert c["strategy"] in ("feed", "html", "pending"), c["id"]
        assert c["source_url"].startswith("http"), c["id"]
        if c["strategy"] == "pending":
            assert c.get("note"), f"{c['id']}: pending には note 必須"
        else:
            assert c["primary_url"].startswith("http"), c["id"]
        if c["strategy"] == "html":
            pattern = c.get("list_re") or c.get("link_re")
            assert pattern, f"{c['id']}: html には link_re か list_re が必須"
            re.compile(pattern)  # コンパイル可能
            if "list_re" in c:
                assert re.compile(c["list_re"]).groups == 2, c["id"]
