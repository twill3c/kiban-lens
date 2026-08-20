# TEST_SPEC.md — kiban-lens

<!-- scaffold template v1.8.0 から展開(2026-08-20)。以後このファイルはプロジェクトが育てる -->

## テスト一覧(すべてオフライン)

| ID | 内容 | 対応要求 | ファイル |
|---|---|---|---|
| T-01 | sources 検証: 23 社(米6中7日10)・ID/名前一意・strategy 語彙・html/browser は正規表現コンパイル可・browser は理由の note 必須・経路未確立(pending)が残っていない | F-01, F-08 | tests/test_sources.py |
| T-02 | HTML フェッチャ: リンク採取・重複排除・list_re(一覧タイトル)・title_re(記事内位置指定)・sort_desc・テンプレート/エラーページ除外・日付/タイトル抽出の各形式・browser は描画経由 | F-01, F-08 | tests/test_fetchers.py |
| T-03 | 翻訳: 日本語判定・新出のみバッチ翻訳・キャッシュ命中時は API 不呼び出し・障害/キー未設定時の劣化継続 | F-03, N-03 | tests/test_translate.py |
| T-04 | パイプライン: 取得失敗時の前回分保持(items/fetched_at)・全社失敗のみ exit 1 | F-02 | tests/test_render_pipeline.py |
| T-05 | レンダラ: 全 23 社と地域見出しの出現・JST 変換・和訳+原文併記・pending 表示・フッタ規約・決定性 | F-04, F-05, N-02 | tests/test_render_pipeline.py |
| T-06 | 説明文: 23 社を過不足なく網羅・字数(20〜200)・updated_on の存在・カード表示・欠落時も描画継続 | F-06 | tests/test_render_pipeline.py |
| T-08 | 健全性: failing(連続失敗・未取得)/ stale(長期未更新)/ undated / healthy の判定と閾値の内外・重い順の整列・レポート整形・pipeline の fail_streak と last_ok_at の記録とリセット・ページの警告表示と後方互換 | F-09 | tests/test_health.py, tests/test_render_pipeline.py |
| T-07 | フィルタ: 地域/期間チップの出現・カードの data-region/data-latest・セクションの地域束ね・閲覧時点基準(cutoff 関数)・latest_date ヘルパ | F-07 | tests/test_render_pipeline.py |

## 実行

```bash
python -m pytest -q
```
