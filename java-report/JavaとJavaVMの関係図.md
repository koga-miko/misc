# JavaとJavaVMの関係図

```mermaid
graph TB
    subgraph "アプリケーション層"
        JAVA["Java Application<br/>(ソースコード)<br/>HelloWorld.java"]
    end
    
    subgraph "コンパイル"
        COMPILER["Java Compiler<br/>(javac)"]
    end
    
    subgraph "バイトコード"
        BYTECODE["Java Bytecode<br/>(機械語ではない)<br/>HelloWorld.class"]
    end
    
    subgraph "実行環境"
        subgraph "Java Virtual Machine"
            CLASS_LOADER["Class Loader<br/>(クラスの読み込み)"]
            BYTECODE_VERIFIER["Bytecode Verifier<br/>(バイトコード検証)"]
            EXECUTION_ENGINE["Execution Engine<br/>(実行)"]
            GC["Garbage Collector<br/>(メモリ管理)"]
        end
    end
    
    subgraph "OS層"
        OS["Operating System<br/>(Windows/Linux/macOS)"]
    end
    
    subgraph "ハードウェア"
        HARDWARE["CPU・メモリ・ストレージ"]
    end
    
    JAVA -->|javac| COMPILER
    COMPILER -->|生成| BYTECODE
    BYTECODE -->|読み込み| CLASS_LOADER
    CLASS_LOADER -->|検証| BYTECODE_VERIFIER
    BYTECODE_VERIFIER -->|実行| EXECUTION_ENGINE
    EXECUTION_ENGINE -->|管理| GC
    
    EXECUTION_ENGINE -->|システムコール| OS
    OS -->|制御| HARDWARE
    
    style JAVA fill:#e1f5ff
    style COMPILER fill:#fff3e0
    style BYTECODE fill:#f3e5f5
    style CLASS_LOADER fill:#e8f5e9
    style EXECUTION_ENGINE fill:#e8f5e9
    style GC fill:#e8f5e9
    style OS fill:#fce4ec
    style HARDWARE fill:#f1f8e9
```

## JavaVMの特徴

### 1. **プラットフォーム独立性（Write Once, Run Anywhere）**
```mermaid
graph LR
    JAVA["Java<br/>ソースコード"]
    BYTECODE["JavaBytecode<br/>(.class)"]
    
    BYTECODE -->|Windows上のJVM| WIN["Windows<br/>実行"]
    BYTECODE -->|Linux上のJVM| LINUX["Linux<br/>実行"]
    BYTECODE -->|macOS上のJVM| MAC["macOS<br/>実行"]
    
    JAVA -->|一度コンパイル| BYTECODE
    
    style JAVA fill:#e1f5ff
    style BYTECODE fill:#f3e5f5
    style WIN fill:#fce4ec
    style LINUX fill:#fce4ec
    style MAC fill:#fce4ec
```

### 2. **JVMのメモリ構造**
```mermaid
graph TB
    JVM["Java Virtual Machine"]
    
    subgraph "メモリ領域"
        HEAP["ヒープ<br/>(オブジェクト格納)<br/>動的に確保"]
        STACK["スタック<br/>(ローカル変数)<br/>メソッド呼び出し]"]
        METHOD_AREA["メソッド領域<br/>(クラス情報)<br/>静的変数"]
    end
    
    GC["自動ガベージコレクション<br/>(使用されないオブジェクトを削除)"]
    
    JVM --> HEAP
    JVM --> STACK
    JVM --> METHOD_AREA
    HEAP --> GC
    
    style JVM fill:#fff3e0
    style HEAP fill:#e8f5e9
    style STACK fill:#e8f5e9
    style METHOD_AREA fill:#e8f5e9
    style GC fill:#ffebee
```

