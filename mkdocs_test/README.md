# システム設計書サイト

MkDocs + Material for Mkdocsで作成したシステム設計書のサンプルプロジェクトです。
Mermaidを使用したシーケンス図や各種ダイアグラムを含んでいます。

## 特徴

- Material for MkDocsによる洗練されたデザイン
- Mermaidによるシーケンス図の表示
- ダークモード対応
- レスポンシブデザイン
- 日本語検索対応
- コードハイライト

## クイックスタート

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. ローカルサーバーの起動

```bash
mkdocs serve
```

ブラウザで http://127.0.0.1:8000 にアクセスしてください。

### 3. ビルド

```bash
mkdocs build
```

## プロジェクト構造

```
mkdocs_test/
├── mkdocs.yml              # MkDocs設定ファイル
├── requirements.txt        # Python依存パッケージ
├── README.md              # このファイル
└── docs/                  # ドキュメントソース
    ├── index.md           # トップページ
    ├── overview/          # システム概要
    │   ├── architecture.md
    │   └── system-config.md
    ├── diagrams/          # シーケンス図
    │   ├── auth-sequence.md
    │   ├── data-processing.md
    │   └── api-integration.md
    └── guides/            # ガイド
        ├── setup.md
        └── deployment.md
```

## サンプルコンテンツ

### シーケンス図

- **ユーザー認証フロー** - OAuth2.0を使用した認証プロセス
- **データ処理フロー** - バッチ処理とストリーム処理
- **API連携フロー** - 外部APIとの連携パターン

### システム図

- システムアーキテクチャ図
- システム構成図

## カスタマイズ

### テーマカラーの変更

`mkdocs.yml` の `theme.palette.primary` を変更:

```yaml
theme:
  palette:
    primary: blue  # indigo, blue, teal など
```

### ナビゲーションの編集

`mkdocs.yml` の `nav` セクションを編集:

```yaml
nav:
  - ホーム: index.md
  - 新しいセクション:
    - ページ1: path/to/page1.md
```

## デプロイ

### GitHub Pagesへのデプロイ

```bash
mkdocs gh-deploy
```

詳細は [デプロイ手順](docs/guides/deployment.md) を参照してください。

## ライセンス

MIT License

## 参考リンク

- [MkDocs公式ドキュメント](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Mermaid Documentation](https://mermaid.js.org/)
