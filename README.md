# kiban-lens — 基盤レンズ

AI 基盤モデルを提供する主要企業(米国 6・中国 7・日本 10 の計 23 社)の公式ブログ / ニュースの
最新 5 件を、**Claude(Haiku)による和訳付き**で一覧する静的ダッシュボード。

## 使い方

```bash
pip install anthropic          # 和訳に使用(未インストール/キー未設定でも原文表示で動く)
python -m src.fetch            # 収集 → 和訳(キャッシュ)→ out/index.html 生成
python -m pytest -q            # テスト(すべてオフライン)
```

## しくみ

- `src/sources.py` — 23 社の取得経路(RSS/Atom フィード or 静的 HTML 解析)を宣言
- `src/fetchers.py` — HTML は「一覧からリンク採取 → 各記事ページから日付・タイトル抽出」の統一方式
- `src/translate.py` — 英語・中国語の見出しだけを claude-haiku-4-5 で一括和訳し `data/translations.json` に永続キャッシュ(新出のみ翻訳・失敗時は原文)
- `data/profiles.json` — 各社の説明文(月次 routine が点検・更新。仕様は `docs/routine-monthly-profiles.md`)
- `src/render.py` — 地域別 3 セクション・説明文・和訳+原文併記・地域/期間フィルタ付きの `out/index.html` を生成
- `.github/workflows/collect.yml` — 6 時間ごとに実行し差分コミット → Vercel 自動デプロイ

## 既知の制約

- **browser 戦略の 2 社**(Zhipu AI・Tencent)は JS レンダリング必須のため Playwright で取得する。
  ローカルで `pip install playwright && python -m playwright install chromium` していない場合は
  この 2 社だけ取得失敗(前回分を保持)になる — CI では自動導入される
- Qwen は公式ブログの qwen.ai 移転(JS 必須)により旧公式フィードを使用(新着が遅延する可能性)
- Baidu・Tencent は AI 専門ブログが JS 必須のため公式コーポレートニュースで代替
- rinna は rinna.co.jp が NXDOMAIN(ドメイン消滅)のため対象から除外し、LLM-jp を追加した(2026-08-21)
