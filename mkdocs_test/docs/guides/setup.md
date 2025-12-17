# セットアップ手順

## 必要な環境

- Python 3.8以上
- pip (Pythonパッケージマネージャー)
- Git

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/your-project.git
cd your-project
```

### 2. 仮想環境の作成

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化 (macOS/Linux)
source venv/bin/activate

# 仮想環境の有効化 (Windows)
venv\Scripts\activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## ローカル開発サーバーの起動

```bash
mkdocs serve
```

以下のURLでアクセスできます:
```
http://127.0.0.1:8000
```

!!! success "成功"
    ブラウザでサイトが表示されれば成功です！

## ディレクトリ構造

```
mkdocs_test/
├── mkdocs.yml          # MkDocs設定ファイル
├── docs/               # ドキュメントソース
│   ├── index.md
│   ├── overview/       # システム概要
│   ├── diagrams/       # シーケンス図
│   └── guides/         # ガイド
├── site/               # ビルド後の静的ファイル (自動生成)
└── requirements.txt    # Python依存パッケージ
```

## コンテンツの編集

### Markdownファイルの編集

`docs/` ディレクトリ内の `.md` ファイルを編集します。

```bash
# 例: トップページの編集
vim docs/index.md
```

保存すると自動的にブラウザがリロードされます。

### シーケンス図の追加

Mermaid記法を使用してシーケンス図を記述できます。

````markdown
```mermaid
sequenceDiagram
    participant A as サービスA
    participant B as サービスB
    A->>B: リクエスト
    B-->>A: レスポンス
```
````

### 新しいページの追加

1. `docs/` 内に新しい `.md` ファイルを作成
2. `mkdocs.yml` の `nav:` セクションに追加

```yaml
nav:
  - ホーム: index.md
  - 新しいページ: path/to/newpage.md
```

## ビルド

静的サイトをビルドします。

```bash
mkdocs build
```

ビルド成果物は `site/` ディレクトリに生成されます。

## トラブルシューティング

### ポートが既に使用されている場合

別のポートを指定して起動します。

```bash
mkdocs serve -a 127.0.0.1:8001
```

### Pythonバージョンの確認

```bash
python --version
```

Python 3.8以上が必要です。

!!! tip "ヒント"
    開発サーバーは自動リロード機能を持っているため、ファイルを保存するだけで変更が反映されます。
