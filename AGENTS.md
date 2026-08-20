<!-- scaffold:block agents_core v1.8.0 -->
## 共通規律(scaffold 管理領域 — 手動編集禁止)

このセクションはスキャフォールド・レジストリが管理する。内容を変更したい場合は、
このファイルを直接編集せず、失敗ログ → HARNESS_CHANGELOG 起票 → レジストリ改訂 → `scaffoldctl update` の経路で行うこと。

### 7 段階ループプロトコル

| 段階 | 名称 | 完了条件 |
|---|---|---|
| 1 | 計画 | 対象の要求 ID を特定し、`loop_start` を記録した |
| 2 | 文脈読込 | SPEC.md / IMPLEMENTATION_GUIDE.md の該当箇所と、直近ループのログを読んだ |
| 3 | テスト先行 | TEST_SPEC.md にトレースする失敗するテストを書き、赤を確認した |
| 4 | 実装 | ファイル編集 2 回ごとにテストを実行し、赤のまま次の編集に進んでいない |
| 5 | 検証 | 全テスト合格 + 独立再計算(該当時)を確認した |
| 6 | 文書同期 | SPEC/docs と実装の乖離(SPEC-DRIFT)を解消し、生成ドキュメントを再生成した |
| 7 | 完了 | `loop_end` を記録し、ループログ validate に合格し、専用コミットを積んだ |

### ループ可観測性

全ループは loop-observability の規律(LOOP_LOG_SPEC / FAILURE_TAXONOMY)に従い
`logs/loops/{loop_id}.jsonl` に記録する。失敗は気づいた瞬間に分類コード付きで記録する。
ツーストライク(LL-10)と S1 即時起票(LL-12)は本プロジェクトでも有効である。

### エスカレーション規範

以下の場合は作業を止め、`escalation` を記録してから人間に確認する:
仕様の複数解釈(SPEC-AMB 相当)/ スコープ外ファイルへの変更が必要になった /
破壊的操作(履歴改変・データ削除・強制 push)/ 同種の修正の 3 回目の失敗(PROC-LOOP)。

### コミット規約

Conventional Commits(feat/fix/test/docs/refactor/chore)。スキャフォールド更新は
`chore: scaffold vX.Y.Z` の専用コミットで行い、機能変更と混ぜない。
<!-- /scaffold:block agents_core -->

## プロジェクト固有(kiban-lens)

- **正体**: AI 基盤モデル 23 社(米6中7日10)の公式ブログ最新 5 件+Claude 和訳の一覧(基盤レンズ)。koho-lens の姉妹
- **構成**: sources.py(経路宣言)→ fetch.py(収集・劣化継続)→ translate.py(Haiku 和訳+data/translations.json キャッシュ)→ render.py(out/index.html)。collect.yml が 6 時間 cron
- **翻訳規範**: 新出見出しのみ一括翻訳(claude-haiku-4-5・構造化出力)。キー未設定/障害時は原文表示で劣化継続。和訳には必ず原文を併記
- **経路変更時**: sources.py を編集 → tools/probe_endpoints.py で実地確認 → pytest(オフライン)→ 実行テスト → コミット。pending 解消(JS サイト)は headless 化か代替経路で
- **説明文**: `data/profiles.json`(会社ID → 2〜3 文)。月次クラウド routine が点検・更新する(仕様正本 `docs/routine-monthly-profiles.md` — 任務変更はこのファイルの編集だけでよい)。会社を増減したら profiles.json も同時に更新すること(T-06 が過不足を検査)
- **フィルタ**: 地域(すべて/米国/中国/日本)と期間(直近1ヶ月/1週間・排他)。**期間の基準は閲覧時点から JS が計算する** — ビルド時に日付を焼き込まないこと(腐るため)
- **テストは全てオフライン**。ネットワークを触るテストを追加しないこと(CI は 6h cron と分離)
