複数リポジトリの運用で発生しているトラブルを防ぐため、以下のような運用方針を提案します。

## 基本方針：ブランチ命名規則による明確な区別

リポジトリを間違える主な原因は「どちらで作業しているか分からなくなる」ことです。これをブランチ名で視覚的に防ぎます。

```
# Gerritリポジトリでの作業
feature/gerrit-TICKET-123-description

# GitLabリポジトリでの作業  
feature/gitlab-ISSUE-456-description
```

この命名規則により：
- `git branch`コマンドで現在位置が一目瞭然
- プレフィックスでどちらのリポジトリ用か判別可能
- レビュー時にも誤りに気づきやすい

## 推奨フロー：Gerrit寄りの運用

GitHubフローよりGerritフローを基準にすることを推奨します。理由は：

1. **1コミット1レビュー**の原則が予期せぬコミット混入を防ぐ
2. 委託元のレビュー負荷が明確（コミット単位で判断）
3. Change-Idによる変更追跡が厳密

### 具体的な運用ルール

**委託先（開発者）の作業フロー：**

```bash
# 1. 作業開始時に必ずリポジトリとチケット番号を確認
git clone <gerrit-repo>
cd project
git checkout -b feature/gerrit-TICKET-123-add-sensor-driver

# 2. コミット前のチェックリスト実行
./scripts/pre-commit-check.sh  # 後述のスクリプト

# 3. Gerrit: 1機能1コミットで完結させる
git add src/sensor_driver.c
git commit -m "[TICKET-123] Add temperature sensor driver"

# 4. プッシュ前に再確認
git log --oneline -1  # コミットメッセージにチケット番号があるか
git branch --show-current  # ブランチ名が正しいか確認

# 5. Gerrit: refs/for/mainにプッシュ
git push origin HEAD:refs/for/main
```

**GitLabでも同様だが、プレフィックスを変更：**

```bash
git checkout -b feature/gitlab-ISSUE-456-update-display
git commit -m "[ISSUE-456] Update display brightness control"
git push origin feature/gitlab-ISSUE-456-update-display
```

## トラブル防止の具体的対策

### 1. commit-msgフックの導入

両リポジトリの `.git/hooks/commit-msg` に配置：

```bash
#!/bin/bash
# Gerritリポジトリ用
BRANCH=$(git symbolic-ref --short HEAD)
MSG=$(cat "$1")

# ブランチ名にgerritが含まれる場合のみチェック
if [[ $BRANCH == *"gerrit"* ]]; then
    if ! echo "$MSG" | grep -q "\[TICKET-[0-9]\+\]"; then
        echo "Error: Gerritリポジトリではコミットメッセージに[TICKET-XXX]が必要です"
        exit 1
    fi
fi

# GitLabリポジトリ用は同様にgitlab/ISSUEをチェック
```

### 2. プレコミットチェックスクリプト

`scripts/pre-commit-check.sh`:

```bash
#!/bin/bash
REPO_TYPE=""
BRANCH=$(git branch --show-current)

# リポジトリタイプを判定
if git remote -v | grep -q "gerrit"; then
    REPO_TYPE="gerrit"
elif git remote -v | grep -q "gitlab"; then
    REPO_TYPE="gitlab"
fi

echo "=== プレコミットチェック ==="
echo "リポジトリ: $REPO_TYPE"
echo "ブランチ: $BRANCH"
echo ""

# ブランチ名とリポジトリタイプの整合性チェック
if [[ $REPO_TYPE == "gerrit" ]] && [[ $BRANCH != *"gerrit"* ]]; then
    echo "⚠️  警告: Gerritリポジトリですがブランチ名にgerritが含まれていません"
    read -p "このまま続行しますか? (y/N): " confirm
    [[ $confirm != "y" ]] && exit 1
fi

# ステージングされたファイルの確認
echo "コミット対象ファイル:"
git diff --cached --name-only
echo ""
read -p "これらのファイルをコミットしますか? (y/N): " confirm
[[ $confirm != "y" ]] && exit 1
```

### 3. マージリクエスト時のテンプレート

GitLabの `.gitlab/merge_request_templates/default.md`:

```markdown
## チェックリスト（委託先記入）
- [ ] ブランチ名が `feature/gitlab-ISSUE-XXX-*` 形式
- [ ] コミットメッセージに `[ISSUE-XXX]` を含む
- [ ] Gerritリポジトリへの誤プッシュでないことを確認
- [ ] 関連するチケット番号: ISSUE-XXX

## 変更内容
（説明を記載）

## テスト結果
（テスト実施内容）
```

### 4. 委託元のレビューチェックポイント

**Gerritでのレビュー観点：**
- Change-Idが正しく付与されているか
- 1コミット1機能になっているか
- チケット番号がコミットメッセージに含まれているか

**GitLabでのレビュー観点：**
- ブランチ名が規約に従っているか
- MRに不要なコミットが含まれていないか（`git log`で確認）
- CIパイプラインが通過しているか

## 運用定着のための工夫

1. **初回セットアップスクリプトの提供**
```bash
# setup-repo.sh
#!/bin/bash
REPO_TYPE=$1  # gerrit or gitlab

if [[ -z $REPO_TYPE ]]; then
    echo "Usage: ./setup-repo.sh [gerrit|gitlab]"
    exit 1
fi

# フックのインストール
cp hooks/commit-msg-$REPO_TYPE .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg

# プレコミットチェックのエイリアス設定
git config alias.safe-commit '!bash scripts/pre-commit-check.sh && git commit'

echo "✓ $REPO_TYPE リポジトリのセットアップが完了しました"
echo "今後は 'git safe-commit' を使用してください"
```

2. **週次レビュー会での確認項目**
   - 誤コミット・誤プッシュの発生件数
   - ブランチ命名規則の遵守率
   - レビュー指摘事項の傾向分析

3. **ドキュメント整備**
   - `CONTRIBUTING.md` に両リポジトリの運用ルールを明記
   - 図解入りのフローチャートを用意（Gerrit/GitLabで色分け）

この運用により、視覚的な区別とツールによる自動チェックで、ヒューマンエラーを大幅に減らせます。特にGerritの厳密なレビューフローを基準にすることで、予期せぬコミット混入も防げます。