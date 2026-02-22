# オブジェクト指向を学習するための実践的クラス（NotificationSystem）

## 概要

「通知システム」を題材に、オブジェクト指向の4つの主要概念（カプセル化・継承・多態（ポリモーフィズム）・移譲（コンポジション））を
1つのプログラムに統合した学習用サンプル。

実行方法: `java NotificationSystem.java`

## クラス構成

```
NotificationSystem          … メインクラス（デモ実行）
├── NotificationRecord      … 通知レコード（カプセル化）
├── Notifier (abstract)     … 通知手段の抽象基底クラス（継承・多態）
│   ├── EmailNotifier       … Email 送信（継承）
│   └── SlackNotifier       … Slack 投稿（継承）
├── RetryPolicy             … リトライ制御（移譲先）
└── NotificationService     … 通知サービス（移譲元）
```

## OOP 4つの概念とコードの対応

### 1. カプセル化 — NotificationRecord

フィールドを `private` で隠蔽し、状態遷移を専用メソッドに限定する。

```java
class NotificationRecord {
    private final String recipient;   // 外部から直接変更できない
    private String status;            // "PENDING" → "SENT" or "FAILED"

    void markSent() {                 // 状態遷移は必ずメソッド経由
        if (!"PENDING".equals(status)) {
            throw new IllegalStateException("不正な遷移");
        }
        this.status = "SENT";
    }
}
```

- フィールドは `private` で外部からのアクセスを遮断
- getter で読み取りのみ公開
- `markSent()` / `markFailed()` で状態遷移のルールを強制し、不正な操作を例外で防止

### 2. 継承 — Notifier → EmailNotifier / SlackNotifier

共通の振る舞いを基底クラスにまとめ、サブクラスで固有の処理を実装する。

```java
abstract class Notifier {
    private final String name;
    abstract boolean send(String recipient, String message);  // サブクラスが実装
    void log(String text) { /* 共通処理 */ }                  // 再利用
}

class EmailNotifier extends Notifier {
    @Override
    boolean send(String recipient, String message) {
        // Email 固有の送信ロジック
    }
}
```

- `Notifier` が `name` フィールドと `log()` メソッドを提供（共通部分の再利用）
- `send()` を抽象メソッドとして定義し、各サブクラスに実装を強制

### 3. 多態（ポリモーフィズム） — Notifier 型で統一的に扱う

異なるサブクラスのインスタンスを同じ型の変数で扱い、実行時に適切なメソッドが呼ばれる。

```java
Notifier[] notifiers = {
    new EmailNotifier("smtp.example.com"),
    new SlackNotifier("https://hooks.slack.com/xxx")
};
for (Notifier n : notifiers) {
    n.send("user@example.com", "テスト");  // 実行時にサブクラスの send() が呼ばれる
}
```

- 呼び出し側は `Notifier` 型だけを知っていればよい
- 新しい通知手段を追加しても、呼び出し側のコードを変更する必要がない

### 4. 移譲（コンポジション） — NotificationService → Notifier + RetryPolicy

自クラスで処理を実装せず、専門のオブジェクトに処理を委ねる。

```java
class NotificationService {
    private final Notifier notifier;       // 送信処理を移譲
    private final RetryPolicy retryPolicy; // リトライ制御を移譲

    void send(NotificationRecord record) {
        boolean success = retryPolicy.execute(record,
            () -> notifier.send(record.getRecipient(), record.getMessage()));
        // ...
    }
}
```

- `NotificationService` は「何で送るか」「何回リトライするか」を自分で決めない
- コンストラクタで注入されたオブジェクトに判断を委ねる（依存性の注入）
- `Notifier` を差し替えるだけで Email → Slack に切り替え可能（多態との連携）

## デモの実行フロー

| ステップ | 確認する概念 | 内容 |
|---------|------------|------|
| 1 | カプセル化 | `NotificationRecord` の状態が外部から直接変更できないことを確認 |
| 2 | 多態 | `EmailNotifier` と `SlackNotifier` を `Notifier[]` で統一的に扱い送信 |
| 3 | 移譲 | `NotificationService` に `Notifier` と `RetryPolicy` を注入し、成功・失敗・切り替えの各ケースを実行 |
| 4 | カプセル化 | 送信済みレコードに再度 `markSent()` を呼ぶと `IllegalStateException` が発生 |

## クラス図

詳細なクラス図は [ClassDiagram_for_NotificationSystem.md](ClassDiagram_for_NotificationSystem.md) を参照。

## 関連ファイル

- [NotificationSystem.java](NotificationSystem.java) — ソースコード
- [ClassDiagram_for_NotificationSystem.md](ClassDiagram_for_NotificationSystem.md) — Mermaid クラス図
