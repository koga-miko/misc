# NotificationSystem クラス図

```mermaid
classDiagram
    direction TB

    class NotificationRecord {
        -String recipient
        -String message
        -String status
        -int attemptCount
        +getRecipient() String
        +getMessage() String
        +getStatus() String
        +getAttemptCount() int
        +markSent() void
        +markFailed() void
        +incrementAttempt() void
        +toString() String
    }

    class Notifier {
        <<abstract>>
        -String name
        +getName() String
        +send(String recipient, String message) boolean*
        +log(String text) void
    }

    class EmailNotifier {
        -String smtpServer
        +send(String recipient, String message) boolean
    }

    class SlackNotifier {
        -String webhookUrl
        +send(String recipient, String message) boolean
    }

    class RetryPolicy {
        -int maxRetries
        +execute(NotificationRecord record, Supplier~Boolean~ action) boolean
        +toString() String
    }

    class NotificationService {
        -Notifier notifier
        -RetryPolicy retryPolicy
        +send(NotificationRecord record) void
    }

    class NotificationSystem {
        +main(String[] args)$ void
    }

    Notifier <|-- EmailNotifier : 継承
    Notifier <|-- SlackNotifier : 継承
    NotificationService --> Notifier : 移譲（送信）
    NotificationService --> RetryPolicy : 移譲（リトライ）
    NotificationService ..> NotificationRecord : 使用
    RetryPolicy ..> NotificationRecord : 使用
    NotificationSystem ..> NotificationService : 生成・利用
    NotificationSystem ..> NotificationRecord : 生成・利用
```

## OOP概念とクラスの対応

| 概念 | 図中の表現 |
|------|-----------|
| **カプセル化** | `NotificationRecord` の `-` (private) フィールドと `+` (package) メソッドによるアクセス制御 |
| **継承** | `Notifier <\|-- EmailNotifier / SlackNotifier` の実線矢印 |
| **多態** | `Notifier` が `<<abstract>>` で `send()` を抽象メソッドとして定義し、サブクラスが各自実装 |
| **移譲** | `NotificationService --> Notifier / RetryPolicy` の実線矢印（コンポジション） |
