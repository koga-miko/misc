# デプロイ手順

## 概要

MkDocsで生成した静的サイトを各種プラットフォームにデプロイする方法を説明します。

## GitHub Pagesへのデプロイ

### 自動デプロイ (推奨)

MkDocsのコマンドを使用して簡単にデプロイできます。

```bash
mkdocs gh-deploy
```

このコマンドは以下を自動で実行します:
1. `mkdocs build` でサイトをビルド
2. `gh-pages` ブランチを作成/更新
3. GitHubにプッシュ

!!! info "初回デプロイ時"
    GitHubリポジトリの Settings > Pages で、Source を `gh-pages` ブランチに設定してください。

### 手動デプロイ

```bash
# ビルド
mkdocs build

# gh-pagesブランチに切り替え
git checkout gh-pages

# ビルド成果物をコピー
cp -r site/* .

# コミット & プッシュ
git add .
git commit -m "Deploy documentation"
git push origin gh-pages
```

## GitHub Actionsでの自動デプロイ

`.github/workflows/deploy-docs.yml` を作成:

```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Deploy to GitHub Pages
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          mkdocs gh-deploy --force
```

## Netlifyへのデプロイ

### 設定ファイルの作成

`netlify.toml` を作成:

```toml
[build]
  command = "mkdocs build"
  publish = "site"

[build.environment]
  PYTHON_VERSION = "3.11"
```

### デプロイ手順

1. Netlifyにログイン
2. "New site from Git" を選択
3. リポジトリを接続
4. ビルドコマンドとディレクトリが自動設定される
5. "Deploy site" をクリック

!!! success "自動デプロイ"
    以降、mainブランチへのpush時に自動でデプロイされます。

## AWS S3 + CloudFrontへのデプロイ

### S3バケットの作成

```bash
aws s3 mb s3://your-docs-bucket
aws s3 website s3://your-docs-bucket --index-document index.html
```

### ビルドとアップロード

```bash
# ビルド
mkdocs build

# S3にアップロード
aws s3 sync site/ s3://your-docs-bucket --delete

# CloudFrontのキャッシュをクリア (オプション)
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### デプロイスクリプト

`deploy.sh` を作成:

```bash
#!/bin/bash
set -e

echo "Building documentation..."
mkdocs build

echo "Uploading to S3..."
aws s3 sync site/ s3://your-docs-bucket --delete

echo "Clearing CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

echo "Deployment complete!"
```

## Dockerでのデプロイ

### Dockerfileの作成

```dockerfile
FROM python:3.11-slim

WORKDIR /docs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdocs build

FROM nginx:alpine
COPY --from=0 /docs/site /usr/share/nginx/html

EXPOSE 80
```

### ビルドと実行

```bash
# イメージのビルド
docker build -t docs-site .

# コンテナの起動
docker run -d -p 80:80 docs-site
```

## デプロイ前チェックリスト

- [ ] ローカルでビルドが成功することを確認
- [ ] すべてのリンクが正しく動作することを確認
- [ ] シーケンス図が正しく表示されることを確認
- [ ] レスポンシブデザインの確認 (モバイル表示)
- [ ] 検索機能の動作確認
- [ ] ナビゲーションメニューの確認

## 本番環境の推奨設定

### パフォーマンス最適化

```yaml
# mkdocs.yml
plugins:
  - search
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
```

### SEO設定

```yaml
# mkdocs.yml
site_name: システム設計書
site_description: システム設計の詳細ドキュメント
site_author: Development Team
site_url: https://your-domain.com

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/your-org
```

## モニタリング

### アクセス解析 (Google Analytics)

```yaml
# mkdocs.yml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

!!! warning "注意"
    本番環境へのデプロイ前に、必ずステージング環境でテストしてください。

## ロールバック手順

### GitHub Pages

```bash
# 前のコミットに戻す
git checkout gh-pages
git reset --hard HEAD~1
git push origin gh-pages --force
```

### Netlify

管理画面から以前のデプロイを選択して "Publish deploy" をクリック

!!! tip "ベストプラクティス"
    - デプロイ前にローカルで十分にテスト
    - CI/CDパイプラインで自動テストを実行
    - デプロイ履歴を記録
    - 定期的なバックアップ
