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
- `src/render.py` — 地域別 3 セクション・和訳+原文併記で `out/index.html` を生成
- `.github/workflows/collect.yml` — 6 時間ごとに実行し差分コミット → Vercel 自動デプロイ

## 既知の制約

- **取得経路調査中(5 社)**: Moonshot AI・Zhipu AI・ByteDance Seed・Tencent は JS レンダリング必須、
  rinna は収集環境から DNS 不達。カードに理由を表示し、経路確立は後続ループで対応
- Qwen は公式ブログの qwen.ai 移転(JS 必須)により旧公式フィードを使用(新着が遅延する可能性)
- Baidu・Tencent 等は AI 専門ブログが JS 必須のため公式コーポレートニュースで代替
