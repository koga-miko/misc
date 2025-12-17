# mkdocs.yml 設定ファイル詳細解説

このドキュメントでは、本プロジェクトの `mkdocs.yml` 設定ファイルの各項目について詳しく解説します。

## 目次

1. [サイト基本情報](#サイト基本情報)
2. [テーマ設定](#テーマ設定)
3. [Markdown拡張機能](#markdown拡張機能)
4. [プラグイン](#プラグイン)
5. [追加JavaScript](#追加javascript)
6. [ナビゲーション構造](#ナビゲーション構造)

---

## サイト基本情報

```yaml
site_name: システム設計書
site_description: サンプルシステムの設計ドキュメント
site_author: Development Team
```

### 各項目の説明

| 項目 | 説明 | 用途 |
|------|------|------|
| `site_name` | サイトのタイトル | ブラウザタブ、ヘッダーに表示される |
| `site_description` | サイトの説明文 | SEO対策、メタタグに使用される |
| `site_author` | サイト作成者 | メタタグに含まれる著者情報 |

### カスタマイズ例

```yaml
site_name: My Project Documentation
site_description: Comprehensive guide for my awesome project
site_author: John Doe
site_url: https://example.com  # サイトのURL（SEO向上）
```

---

## テーマ設定

### 基本設定

```yaml
theme:
  name: material
  language: ja
```

- **`name: material`**: Material for MkDocsテーマを使用
  - Googleのマテリアルデザインを採用
  - モダンで洗練されたUI
  - レスポンシブ対応

- **`language: ja`**: 日本語UIに設定
  - 検索プレースホルダー、ナビゲーションなどが日本語表示
  - 検索機能も日本語対応

### カラーパレット設定

```yaml
palette:
  # Light mode
  - media: "(prefers-color-scheme: light)"
    scheme: default
    primary: indigo
    accent: indigo
    toggle:
      icon: material/brightness-7
      name: ダークモードに切り替え
  # Dark mode
  - media: "(prefers-color-scheme: dark)"
    scheme: slate
    primary: indigo
    accent: indigo
    toggle:
      icon: material/brightness-4
      name: ライトモードに切り替え
```

#### ライトモード設定

| 項目 | 値 | 説明 |
|------|-----|------|
| `media` | `(prefers-color-scheme: light)` | OSのカラースキーム設定に追従 |
| `scheme` | `default` | デフォルト（ライト）カラースキーム |
| `primary` | `indigo` | プライマリカラー（ヘッダー、リンクなど） |
| `accent` | `indigo` | アクセントカラー（ホバー時など） |
| `toggle.icon` | `material/brightness-7` | 太陽アイコン |
| `toggle.name` | トグルボタンのツールチップテキスト | ユーザーに表示される説明 |

#### ダークモード設定

| 項目 | 値 | 説明 |
|------|-----|------|
| `media` | `(prefers-color-scheme: dark)` | OSのダークモード設定に追従 |
| `scheme` | `slate` | ダークカラースキーム |
| `toggle.icon` | `material/brightness-4` | 月アイコン |

#### 利用可能なカラー

**Primary/Accentカラー:**
- `red`, `pink`, `purple`, `deep purple`
- `indigo`, `blue`, `light blue`, `cyan`
- `teal`, `green`, `light green`, `lime`
- `yellow`, `amber`, `orange`, `deep orange`

**変更例:**
```yaml
primary: blue
accent: orange
```

### フィーチャー設定

```yaml
features:
  - navigation.tabs
  - navigation.sections
  - navigation.expand
  - navigation.top
  - search.suggest
  - search.highlight
  - content.code.copy
  - content.code.annotate
```

#### 各フィーチャーの詳細

| フィーチャー | 機能 |
|------------|------|
| `navigation.tabs` | トップレベルのナビゲーションをタブ表示 |
| `navigation.sections` | セクションをグループ化して表示 |
| `navigation.expand` | サブセクションを展開した状態で表示 |
| `navigation.top` | 「トップへ戻る」ボタンを表示 |
| `search.suggest` | 検索時にサジェスト（候補）を表示 |
| `search.highlight` | 検索結果のキーワードをハイライト表示 |
| `content.code.copy` | コードブロックにコピーボタンを追加 |
| `content.code.annotate` | コードに注釈（アノテーション）を追加可能 |

#### その他の便利なフィーチャー

```yaml
features:
  - navigation.instant      # ページ読み込みを高速化（SPA風）
  - navigation.tracking     # URLにアンカーを自動追加
  - toc.follow             # 目次が現在位置を追従
  - toc.integrate          # 目次をサイドバーに統合
  - header.autohide        # スクロール時にヘッダーを自動非表示
```

---

## Markdown拡張機能

### 1. Superfences（コードフェンス拡張）

```yaml
- pymdownx.superfences:
    custom_fences:
      - name: mermaid
        class: mermaid
        format: !!python/name:pymdownx.superfences.fence_code_format
```

**機能:**
- Mermaid記法でダイアグラムを作成可能
- ネストしたコードブロックにも対応

**使用例:**
````markdown
```mermaid
graph LR
    A[開始] --> B[処理]
    B --> C[終了]
```
````

### 2. Tabbed（タブ表示）

```yaml
- pymdownx.tabbed:
    alternate_style: true
```

**機能:**
- コンテンツをタブで切り替え表示

**使用例:**
````markdown
=== "Python"
    ```python
    print("Hello")
    ```

=== "JavaScript"
    ```javascript
    console.log("Hello");
    ```
````

### 3. Admonition（注意書き）

```yaml
- admonition
```

**機能:**
- 警告、ヒント、注意などのボックスを表示

**使用例:**
```markdown
!!! note "注意"
    これは重要な情報です。

!!! warning "警告"
    この操作は危険です。

!!! tip "ヒント"
    こうするともっと良くなります。
```

**利用可能なタイプ:**
- `note`, `abstract`, `info`, `tip`, `success`
- `question`, `warning`, `failure`, `danger`, `bug`
- `example`, `quote`

### 4. Details（折りたたみ）

```yaml
- pymdownx.details
```

**機能:**
- Admonitionを折りたたみ可能にする

**使用例:**
```markdown
??? note "クリックして展開"
    このコンテンツは折りたたまれています。
```

### 5. Highlight（シンタックスハイライト）

```yaml
- pymdownx.highlight:
    anchor_linenums: true
```

**機能:**
- コードブロックのシンタックスハイライト
- 行番号の表示
- 行番号へのアンカーリンク

**使用例:**
````markdown
```python linenums="1"
def hello():
    print("Hello, World!")
```
````

### 6. InlineHilite（インラインコードハイライト）

```yaml
- pymdownx.inlinehilite
```

**機能:**
- インラインコードのシンタックスハイライト

**使用例:**
```markdown
変数 `#!python x = 10` を設定します。
```

### 7. Snippets（ファイル埋め込み）

```yaml
- pymdownx.snippets
```

**機能:**
- 外部ファイルの内容を埋め込み

**使用例:**
```markdown
--8<-- "path/to/file.txt"
```

### 8. Attr List（属性リスト）

```yaml
- attr_list
```

**機能:**
- 要素にCSSクラスやID、属性を追加

**使用例:**
```markdown
![画像](image.png){ width="300" }

テキスト { .custom-class #my-id }
```

### 9. MD in HTML（HTML内でMarkdown）

```yaml
- md_in_html
```

**機能:**
- HTMLタグ内でMarkdown記法を使用可能

**使用例:**
```markdown
<div markdown="1">
## Markdownの見出し
これは**太字**です。
</div>
```

### 10. Tables（テーブル）

```yaml
- tables
```

**機能:**
- GitHub風のテーブル記法をサポート

**使用例:**
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
```

### 11. TOC（目次）

```yaml
- toc:
    permalink: true
```

**機能:**
- 目次の自動生成
- 見出しにパーマリンクアイコンを追加

**オプション:**
- `permalink: true` - 見出しにリンクアイコンを表示
- `permalink: ⚓︎` - カスタムアイコンを指定
- `toc_depth: 3` - 目次に含める見出しレベルを指定

---

## プラグイン

```yaml
plugins:
  - search:
      lang: ja
  - mermaid2
```

### 1. Search（検索機能）

```yaml
- search:
    lang: ja
```

**機能:**
- サイト内全文検索
- 日本語対応

**オプション例:**
```yaml
- search:
    lang: ja
    separator: '[\s\-\.]+'  # 検索トークンの区切り文字
    prebuild_index: true    # ビルド時にインデックス作成（高速化）
```

### 2. Mermaid2（ダイアグラム）

```yaml
- mermaid2
```

**機能:**
- Mermaidダイアグラムのレンダリング
- シーケンス図、フローチャート、ガントチャートなど

**サポートするダイアグラムタイプ:**
- シーケンス図（Sequence Diagram）
- フローチャート（Flowchart）
- クラス図（Class Diagram）
- ステート図（State Diagram）
- ガントチャート（Gantt Chart）
- パイチャート（Pie Chart）
- ER図（Entity Relationship Diagram）
- Git Graph

### その他の便利なプラグイン

```yaml
plugins:
  - minify:              # HTML/CSS/JSの圧縮
      minify_html: true
  - git-revision-date    # 最終更新日を表示
  - awesome-pages        # ページ順序を柔軟に管理
  - macros               # 変数やマクロを使用
```

---

## 追加JavaScript

```yaml
extra_javascript:
  - https://unpkg.com/mermaid@10/dist/mermaid.min.js
```

**目的:**
- Mermaidライブラリの読み込み
- ダイアグラムをブラウザ上でレンダリング

**バージョン指定例:**
```yaml
extra_javascript:
  - https://unpkg.com/mermaid@10.6.1/dist/mermaid.min.js
```

**ローカルファイルの追加:**
```yaml
extra_javascript:
  - javascripts/custom.js
  - javascripts/analytics.js
```

---

## ナビゲーション構造

```yaml
nav:
  - ホーム: index.md
  - システム概要:
    - アーキテクチャ: overview/architecture.md
    - システム構成: overview/system-config.md
  - シーケンス図:
    - ユーザー認証フロー: diagrams/auth-sequence.md
    - データ処理フロー: diagrams/data-processing.md
    - API連携フロー: diagrams/api-integration.md
  - ガイド:
    - セットアップ手順: guides/setup.md
    - デプロイ手順: guides/deployment.md
```

### 構造の説明

**階層構造:**
```
ホーム（トップレベル）
├── システム概要（セクション）
│   ├── アーキテクチャ
│   └── システム構成
├── シーケンス図（セクション）
│   ├── ユーザー認証フロー
│   ├── データ処理フロー
│   └── API連携フロー
└── ガイド（セクション）
    ├── セットアップ手順
    └── デプロイ手順
```

### ナビゲーション記法のパターン

#### 1. シンプルなページ
```yaml
- ページ名: path/to/file.md
```

#### 2. セクションでグループ化
```yaml
- セクション名:
  - サブページ1: path/to/page1.md
  - サブページ2: path/to/page2.md
```

#### 3. セクションにインデックスページ
```yaml
- セクション名:
  - overview/index.md  # セクションのトップページ
  - サブページ1: overview/page1.md
  - サブページ2: overview/page2.md
```

#### 4. 多階層のネスト
```yaml
- 大セクション:
  - 中セクション:
    - 小セクション:
      - ページ: path/to/page.md
```

### ナビゲーションの自動生成

`nav` を省略すると、ディレクトリ構造から自動生成されます:

```yaml
# nav を省略または削除
# ファイルシステムの構造に基づいて自動的にナビゲーション作成
```

---

## 実践的なカスタマイズ例

### 1. 企業サイト風にカスタマイズ

```yaml
site_name: ABC Corporation Docs
theme:
  name: material
  palette:
    primary: blue
    accent: orange
  logo: assets/logo.png
  favicon: assets/favicon.ico
  features:
    - navigation.instant
    - navigation.tabs.sticky
```

### 2. 多言語対応

```yaml
plugins:
  - i18n:
      default_language: ja
      languages:
        ja: 日本語
        en: English
```

### 3. ソーシャルリンクの追加

```yaml
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/your-org
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/your-account
    - icon: fontawesome/brands/linkedin
      link: https://linkedin.com/company/your-company
```

### 4. カスタムCSS

```yaml
extra_css:
  - stylesheets/extra.css
```

`docs/stylesheets/extra.css`:
```css
:root {
  --md-primary-fg-color: #2196F3;
}

.md-header {
  background: linear-gradient(to right, #667eea 0%, #764ba2 100%);
}
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. Mermaidダイアグラムが表示されない

**原因:** mermaid2プラグインとJavaScriptの重複読み込み

**解決策:**
```yaml
# どちらか一方を使用
plugins:
  - mermaid2

# または
extra_javascript:
  - https://unpkg.com/mermaid@10/dist/mermaid.min.js
```

#### 2. 日本語検索が機能しない

**確認項目:**
```yaml
plugins:
  - search:
      lang: ja  # 必ず指定
```

#### 3. ナビゲーションが表示されない

**確認項目:**
- ファイルパスが正しいか
- インデントが正しいか（YAMLは厳密）
- ファイルが実際に存在するか

---

## まとめ

このmkdocs.yml設定により、以下が実現されています:

✅ **洗練されたデザイン** - Material for MkDocsテーマ
✅ **ダークモード対応** - ユーザーの好みに応じて切り替え可能
✅ **高度なMarkdown機能** - 図表、コード、注意書きなど
✅ **ダイアグラム対応** - Mermaidでシーケンス図など作成可能
✅ **日本語対応** - UIと検索が日本語に対応
✅ **使いやすいナビゲーション** - タブ、セクション、階層構造

必要に応じて設定をカスタマイズして、プロジェクトに最適なドキュメントサイトを構築できます。

---

## 参考リンク

- [MkDocs公式ドキュメント](https://www.mkdocs.org/)
- [Material for MkDocs公式サイト](https://squidfunk.github.io/mkdocs-material/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)
- [Mermaid公式ドキュメント](https://mermaid.js.org/)
