# TEST_SPEC.md — kiban-lens

<!-- scaffold template v1.8.0 から展開(2026-08-20)。以後このファイルはプロジェクトが育てる -->

## テスト一覧(すべてオフライン)

| ID | 内容 | 対応要求 | ファイル |
|---|---|---|---|
| T-01 | sources 検証: 23 社(米6中7日10)・ID/名前一意・strategy 語彙・html は正規表現コンパイル可・pending は note 必須 | F-01 | tests/test_sources.py |
| T-02 | HTML フェッチャ: リンク採取・重複排除・list_re(一覧タイトル)・sort_desc・テンプレート残骸除外・日付/タイトル抽出の各形式 | F-01 | tests/test_fetchers.py |
| T-03 | 翻訳: 日本語判定・新出のみバッチ翻訳・キャッシュ命中時は API 不呼び出し・障害/キー未設定時の劣化継続 | F-03, N-03 | tests/test_translate.py |
| T-04 | パイプライン: 取得失敗時の前回分保持(items/fetched_at)・全社失敗のみ exit 1 | F-02 | tests/test_render_pipeline.py |
| T-05 | レンダラ: 全 23 社と地域見出しの出現・JST 変換・和訳+原文併記・pending 表示・フッタ規約・決定性 | F-04, F-05, N-02 | tests/test_render_pipeline.py |

## 実行

```bash
python -m pytest -q
```
