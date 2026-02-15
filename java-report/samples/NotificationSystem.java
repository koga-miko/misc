/**
 * オブジェクト指向の主要概念を学ぶための実践サンプル: 通知システム
 *
 * 含まれる概念:
 *   - カプセル化: NotificationRecord がフィールドを隠蔽し、状態遷移を制御
 *   - 継承:       Notifier を基底クラスとして EmailNotifier / SlackNotifier が拡張
 *   - 多態:       Notifier 型の変数で異なるサブクラスを統一的に扱う
 *   - 移譲:       NotificationService が Notifier と RetryPolicy に処理を委ねる
 *
 * 実行: java NotificationSystem.java
 */

// ============================================================
// カプセル化: 通知レコードの状態を外部から不正に操作できないようにする
// ============================================================
class NotificationRecord {
    private final String recipient;
    private final String message;
    private String status;    // "PENDING" -> "SENT" or "FAILED"
    private int attemptCount;

    NotificationRecord(String recipient, String message) {
        this.recipient = recipient;
        this.message = message;
        this.status = "PENDING";
        this.attemptCount = 0;
    }

    // 外部には読み取り専用で公開
    String getRecipient()  { return recipient; }
    String getMessage()    { return message; }
    String getStatus()     { return status; }
    int getAttemptCount()  { return attemptCount; }

    // 状態遷移は専用メソッド経由でのみ許可 — 不正な遷移を防ぐ
    void markSent() {
        if (!"PENDING".equals(status)) {
            throw new IllegalStateException("PENDING 以外から SENT には遷移できません: " + status);
        }
        this.status = "SENT";
    }

    void markFailed() {
        if (!"PENDING".equals(status)) {
            throw new IllegalStateException("PENDING 以外から FAILED には遷移できません: " + status);
        }
        this.status = "FAILED";
    }

    void incrementAttempt() {
        attemptCount++;
    }

    @Override
    public String toString() {
        return String.format("[%s] To:%s \"%s\" (試行:%d回)", status, recipient, message, attemptCount);
    }
}

// ============================================================
// 継承 + 多態: 通知手段の抽象化
// ============================================================
abstract class Notifier {
    private final String name;

    Notifier(String name) {
        this.name = name;
    }

    String getName() { return name; }

    /**
     * サブクラスが実装する送信処理。
     * 成功なら true、失敗なら false を返す。
     */
    abstract boolean send(String recipient, String message);

    // 共通のログ出力 — サブクラスから利用できるユーティリティ
    void log(String text) {
        System.out.printf("  [%s] %s%n", name, text);
    }
}

// --- 継承: Email による通知 ---
class EmailNotifier extends Notifier {
    private final String smtpServer;

    EmailNotifier(String smtpServer) {
        super("Email");
        this.smtpServer = smtpServer;
    }

    @Override
    boolean send(String recipient, String message) {
        // 実際の送信の代わりにシミュレーション
        log("SMTP(" + smtpServer + ") → " + recipient + " : " + message);
        // "@" を含まないアドレスは失敗するシミュレーション
        boolean success = recipient.contains("@");
        log(success ? "送信成功" : "送信失敗 — 不正なアドレス");
        return success;
    }
}

// --- 継承: Slack による通知 ---
class SlackNotifier extends Notifier {
    private final String webhookUrl;

    SlackNotifier(String webhookUrl) {
        super("Slack");
        this.webhookUrl = webhookUrl;
    }

    @Override
    boolean send(String recipient, String message) {
        log("Webhook(" + webhookUrl + ") → #" + recipient + " : " + message);
        // チャンネル名が "#" で始まれば成功とするシミュレーション
        boolean success = recipient.startsWith("#");
        log(success ? "投稿成功" : "投稿失敗 — チャンネル名が不正");
        return success;
    }
}

// ============================================================
// 移譲: リトライポリシーを独立したクラスとして切り出す
// ============================================================
class RetryPolicy {
    private final int maxRetries;

    RetryPolicy(int maxRetries) {
        this.maxRetries = maxRetries;
    }