### 3. **バイトコード実行フロー**
```mermaid
sequenceDiagram
    participant Java as Javaプログラム
    participant ClassLoader as ClassLoader
    participant Verifier as BytecodeVerifier
    participant Engine as ExecutionEngine
    participant OS as OS/Hardware
    
    Java->>ClassLoader: .classファイル読み込み
    ClassLoader->>Verifier: バイトコード検証
    Verifier->>Engine: セキュリティチェック完了
    Engine->>Engine: JIT/インタプリタで実行
    Engine->>OS: ネイティブコール
    OS->>OS: CPU実行
    OS-->>Engine: 結果返却
```

## JVMの2つの実行方式

```mermaid
graph TB
    BYTECODE["バイトコード<br/>(.class ファイル)"]
    
    subgraph "インタプリタ方式"
        INTERP["1命令ずつ読む<br/>→実行<br/>→読む<br/>→実行..."]
        INTERP_CHAR["特徴:<br/>- 遅い<br/>- メモリ効率的<br/>- 起動時間短い"]
    end
    
    subgraph "JIT（Just-In-Time）コンパイル"
        JIT["頻繁に実行される<br/>コード部分を<br/>ネイティブコードに<br/>コンパイル"]
        JIT_CHAR["特徴:<br/>- 高速実行<br/>- メモリ多く使用<br/>- 実行中に最適化"]
    end
    
    subgraph "AOT（Ahead-Of-Time）コンパイル"
        AOT["実行前に<br/>すべてをネイティブコードに<br/>コンパイル"]
        AOT_CHAR["特徴:<br/>- 最速<br/>- 起動時間長い<br/>- GraalVM Native Image"]
    end
    
    BYTECODE --> INTERP
    BYTECODE --> JIT
    BYTECODE --> AOT
    
    INTERP --> INTERP_CHAR
    JIT --> JIT_CHAR
    AOT --> AOT_CHAR
    
    style BYTECODE fill:#e1f5ff
    style INTERP fill:#fff3e0
    style JIT fill:#e8f5e9
    style AOT fill:#f3e5f5
```

## 実際のJVM動作フロー

```mermaid
sequenceDiagram
    participant App as Javaアプリ開始
    participant CL as ClassLoader
    participant Exec as ExecutionEngine
    participant JIT as JITコンパイラ
    participant CPU as CPU
    
    App->>CL: 必要なクラスを読み込み
    Note over CL: 全クラスを一気にロードするのではなく<br/>必要になったときだけロード（遅延ロード）
    
    CL->>Exec: 最初はインタプリタで実行
    Exec->>CPU: バイトコード命令1を解釈して実行
    Exec->>CPU: バイトコード命令2を解釈して実行
    Note over Exec: ループ内の処理など<br/>頻繁に実行される部分を検出
    
    rect rgb(100, 200, 100)
        Note over JIT: ホットスポット検出！<br/>このコード部分は何度も実行されている
        Exec->>JIT: このメソッドをJIT対象にマーク
        JIT->>JIT: バイトコード → ネイティブコード変換
        JIT->>Exec: 最適化されたネイティブコード
    end
    
    Exec->>CPU: 以降はネイティブコードで高速実行
    Note over Exec: 2回目以降は<br/>インタプリタを経由しない
```

## 具体例

```
【実行例：ループ処理】

int sum = 0;
for (int i = 0; i < 1000000; i++) {
    sum += i;  // ← この部分が何度も実行される
}

【実行の流れ】
1回目〜数百回: インタプリタで実行（遅い）
          ↓
    ホットスポット検出（この部分は頻繁に実行される）
          ↓
JIT: このループをネイティブコードにコンパイル
          ↓
数百回目以降: ネイティブコードで実行（高速）
```

## 答え：**段階的実行**

1. **クラスロード** - 必要なクラスだけ読み込み（遅延ロード）
2. **初期実行** - インタプリタで命令を逐一読んで実行
3. **ホットスポット検出** - 何度も実行される部分を検出
4. **JIT最適化** - そこをネイティブコードに変換
5. **高速実行** - 以降はネイティブコードで実行

**すべてロードされるわけではなく、すべてJITコンパイルされるわけでもなく、実行パターンに応じて動的に最適化される**のが現代JVMの特徴です。
