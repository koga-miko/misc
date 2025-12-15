# gRPC Demo - 4つの通信方法とTLS暗号化

このプロジェクトは、gRPCの4つの通信パターンをTLS/SSL暗号化を使用して実装したデモです。

## 4つの通信パターン

1. **Unary RPC**: 単一リクエスト → 単一レスポンス
2. **Server Streaming RPC**: 単一リクエスト → ストリームレスポンス
3. **Client Streaming RPC**: ストリームリクエスト → 単一レスポンス
4. **Bidirectional Streaming RPC**: ストリームリクエスト ↔ ストリームレスポンス

## セットアップ

### 簡単セットアップ（推奨）

```bash
./setup.sh
```

このスクリプトが自動的に以下を実行します:
- 依存関係のインストール
- protoファイルからPythonコードを生成

### 手動セットアップ

#### 1. 依存関係のインストール

```bash
pip3 install -r requirements.txt
```

#### 2. protoファイルからPythonコードを生成

```bash
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. demo.proto
```

このコマンドで以下のファイルが生成されます:
- `demo_pb2.py` - メッセージクラス
- `demo_pb2_grpc.py` - サービススタブとサービサー

## 使い方

### サーバーの起動

```bash
python3 server.py
```

サーバーはポート50051でTLS/SSL暗号化を有効にして起動します。

### クライアントの実行

別のターミナルで:

```bash
python3 client.py
```

クライアントは4つの通信パターンを順番にテストします。

## TLS/SSL証明書

証明書と秘密鍵は `certs/` ディレクトリに格納されています:
- `server-cert.pem` - サーバー証明書（自己署名）
- `server-key.pem` - サーバー秘密鍵

これらは開発/テスト用の自己署名証明書です。本番環境では正式な証明書を使用してください。

## ファイル構成

```
.
├── README.md
├── requirements.txt        # Python依存関係
├── setup.sh               # セットアップスクリプト
├── demo.proto             # protoファイル定義
├── demo_pb2.py            # 生成されるメッセージクラス
├── demo_pb2_grpc.py       # 生成されるサービススタブ
├── server.py              # gRPCサーバー実装
├── client.py              # gRPCクライアント実装
└── certs/
    ├── server-cert.pem    # サーバー証明書
    └── server-key.pem     # サーバー秘密鍵
```

## 動作確認

正常に動作すると、クライアントは以下のような出力を表示します:

```
============================================================
gRPC Client with TLS - Testing 4 Communication Patterns
============================================================

[1] Testing Unary RPC
------------------------------------------------------------
✓ Response: Hello, Alice! This is a unary response.

[2] Testing Server Streaming RPC
------------------------------------------------------------
✓ Received: #1 - Server streaming message #1
✓ Received: #2 - Server streaming message #2
...

[3] Testing Client Streaming RPC
------------------------------------------------------------
  → Sending value: 10
  → Sending value: 20
  ...
✓ Response: Sum=150, Count=5

[4] Testing Bidirectional Streaming RPC
------------------------------------------------------------
  → Sending: Hello
✓ Received: Echo: Hello (seq: 1)
...
```