    /**
     * 送信処理(action)をリトライ付きで実行する。
     * 成功したら true を返し、最大回数に達したら false を返す。
     */
    boolean execute(NotificationRecord record, java.util.function.Supplier<Boolean> action) {
        for (int i = 0; i < maxRetries; i++) {
            record.incrementAttempt();
            System.out.printf("    → 試行 %d/%d%n", record.getAttemptCount(), maxRetries);
            if (action.get()) {
                return true;
            }
        }
        return false;
    }

    @Override
    public String toString() {
        return "RetryPolicy(max=" + maxRetries + ")";
    }
}

// ============================================================
// 移譲: NotificationService は自分で送信せず Notifier と RetryPolicy に委ねる
// ============================================================
class NotificationService {
    private final Notifier notifier;         // 送信手段への移譲
    private final RetryPolicy retryPolicy;   // リトライ制御への移譲

    NotificationService(Notifier notifier, RetryPolicy retryPolicy) {
        this.notifier = notifier;
        this.retryPolicy = retryPolicy;
    }

    void send(NotificationRecord record) {
        System.out.printf("%s で送信開始 (%s)%n", notifier.getName(), retryPolicy);

        // retryPolicy に「何を繰り返すか」を渡す — 移譲の典型パターン
        boolean success = retryPolicy.execute(record,
            () -> notifier.send(record.getRecipient(), record.getMessage()));

        if (success) {
            record.markSent();
        } else {
            record.markFailed();
        }
        System.out.println("結果: " + record);
    }
}

// ============================================================
// メインクラス: 各概念の動作を確認する
// ============================================================
public class NotificationSystem {
    public static void main(String[] args) {
        System.out.println("=== オブジェクト指向 通知システム デモ ===\n");

        // --- 1. カプセル化の確認 ---
        System.out.println("■ カプセル化: NotificationRecord の状態は外から直接変更できない");
        NotificationRecord rec = new NotificationRecord("user@example.com", "こんにちは");
        System.out.println("  初期状態: " + rec);
        // rec.status = "SENT";  // ← コンパイルエラー: private フィールドに直接アクセスできない

        // --- 2. 多態の確認: 異なる Notifier を同じ型で扱う ---
        System.out.println("\n■ 多態: Notifier 型で Email と Slack を統一的に扱う");
        Notifier[] notifiers = {
            new EmailNotifier("smtp.example.com"),
            new SlackNotifier("https://hooks.slack.com/xxx")
        };
        for (Notifier n : notifiers) {
            // 実行時に各サブクラスの send() が呼ばれる = 多態
            n.send("user@example.com", "テスト");
        }

        // --- 3. 移譲の確認: NotificationService が組み立てで動作を変える ---
        System.out.println("\n■ 移譲: NotificationService は Notifier と RetryPolicy に処理を委ねる");
        RetryPolicy policy = new RetryPolicy(3);

        // 成功ケース: 正しいメールアドレス
        System.out.println("\n--- 成功ケース ---");
        NotificationRecord success = new NotificationRecord("dev@example.com", "デプロイ完了");
        NotificationService emailService = new NotificationService(new EmailNotifier("smtp.example.com"), policy);
        emailService.send(success);

        // 失敗ケース: 不正なアドレスで最大リトライまで到達
        System.out.println("\n--- 失敗ケース (リトライ上限) ---");
        NotificationRecord failure = new NotificationRecord("invalid-address", "届かない通知");
        emailService.send(failure);

        // Slack に切り替え — Notifier を差し替えるだけで動作が変わる(多態 + 移譲)
        System.out.println("\n--- Slack に切り替え ---");
        NotificationRecord slackMsg = new NotificationRecord("#general", "リリースしました");
        NotificationService slackService = new NotificationService(new SlackNotifier("https://hooks.slack.com/xxx"), policy);
        slackService.send(slackMsg);

        // --- 4. カプセル化: 不正な状態遷移の防止 ---
        System.out.println("\n■ カプセル化: 送信済みレコードを再度 markSent() すると例外");
        try {
            success.markSent(); // 既に SENT → 例外
        } catch (IllegalStateException e) {
            System.out.println("  例外捕捉: " + e.getMessage());
        }

        System.out.println("\n=== デモ終了 ===");
    }
}
